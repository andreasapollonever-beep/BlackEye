"""Fillet weld group — EN 1993-1-8 §4.5.3 (directional and simplified methods).

The weld group is a rectangle of fillet welds (any of its four sides) joining a member end to
a plate, loaded by an axial force N (normal to the plate), a shear V (vertical, in the plate)
and a moment M (about the horizontal axis).  Throat stresses by the elastic method on the
throat area unfolded into the plane of the joint.
"""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec3_bolts import PLATE
from ..report.scene3d import PALETTE, Scene3D

BETA_W = {"S235": 0.8, "S275": 0.85, "S355": 0.9}  # Table 4.1
HINT = "Increase the throat thickness a, weld more sides or use longer welds."


@register
class WeldEC3(DesignModule):
    id = "ec3_weld"
    title = "Fillet weld group"
    category = "Steel"
    has_3d = True
    uses_annex = True
    standard = "EN 1993-1-8 §4.5"
    description = ("Rectangular group of fillet welds under axial force, shear and bending: "
                   "throat stresses σ⊥, τ⊥, τ∥ by the directional method (Eq. 4.1) and the "
                   "simplified method, with the weld detailing rules. Interactive 3D model.")

    fields = [
        Field("b", "Width of the weld group b (horizontal welds)", "mm", 200.0, min=20,
              group="Weld group"),
        Field("h", "Height of the weld group h (vertical welds)", "mm", 300.0, min=20,
              group="Weld group"),
        Field("top", "Weld along the top (horizontal)", kind="bool", default=True,
              group="Weld group"),
        Field("bottom", "Weld along the bottom (horizontal)", kind="bool", default=True,
              group="Weld group"),
        Field("sides", "Welds along both sides (vertical)", kind="bool", default=True,
              group="Weld group"),
        Field("a", "Throat thickness a", "mm", 5.0, min=3, max=20, group="Weld group",
              help="a ≥ 3 mm (4.5.2(2)); leg length ≈ 1.41 a."),
        Field("grade", "Steel grade (weaker part)", kind="choice", choices=list(PLATE),
              default="S275", group="Weld group"),
        Field("t", "Thickness of the thinner part", "mm", 12.0, min=3, group="Weld group"),
        Field("N", "Axial force N_Ed (tension +)", "kN", 150.0, group="Design actions"),
        Field("V", "Shear force V_Ed (vertical)", "kN", 120.0, min=0, group="Design actions"),
        Field("M", "Moment M_Ed (about the horizontal axis)", "kNm", 20.0,
              group="Design actions"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        gM2 = na.gamma_M2
        b, h, a = inp["b"], inp["h"], inp["a"]
        if not (inp["top"] or inp["bottom"] or inp["sides"]):
            raise InputError("Choose at least one weld", "top")
        fu = PLATE[inp["grade"]][1]
        bw = BETA_W[inp["grade"]]
        calc.heading("Weld group (throat area unfolded into the joint plane)")
        nh = int(inp["top"]) + int(inp["bottom"])
        Lh, Lv = nh * b, (2 * h if inp["sides"] else 0.0)
        Aw = calc.formula("A_w", "a (Σ l_horizontal + Σ l_vertical)", a * (Lh + Lv), "mm²",
                          "Throat area")
        Av = a * Lv
        # second moment about the horizontal centroidal axis
        yc = 0.0
        if nh == 1:  # one horizontal weld: centroid moves
            yh = h / 2 if inp["top"] else -h / 2
            yc = (a * b * yh) / (a * (Lh + Lv)) if Aw else 0.0
        Iw = 0.0
        if inp["top"]:
            Iw += a * b * (h / 2 - yc) ** 2
        if inp["bottom"]:
            Iw += a * b * (-h / 2 - yc) ** 2
        if inp["sides"]:
            Iw += 2 * (a * h**3 / 12 + a * h * yc**2)
        Iw = calc.formula("I_w", "Σ a l y²  (+ a h³/12 for vertical welds)", Iw, "cm⁴",
                          "Second moment of the throat area")
        ymax = h / 2 + abs(yc)
        calc.input("f_u", fu, "N/mm²", calc.tr("Ultimate strength ({g})", g=inp["grade"]))
        calc.input("β_w", bw, "", "Correlation factor (Table 4.1)", dp=2)
        calc.text("γ_M2 = {g:g} (National Annex).", g=gM2)

        calc.heading("Detailing (4.5.2, 4.5.4)")
        calc.check_min("Throat a ≥ 3 mm", a, 3.0, "mm", "4.5.2(2)", hint=HINT)
        calc.check_limit("Throat a ≤ 0.7 t (practical maximum)", a, 0.7 * inp["t"], "mm",
                         "good practice", hint="Reduce a or check the thinner part.")
        for L_, name in ((b, "b"), (h, "h")):
            calc.check_min(calc.tr("Weld length {n} ≥ max(30 mm, 6a)", n=name), L_,
                           max(30.0, 6 * a), "mm", "4.5.4(1)", hint=HINT)

        calc.heading("Throat stresses — directional method (4.5.3.2)")
        N, V, M = inp["N"], inp["V"], inp["M"]
        sw = calc.formula("σ_w", "N/A_w + M y_max / I_w", abs(N) / Aw + abs(M) * ymax / Iw,
                          "N/mm²", "Normal stress on the unfolded throat (extreme fibre)", dp=1)
        s_perp = calc.formula("σ⊥ = τ⊥", "σ_w / √2", sw / math.sqrt(2), "N/mm²",
                              "Fillet weld at 45°", dp=1)
        if Av > 0:
            t_par = calc.formula("τ∥", "V / (a Σ l_vertical)", V / Av, "N/mm²",
                                 "Shear along the vertical welds", dp=1)
        else:
            t_par = 0.0
            if V > 0:
                calc.warn("Without vertical welds the shear is carried across the horizontal "
                          "welds (τ⊥) — conservatively added to the normal stress.")
                s_perp = math.hypot(s_perp, V / Aw)
        seq = calc.formula("σ_eq", "√(σ⊥² + 3(τ⊥² + τ∥²))",
                           math.sqrt(s_perp**2 + 3 * (s_perp**2 + t_par**2)), "N/mm²", dp=1)
        calc.check("Weld: √(σ⊥² + 3(τ⊥² + τ∥²)) ≤ f_u/(β_w γ_M2)", seq, fu / (bw * gM2),
                   "N/mm²", "Eq. 4.1", hint=HINT)
        calc.check("Weld: σ⊥ ≤ 0.9 f_u / γ_M2", s_perp, 0.9 * fu / gM2, "N/mm²", "Eq. 4.1",
                   hint=HINT)

        calc.heading("Simplified method (4.5.3.3) — for information")
        fvw = calc.formula("f_vw,d", "f_u / (√3 β_w γ_M2)", fu / (math.sqrt(3) * bw * gM2),
                           "N/mm²", ref="Eq. 4.4", dp=1)
        res = math.sqrt(sw**2 + t_par**2)
        calc.formula("F_w,Ed / a", "√(σ_w² + τ∥²)", res, "N/mm²",
                     "Resultant stress per unit throat (most stressed point)", dp=1)
        calc.formula("utilisation", "F_w,Ed / F_w,Rd", res / fvw, "", dp=3)
        calc.model3d = cls._scene(calc, inp, seq / (fu / (bw * gM2)))

    @staticmethod
    def _scene(calc, inp, u) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        b, h, a = m(inp["b"]), m(inp["h"]), m(inp["a"]) * 1.41
        sc = Scene3D("weld", calc.tr)
        for key, label in (("steel", "Plates"), ("weld", "Welds"), ("loads", "Loads")):
            sc.layer(key, label, toggle=key != "steel")
        sc.box("steel", (0, 0, -0.01), (b + 0.2, h + 0.2, 0.02), "#7d8794")
        sc.box("steel", (0, 0, 0.15), (b, h, 0.3), PALETTE["steel"], opacity=0.5)
        col = "#e03b3b" if u > 1 else "#e3a008" if u > 0.8 else "#2e9b5f"
        if inp["top"]:
            sc.box("weld", (0, h / 2 + a / 2, a / 2), (b, a, a), col)
        if inp["bottom"]:
            sc.box("weld", (0, -h / 2 - a / 2, a / 2), (b, a, a), col)
        if inp["sides"]:
            for sx in (-1, 1):
                sc.box("weld", (sx * (b / 2 + a / 2), 0, a / 2), (a, h, a), col)
        sc.arrow("loads", (0, 0, 0.9), (0, 0, -1), 0.5, PALETTE["load"], 0.06)
        sc.arrow("loads", (b / 2 + 0.25, h / 2 + 0.3, 0.3), (0, -1, 0), 0.3, "#e03b3b", 0.05)
        sc.label("loads", calc.tr("U = {u:.2f}", u=u), (0, h / 2 + 0.15, 0.3), "result")
        return sc.to_dict()
