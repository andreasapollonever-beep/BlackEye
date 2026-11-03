"""Berlin wall (soldier pile wall with timber lagging) — EN 1997-1, EN 1993-1-1, EN 1995-1-1,
EN 1998-5.

Coordinate z is the depth below the top of the wall (ground level behind),
H the excavation depth, t the embedment below the excavation level.  All
loads are per pile (N/mm along the pile) unless stated per metre.

Method (EAB / Weissenbach practice, CALTRANS Trenching & Shoring Manual):

* above the excavation level the lagging transfers the active pressure of the
  full pile spacing ``a`` to each pile;
* below the excavation level the active pressure acts on the pile width ``b``
  only (EAB R 15) and the passive resistance on an effective width
  ``f·b ≤ a`` with ``f = 0.08 φ' ≤ 3`` (spatial / arching effect);
* cantilever walls: Blum's method, rotation about the toe, ``t = 1.2 t₀``;
* single anchor row: free earth support, moments about the anchor, ``t = t₀``.
"""

from __future__ import annotations

import math

import numpy as np

from ..analysis import UDL, Beam, Support
from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..design.geotech import k_mononobe_okabe, ka_coulomb, kp_coulomb, kp_seismic
from ..design.walls import APPROACHES, COMBOS
from ..report.scene3d import PALETTE, Scene3D
from ..report.svg import vertical_diagrams
from ..sections.steel import get_section, section_names

GRADES = {"S235": 235.0, "S275": 275.0, "S355": 355.0}
E_STEEL = 210000.0
HINT_EMBED = ("Increase the embedment depth of the piles, use a closer pile spacing or add "
              "(another) anchor row.")
HINT_PILE = "Choose a heavier pile section (e.g. next HEB size), reduce the pile spacing or add an anchor."
HINT_LAG = "Use thicker lagging boards or reduce the pile spacing."
HINT_ANCHOR = ("Use anchors with a higher design resistance (longer grout body / larger tendon) "
               "or reduce the pile spacing.")


@register
class BerlinWallEC7(DesignModule):
    id = "ec7_berlin_wall"
    title = "Berlin wall (soldier pile wall)"
    category = "Geotechnical"
    standard = "EN 1997-1, EN 1993-1-1, EN 1995-1-1, EN 1998-5"
    description = ("Steel soldier piles with timber lagging, cantilever or with one anchor row: "
                   "active/passive earth pressure with spatial passive resistance, embedment "
                   "(Blum / free earth support), pile bending and shear (EC3), lagging (EC5), "
                   "anchor force, seismic case and indicative deflection. Interactive 3D model.")

    fields = [
        Field("H", "Excavation depth H", "m", 5.0, min=1, max=15, group="Geometry"),
        Field("a", "Pile spacing a (centre to centre)", "m", 2.0, min=0.5, max=4,
              group="Geometry", help="Typical 1.5–3.0 m."),
        Field("t", "Provided embedment below excavation t", "m", 3.5, min=0.5,
              group="Geometry"),
        Field("support", "Support system", kind="choice",
              choices=["Cantilever", "Single anchor row"], default="Single anchor row",
              group="Geometry"),
        Field("z_a", "Anchor depth below top", "m", 1.5, min=0.3, group="Anchors"),
        Field("alpha", "Anchor inclination below horizontal", "°", 20.0, min=0, max=45,
              group="Anchors"),
        Field("R_ad", "Anchor design resistance R_a,d (per anchor)", "kN", 450.0, min=1,
              group="Anchors", help="From anchor design / suitability tests (EN 1997-1 §8)."),
        Field("n_view", "Number of piles shown in 3D", kind="int", default=6, min=2, max=12,
              group="Geometry"),
        Field("section", "Pile section", kind="choice", choices=section_names(),
              default="HEB 240", group="Soldier piles"),
        Field("grade", "Steel grade", kind="choice", choices=list(GRADES), default="S355",
              group="Soldier piles"),
        Field("t_lag", "Lagging board thickness", "mm", 80.0, min=30, max=200, group="Lagging"),
        Field("lag_red", "Lagging pressure factor (arching)", "", 0.6, min=0.3, max=1.0,
              group="Lagging",
              help="Arching reduces the pressure on the boards: ~0.6 in competent soils, "
                   "1.0 in soft clay or loose sand."),
        Field("phi", "Soil φ'k", "°", 32.0, min=20, max=45, group="Soil"),
        Field("c", "Soil c'k", "kN/m²", 0.0, min=0, group="Soil"),
        Field("gamma", "Soil γ", "kN/m³", 19.0, min=10, group="Soil"),
        Field("delta_a", "Active wall friction δa/φ'", "", 0.667, min=0, max=0.667,
              group="Soil"),
        Field("delta_p", "Passive wall friction δp/φ'", "", 0.333, min=0, max=0.5,
              group="Soil", help="Keep ≤ 0.5: Coulomb overestimates passive resistance."),
        Field("q", "Surcharge behind the wall (variable)", "kN/m²", 10.0, min=0, group="Soil"),
        Field("approach", "Design approach", kind="choice", choices=list(APPROACHES),
              default="DA1", group="Design basis"),
        Field("seismic", "Include seismic design (EN 1998-5)", kind="bool", default=True,
              group="Seismic"),
        Field("ag", "Design ground acceleration αgR·γI", "", 0.16, min=0, max=0.6,
              group="Seismic", help="In g. Greece: Zone I 0.16, Zone II 0.24, Zone III 0.36."),
        Field("S", "Soil factor S", "", 1.2, min=1.0, max=1.8, group="Seismic"),
        Field("r", "Displacement factor r", kind="choice", choices=["1.0", "1.5", "2.0"],
              default="1.0", group="Seismic",
              help="EN 1998-5 Table 7.1: use 1.0 for anchored / propped walls."),
        Field("psi2", "ψ2 for surcharge", "", 0.3, min=0, max=1, group="Seismic"),
    ]

    # ===================================================================== run
    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        H, a, t_prov = inp["H"], inp["a"], inp["t"]
        anchored = inp["support"] == "Single anchor row"
        zA = inp["z_a"]
        if anchored and zA >= H:
            raise InputError("The anchor must be above the excavation level", "z_a")
        sec = get_section(inp["section"])
        b = sec.b
        if b >= a:
            raise InputError("Pile spacing must be larger than the pile width", "a")
        fy = GRADES[inp["grade"]] if sec.tf <= 40 else GRADES[inp["grade"]] - 20
        phik = math.radians(inp["phi"])
        f_arch = min(0.08 * inp["phi"], 3.0)
        b_p = min(f_arch * b, a)

        calc.heading("Geometry and soil")
        calc.input("H", H, "m", "Excavation depth")
        calc.input("a", a, "m", "Pile spacing")
        calc.label("Pile section", f"{sec.name} {inp['grade']}", "Soldier piles")
        calc.input("b", b, "mm", "Pile (flange) width")
        calc.label("Support", inp["support"], "Support system")
        if anchored:
            calc.input("z_A", zA, "m", "Anchor depth below top")
        calc.input("φ'_k", inp["phi"], "°", "Angle of shearing resistance")
        calc.input("c'_k", inp["c"], "kN/m²", "Effective cohesion")
        calc.input("γ", inp["gamma"], "kN/m³", "Unit weight")
        calc.input("q_k", inp["q"], "kN/m²", "Surcharge behind the wall")
        fig_index = len(calc.items)
        calc.heading("Method")
        calc.text("Above the excavation level the lagging transfers the active pressure of the "
                  "full pile spacing a to each pile. Below the excavation level the active "
                  "pressure acts on the pile width b (EAB R 15) and the passive resistance on "
                  "an effective width b_p = f·b ≤ a, f = 0.08φ' ≤ 3 (spatial effect of single "
                  "piles).")
        calc.formula("f", "0.08 φ'_k ≤ 3.0", f_arch, "", "Arching (spatial) factor",
                     ref="CALTRANS T&S 5.6", dp=2)
        calc.formula("b_p", "min(f b, a)", b_p, "mm", "Effective width for passive resistance")
        calc.text("Embedment: Blum's method for cantilevers (t = 1.2 t₀, rotation about the "
                  "toe); free earth support for a single anchor row (moment equilibrium about "
                  "the anchor, t = t₀).")
        calc.note("Berlin walls are not watertight: the groundwater must be lowered below the "
                  "excavation level (not modelled here).")

        combos = []
        for name in APPROACHES[inp["approach"]]:
            gu, gf, gq, gphi, gc, _, _ = COMBOS[name]
            gRe = 1.4 if name == "DA2" else 1.0
            combos.append({"name": name, "gG": gu, "gQ": gq, "gphi": gphi, "gc": gc,
                           "gRe": gRe, "seis": None})
        if inp["seismic"] and inp["ag"] > 0:
            kh = inp["ag"] * inp["S"] / float(inp["r"])
            for sgn in (1, -1):
                combos.append({"name": calc.tr("Seismic"), "gG": 1.0, "gQ": inp["psi2"],
                               "gphi": 1.25, "gc": 1.25, "gRe": 1.0,
                               "seis": (kh, 0.5 * kh * sgn)})

        results = []
        for cb in combos:
            results.append(cls._combination(calc, inp, cb, anchored, b, b_p, phik))
        # keep only the worse of the two seismic signs in the report
        seis = [r for r in results if r["cb"]["seis"]]
        if len(seis) == 2:
            drop = min(seis, key=lambda r: r["t_req"])
            results.remove(drop)
        for r in results:
            cls._report_combination(calc, inp, r, anchored, t_prov)

        gov_t = max(results, key=lambda r: r["t_req"])
        gov_M = max(results, key=lambda r: r["M"])

        # ----------------------------------------------------------- pile
        calc.heading("Soldier pile — EN 1993-1-1")
        calc.text("The design forces are the largest of all combinations (governing: "
                  "**{name}**). The lagging restrains the pile laterally, so lateral-torsional "
                  "buckling is not relevant.", name=gov_M["cb"]["name"])
        MEd = calc.formula("M_Ed", "max |M(z)|", gov_M["M"], "kNm", "Maximum design moment")
        VEd = calc.formula("V_Ed", "max |V(z)|", max(r["V"] for r in results), "kN",
                           "Maximum design shear")
        eps = math.sqrt(235 / fy)
        cf = (sec.b - sec.tw - 2 * sec.r) / 2 / sec.tf
        cw = sec.d / sec.tw
        cls_ = max(1 if cf <= 9 * eps else 2 if cf <= 10 * eps else 3,
                   1 if cw <= 72 * eps else 2 if cw <= 83 * eps else 3)
        Wy = sec.Wpl_y if cls_ <= 2 else sec.Wel_y
        calc.text("Section class {n} (flange c/t = {cf:.1f}, web c/t = {cw:.1f}).", n=cls_,
                  cf=cf, cw=cw)
        McRd = calc.formula("M_c,Rd", "W_y f_y / γ_M0", Wy * fy, "kNm", ref="6.2.5")
        VplRd = calc.formula("V_pl,Rd", "A_v f_y / (√3 γ_M0)", sec.Av_z * fy / math.sqrt(3), "kN",
                             ref="6.2.6")
        if VEd > 0.5 * VplRd:
            rho = (2 * VEd / VplRd - 1) ** 2
            McRd = calc.formula("M_v,Rd", "(W_pl − ρA_w²/(4t_w)) f_y", (sec.Wpl_y - rho *
                                (sec.hw * sec.tw) ** 2 / (4 * sec.tw)) * fy, "kNm", ref="6.2.8")
        calc.check("Pile bending: M_Ed ≤ M_c,Rd", MEd, McRd, "kNm", "EN 1993-1-1 6.2.5",
                   hint=HINT_PILE)
        calc.check("Pile shear: V_Ed ≤ V_pl,Rd", VEd, VplRd, "kN", "EN 1993-1-1 6.2.6",
                   hint=HINT_PILE)

        # -------------------------------------------------------- embedment
        calc.heading("Embedment depth")
        calc.formula("t_req", "max over combinations", gov_t["t_req"], "m",
                     calc.tr("Required embedment (governing: {name})", name=gov_t["cb"]["name"]))
        calc.input("t_prov", t_prov, "m", "Provided embedment")
        calc.check_min("Embedment: t_prov ≥ t_req", t_prov, gov_t["t_req"], "m",
                       "EN 1997-1 9.7.4", hint=HINT_EMBED)

        # ----------------------------------------------------------- anchor
        if anchored:
            calc.heading("Anchor")
            Ah = max(r["A"] for r in results)
            calc.formula("A_h,d", "Σ E_a,d − Σ E_p,d (per pile)", Ah, "kN",
                         "Horizontal anchor force per pile")
            Ad = calc.formula("A_d", "A_h,d / cos α", Ah / math.cos(math.radians(inp["alpha"])),
                              "kN", "Design anchor force (one anchor per pile)")
            calc.input("R_a,d", inp["R_ad"], "kN", "Anchor design resistance")
            calc.check("Anchor: A_d ≤ R_a,d", Ad, inp["R_ad"], "kN", "EN 1997-1 8.5",
                       hint=HINT_ANCHOR)
            calc.formula("V_A", "A_d sin α", Ad * math.sin(math.radians(inp["alpha"])), "kN",
                         "Vertical component carried by the pile into the ground (check pile "
                         "base / skin friction)")

        # ---------------------------------------------------------- lagging
        cls._lagging(calc, inp, a, b, results)

        # -------------------------------------------------------- deflection
        calc.heading("Deflection (indicative)")
        char = cls._combination(calc, inp, {"name": "char", "gG": 1.0, "gQ": 1.0, "gphi": 1.0,
                                            "gc": 1.0, "gRe": 1.0, "seis": None},
                                anchored, b, b_p, phik, need_beam=True, EI=E_STEEL * sec.Iy)
        d_top = calc.formula("δ_top", "beam model, characteristic loads", abs(char["d_top"]), "mm",
                             "Horizontal displacement at the top of the pile")
        calc.note("Limit-equilibrium beam model (pile supported at the anchor and at the "
                  "theoretical toe, characteristic pressures). Real displacements depend on "
                  "soil stiffness — use a subgrade-reaction or FE analysis where movements "
                  "matter.")
        calc.text("Ratio δ_top / H = 1/{n:.0f}.", n=H / max(d_top, 1e-6))

        # ---------------------------------------------------------- figures
        design = cls._combination(calc, inp, gov_M["cb"], anchored, b, b_p, phik,
                                  need_beam=True, EI=E_STEEL * sec.Iy)
        calc.figure(vertical_diagrams(
            design["zg"] / 1000, H / 1000, t_prov / 1000,
            [(calc.tr("Pressure per pile [kN/m]"), design["fa"] - design["fp"], "#c47a2c"),
             (calc.tr("Shear V [kN]"), design["Vz"] / 1e3, "#2a6f97"),
             (calc.tr("Moment M [kNm]"), design["Mz"] / 1e6, "#c0392b"),
             (calc.tr("Deflection δ [mm] (char.)"), np.interp(design["zg"], char["zg"],
                                                             char["dz"]), "#2e8b57")],
            zA / 1000 if anchored else None),
            calc.tr("Design net pressure, shear and moment along the pile ({name}) and "
                    "characteristic deflection", name=gov_M["cb"]["name"]))
        calc.items.insert(fig_index, calc.items.pop())
        calc.model3d = cls._scene(calc, inp, sec, anchored, design, char, gov_t, gov_M,
                                  results)

    # ================================================================ engine
    @staticmethod
    def _coeffs(inp, cb, phik):
        phid = math.atan(math.tan(phik) / cb["gphi"])
        cd = inp["c"] / cb["gc"]
        da, dp = inp["delta_a"] * phid, inp["delta_p"] * phid
        Ka = ka_coulomb(phid, 0.0, da)
        Kah = Ka * math.cos(da)
        Kph = kp_coulomb(phid, dp) * math.cos(dp)
        Kmin = ka_coulomb(math.radians(40), 0.0, math.radians(40) * 2 / 3) * math.cos(
            math.radians(40) * 2 / 3)
        out = {"phid": phid, "cd": cd, "Kah": Kah, "Kph": Kph, "Kmin": Kmin, "dE": 0.0}
        if cb["seis"]:
            kh, kv = cb["seis"]
            theta = math.atan(kh / (1 + kv))
            Kae = k_mononobe_okabe(phid, 0.0, da, theta) * math.cos(da)
            out.update({"Kae": Kae, "Kph": kp_seismic(phid, theta) * (1 + kv),
                        "theta": theta, "kv": kv})
            out["dE"] = 0.5 * inp["gamma"] * inp["H"] * ((1 + kv) * Kae - Kah)
        return out

    @classmethod
    def _pressures(cls, inp, cb, k, zg, b, b_p):
        """Design active (per pile) and passive (per pile) line loads at depths zg."""
        H, a, g, q = inp["H"], inp["a"], inp["gamma"], inp["q"]
        eG = np.maximum(k["Kah"] * g * zg - 2 * k["cd"] * math.sqrt(k["Kah"]), k["Kmin"] * g * zg)
        Kq = k.get("Kae", k["Kah"]) if cb["seis"] else k["Kah"]
        eQ = Kq * q * np.ones_like(zg)
        e = cb["gG"] * eG + cb["gQ"] * eQ
        if cb["seis"]:
            e = e + np.where(zg <= H, max(k["dE"], 0.0), 0.0)
        width = np.where(zg <= H, a, b)
        fa = e * width
        zp = np.maximum(zg - H, 0.0)
        ep = (k["Kph"] * g * zp + 2 * k["cd"] * math.sqrt(k["Kph"])) * (zg > H)
        fp = ep * b_p / cb["gRe"]
        return fa, fp, e, ep / cb["gRe"]

    @classmethod
    def _combination(cls, calc, inp, cb, anchored, b, b_p, phik, need_beam=True, EI=None):
        H = inp["H"]
        zA = inp["z_a"]
        k = cls._coeffs(inp, cb, phik)

        def moment(t):
            zg = np.linspace(0, H + t, 1200)
            fa, fp, _, _ = cls._pressures(inp, cb, k, zg, b, b_p)
            piv = zA if anchored else H + t
            arm = (zg - piv) if anchored else (piv - zg)
            return np.trapezoid((fa - fp) * arm, zg)

        lo, hi = 1.0, 6 * H
        if moment(hi) > 0:
            t0 = float("inf")
        else:
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if moment(mid) > 0:
                    lo = mid
                else:
                    hi = mid
            t0 = 0.5 * (lo + hi)
        res = {"cb": cb, "k": k, "t0": t0,
               "t_req": t0 * (1.0 if anchored else 1.2), "A": 0.0, "M": float("inf"),
               "V": float("inf"), "d_top": 0.0}
        if not math.isfinite(t0):
            return res
        zg = np.linspace(0, H + t0, 1200)
        fa, fp, e, ep = cls._pressures(inp, cb, k, zg, b, b_p)
        res.update({"zg": zg, "fa": fa, "fp": fp, "e": e, "ep": ep})
        if anchored:
            res["A"] = max(float(np.trapezoid(fa - fp, zg)), 0.0)
        # beam model (pile as a beam along depth, net load towards the excavation)
        if need_beam:
            n = 80
            edges = np.linspace(0, H + t0, n + 1)
            net = np.interp(0.5 * (edges[1:] + edges[:-1]), zg, fa - fp)
            sup = [Support(zA, "pinned"), Support(H + t0, "pinned")] if anchored else \
                [Support(H + t0, "fixed")]
            beam = Beam(H + t0, EI or E_STEEL * 1e8, 1.0, sup,
                        udls=[UDL(x1, x2, w) for x1, x2, w in zip(edges[:-1], edges[1:], net)
                              if abs(w) > 0])
            r = beam.solve()
            res["M"] = float(np.max(np.abs(r.moment)))
            res["V"] = float(np.max(np.abs(r.shear)))
            res["Mz"] = np.interp(zg, r.x, r.moment)
            res["Vz"] = np.interp(zg, r.x, r.shear)
            res["dz"] = np.interp(zg, r.xd, r.deflection)
            res["d_top"] = float(r.deflection[0])
        return res

    @staticmethod
    def _report_combination(calc, inp, r, anchored, t_prov) -> None:
        cb, k = r["cb"], r["k"]
        title = cb["name"] if not cb["seis"] else calc.tr("Seismic")
        calc.heading(calc.tr("Earth pressure and embedment — {name}", name=title))
        if cb["seis"]:
            kh, kv = cb["seis"]
            calc.formula("k_h", "α S / r", kh, "", ref="EN 1998-5 Eq. 7.1", dp=4)
            calc.formula("k_v", "±0.5 k_h (governing sign)", kv, "", dp=4)
            calc.formula("θ", "atan(k_h / (1 ± k_v))", math.degrees(k["theta"]), "°", dp=2)
            calc.formula("K_ae,h", "Mononobe-Okabe (Eq. E.2) × cos δ_a", k["Kae"], "",
                         ref="EN 1998-5 E.4", dp=4)
            calc.formula("Δe_ae", "½ γ H ((1 ± k_v) K_ae,h − K_ah)", k["dE"], "kN/m²",
                         "Dynamic increment, uniform over the retained height", dp=2)
        else:
            calc.text("γ_G = {g}, γ_Q = {q}, γ_φ' = {p}, γ_Re = {re} (passive resistance).",
                      g=cb["gG"], q=cb["gQ"], p=cb["gphi"], re=cb["gRe"])
        calc.formula("φ'_d", "atan(tan φ'_k / γ_φ')", math.degrees(k["phid"]), "°", dp=2)
        calc.formula("K_ah", "Coulomb, δ_a, × cos δ_a", k["Kah"], "", ref="EN 1997-1 Annex C",
                     dp=4)
        calc.formula("K_ph", "Coulomb, δ_p, × cos δ_p" if not cb["seis"] else
                     "EN 1998-5 Eq. E.4 × (1 ± k_v)", k["Kph"], "", dp=3)
        if not math.isfinite(r["t0"]):
            calc.warn("No equilibrium found — passive resistance is insufficient even for a "
                      "very deep embedment.")
            calc.check(calc.tr("{name}: equilibrium of the wall", name=title), 1.0, 0.0, "",
                       "EN 1997-1 9.7", hint=HINT_EMBED)
            return
        calc.formula("t_0", "Σ M_pivot(E_a,d) = Σ M_pivot(E_p,d)", r["t0"], "m",
                     "Theoretical embedment (moment equilibrium)")
        calc.formula("t_req", "t_0" if anchored else "1.2 t_0", r["t_req"], "m",
                     "Required embedment")
        if anchored:
            calc.formula("A_h", "Σ E_a,d − Σ E_p,d", r["A"], "kN", "Horizontal anchor force per pile")
        calc.formula("M_max", "beam model", r["M"], "kNm", "Maximum moment in the pile")
        calc.check_min(calc.tr("{name}: t_prov ≥ t_req", name=title), t_prov, r["t_req"], "m",
                       "EN 1997-1 9.7.4", hint=HINT_EMBED)

    @staticmethod
    def _lagging(calc, inp, a, b, results) -> None:
        calc.heading("Timber lagging — EN 1995-1-1 (C24)")
        H = inp["H"]
        e_max = max(float(np.interp(H, r["zg"], r["e"])) for r in results if "zg" in r)
        lam = inp["lag_red"]
        p = calc.formula("p_d", "λ e_ah,d(z = H)", lam * e_max, "kN/m²",
                         "Design pressure on the boards at the excavation level (arching factor λ)")
        L = calc.formula("l", "a − b", a - b, "m", "Clear span of the boards")
        M = p * L**2 / 8  # per mm height
        calc.formula("m_Ed", "p_d l² / 8", M, "kNm/m", "Bending moment per metre height")
        fmd = calc.formula("f_m,d", "k_mod f_m,k / γ_M = 0.9 × 24 / 1.3", 0.9 * 24 / 1.3, "N/mm²",
                           ref="EN 1995-1-1 2.4.1")
        fvd = 0.67 * 0.9 * 4.0 / 1.3
        t_req_b = math.sqrt(6 * M / fmd)
        t_req_v = 1.5 * (p * L / 2) / fvd
        t_req = calc.formula("t_lag,req", "max(√(6 m_Ed / f_m,d), 1.5 v_Ed / f_v,d)",
                             max(t_req_b, t_req_v), "mm", "Required board thickness")
        calc.check_min("Lagging: t_prov ≥ t_req", inp["t_lag"], t_req, "mm", "EN 1995-1-1 6.1",
                       hint=HINT_LAG)

    # ---------------------------------------------------------------- 3D
    @staticmethod
    def _scene(calc, inp, sec, anchored, design, char, gov_t, gov_M, results) -> dict:
        m = lambda v: v / 1000.0  # noqa: E731
        H, a, t = m(inp["H"]), m(inp["a"]), m(inp["t"])
        hs, bs, tf, tw = m(sec.h), m(sec.b), m(sec.tf), m(sec.tw)
        n = inp["n_view"]
        L = (n - 1) * a
        zs = [-L / 2 + i * a for i in range(n)]
        sc = Scene3D("berlin_wall", calc.tr)
        for key, label in (("steel", "Soldier piles"), ("lagging", "Timber lagging"),
                           ("anchors", "Anchors"), ("soil", "Soil"), ("active", "Active pressure"),
                           ("passive", "Passive resistance"), ("moment", "Bending moment"),
                           ("deflection", "Deflected shape (exaggerated)"), ("dims", "Dimensions")):
            sc.layer(key, label, toggle=key != "steel")
        depth = H + t
        for z in zs:
            yc = -depth / 2
            sc.box("steel", (tf / 2, yc, z), (tf, depth, bs), PALETTE["steel"])
            sc.box("steel", (hs - tf / 2, yc, z), (tf, depth, bs), PALETTE["steel"])
            sc.box("steel", (hs / 2, yc, z), (hs - 2 * tf, depth, tw), PALETTE["steel"])
        tl = m(inp["t_lag"])
        nb = max(int(H / 0.22), 1)
        hb = H / nb
        for z1, z2 in zip(zs[:-1], zs[1:]):
            for i in range(nb):
                y = -(i + 0.5) * hb
                sc.box("lagging", (tf + tl / 2, y, (z1 + z2) / 2), (tl, hb - 0.025, z2 - z1 - tw),
                       "#a0703c", edges=False)
        W = L + 4
        back = max(2 * H, 6.0)
        sc.box("soil", (hs + back / 2, -(depth + 1) / 2, 0), (back, depth + 1, W), PALETTE["soil"],
               opacity=0.18, edges=False)
        sc.box("soil", (-back / 2, -H - (t + 1) / 2, 0), (back, t + 1, W), PALETTE["soil2"],
               opacity=0.28, edges=False)
        if inp["q"] > 0:
            sc.box("soil", (hs + 2.5, 0.03, 0), (4.0, 0.06, W * 0.8), PALETTE["surcharge"],
                   opacity=0.5)
        if anchored:
            al = math.radians(inp["alpha"])
            yA = -m(inp["z_a"])
            Lfree, Lb = max(5.0, 0.9 * H), 5.0
            d = (math.cos(al), -math.sin(al), 0)
            sc.box("anchors", (-0.15, yA, 0), (0.3, 0.3, L + bs), "#4b5563")
            for z in zs:
                p0 = (hs, yA, z)
                p1 = (hs + d[0] * Lfree, yA + d[1] * Lfree, z)
                p2 = (p1[0] + d[0] * Lb, p1[1] + d[1] * Lb, z)
                sc.line("anchors", [(-0.3, yA, z), p1], "#111827")
                sc.cylinder("anchors", p1, p2, 0.09, "#9ca3af")
            Ad = max(r["A"] for r in results) / 1000 / math.cos(al)
            sc.label("anchors", calc.tr("A_d = {a:.0f} kN per anchor", a=Ad),
                     (hs + d[0] * Lfree, yA + d[1] * Lfree + 0.3, zs[-1]), "result")
        # pressure diagrams at the near end (per metre width, design, governing moment case)
        zg = design["zg"] / 1000
        e, ep = design["e"] * 1000, design["ep"] * 1000  # kN/m²
        pmax = max(float(e.max()), float(ep.max()), 1.0)
        s = max(1.0, 0.35 * H) / pmax
        zend = zs[-1] + bs / 2 + 0.6
        act = [(hs, 0)] + [(hs + v * s, -y) for v, y in zip(e, zg)] + [(hs, -zg[-1])]
        for zz in (zend, zs[0] - bs / 2 - 0.6):
            sc.prism("active", act, 0.04, PALETTE["earth"], opacity=0.6, z=zz)
        sel = zg >= H
        pas = [(0, -H)] + [(-v * s, -y) for v, y in zip(ep[sel], zg[sel])] + [(0, -zg[-1])]
        for zz in (zend, zs[0] - bs / 2 - 0.6):
            sc.prism("passive", pas, 0.04, PALETTE["bearing"], opacity=0.6, z=zz)
        for i in range(10):
            y = zg[-1] * (i + 0.5) / 10
            v = float(np.interp(y, zg, e)) * s
            if v > 0.03:
                sc.arrow("active", (hs + v, -y, zend), (-1, 0, 0), v, PALETTE["earth"], 0.1)
            if y > H:
                vp = float(np.interp(y, zg, ep)) * s
                if vp > 0.03:
                    sc.arrow("passive", (-vp, -y, zend), (1, 0, 0), vp, PALETTE["bearing"], 0.1)
        sc.label("active", calc.tr("e_a,max = {v:.1f} kN/m²", v=float(e.max())),
                 (hs + float(e.max()) * s, -H, zend), "earth")
        if ep.max() > 0:
            sc.label("passive", calc.tr("e_p,max = {v:.0f} kN/m² (on b_p)", v=float(ep.max())),
                     (-float(ep.max()) * s, -zg[-1], zend), "bearing")
        sc.legend_item(PALETTE["earth"], calc.tr("Active pressure, design ({name})",
                                                 name=gov_M["cb"]["name"]))
        sc.legend_item(PALETTE["bearing"], calc.tr("Passive resistance, design (on b_p)"))
        # moment diagram beside the middle pile
        zm = zs[n // 2]
        Mz = design["Mz"] / 1e6
        Mmax = float(np.max(np.abs(Mz))) or 1.0
        sm = max(1.0, 0.3 * H) / Mmax
        mpoly = [(-0.6, 0)] + [(-0.6 - v * sm, -y) for v, y in zip(Mz, zg)] + [(-0.6, -zg[-1])]
        sc.prism("moment", mpoly, 0.04, "#c0392b", opacity=0.6, z=zm)
        k = int(np.argmax(np.abs(Mz)))
        sc.label("moment", calc.tr("M_max = {v:.0f} kNm", v=Mmax),
                 (-0.6 - Mz[k] * sm, -zg[k], zm), "result")
        sc.legend_item("#c0392b", calc.tr("Bending moment per pile, M_max = {v:.0f} kNm", v=Mmax))
        # deflected shape (characteristic, exaggerated)
        dz = char["dz"]
        dmax = float(np.max(np.abs(dz))) or 1.0
        ex = max(0.4, 0.08 * H) / (dmax / 1000)
        zc = char["zg"] / 1000
        sc.line("deflection", [(-(d / 1000) * ex, -y, zm) for d, y in zip(dz[::10], zc[::10])],
                "#2e8b57")
        sc.label("deflection", calc.tr("δ_top = {d:.1f} mm (× {x:.0f})", d=abs(char["d_top"]),
                                       x=ex), (-(char["d_top"] / 1000) * ex, 0.2, zm), "bearing")
        sc.label("dims", f"H = {H:.2f} m", (-0.3, -H / 2, zs[0] - 0.4), "dim")
        sc.label("dims", calc.tr("t = {t:.2f} m (req. {r:.2f} m)", t=t, r=m(gov_t["t_req"])),
                 (-0.3, -H - t / 2, zs[0] - 0.4), "dim")
        sc.label("dims", f"a = {a:.2f} m", (hs + 0.2, 0.15, (zs[0] + zs[1]) / 2), "dim")
        sc.label("dims", f"{sec.name}", (hs / 2, 0.35, zs[0]), "dim")
        return sc.to_dict()
