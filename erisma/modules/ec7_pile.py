"""Single pile — axial resistance from ground parameters (EN 1997-1 §7.6) and lateral
resistance (Broms, free head), with the structural check of the pile (EN 1992-1-1).

Static formulae (characteristic, per unit shaft area):

* clay, shaft  q_s = α c_u            base  q_b = 9 c_u
* sand, shaft  q_s = K tan δ σ'_v,    K = (K/K0)(1 − sin φ'), δ = (δ/φ') φ'
* sand, base   q_b = η_b N_q* σ'_v ≤ η_b · 0.5 p_a N_q* tan φ'  (Meyerhof 1976)
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import APPROACH_CHOICES, check_approach, get_annex
from ..design.ec2 import bar_area, circular_moment_resistance
from ..design.geotech import kp_rankine
from ..report.scene3d import PALETTE, Scene3D
from ..report.svg import vertical_diagrams

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50"]
BARS = ["12", "14", "16", "20", "25"]
GW = 9.81e-6  # γ_w [N/mm³]
# Pile type -> (K/K0, δ/φ', base efficiency η_b)
TYPES = {"Bored": (1.0, 1.0, 0.5), "CFA": (0.9, 1.0, 0.5), "Driven": (1.5, 0.75, 1.0)}
# Meyerhof (1976) bearing capacity factor N_q* for deep foundations
NQ_PHI = [20, 25, 28, 30, 32, 34, 35, 36, 38, 40, 42, 45]
NQ_VAL = [12.4, 26.0, 39.7, 56.7, 81.0, 115.0, 143.0, 168.0, 231.0, 346.0, 525.0, 930.0]
METHODS = ["Alternative method (model factor)", "Ground test profiles (ξ3, ξ4)"]
HINT_AX = "Increase the pile length or diameter (or found the pile in a stronger layer)."
HINT_TEN = "Increase the pile length or diameter, or use more piles."
HINT_LAT = "Increase the pile diameter or its reinforcement, or reduce the head load."
HINT_STR = "Use a stronger concrete or more longitudinal reinforcement (or a larger pile)."


def nq_meyerhof(phi_deg: float) -> float:
    return float(np.exp(np.interp(phi_deg, NQ_PHI, np.log(NQ_VAL))))


def xi_factor(table: dict, n: int) -> float:
    ks = sorted(table)
    return float(np.interp(min(max(n, ks[0]), ks[-1]), ks, [table[k] for k in ks]))


def broms(soil: str, D: float, L: float, e: float, My: float, cu: float, gamma: float,
          phi: float) -> tuple[float, str, float]:
    """Broms (1964) free-head ultimate lateral load → (H_u, mode, M_max).  N, mm."""
    def bisect(f, lo, hi):
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if f(mid) > 0:
                hi = mid
            else:
                lo = mid
        return 0.5 * (lo + hi)

    if soil == "Clay":
        def mmax(H):
            return H * (e + 1.5 * D + 0.5 * H / (9 * cu * D))
        g_max = L - 1.5 * D
        if g_max <= 0:
            return 0.0, "short", 0.0

        def short(H):  # Mmax − 2.25 D g² cu with g = L − 1.5D − f
            g = L - 1.5 * D - H / (9 * cu * D)
            return mmax(H) - 2.25 * D * cu * max(g, 0.0) ** 2 if g > 0 else 1.0
        Hs = bisect(short, 0.0, 9 * cu * D * g_max)
        if mmax(Hs) <= My:
            return Hs, "short", mmax(Hs)
        Hl = bisect(lambda H: mmax(H) - My, 0.0, Hs)
        return Hl, "long", My
    Kp = kp_rankine(phi)

    def mmax_s(H):
        return H * (e + 0.67 * 0.82 * math.sqrt(H / (gamma * D * Kp)))
    Hs = 0.5 * gamma * D * L**3 * Kp / (e + L)
    if mmax_s(Hs) <= My:
        return Hs, "short", mmax_s(Hs)
    Hl = bisect(lambda H: mmax_s(H) - My, 0.0, Hs)
    return Hl, "long", My


@register
class PileEC7(DesignModule):
    id = "ec7_pile"
    title = "Single pile — axial and lateral"
    category = "Geotechnical"
    has_3d = True
    uses_annex = True
    standard = "EN 1997-1 §7, EN 1992-1-1"
    description = ("Bored, CFA or driven pile in layered clay/sand: shaft and base resistance "
                   "from soil parameters (α-method, β-method, Meyerhof N_q*), partial and "
                   "correlation/model factors of the National Annex, tension, lateral "
                   "resistance (Broms) and structural check. Interactive 3D model.")

    fields = [
        Field("ptype", "Pile type", kind="choice", choices=list(TYPES), default="Bored",
              group="Pile"),
        Field("D", "Pile diameter D", "m", 0.80, min=0.2, max=3.0, group="Pile"),
        Field("L", "Pile length L (below ground)", "m", 18.0, min=2, max=80, group="Pile"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C30/37",
              group="Pile"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Pile"),
        Field("nbar", "Longitudinal bars", "", 10, kind="int", min=6, max=40, group="Pile"),
        Field("dia", "Bar Ø", kind="choice", choices=BARS, default="20", group="Pile"),
        Field("cover", "Cover to bar centre", "mm", 75.0, min=40, max=150, group="Pile",
              help="Bored piles: cover 75 mm to the links is usual (EN 1536)."),
        Field("G", "Axial load — permanent G", "kN", 800.0, min=0,
              group="Characteristic loads at the pile head"),
        Field("Q", "Axial load — variable Q", "kN", 250.0, min=0,
              group="Characteristic loads at the pile head"),
        Field("T", "Uplift (tension) load — variable", "kN", 0.0, min=0,
              group="Characteristic loads at the pile head",
              help="e.g. wind uplift; checked against shaft resistance in tension."),
        Field("HG", "Horizontal load — permanent", "kN", 20.0, min=0,
              group="Characteristic loads at the pile head"),
        Field("HQ", "Horizontal load — variable", "kN", 30.0, min=0,
              group="Characteristic loads at the pile head"),
        Field("e", "Height of the horizontal load above ground e", "m", 0.0, min=0,
              group="Characteristic loads at the pile head"),
        Field("zw", "Groundwater depth below ground", "m", 3.0, min=0, group="Ground"),
        Field("layers", "Soil layers (from the ground surface down)", kind="table",
              group="Ground", default=[
                  {"h": 3.0, "soil": "Clay", "gamma": 19.0, "phi": 25.0, "cu": 40.0},
                  {"h": 7.0, "soil": "Clay", "gamma": 20.0, "phi": 25.0, "cu": 90.0},
                  {"h": 20.0, "soil": "Sand", "gamma": 20.0, "phi": 34.0, "cu": 0.0}],
              columns=[Field("h", "Thickness", "m", 2.0, min=0.1),
                       Field("soil", "Soil", kind="choice", choices=["Clay", "Sand"],
                             default="Sand"),
                       Field("gamma", "γ", "kN/m³", 19.0, min=10),
                       Field("phi", "φ' (sand)", "°", 30.0, min=0, max=45),
                       Field("cu", "c_u (clay)", "kN/m²", 50.0, min=0)]),
        Field("alpha", "Adhesion factor α (clay)", "", 0.5, min=0.2, max=1.0, group="Ground",
              help="Typical 0.45–0.5 for bored piles in stiff clay; 0.5–1.0 driven."),
        Field("method", "Characteristic resistance", kind="choice", choices=METHODS,
              default=METHODS[0], group="Design",
              help="Alternative method: R_k = R_cal / γ_Rd (7.6.2.3(8)). Ground test "
                   "profiles: R_k = min(R_mean/ξ3, R_min/ξ4) (7.6.2.3(5))."),
        Field("gRd", "Model factor γ_Rd", "", 1.4, min=1.0, max=2.0, group="Design",
              help="Cyprus NA 2.19: at least 1.25. About 1.4 when no load tests are made."),
        Field("n_prof", "Number of test profiles n", "", 1, kind="int", min=1, max=10,
              group="Design"),
        Field("stiff", "Stiff pile cap (ξ / 1.1, 7.6.2.3(7))", kind="bool", default=False,
              group="Design"),
        Field("approach", "Design approach", kind="choice", choices=APPROACH_CHOICES,
              default="National Annex", group="Design"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        D, L = inp["D"], inp["L"]
        layers = inp["layers"]
        if not layers:
            raise InputError("Add at least one soil layer", "layers")
        if sum(r["h"] for r in layers) < L + 1e-6:
            raise InputError("The soil layers must reach at least the pile toe (sum of "
                             "thicknesses ≥ L)", "layers")
        for r in layers:
            if r["soil"] == "Clay" and r["cu"] <= 0:
                raise InputError("Clay layers need c_u > 0", "layers")
            if r["soil"] == "Sand" and r["phi"] <= 0:
                raise InputError("Sand layers need φ' > 0", "layers")
        if (inp["method"] == METHODS[0] and na.pile_model_min
                and inp["gRd"] < na.pile_model_min - 1e-9):
            raise InputError(calc.tr("The National Annex requires a model factor of at least "
                                     "{m:g}", m=na.pile_model_min), "gRd")
        Kr, dr, eta_b = TYPES[inp["ptype"]]
        A_b = math.pi * D**2 / 4
        perim = math.pi * D

        calc.heading("Pile and ground")
        calc.label("Pile type", inp["ptype"])
        calc.input("D", D, "m", "Pile diameter")
        calc.input("L", L, "m", "Pile length below ground")
        calc.input("z_w", inp["zw"], "m", "Groundwater depth")
        calc.table(["Layer", "From – to [m]", "Soil", "γ [kN/m³]", "φ' [°]", "c_u [kN/m²]"],
                   cls._layer_rows(calc, layers), caption="Soil profile (characteristic values)")
        calc.text("Pile type factors: K/K0 = {k:g}, δ/φ' = {d:g}, base efficiency η_b = {e:g} "
                  "(non-displacement piles mobilise about half of the driven-pile base "
                  "resistance).", k=Kr, d=dr, e=eta_b)

        # ---------------------------------------------------------- characteristic resistances
        calc.heading("Calculated resistance from ground parameters (unfactored)")
        prof = cls._profile(inp, layers, 1.0, 1.0)
        Rb, Rs, qb = prof["Rb"], prof["Rs"], prof["qb"]
        calc.table(["Layer", "Soil", "Thickness in pile [m]", "q_s,mean [kN/m²]", "R_s [kN]"],
                   prof["rows"], caption="Shaft resistance per layer")
        calc.formula("R_s,cal", "Σ π D ∫ q_s dz", Rs, "kN", "Shaft resistance", ref="7.6.2.3")
        calc.formula("q_b", prof["qb_expr"], qb, "kN/m²", "Unit base resistance", dp=0)
        calc.formula("R_b,cal", "q_b π D²/4", Rb, "kN", "Base resistance")
        Wp = 25e-6 * A_b * L
        calc.formula("W_p", "γ_c π D²/4 L", Wp, "kN", "Pile self weight")
        Wnet = calc.formula("ΔW", "W_p − weight of displaced soil", max(Wp - A_b * prof["sv_toe_total"], 0.0),
                            "kN", "Net pile weight, added to the permanent load")

        calc.heading("Characteristic resistance")
        if inp["method"] == METHODS[0]:
            gRd = calc.input("γ_Rd", inp["gRd"], "", "Model factor (alternative method)", dp=2)
            Rbk = calc.formula("R_b,k", "R_b,cal / γ_Rd", Rb / gRd, "kN", ref="7.6.2.3(8)")
            Rsk = calc.formula("R_s,k", "R_s,cal / γ_Rd", Rs / gRd, "kN")
        else:
            n = inp["n_prof"]
            x3, x4 = xi_factor(na.xi3, n), xi_factor(na.xi4, n)
            if inp["stiff"]:
                x3, x4 = max(x3 / 1.1, 1.0), max(x4 / 1.1, 1.0)
            calc.formula("ξ_3", calc.tr("Table A.10, n = {n}", n=n), x3, "", ref="A.3.3.3",
                         dp=3)
            calc.formula("ξ_4", calc.tr("Table A.10, n = {n}", n=n), x4, "", dp=3)
            calc.text("One calculated profile is used for both the mean and the minimum value, "
                      "so R_c,k = R_c,cal / max(ξ3, ξ4).")
            xi = max(x3, x4)
            Rbk = calc.formula("R_b,k", "R_b,cal / ξ", Rb / xi, "kN", ref="Eq. 7.8")
            Rsk = calc.formula("R_s,k", "R_s,cal / ξ", Rs / xi, "kN")

        # ---------------------------------------------------------- design per combination
        check_approach(calc, na, inp["approach"])
        Gt = inp["G"] + Wnet
        gov = {"u": -1.0}
        for name in na.combinations(inp["approach"]):
            gG, gGf, gQ, gphi, gcf, _, _ = na.combos[name]
            rset = na.pile_sets.get(name, "R2")
            gb, gs, gt, gst = na.pile_R[inp["ptype"]][rset]
            calc.heading(calc.tr("Axial design — {name} (set {r})", name=name, r=rset))
            calc.text("γ_G = {g}, γ_Q = {q}; γ_b = {b}, γ_s = {s}, γ_s,t = {st} "
                      "(EN 1997-1 Tables A.6–A.8 / National Annex).",
                      g=gG, q=gQ, b=gb, s=gs, st=gst)
            Fcd = calc.formula("F_c,d", "γ_G (G + ΔW) + γ_Q Q", gG * Gt + gQ * inp["Q"], "kN",
                               "Design compressive load")
            Rcd = calc.formula("R_c,d", "R_b,k / γ_b + R_s,k / γ_s", Rbk / gb + Rsk / gs, "kN",
                               "Design compressive resistance", ref="Eq. 7.7")
            c = calc.check(calc.tr("{name} compression: F_c,d ≤ R_c,d", name=name), Fcd, Rcd,
                           "kN", "7.6.2.1", hint=HINT_AX)
            if c.utilisation > gov["u"]:
                gov.update(u=c.utilisation, name=name, Fcd=Fcd, Rcd=Rcd)
            if inp["T"] > 0:
                Ftd = calc.formula("F_t,d", "γ_Q T − γ_G,fav (G + ΔW)",
                                   max(gQ * inp["T"] - gGf * Gt, 0.0), "kN",
                                   "Design tension load (net of the favourable permanent load)")
                Rtd = calc.formula("R_t,d", "R_s,k / γ_s,t", Rsk / gst, "kN",
                                   "Design tensile resistance", ref="7.6.3")
                calc.check(calc.tr("{name} tension: F_t,d ≤ R_t,d", name=name), Ftd, Rtd, "kN",
                           "7.6.3.1", hint=HINT_TEN)

        cls._lateral(calc, inp, na, layers, gov)
        cls._structural(calc, inp, na, gov)
        z, qs_z = prof["z"], prof["qs"]
        Rz = np.concatenate([[0], np.cumsum((qs_z[1:] + qs_z[:-1]) / 2 * np.diff(z))]) * perim
        calc.figure(vertical_diagrams(z / 1000, L / 1000, 0.0, [
            (calc.tr("σ'_v [kN/m²]"), prof["sv"] * 1000, "#8a6d3b"),
            (calc.tr("q_s [kN/m²]"), qs_z * 1000, "#2e9b5f"),
            (calc.tr("R_s(z) [kN]"), Rz / 1000, "#2a6f97")]),
            "Effective stress, unit shaft resistance and cumulative shaft resistance")
        calc.model3d = cls._scene(calc, inp, layers, prof, gov)

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _layer_rows(calc, layers):
        rows, top = [], 0.0
        for i, r in enumerate(layers):
            rows.append([str(i + 1), f"{top / 1000:.1f} – {(top + r['h']) / 1000:.1f}",
                         calc.tr(r["soil"]), f"{r['gamma'] * 1e6:g}",
                         f"{r['phi']:g}" if r["soil"] == "Sand" else "—",
                         f"{r['cu'] * 1e3:g}" if r["soil"] == "Clay" else "—"])
            top += r["h"]
        return rows

    @staticmethod
    def _profile(inp, layers, gphi: float, gcu: float) -> dict:
        """Shaft and base resistance with strengths divided by (γ_φ', γ_cu)."""
        D, L, zw = inp["D"], inp["L"], inp["zw"]
        Kr, dr, eta_b = TYPES[inp["ptype"]]
        z = np.linspace(0.0, L, 301)
        sv = np.zeros_like(z)
        qs = np.zeros_like(z)
        bounds = np.cumsum([0.0] + [r["h"] for r in layers])

        def layer_at(zz):
            i = int(np.searchsorted(bounds, zz, side="right") - 1)
            return layers[min(max(i, 0), len(layers) - 1)]

        def sv_at(zz):
            s, top = 0.0, 0.0
            for r in layers:
                bot = min(top + r["h"], zz)
                if bot > top:
                    dry = max(min(bot, zw) - top, 0.0)
                    s += r["gamma"] * dry + (r["gamma"] - GW) * (bot - top - dry)
                top += r["h"]
                if top >= zz:
                    break
            return s

        for i, zz in enumerate(z):
            r = layer_at(min(zz, L - 1e-6))
            sv[i] = sv_at(zz)
            if r["soil"] == "Clay":
                qs[i] = inp["alpha"] * r["cu"] / gcu
            else:
                ph = math.atan(math.tan(math.radians(r["phi"])) / gphi)
                qs[i] = Kr * (1 - math.sin(ph)) * math.tan(dr * ph) * sv[i]
        perim = math.pi * D
        Rs = float(np.trapezoid(qs, z)) * perim
        rows, top = [], 0.0
        for k, r in enumerate(layers):
            a, b = top, min(top + r["h"], L)
            top += r["h"]
            if b <= a:
                continue
            m = (z >= a - 1e-9) & (z <= b + 1e-9)
            Rk = float(np.trapezoid(qs[m], z[m])) * perim
            rows.append([str(k + 1), r["soil"], f"{(b - a) / 1000:.2f}",
                         f"{Rk / (perim * (b - a)) * 1000:.1f}", f"{Rk / 1000:.0f}"])
        rt = layer_at(L - 1e-6)
        sv_toe = sv[-1]
        if rt["soil"] == "Clay":
            qb = 9 * rt["cu"] / gcu
            expr = "9 c_u"
        else:
            ph = math.degrees(math.atan(math.tan(math.radians(rt["phi"])) / gphi))
            Nq = nq_meyerhof(ph)
            qb = eta_b * min(Nq * sv_toe, 0.5 * 0.1 * Nq * math.tan(math.radians(ph)))
            expr = (f"η_b min(N_q* σ'_v, 0.5 p_a N_q* tan φ'), N_q* = {Nq:.0f} (Meyerhof), "
                    f"σ'_v = {sv_toe * 1000:.0f} kN/m²")
        # total (not effective) vertical stress at the toe for the displaced-soil weight
        sv_tot = sv_toe + GW * max(L - zw, 0.0)
        return {"z": z, "sv": sv, "qs": qs, "Rs": Rs, "qb": qb, "Rb": qb * math.pi * D**2 / 4,
                "qb_expr": expr, "rows": rows, "sv_toe_total": sv_tot}

    @classmethod
    def _lateral(cls, calc, inp, na, layers, gov) -> None:
        D, L, e = inp["D"], inp["L"], inp["e"]
        top = layers[0]
        calc.heading("Lateral resistance — Broms (1964), free head")
        calc.text("Homogeneous soil with the properties of the top layer ({s}); the "
                  "resistance of the upper soil governs the lateral behaviour.",
                  s=calc.tr(top["soil"]))
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyd = na.alpha_cc * fck / na.gamma_c, inp["fyk"] / na.gamma_s
        dcal = cls._dcal(inp)
        My = circular_moment_resistance(dcal, inp["nbar"], float(inp["dia"]),
                                        inp["cover"] - (D - dcal) / 2, fcd, fyd, inp["G"])[0]
        calc.formula("M_y", "M_Rd of the pile section at N = G_k", My, "kNm",
                     "Yield moment for Broms' long-pile mode")
        zr = min(L, 5 * D)
        prof = cls._profile(inp, layers, 1.0, 1.0)
        gam = float(np.interp(zr, prof["z"], prof["sv"])) / zr
        calc.formula("γ'_avg", "σ'_v(5D) / 5D", gam, "kN/m³", "Mean effective unit weight", dp=2)
        worst = None
        for name in na.combinations(inp["approach"]):
            gG, _, gQ, gphi, gcf, _, _ = na.combos[name]
            gcu = na.gamma_cu_M2 if gphi > 1.0 else 1.0
            gRe = na.gRe(name)
            cu = top["cu"] / gcu
            phi = math.atan(math.tan(math.radians(top["phi"])) / gphi) if top["phi"] > 0 else 0
            Hu, mode, Mm = broms(top["soil"], D, L, e, My, cu, gam, phi)
            Hd = gG * inp["HG"] + gQ * inp["HQ"]
            HRd = Hu / gRe
            calc.heading(name, 2)
            if top["soil"] == "Clay":
                calc.formula("c_u,d", "c_u / γ_cu", cu, "kN/m²", dp=1)
            else:
                calc.formula("φ'_d", "atan(tan φ' / γ_φ')", math.degrees(phi), "°", dp=1)
            calc.formula("H_u", calc.tr("Broms, {m} pile", m=calc.tr(mode)), Hu, "kN",
                         "Ultimate lateral resistance")
            calc.formula("H_Rd", "H_u / γ_R,e", HRd, "kN",
                         calc.tr("Design lateral resistance (γ_R,e = {g:g})", g=gRe))
            calc.formula("H_d", "γ_G H_G + γ_Q H_Q", Hd, "kN", "Design horizontal load")
            calc.check(calc.tr("{name} lateral: H_d ≤ H_Rd", name=name), Hd, HRd, "kN",
                       "EN 1997-1 7.7", hint=HINT_LAT)
            Med = Mm * Hd / Hu if Hu > 0 else 0.0
            if worst is None or Med > worst[0]:
                worst = (Med, name)
        gov["Mmax"] = worst[0] if worst else 0.0
        calc.note("Pile head displacement is not calculated here — check it with a subgrade "
                  "reaction analysis where the structure is sensitive to movement.")

    @staticmethod
    def _dcal(inp) -> float:
        """EN 1992-1-1 2.3.4.2(2): reduced design diameter of cast-in-place piles."""
        D = inp["D"]
        if inp["ptype"] == "Driven":
            return D
        if D < 400:
            return 0.95 * D
        return D - 20 if D <= 1000 else 0.98 * D

    @classmethod
    def _structural(cls, calc, inp, na, gov) -> None:
        calc.heading("Structural check of the pile (EN 1992-1-1)")
        D = inp["D"]
        dcal = cls._dcal(inp)
        calc.formula("d_cal", "EN 1992-1-1 2.3.4.2(2)" if inp["ptype"] != "Driven"
                     else "d_nom (precast)", dcal, "mm", "Design diameter")
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd = calc.formula("f_cd", "α_cc f_ck / γ_c", na.alpha_cc * fck / na.gamma_c, "N/mm²",
                           dp=2)
        fyd = inp["fyk"] / na.gamma_s
        dia, n = float(inp["dia"]), inp["nbar"]
        As = calc.formula("A_s", f"{n} Ø{dia:g}", n * bar_area(dia), "mm²", "Longitudinal bars")
        Ac = math.pi * dcal**2 / 4
        calc.check_min("Minimum reinforcement A_s ≥ 0.5 % A_c (A_c ≤ 0.5 m²)", As,
                       0.005 * min(Ac, 0.5e6) if Ac <= 1e6 else 0.0025 * Ac, "mm²",
                       "EN 1992-1-1 9.8.5 Table 9.6N", hint=HINT_STR)
        NEd = gov.get("Fcd", 0.0)
        NRd = calc.formula("N_Rd", "A_c f_cd + A_s f_yd", Ac * fcd + As * fyd, "kN",
                           "Axial resistance (pile laterally restrained by the soil)")
        calc.check("Axial: N_Ed ≤ N_Rd", NEd, NRd, "kN", "6.1", hint=HINT_STR)
        MRd = circular_moment_resistance(dcal, n, dia, inp["cover"] - (D - dcal) / 2, fcd, fyd,
                                         NEd)[0]
        calc.formula("M_Ed", "M_max (Broms) at H_d", gov.get("Mmax", 0.0), "kNm",
                     "Maximum moment in the pile")
        calc.check("Bending with axial force: M_Ed ≤ M_Rd(N_Ed)", gov.get("Mmax", 0.0), MRd,
                   "kNm", "6.1", hint=HINT_STR)

    # ---------------------------------------------------------------- 3D
    @staticmethod
    def _scene(calc, inp, layers, prof, gov) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        D, L, zw = m(inp["D"]), m(inp["L"]), m(inp["zw"])
        sc = Scene3D("pile", calc.tr)
        for key, label in (("pile", "Pile"), ("soil", "Soil layers"), ("water", "Groundwater"),
                           ("shaft", "Shaft resistance"), ("loads", "Loads")):
            sc.layer(key, label, toggle=key != "pile")
        W = max(6 * D, 4.0)
        top = 0.0
        cols = {"Clay": "#a88b6a", "Sand": PALETTE["soil"]}
        for i, r in enumerate(layers):
            h = m(r["h"])
            if top >= L + 3:
                break
            hh = min(h, L + 3 - top)
            sc.box("soil", (0, -top - hh / 2, 0), (W, hh, W), cols[r["soil"]],
                   opacity=0.12 + 0.05 * (i % 2), edges=True)
            sc.label("soil", f"{calc.tr(r['soil'])} {i + 1}", (W / 2, -top - hh / 2, W / 2),
                     "")
            top += h
        if zw < L + 3:
            sc.box("water", (0, -zw, 0), (W, 0.01, W), PALETTE["water"], opacity=0.35,
                   edges=False)
            sc.label("water", "▽ GWL", (-W / 2, -zw + 0.15, W / 2), "")
        sc.cylinder("pile", (0, 0.5, 0), (0, -L, 0), D / 2, PALETTE["concrete"])
        qs, z = prof["qs"], prof["z"]
        qmax = float(qs.max()) or 1.0
        for zz, q in zip(z[::25], qs[::25]):
            ln = 0.15 + 0.9 * q / qmax
            for ang in (0, math.pi):
                d = (math.cos(ang), 0, math.sin(ang))
                sc.arrow("shaft", (d[0] * (D / 2 + ln + 0.05), -m(zz), 0), (-d[0], 0, 0), ln,
                         PALETTE["bearing"], 0.12)
        sc.arrow("shaft", (0, -L - 1.0, 0), (0, 1, 0), 0.9, PALETTE["bearing"], 0.25)
        sc.label("shaft", calc.tr("R_b,cal = {r:.0f} kN", r=prof["Rb"] / 1000),
                 (D, -L - 0.8, 0), "result")
        sc.label("shaft", calc.tr("R_s,cal = {r:.0f} kN", r=prof["Rs"] / 1000),
                 (D + 1.0, -L / 2, 0), "result")
        if gov.get("Fcd"):
            sc.arrow("loads", (0, 2.3, 0), (0, -1, 0), 1.7, PALETTE["load"], 0.3)
            sc.label("loads", calc.tr("F_c,d = {f:.0f} kN ({n})", f=gov["Fcd"] / 1000,
                                      n=gov["name"]), (0, 2.5, 0), "result")
        H = inp["HG"] + inp["HQ"]
        if H > 0:
            sc.arrow("loads", (-2.0, 0.3 + m(inp["e"]), 0), (1, 0, 0), 1.6, PALETTE["load"],
                     0.25)
        sc.views["default"] = {"pos": [L * 0.9, 2, L * 1.1], "target": [0, -L / 2, 0]}
        return sc.to_dict()
