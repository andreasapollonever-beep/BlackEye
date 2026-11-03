"""Pile cap on 2, 3 or 4 piles — strut-and-tie model, EN 1992-1-1 §6.5 and §9.8.1."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec2 import bar_area
from ..report.scene3d import PALETTE, Scene3D

CONCRETE = ["C25/30", "C30/37", "C35/45"]
BARS = ["16", "20", "25", "32"]
HINT_T = "Use more or larger tie bars, or a deeper cap."
HINT_N = "Increase the column or pile size, or the concrete class."
HINT_A = "Make the cap deeper so that the struts are steeper (θ ≥ 26.5°)."


def layout(n: int, s: float):
    """Pile coordinates (mm) for a spacing s."""
    if n == 2:
        return [(-s / 2, 0.0), (s / 2, 0.0)]
    if n == 3:
        r = s / math.sqrt(3)
        return [(r * math.cos(a), r * math.sin(a)) for a in (math.pi / 2, math.pi * 7 / 6,
                                                             math.pi * 11 / 6)]
    return [(x, y) for x in (-s / 2, s / 2) for y in (-s / 2, s / 2)]


@register
class PileCapEC2(DesignModule):
    id = "ec2_pile_cap"
    title = "Pile cap (strut-and-tie)"
    category = "Concrete"
    has_3d = True
    uses_annex = True
    standard = "EN 1992-1-1 §6.5, §9.8.1"
    description = ("Rigid pile cap on 2, 3 or 4 piles under a column: pile loads with moments, "
                   "strut-and-tie model, tie reinforcement, strut angle and node stresses at "
                   "the column and the piles. Interactive 3D model.")

    fields = [
        Field("n", "Number of piles", kind="choice", choices=["2", "3", "4"], default="4",
              group="Geometry"),
        Field("D", "Pile diameter", "mm", 600.0, min=250, max=1500, group="Geometry"),
        Field("s", "Pile spacing (centre to centre)", "mm", 1800.0, min=600, group="Geometry",
              help="Usually ≥ 3 D."),
        Field("h", "Cap depth h", "mm", 1000.0, min=400, max=3000, group="Geometry"),
        Field("c", "Column size (square)", "mm", 500.0, min=200, group="Geometry"),
        Field("edge", "Edge distance beyond the piles", "mm", 300.0, min=150, group="Geometry"),
        Field("NEd", "Design axial load N_Ed", "kN", 3500.0, min=0, group="Design actions"),
        Field("Mx", "Design moment M_x,Ed", "kNm", 150.0, group="Design actions"),
        Field("My", "Design moment M_y,Ed", "kNm", 0.0, group="Design actions"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C30/37",
              group="Materials"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Materials"),
        Field("cover", "Cover to the tie bars", "mm", 75.0, min=50, group="Materials"),
        Field("nbar", "Tie bars per tie", "", 7, kind="int", min=2, max=30,
              group="Reinforcement"),
        Field("dia", "Tie bar Ø", kind="choice", choices=BARS, default="20",
              group="Reinforcement"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        n, D, s, h, c = int(inp["n"]), inp["D"], inp["s"], inp["h"], inp["c"]
        if s < 2 * D:
            raise InputError("Pile spacing must be at least twice the pile diameter", "s")
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyd = na.alpha_cc * fck / na.gamma_c, inp["fyk"] / na.gamma_s
        dia = float(inp["dia"])
        d = h - inp["cover"] - dia
        piles = layout(n, s)
        N, Mx, My = inp["NEd"], inp["Mx"], inp["My"]
        calc.heading("Pile loads (rigid cap)")
        calc.formula("d", "h − c − φ", d, "mm", "Effective depth to the ties")
        Ixx = sum(y * y for _, y in piles)
        Iyy = sum(x * x for x, _ in piles)
        P = []
        for x, y in piles:
            P.append(N / n + (Mx * x / Iyy if Iyy else 0) + (My * y / Ixx if Ixx else 0))
        rows = [[str(i + 1), f"{x / 1000:.2f}", f"{y / 1000:.2f}", f"{p / 1000:.0f}"]
                for i, ((x, y), p) in enumerate(zip(piles, P))]
        calc.table(["Pile", "x [m]", "y [m]", "P_Ed [kN]"], rows,
                   caption="P = N/n + M_x x/Σx² + M_y y/Σy²")
        Pmax = calc.formula("P_max", "max P_Ed", max(P), "kN", "Governing pile load")
        if min(P) < 0:
            calc.warn("A pile is in tension — check the pile for uplift and anchor its bars.")

        calc.heading("Strut-and-tie model (6.5)")
        z = 0.9 * d
        r = math.hypot(*piles[0])  # distance column centre → pile
        a = max(r - 0.25 * c * (math.sqrt(2) if n == 4 else 1.0), 1.0)
        theta = calc.formula("θ", "atan(z / a), z = 0.9d, a = r − c/4", math.degrees(math.atan(z / a)),
                             "°", calc.tr("Strut angle (r = {r:.0f} mm)", r=r), dp=1)
        calc.check_min("Strut angle θ ≥ 26.5° (cot θ ≤ 2)", theta, 26.5, "°", "6.5.2 / 6.2.3",
                       hint=HINT_A)
        Fh = Pmax * a / z  # horizontal component per pile
        if n == 2:
            T = Fh
            tie = "T = P a / z (one tie between the piles)"
        elif n == 3:
            T = Fh / math.sqrt(3)
            tie = "T = P a / (√3 z) (three ties along the sides)"
        else:
            T = Fh / math.sqrt(2)
            tie = "T = P a / (√2 z) (ties along the sides, both directions)"
        T = calc.formula("T_Ed", tie, T, "kN", "Tie force", ref="6.5.3")
        As = calc.formula("A_s", f"{inp['nbar']} Ø{dia:g}", inp["nbar"] * bar_area(dia), "mm²",
                          "Reinforcement of one tie")
        calc.check("Tie: T_Ed ≤ A_s f_yd", T, As * fyd, "kN", "6.5.3", hint=HINT_T)
        nu = 1 - fck / 250
        calc.heading("Nodes (6.5.4)")
        Ac = c * c
        s_col = calc.formula("σ_c,col", "N_Ed / c²", N / Ac, "N/mm²",
                             "Compression under the column", dp=2)
        calc.check("Column node (C-C-C): σ ≤ 1.0 ν' f_cd", s_col, nu * fcd, "N/mm²", "Eq. 6.60",
                   hint=HINT_N)
        Ap = math.pi * D**2 / 4
        s_p = calc.formula("σ_c,pile", "P_max / (π D²/4)", Pmax / Ap, "N/mm²",
                           "Compression over the pile", dp=2)
        calc.check("Pile node (C-C-T): σ ≤ 0.85 ν' f_cd", s_p, 0.85 * nu * fcd, "N/mm²",
                   "Eq. 6.61", hint=HINT_N)
        calc.heading("Detailing (9.8.1)")
        calc.check_min("Edge distance beyond the pile face ≥ 150 mm", inp["edge"], 150.0, "mm",
                       "good practice", hint="Increase the cap plan size.")
        calc.text("Tie bars over the piles within 1.5 D of the pile centre, anchored beyond the "
                  "pile with a bend (9.8.1(3)); surface reinforcement on the other faces.")
        calc.model3d = cls._scene(calc, inp, piles, P)

    @staticmethod
    def _scene(calc, inp, piles, P) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        h, c, D, e = m(inp["h"]), m(inp["c"]), m(inp["D"]), m(inp["edge"])
        xs = [m(x) for x, _ in piles]
        ys = [m(y) for _, y in piles]
        W = max(xs) - min(xs) + D + 2 * e
        Lz = max(ys) - min(ys) + D + 2 * e
        sc = Scene3D("pile_cap", calc.tr)
        for key, label in (("concrete", "Cap and column"), ("piles", "Piles"),
                           ("struts", "Struts and ties"), ("loads", "Pile loads")):
            sc.layer(key, label, toggle=key != "concrete")
        sc.box("concrete", (0, h / 2, 0), (W, h, Lz), PALETTE["concrete"], opacity=0.45)
        sc.box("concrete", (0, h + 0.75, 0), (c, 1.5, c), "#9aa0a8")
        for x, y, p in zip(xs, ys, P):
            sc.cylinder("piles", (x, 0.1, y), (x, -3.0, y), D / 2, "#b4b8bf")
            sc.line("struts", [(0, h, 0), (x, 0.15, y)], "#e03b3b")
            sc.label("loads", f"{p / 1000:.0f} kN", (x, -0.5, y), "force")
        for i in range(len(xs)):
            j = (i + 1) % len(xs)
            if len(xs) == 4 and i in (1, 3):
                j = (i + 2) % 4 if i == 1 else 0
            sc.line("struts", [(xs[i], 0.15, ys[i]), (xs[j], 0.15, ys[j])], "#2a6f97")
        return sc.to_dict()
