"""Liquefaction potential of sandy layers from SPT — EN 1998-5 §4.1.4 and Annex B.

Seismic shear stress τ_e = 0.65 α S σ_v0 (Eq. 4.3).  Cyclic resistance from the corrected blow
count (N1)60 with the fines correction and the CRR curve of Youd et al. (2001, NCEER), which
reproduces the empirical chart of EN 1998-5 Annex B, scaled by the magnitude factor C_M of
Table B.1.  Safety factor λ of the National Annex (4.1.4(11)).
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..report.scene3d import Scene3D, heat_color

GW = 9.81e-6
CM = {5.5: 2.86, 6.0: 2.20, 6.5: 1.69, 7.0: 1.30, 7.5: 1.00, 8.0: 0.67}  # Table B.1 (7.5: 1)
HINT = ("Improve the ground (vibro-compaction, stone columns, grouting), lower the water table, "
        "or found on piles through the liquefiable layer.")


def crr75(n: float) -> float:
    """Youd et al. (2001) clean-sand CRR for M = 7.5; ∞ for (N1)60cs ≥ 30."""
    if n >= 30:
        return math.inf
    return 1 / (34 - n) + n / 135 + 50 / (10 * n + 45) ** 2 - 1 / 200


def fines(n160: float, fc: float) -> float:
    if fc <= 5:
        a, b = 0.0, 1.0
    elif fc >= 35:
        a, b = 5.0, 1.2
    else:
        a, b = math.exp(1.76 - 190 / fc**2), 0.99 + fc**1.5 / 1000
    return a + b * n160


@register
class LiquefactionEC8(DesignModule):
    id = "ec8_5_liquefaction"
    title = "Liquefaction potential"
    category = "Geotechnical"
    has_3d = True
    uses_annex = True
    standard = "EN 1998-5 §4.1.4, Annex B"
    description = ("Saturated sandy layers from SPT blow counts: overburden and fines "
                   "corrections, cyclic resistance with the magnitude factor C_M, seismic shear "
                   "stress τ_e and the factor of safety against liquefaction for each layer. "
                   "Interactive 3D soil column.")

    fields = [
        Field("ag", "Reference ground acceleration a_gR", "", 0.25, min=0, max=0.6,
              group="Earthquake", help="In g; zone buttons of the National Annex."),
        Field("importance", "Importance class", kind="choice", choices=["I", "II", "III", "IV"],
              default="II", group="Earthquake"),
        Field("S", "Soil factor S", "", 1.15, min=1.0, max=1.8, group="Earthquake",
              help="EN 1998-1 Table 3.2 (ground type C: 1.15)."),
        Field("Ms", "Surface wave magnitude M_s", kind="choice",
              choices=["5.5", "6.0", "6.5", "7.0", "7.5", "8.0"], default="6.5", group="Earthquake",
              help="Design earthquake magnitude for the site."),
        Field("zw", "Groundwater depth", "m", 2.0, min=0, group="Ground"),
        Field("layers", "Soil layers (from the surface down)", kind="table", group="Ground",
              default=[
                  {"h": 2.0, "soil": "Sand", "gamma": 18.0, "N60": 12, "FC": 10.0},
                  {"h": 4.0, "soil": "Sand", "gamma": 19.0, "N60": 18, "FC": 8.0},
                  {"h": 3.0, "soil": "Silty sand", "gamma": 19.0, "N60": 17, "FC": 25.0},
                  {"h": 6.0, "soil": "Sand", "gamma": 20.0, "N60": 28, "FC": 5.0},
                  {"h": 5.0, "soil": "Clay", "gamma": 20.0, "N60": 20, "FC": 70.0}],
              columns=[Field("h", "Thickness", "m", 2.0, min=0.2),
                       Field("soil", "Soil", kind="choice",
                             choices=["Sand", "Silty sand", "Clay"], default="Sand"),
                       Field("gamma", "γ", "kN/m³", 19.0, min=10),
                       Field("N60", "SPT N_60", "", 10.0, min=0, max=100),
                       Field("FC", "Fines content", "%", 10.0, min=0, max=100)],
              help="N_60: SPT blow count corrected to 60 % energy. Clays (FC > 35 % plastic) "
                   "are not checked."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        layers = inp["layers"]
        if not layers:
            raise InputError("Add at least one soil layer", "layers")
        gI = na.gamma_I[inp["importance"]]
        alpha = gI * inp["ag"]
        S = inp["S"]
        Ms = float(inp["Ms"])
        cm = float(np.interp(Ms, list(CM), list(CM.values())))
        lam = na.liq_lambda
        zw = inp["zw"]
        calc.heading("Seismic action")
        calc.input("a_gR", inp["ag"], "", "Reference ground acceleration [g]", dp=3)
        calc.formula("α", "γ_I a_gR / g", alpha, "", calc.tr("γ_I = {g:g}", g=gI), dp=3)
        calc.input("S", S, "", "Soil factor", dp=2)
        calc.formula("αS", "α S", alpha * S, "", dp=3)
        if alpha * S < 0.15:
            calc.note("αS < 0.15: EN 1998-5 4.1.4(4) allows liquefaction to be neglected for "
                      "sands with clay content > 20 % (PI > 10), silt > 35 % with N1,60 > 20, "
                      "or clean sands with N1,60 > 30.")
        calc.formula("C_M", "Table B.1", cm, "", calc.tr("Magnitude factor, M_s = {m:g}", m=Ms),
                     ref="EN 1998-5 B", dp=2)
        calc.input("λ", lam, "", "Required safety factor (National Annex)", dp=2)
        calc.heading("Layers below the water table")
        calc.text("τ_e = 0.65 α S σ_v0 (Eq. 4.3); C_N = (100/σ'_v0)^½ with 0.5 ≤ C_N ≤ 2 "
                  "(B.1(4)); (N1)60,cs with the fines correction; CRR_7.5 by Youd et al. (2001); "
                  "factor of safety FS = C_M CRR_7.5 σ'_v0 / τ_e ≥ λ.")
        top, rows, res = 0.0, [], []
        for i, r in enumerate(layers):
            zm = top + r["h"] / 2
            sv = sv_e = 0.0
            t2 = 0.0
            for rr in layers:
                b = min(t2 + rr["h"], zm)
                if b > t2:
                    sv += rr["gamma"] * (b - t2)
                    sv_e += rr["gamma"] * (b - t2) - GW * max(b - max(t2, zw), 0.0)
                t2 += rr["h"]
                if t2 >= zm:
                    break
            fc = r["FC"] * 100  # field unit % → stored as a fraction
            row = [str(i + 1), f"{top / 1000:.1f}–{(top + r['h']) / 1000:.1f}", calc.tr(r["soil"]),
                   f"{r['N60']:g}", f"{fc:g}"]
            if r["soil"] == "Clay" or zm <= zw or zm > 20000:
                why = ("clay" if r["soil"] == "Clay" else "above water" if zm <= zw else "> 20 m")
                rows.append(row + ["—"] * 5 + [calc.tr(why)])
                res.append((r, None))
            else:
                CN = min(max(math.sqrt(100e-3 / sv_e), 0.5), 2.0)
                n1 = CN * r["N60"]
                ncs = fines(n1, fc)
                crr = crr75(ncs) * cm
                tau = 0.65 * alpha * S * sv
                FS = crr * sv_e / tau if tau > 0 else math.inf
                rows.append(row + [f"{sv_e * 1000:.0f}", f"{n1:.1f}", f"{ncs:.1f}",
                                   "∞" if math.isinf(crr) else f"{crr:.3f}",
                                   "∞" if math.isinf(FS) else f"{FS:.2f}",
                                   calc.tr("OK") if FS >= lam else calc.tr("Liquefiable")])
                res.append((r, FS))
                if math.isfinite(FS):
                    calc.check_min(calc.tr("Layer {i} at z = {z:.1f} m: FS ≥ λ", i=i + 1, z=zm / 1000),
                                   FS, lam, "", "EN 1998-5 4.1.4(11)", hint=HINT)
            top += r["h"]
        calc.table(["Layer", "z [m]", "Soil", "N_60", "FC [%]", "σ'_v0 [kN/m²]", "(N1)60",
                    "(N1)60,cs", "C_M CRR", "FS", "Result"], rows,
                   caption="Liquefaction assessment at the middle of each layer")
        if not any(fs is not None for _, fs in res):
            calc.note("No saturated sandy layer within 20 m — no liquefaction check needed.")
        calc.model3d = cls._scene(calc, inp, res, lam)

    @staticmethod
    def _scene(calc, inp, res, lam) -> dict:
        sc = Scene3D("liquefaction", calc.tr)
        sc.layer("soil", "Soil layers", toggle=False)
        sc.layer("water", "Groundwater")
        sc.layer("notes", "Results")
        top = 0.0
        for i, (r, fs) in enumerate(res):
            h = r["h"] / 1000
            if fs is None:
                col = "#a88b6a" if r["soil"] == "Clay" else "#d9bf8c"
            else:
                col = heat_color(1.0 - min(fs / (2 * lam), 1.0))
            sc.box("soil", (0, -top - h / 2, 0), (4, h, 4), col, opacity=0.85)
            txt = f"{calc.tr(r['soil'])}: " + ("—" if fs is None else
                                               ("FS ∞" if math.isinf(fs) else f"FS = {fs:.2f}"))
            sc.label("notes", txt, (2.2, -top - h / 2, 2.2), "result" if fs is None or fs >= lam
                     else "force")
            top += h
        zw = inp["zw"] / 1000
        sc.box("water", (0, -zw, 0), (4.4, 0.02, 4.4), "#2f8fd8", opacity=0.6)
        sc.label("water", "▽ GWL", (-2.4, -zw + 0.2, 2.2), "")
        sc.legend_item(heat_color(1.0), calc.tr("Liquefiable (FS < λ)"))
        sc.legend_item(heat_color(0.0), calc.tr("Safe (FS ≥ 2λ)"))
        return sc.to_dict()
