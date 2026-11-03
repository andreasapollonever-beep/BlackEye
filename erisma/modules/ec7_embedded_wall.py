"""Embedded RC pile wall (contiguous or secant) with several anchor rows.

Analysis: elastic beam on elastic–plastic Winkler springs (subgrade reaction method).
On both faces the earth pressure starts from the at-rest value and changes with the wall
displacement u (positive towards the excavation) by k_h·u, bounded by the active and the
passive pressure.  Anchors are springs E·A/L_free·cos²α, locked off at their prestress.

EN 1997-1 §9: combinations with factored actions (DA1-C1, DA2) are analysed with
characteristic soil and the effects multiplied by γ_G (variable surcharge scaled by
γ_Q/γ_G); combinations with factored strength (DA1-C2, DA3) are analysed with design soil
parameters.  The mobilised passive resistance is checked against E_p / γ_R,e.
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import APPROACH_CHOICES, check_approach, get_annex
from ..design.ec2 import bar_area, circular_moment_resistance, concrete_props
from ..design.geotech import k_mononobe_okabe, kp_seismic
from ..report.scene3d import PALETTE, Scene3D
from ..report.svg import vertical_diagrams

GW = 9.81e-6
ES = 200000.0
CONCRETE = ["C25/30", "C30/37", "C35/45"]
BARS = ["16", "20", "25", "32"]
LINKS = ["8", "10", "12"]
HINT_EMB = "Increase the embedment (longer piles) or lower the bottom anchor row."
HINT_M = "Use a larger pile diameter or more reinforcement, or add an anchor row."
HINT_V = "Use closer or larger links (spiral)."
HINT_A = "Use anchors with a higher resistance, closer horizontal spacing or add a row."


def _ka(phi, delta):
    """Coulomb active coefficient, vertical wall, horizontal ground (horizontal component)."""
    r = math.sqrt(math.sin(phi + delta) * math.sin(phi) / math.cos(delta))
    return math.cos(phi) ** 2 / (math.cos(delta) * (1 + r) ** 2) * math.cos(delta)


def _kp(phi, delta):
    """Coulomb passive coefficient (δ ≤ φ/2), horizontal component."""
    r = math.sqrt(math.sin(phi + delta) * math.sin(phi) / math.cos(delta))
    return math.cos(phi) ** 2 / (math.cos(delta) * (1 - r) ** 2) * math.cos(delta)


def solve_wall(H, t, a, EI, kh, phi, c, gam, gsat, q, zw, anchors, d_a, d_p,
               seismic=None, n_el=None) -> dict:
    """Winkler analysis of one pile (spacing a). Units N, mm, radians.

    anchors: list of (z, k_h [N/mm per pile], P0_h [N per pile]).
    Returns arrays along z and the converged spring state.
    """
    L = H + t
    n = n_el or max(int(L / 100), 60)
    z = np.linspace(0, L, n + 1)
    le = L / n
    K0 = 1 - math.sin(phi)
    Ka, Kp = _ka(phi, d_a), _kp(phi, d_p)
    if seismic:
        Ka, Kp, fv = seismic["KAE"], seismic["KPE"], seismic["fv"]
    else:
        fv = 1.0

    def sv(depth):  # effective vertical stress behind at depth below ground
        dry = np.minimum(depth, zw)
        return (gam * dry + (gsat - GW) * np.maximum(depth - zw, 0.0)) * fv

    sv_b = sv(z) + q
    zf = np.maximum(z - H, 0.0)
    zwf = max(zw - H, 0.0)  # water in front assumed at excavation level or the behind level
    sv_f = (gam * np.minimum(zf, zwf) + (gsat - GW) * np.maximum(zf - zwf, 0.0)) * fv
    two_c = 2 * c
    pa = np.maximum(Ka * sv_b - two_c * math.sqrt(Ka), 0.0)
    pp_b = Kp * sv_b + two_c * math.sqrt(Kp)
    p0_b = np.clip(K0 * sv_b, pa, pp_b)
    front = z > H + 1e-9
    pa_f = np.where(front, np.maximum(Ka * sv_f - two_c * math.sqrt(Ka), 0.0), 0.0)
    pp_f = np.where(front, Kp * sv_f + two_c * math.sqrt(Kp), 0.0)
    p0_f = np.where(front, np.clip(K0 * sv_f, pa_f, pp_f), 0.0)
    # net water pressure (behind level zw, front at max(H, zw)), constant below excavation
    hw = np.clip(z - zw, 0.0, max(H - zw, 0.0)) * GW if zw < H else np.zeros_like(z)
    trib = np.full(n + 1, le)
    trib[0] = trib[-1] = le / 2
    # stiffness matrix of the beam
    ndof = 2 * (n + 1)
    Kb = np.zeros((ndof, ndof))
    k = EI / le**3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le**2, -6 * le, 2 * le**2],
                               [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le**2, -6 * le, 4 * le**2]])
    for e in range(n):
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        Kb[np.ix_(idx, idx)] += k
    anc_nodes = [(int(round(za / le)), ka_, P0) for za, ka_, P0 in anchors]
    state_b = np.zeros(n + 1, dtype=int)  # 0 elastic, -1 active limit, +1 passive limit
    state_f = np.where(front, 0, 9)
    u = np.zeros(n + 1)
    for _ in range(200):
        K = Kb.copy()
        F = np.zeros(ndof)
        for i in range(n + 1):
            w = a * trib[i]
            # behind: p = p0 − k u (pushes towards excavation, +)
            if state_b[i] == 0:
                K[2 * i, 2 * i] += kh * w
                F[2 * i] += p0_b[i] * w
            else:
                F[2 * i] += (pa[i] if state_b[i] < 0 else pp_b[i]) * w
            if state_f[i] == 0:
                K[2 * i, 2 * i] += kh * w
                F[2 * i] -= p0_f[i] * w
            elif state_f[i] != 9:
                F[2 * i] -= (pa_f[i] if state_f[i] < 0 else pp_f[i]) * w
            F[2 * i] += hw[i] * w
        for j, ka_, P0 in anc_nodes:
            K[2 * j, 2 * j] += ka_
            F[2 * j] -= P0
        try:
            sol = np.linalg.solve(K, F)
        except np.linalg.LinAlgError:
            return {"ok": False}
        u = sol[0::2]
        pb = p0_b - kh * u
        pf = np.where(front, p0_f + kh * u, 0.0)
        nb = np.where(pb < pa, -1, np.where(pb > pp_b, 1, 0))
        # once on a limit, stay unless the displacement reverses back inside the range
        nf = np.where(front, np.where(pf < pa_f, -1, np.where(pf > pp_f, 1, 0)), 9)
        if np.array_equal(nb, state_b) and np.array_equal(nf, state_f):
            break
        state_b, state_f = nb, nf
    pb = np.clip(p0_b - kh * u, pa, pp_b)
    pf = np.where(front, np.clip(p0_f + kh * u, pa_f, pp_f), 0.0)
    if abs(u).max() > 0.1 * L or (state_f[front] == 1).all():
        ok = False
    else:
        ok = True
    # internal forces from nodal loads (statics, integrating from the top)
    load = (pb - pf + hw) * a * trib  # N per node, + towards excavation
    Fa = [(j, -(P0 + ka_ * u[j])) for j, ka_, P0 in anc_nodes]  # anchor force on the wall
    nodal = load.copy()
    for j, f in Fa:
        nodal[j] += f
    V = np.cumsum(nodal)
    M = np.zeros(n + 1)
    for i in range(1, n + 1):
        M[i] = M[i - 1] + V[i - 1] * le
    Ep_mob = float(np.sum(pf * a * trib))
    Ep_av = float(np.sum(pp_f * a * trib))
    return {"ok": ok, "z": z, "u": u, "M": M, "V": V, "pb": pb, "pf": pf, "pa": pa,
            "pp_f": pp_f, "hw": hw, "anchors": [-f for _, f in Fa], "Ep_mob": Ep_mob,
            "Ep_av": Ep_av, "Ka": Ka, "Kp": Kp, "K0": K0}


@register
class EmbeddedWallEC7(DesignModule):
    id = "ec7_embedded_wall"
    title = "Embedded pile wall with anchors"
    category = "Geotechnical"
    has_3d = True
    uses_annex = True
    standard = "EN 1997-1 §9, EN 1992-1-1, EN 1998-5"
    description = ("Contiguous or secant bored pile wall, cantilever or with several anchor "
                   "rows: elastic–plastic subgrade reaction analysis (displacements, earth "
                   "pressures, moments, anchor forces), passive mobilisation, RC pile design "
                   "and anchors. Interactive 3D model.")

    fields = [
        Field("H", "Excavation depth H", "m", 7.0, min=1, max=25, group="Geometry"),
        Field("t", "Embedment below excavation t", "m", 5.0, min=0.5, group="Geometry"),
        Field("D", "Pile diameter D", "m", 0.60, min=0.3, max=1.5, group="Geometry"),
        Field("a", "Pile spacing a", "m", 0.75, min=0.3, max=3.0, group="Geometry",
              help="Contiguous wall: a ≥ D (gap ≤ ~0.15 m in stiff soil); secant: a < D."),
        Field("anchors", "Anchor rows", kind="table", group="Anchors", default=[
            {"z": 2.0, "alpha": 20.0, "sh": 2.25, "P0": 300.0, "Lfr": 8.0, "At": 700.0,
             "Rad": 650.0},
            {"z": 4.5, "alpha": 20.0, "sh": 2.25, "P0": 350.0, "Lfr": 6.0, "At": 700.0,
             "Rad": 650.0}],
            columns=[Field("z", "Depth", "m", 2.0, min=0.2),
                     Field("alpha", "Inclination α", "°", 20.0, min=0, max=45),
                     Field("sh", "Horizontal spacing", "m", 2.0, min=0.5),
                     Field("P0", "Lock-off load P_0", "kN", 250.0, min=0),
                     Field("Lfr", "Free length", "m", 6.0, min=3),
                     Field("At", "Tendon area A_t", "mm²", 600.0, min=50),
                     Field("Rad", "Design resistance R_a,d", "kN", 600.0, min=1)],
            help="Leave the table empty for a cantilever wall. Strands Ø15.7: 150 mm² each."),
        Field("phi", "Soil φ'k", "°", 32.0, min=15, max=45, group="Soil"),
        Field("c", "Soil c'k", "kN/m²", 5.0, min=0, group="Soil"),
        Field("gamma", "Soil γ", "kN/m³", 19.0, min=10, group="Soil"),
        Field("gsat", "Soil γ_sat", "kN/m³", 20.0, min=10, group="Soil"),
        Field("zw", "Groundwater depth behind the wall", "m", 20.0, min=0, group="Soil",
              help="In front the water is lowered to the excavation level."),
        Field("q", "Surcharge behind the wall (variable)", "kN/m²", 10.0, min=0, group="Soil"),
        Field("kh", "Modulus of subgrade reaction k_h", "MN/m³", 25.0, min=2, max=200,
              group="Soil", help="Typical: loose sand 10, medium dense 25, dense 50–100, "
                                 "stiff clay 20–40 MN/m³."),
        Field("d_a", "Wall friction δ_a/φ'", "", 0.667, min=0, max=0.667, group="Soil"),
        Field("d_p", "Wall friction δ_p/φ'", "", 0.5, min=0, max=0.5, group="Soil"),
        Field("approach", "Design approach", kind="choice", choices=APPROACH_CHOICES,
              default="National Annex", group="Soil"),
        Field("seismic", "Include seismic design (EN 1998-5)", kind="bool", default=False,
              group="Seismic"),
        Field("ag", "Design ground acceleration αgR·γI", "", 0.20, min=0, max=0.6,
              group="Seismic", show_if="seismic"),
        Field("S", "Soil factor S", "", 1.2, min=1.0, max=1.8, group="Seismic",
              show_if="seismic"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C30/37",
              group="Piles"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Piles"),
        Field("nbar", "Longitudinal bars", "", 12, kind="int", min=6, max=40, group="Piles"),
        Field("dia", "Bar Ø", kind="choice", choices=BARS, default="20", group="Piles"),
        Field("link", "Spiral Ø", kind="choice", choices=LINKS, default="10", group="Piles"),
        Field("s_link", "Spiral pitch", "mm", 150.0, min=50, max=400, group="Piles"),
        Field("cover", "Cover to bar centre", "mm", 85.0, min=50, max=150, group="Piles"),
        Field("EI_f", "Bending stiffness factor (cracking)", "", 0.7, min=0.3, max=1.0,
              group="Piles", help="E_cm I × factor; 0.5–0.7 for cracked RC piles."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        H, t, D, a = inp["H"], inp["t"], inp["D"], inp["a"]
        rows = sorted(inp["anchors"], key=lambda r: r["z"])
        for r in rows:
            if r["z"] >= H:
                raise InputError("Anchor rows must lie above the excavation level", "anchors")
        if a < 0.5 * D:
            raise InputError("Pile spacing is too small (a < D/2)", "a")
        fck = float(inp["concrete"].split("/")[0][1:])
        Ecm = concrete_props(fck)["Ecm"]
        EI = inp["EI_f"] * Ecm * math.pi * D**4 / 64
        kh = inp["kh"]

        def anchors_for(_):
            out = []
            for r in rows:
                al = math.radians(r["alpha"])
                k1 = ES * r["At"] / r["Lfr"] * math.cos(al) ** 2
                share = a / r["sh"]
                out.append((r["z"], k1 * share, r["P0"] * math.cos(al) * share))
            return out

        calc.heading("Wall, anchors and soil")
        calc.input("H", H, "m", "Excavation depth")
        calc.input("t", t, "m", "Embedment")
        calc.input("D", D, "m", "Pile diameter")
        calc.input("a", a, "m", calc.tr("Pile spacing ({w})",
                                        w=calc.tr("secant wall" if a < D else "contiguous wall")))
        calc.formula("EI", "f E_cm π D⁴/64", EI / 1e12, "", calc.tr(
            "Bending stiffness per pile [MNm²] (E_cm = {e:.0f} N/mm²)", e=Ecm), dp=1)
        calc.input("k_h", kh, "MN/m³", "Modulus of subgrade reaction")
        if rows:
            calc.table(["Row", "z [m]", "α [°]", "s_h [m]", "P_0 [kN]", "L_free [m]",
                        "A_t [mm²]", "k_h [kN/mm per pile]"],
                       [[str(i + 1), f"{r['z'] / 1000:g}", f"{r['alpha']:g}",
                         f"{r['sh'] / 1000:g}", f"{r['P0'] / 1000:g}",
                         f"{r['Lfr'] / 1000:g}", f"{r['At']:g}",
                         f"{k / 1000:.1f}"] for i, (r, (_, k, _)) in
                        enumerate(zip(rows, anchors_for(None)))],
                       caption="Anchor rows (stiffness E_s A_t / L_free cos²α × a / s_h)")
        else:
            calc.text("No anchors — cantilever wall.")
        calc.text("Subgrade reaction method: at-rest pressure ± k_h u, bounded by the active "
                  "and passive pressures (Coulomb, δ_a = {da:g}φ', δ_p = {dp:g}φ'). Water "
                  "lowered to the excavation level in front; net water pressure without "
                  "seepage reduction.", da=inp["d_a"], dp=inp["d_p"])

        check_approach(calc, na, inp["approach"])
        phik = math.radians(inp["phi"])
        common = dict(H=H, t=t, a=a, EI=EI, kh=kh, gam=inp["gamma"], gsat=inp["gsat"],
                      zw=inp["zw"], anchors=anchors_for(None))
        # characteristic analysis (SLS)
        char = solve_wall(phi=phik, c=inp["c"], q=inp["q"], d_a=inp["d_a"] * phik,
                          d_p=inp["d_p"] * phik, **common)
        if not char["ok"]:
            raise InputError("The wall is not stable even with characteristic soil strength "
                             "(passive resistance exhausted) — increase the embedment t.", "t")
        calc.heading("Characteristic analysis (serviceability)")
        calc.formula("u_max", "max |u|", float(np.abs(char["u"]).max()), "mm",
                     "Maximum horizontal displacement", dp=1)
        calc.formula("u_top", "u(z = 0)", float(char["u"][0]), "mm", "Displacement of the top",
                     dp=1)
        for i, f in enumerate(char["anchors"]):
            calc.formula(f"P_{i + 1},k", "spring force", f / math.cos(math.radians(
                rows[i]["alpha"])) * rows[i]["sh"] / a, "kN",
                calc.tr("Characteristic anchor force, row {i}", i=i + 1))

        Pk = [fh / math.cos(math.radians(r["alpha"])) * r["sh"] / a
              for r, fh in zip(rows, char["anchors"])]
        results = []
        for name in na.combinations(inp["approach"]):
            gG, _, gQ, gphi, gc, _, _ = na.combos[name]
            gRe = na.gRe(name)
            calc.heading(calc.tr("Design — {name}", name=name))
            if gphi > 1.0:
                phid = math.atan(math.tan(phik) / gphi)
                r = solve_wall(phi=phid, c=inp["c"] / gc, q=inp["q"] * gQ,
                               d_a=inp["d_a"] * phid, d_p=inp["d_p"] * phid, **common)
                f = 1.0
                calc.text("Design soil strength φ'_d = {p:.1f}°, c'_d = {c:.1f} kN/m²; "
                          "surcharge × γ_Q = {q:g}; effects from the analysis directly.",
                          p=math.degrees(phid), c=inp["c"] / gc * 1000, q=gQ)
            else:
                r = solve_wall(phi=phik, c=inp["c"], q=inp["q"] * gQ / gG,
                               d_a=inp["d_a"] * phik, d_p=inp["d_p"] * phik, **common)
                f = gG
                calc.text("Characteristic soil; surcharge × γ_Q/γ_G = {k:.3f}; effects × γ_G "
                          "= {g:g} (factored effects, EN 1997-1 2.4.7.3.2).", k=gQ / gG, g=gG)
            results.append(cls._design(calc, inp, na, name, r, f, gRe, rows, Pk))
        if inp["seismic"] and inp["ag"] > 0:
            calc.heading("Seismic design situation (EN 1998-5 §7.3)")
            kh_s = calc.formula("k_h", "α S / r, r = 1 (anchored/embedded wall)",
                                inp["ag"] * inp["S"], "", ref="EN 1998-5 7.3.2.2", dp=3)
            kv = 0.5 * kh_s
            theta = math.atan(kh_s / (1 - kv))
            phid = math.atan(math.tan(phik) / na.seismic_gamma_phi)
            KAE = k_mononobe_okabe(phid, 0.0, inp["d_a"] * phid, theta) * math.cos(
                inp["d_a"] * phid)
            KPE = kp_seismic(phid, theta)
            calc.formula("K_AE", "Mononobe-Okabe (E.2), k_v = 0.5 k_h", KAE, "", dp=3)
            calc.formula("K_PE", "EN 1998-5 E.4, δ = 0", KPE, "", dp=3)
            r = solve_wall(phi=phid, c=inp["c"] / na.seismic_gamma_c, q=inp["q"] * 0.3,
                           d_a=inp["d_a"] * phid, d_p=0.0,
                           seismic={"KAE": KAE, "KPE": KPE, "fv": 1 - kv}, **common)
            results.append(cls._design(calc, inp, na, calc.tr("Seismic"), r, 1.0, 1.0, rows,
                                       None))
        gov = max(results, key=lambda x: x["Mmax"])
        cls._structural(calc, inp, na, results, fck)
        calc.figure(vertical_diagrams(char["z"] / 1000, H / 1000, t / 1000, [
            (calc.tr("Net pressure [kN/m²]"), (char["pb"] - char["pf"] + char["hw"]) * 1000,
             "#c47a2c"),
            (calc.tr("u [mm]"), char["u"], "#2a6f97"),
            (calc.tr("M [kNm/pile]"), gov["M"] / 1e6, "#e03b3b"),
            (calc.tr("V [kN/pile]"), gov["V"] / 1e3, "#2e9b5f")],
            z_anchor=rows[0]["z"] / 1000 if rows else None),
            calc.tr("Characteristic pressures and displacement; design moments and shears "
                    "({n})", n=gov["name"]))
        calc.model3d = cls._scene(calc, inp, rows, char, gov)

    @staticmethod
    def _design(calc, inp, na, name, r, f, gRe, rows, Pk) -> dict:
        if not r.get("ok"):
            calc.check(calc.tr("{name}: wall stability (passive resistance)", name=name),
                       1.0, 0.0, "", "EN 1997-1 9.7", hint=HINT_EMB)
            n = len(rows)
            return {"name": name, "M": np.zeros(2), "V": np.zeros(2), "Mmax": float("inf"),
                    "Vmax": float("inf"), "anchors": [float("inf")] * n}
        Mmax = f * float(np.abs(r["M"]).max())
        Vmax = f * float(np.abs(r["V"]).max())
        calc.formula("M_Ed", "max |M| × factor", Mmax, "kNm", "Design bending moment per pile")
        calc.formula("V_Ed", "max |V| × factor", Vmax, "kN", "Design shear force per pile")
        Ep_mob = f * r["Ep_mob"]
        Ep_d = r["Ep_av"] / gRe
        calc.formula("E_p,mob", "Σ p_f × factor", Ep_mob, "kN",
                     "Mobilised passive resistance per pile")
        calc.formula("E_p,d", "Σ K_p σ'_v / γ_R,e", Ep_d, "kN",
                     calc.tr("Available design passive resistance (γ_R,e = {g:g})", g=gRe))
        calc.check(calc.tr("{name} embedment: E_p,mob ≤ E_p,d", name=name), Ep_mob, Ep_d, "kN",
                   "EN 1997-1 9.7.4", hint=HINT_EMB)
        anchors = []
        for i, (row, fh) in enumerate(zip(rows, r["anchors"])):
            al = math.radians(row["alpha"])
            P = f * fh / math.cos(al) * row["sh"] / inp["a"]
            rule = na.anchor_sls_factor and Pk is not None
            if rule:
                P = max(P, na.anchor_sls_factor * Pk[i])
            Pd = calc.formula(f"P_{i + 1},d", "F_h / cos α × s_h / a × factor"
                              + (f" ≥ {na.anchor_sls_factor:g} P_k" if rule else ""), P, "kN",
                              calc.tr("Design anchor force, row {i}", i=i + 1))
            calc.check(calc.tr("{name} anchor row {i}: P_d ≤ R_a,d", name=name, i=i + 1), Pd,
                       row["Rad"], "kN", "EN 1997-1 8.5", hint=HINT_A)
            anchors.append(Pd)
        return {"name": name, "M": r["M"] * f, "V": r["V"] * f, "Mmax": Mmax, "Vmax": Vmax,
                "anchors": anchors}

    @staticmethod
    def _structural(calc, inp, na, results, fck) -> None:
        calc.heading("RC pile design (EN 1992-1-1)")
        D = inp["D"]
        fcd = calc.formula("f_cd", "α_cc f_ck / γ_c", na.alpha_cc * fck / na.gamma_c, "N/mm²",
                           dp=2)
        fyd = inp["fyk"] / na.gamma_s
        n, dia = inp["nbar"], float(inp["dia"])
        rs = D / 2 - inp["cover"]
        MRd = calc.formula("M_Rd", "strain compatibility, circular section, N = 0",
                           circular_moment_resistance(D, n, dia, inp["cover"], fcd, fyd, 0.0)[0],
                           "kNm", calc.tr("{n}Ø{d:g}", n=n, d=dia))
        Mmax = max(r["Mmax"] for r in results)
        calc.check("Bending: M_Ed ≤ M_Rd", Mmax, MRd, "kNm", "6.1", hint=HINT_M)
        de = D / 2 + 2 * rs / math.pi
        calc.formula("d_e", "D/2 + 2r_s/π", de, "mm",
                     "Effective depth of the circular section (Feltham 2004)")
        As_t = n / 2 * bar_area(dia)
        k = min(1 + math.sqrt(200 / de), 2.0)
        rho = min(As_t / (D * de), 0.02)
        VRdc = max(0.18 / na.gamma_c * k * (100 * rho * fck) ** (1 / 3),
                   0.035 * k**1.5 * math.sqrt(fck)) * D * de
        dl = float(inp["link"])
        VRds = 2 * bar_area(dl) / inp["s_link"] * 0.9 * de * fyd * 2.5 * math.pi / 4
        calc.formula("V_Rd,c", "C_Rd,c k (100ρ f_ck)^(1/3) D d_e", VRdc, "kN", ref="Eq. 6.2",
                     dp=1)
        calc.formula("V_Rd,s", "(2A_sw/s) 0.9d_e f_yd cot θ π/4, cot θ = 2.5", VRds, "kN",
                     "Spiral (π/4 for the circular shape)", ref="Eq. 6.8", dp=1)
        Vmax = max(r["Vmax"] for r in results)
        calc.check("Shear: V_Ed ≤ max(V_Rd,c, V_Rd,s)", Vmax, max(VRdc, VRds), "kN", "6.2",
                   hint=HINT_V)

    @staticmethod
    def _scene(calc, inp, rows, char, gov) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        H, t, D, a = m(inp["H"]), m(inp["t"]), m(inp["D"]), m(inp["a"])
        L = H + t
        sc = Scene3D("embedded_wall", calc.tr)
        for key, label in (("wall", "Piles"), ("soil", "Soil"), ("anchors", "Anchors"),
                           ("defl", "Deflected shape (×20)"), ("notes", "Results")):
            sc.layer(key, label, toggle=key != "wall")
        npile = max(int(6.0 / a), 4)
        zc0 = -(npile - 1) * a / 2
        for i in range(npile):
            sc.cylinder("wall", (0, 0.5, zc0 + i * a), (0, -L, zc0 + i * a), D / 2,
                        PALETTE["concrete"])
        W = npile * a + 1
        sc.box("soil", (6.0 / 2 + D / 2, -L / 2, 0), (6.0, L + 0.01, W), PALETTE["soil"],
               opacity=0.12, edges=False)
        sc.box("soil", (-4.0 / 2 - D / 2, -H - t / 2, 0), (4.0, t, W), PALETTE["soil"],
               opacity=0.18, edges=False)
        sc.box("wall", (0, 0.6, 0), (D + 0.2, 0.25, W - 0.5),
               "#9aa0a8")
        for i, r in enumerate(rows):
            al = math.radians(r["alpha"])
            z = m(r["z"])
            Lf = m(r["Lfr"])
            nanc = max(int((W - 1) / m(r["sh"])), 1)
            for k in range(nanc + 1):
                zz = -W / 2 + 0.5 + k * m(r["sh"])
                if zz > W / 2 - 0.4:
                    break
                p1 = (D / 2, -z, zz)
                p2 = (D / 2 + Lf * math.cos(al), -z - Lf * math.sin(al), zz)
                p3 = (p2[0] + 4 * math.cos(al), p2[1] - 4 * math.sin(al), zz)
                sc.line("anchors", [p1, p2], "#333333")
                sc.cylinder("anchors", p2, p3, 0.08, "#7d8794")
            sc.label("notes", calc.tr("P_d = {p:.0f} kN", p=gov["anchors"][i] / 1000)
                     if i < len(gov["anchors"]) and math.isfinite(gov["anchors"][i])
                     else f"#{i + 1}", (D / 2 + 1.5, -z + 0.3, W / 2), "force")
        u = char["u"] / 1000 * 20
        pts = [(-uu, -m(zz), W / 2 + 0.1) for uu, zz in zip(u[::3], char["z"][::3])]
        sc.line("defl", pts, "#e03b3b")
        sc.label("notes", calc.tr("u_max = {u:.1f} mm", u=float(np.abs(char["u"]).max())),
                 (-1.5, -H / 2, W / 2), "result")
        sc.label("notes", f"H = {H:.1f} m", (-2.5, -H, W / 2), "")
        sc.views["default"] = {"pos": [-L * 0.8, 1.0, L * 1.0], "target": [0, -L / 2, 0]}
        return sc.to_dict()
