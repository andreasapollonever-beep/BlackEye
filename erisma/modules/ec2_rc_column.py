"""RC column — EN 1992-1-1 §5.8 (slenderness, nominal curvature, biaxial) and EN 1998-1 §5.4."""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..design.annex import get_annex
from ..design.ec2 import ES, bar_area, moment_resistance, section_layers
from ..report.scene3d import PALETTE, Scene3D

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "C45/55", "C50/60"]
BARS = ["12", "14", "16", "18", "20", "22", "25", "28", "32"]
LINKS = ["8", "10", "12"]
HINT_COL = "Increase the column size or the longitudinal reinforcement."


@register
class RCColumnEC2(DesignModule):
    id = "ec2_rc_column"
    title = "RC column"
    category = "Concrete"
    standard = "EN 1992-1-1 §5.8, EN 1998-1 §5.4"
    uses_annex = True
    has_3d = True
    description = ("Rectangular column: imperfections, slenderness, second-order effects "
                   "(nominal curvature), biaxial bending (5.8.9), shear, detailing and EC8 DCM "
                   "rules. Interactive 3D with reinforcement.")

    fields = [
        Field("b", "Width b", "mm", 400.0, min=200, group="Section"),
        Field("h", "Depth h (bending about the strong axis)", "mm", 400.0, min=200,
              group="Section"),
        Field("cover", "Cover to links", "mm", 30.0, min=15, group="Section"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C25/30",
              group="Section"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Section"),
        Field("dia", "Longitudinal bars Ø", kind="choice", choices=BARS, default="16",
              group="Reinforcement"),
        Field("nb", "Bars along b (each face, incl. corners)", kind="int", default=4, min=2,
              group="Reinforcement"),
        Field("nh", "Bars along h (each face, incl. corners)", kind="int", default=4, min=2,
              group="Reinforcement"),
        Field("link", "Links Ø", kind="choice", choices=LINKS, default="8",
              group="Reinforcement"),
        Field("s", "Link spacing", "mm", 100.0, min=50, group="Reinforcement"),
        Field("L", "Clear height", "m", 3.0, min=0.5, group="Geometry"),
        Field("k_h", "Effective length factor (bending in h)", "", 1.0, min=0.5, max=2.5,
              group="Geometry", help="0.5 fixed–fixed, 0.7 fixed–pinned, 1.0 pinned–pinned, "
                                     "2.0 cantilever (or EN 1992-1-1 Eq. 5.15/5.16)."),
        Field("k_b", "Effective length factor (bending in b)", "", 1.0, min=0.5, max=2.5,
              group="Geometry"),
        Field("braced", "Braced column", kind="bool", default=True, group="Geometry",
              help="Unbraced columns use r_m = 1.0 (C = 0.7)."),
        Field("NEd", "Axial force N_Ed (compression +)", "kN", 1200.0, min=0,
              group="Design actions"),
        Field("Mh_top", "M_Ed (h) at top", "kNm", 60.0, group="Design actions",
              help="First-order end moments; same sign = single curvature."),
        Field("Mh_bot", "M_Ed (h) at bottom", "kNm", -30.0, group="Design actions"),
        Field("Mb_top", "M_Ed (b) at top", "kNm", 20.0, group="Design actions"),
        Field("Mb_bot", "M_Ed (b) at bottom", "kNm", -10.0, group="Design actions"),
        Field("VEd", "Shear V_Ed", "kN", 60.0, min=0, group="Design actions"),
        Field("phi_ef", "Effective creep ratio φ_ef", "", 0.8, min=0, max=3,
              group="Design actions"),
        Field("seismic", "Primary seismic column (EN 1998-1 DCM)", kind="bool", default=True,
              group="Seismic"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        b, h, c = inp["b"], inp["h"], inp["cover"]
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd = na.alpha_cc * fck / na.gamma_c
        fyd = inp["fyk"] / na.gamma_s
        dia, dl = float(inp["dia"]), float(inp["link"])
        nb, nh = inp["nb"], inp["nh"]
        n_bars = 2 * nb + 2 * nh - 4
        As = n_bars * bar_area(dia)
        Ac = b * h
        NEd = inp["NEd"]
        if NEd <= 0:
            raise InputError("Give a compressive axial force N_Ed > 0", "NEd")
        cb = c + dl + dia / 2

        calc.heading("Section and materials")
        calc.input("b × h", b, "mm", calc.tr("Column {b:g} × {h:g} mm", b=b, h=h))
        calc.formula("f_cd", "α_cc f_ck / γ_c", fcd, "N/mm²", ref="3.1.6")
        calc.formula("f_yd", "f_yk / γ_s", fyd, "N/mm²")
        calc.formula("A_s", calc.tr("{n}Ø{d:g}", n=n_bars, d=dia), As, "mm²",
                     "Longitudinal reinforcement")
        omega = calc.formula("ω", "A_s f_yd / (A_c f_cd)", As * fyd / (Ac * fcd), "", dp=3)
        n = calc.formula("n", "N_Ed / (A_c f_cd)", NEd / (Ac * fcd), "", "Relative axial force",
                         dp=3)
        NRd = calc.formula("N_Rd", "A_c f_cd + A_s f_yd", Ac * fcd + As * fyd, "kN",
                           "Squash load")
        calc.check("Axial: N_Ed ≤ N_Rd", NEd, NRd, "kN", "6.1", hint=HINT_COL)

        res = {}
        for ax, hh, bb, k, (Mt, Mb) in (("h", h, b, inp["k_h"], (inp["Mh_top"], inp["Mh_bot"])),
                                        ("b", b, h, inp["k_b"], (inp["Mb_top"], inp["Mb_bot"]))):
            calc.heading(calc.tr("Bending in {ax} — slenderness and second order", ax=ax))
            l0 = calc.formula(f"l_0,{ax}", "k L", k * inp["L"], "m", "Effective length")
            lam = calc.formula(f"λ_{ax}", "l_0 √12 / " + ax, l0 * math.sqrt(12) / hh, "",
                               "Slenderness", ref="5.8.3.2", dp=1)
            M01, M02 = sorted((Mt, Mb), key=abs)
            rm = 1.0 if not inp["braced"] or abs(M02) < 1e-9 else M01 / M02
            A = 1 / (1 + 0.2 * inp["phi_ef"])
            B = math.sqrt(1 + 2 * omega)
            C = 1.7 - rm
            lim = calc.formula(f"λ_lim,{ax}", "20 A B C / √n", 20 * A * B * C / math.sqrt(n), "",
                               calc.tr("A = {a:.3f}, B = {b:.3f}, C = {c:.3f}", a=A, b=B, c=C),
                               ref="Eq. 5.13N", dp=1)
            ei = calc.formula(f"e_i,{ax}", "l_0 / 400", l0 / 400, "mm", "Geometric imperfection",
                              ref="5.2(7)")
            e0 = max(hh / 30, 20.0)
            M02e = abs(M02) + NEd * ei
            M01e = abs(M01) * (1 if rm >= 0 else -1) + NEd * ei
            M2 = 0.0
            if lam > lim:
                d = hh - cb
                eyd = fyd / ES
                Kr = min((1 + omega - n) / (1 + omega - 0.4), 1.0)
                beta = 0.35 + fck / 200 - lam / 150
                Kphi = max(1 + beta * inp["phi_ef"], 1.0)
                curv = Kr * Kphi * eyd / (0.45 * d)
                e2 = curv * l0**2 / 10
                calc.text("λ > λ_lim — second-order effects (nominal curvature, 5.8.8).")
                calc.formula("K_r", "(n_u − n)/(n_u − n_bal) ≤ 1", Kr, "", ref="Eq. 5.36", dp=3)
                calc.formula("K_φ", "1 + β φ_ef ≥ 1", Kphi, "", ref="Eq. 5.37", dp=3)
                calc.formula("e_2", "K_r K_φ ε_yd/(0.45 d) l_0² / 10", e2, "mm", ref="5.8.8.2")
                M2 = calc.formula(f"M_2,{ax}", "N_Ed e_2", NEd * e2, "kNm", "Second-order moment")
                M0e = max(0.6 * M02e + 0.4 * M01e, 0.4 * M02e)
                MEd = max(M02e, M0e + M2, abs(M01e) + 0.5 * M2, NEd * e0)
            else:
                calc.text("λ ≤ λ_lim — second-order effects may be ignored (5.8.3.1).")
                MEd = max(M02e, NEd * e0)
            MEd = calc.formula(f"M_Ed,{ax}", "max(M_02 + N e_i, M_0e + M_2, N e_0)", MEd, "kNm",
                               calc.tr("Design moment (e_0 = max({ax}/30, 20 mm) = {e:.0f} mm)",
                                       ax=ax, e=e0), ref="5.8.8.2 / 6.1(4)")
            layers = section_layers(bb, hh, nb if ax == "h" else nh, nh if ax == "h" else nb,
                                    dia, cb)
            MRd, x = moment_resistance(bb, hh, layers, fcd, fyd, NEd)
            MRd = calc.formula(f"M_Rd,{ax}", "strain compatibility at N_Ed", MRd, "kNm",
                               calc.tr("Moment resistance (x = {x:.0f} mm)", x=x), ref="6.1")
            calc.check(calc.tr("Bending in {ax}: M_Ed ≤ M_Rd", ax=ax), MEd, MRd, "kNm", "6.1",
                       hint=HINT_COL)
            res[ax] = (MEd, MRd)

        calc.heading("Biaxial bending (5.8.9)")
        ratio = NEd / NRd
        a = float(np.interp(ratio, [0.1, 0.7, 1.0], [1.0, 1.5, 2.0]))
        a = calc.formula("a", "Table: N_Ed/N_Rd 0.1 → 1.0, 0.7 → 1.5, 1.0 → 2.0", a, "",
                         ref="Eq. 5.39", dp=3)
        r = lambda m: m[0] / m[1] if m[1] > 0 else float("inf")  # noqa: E731
        u = r(res["h"]) ** a + r(res["b"]) ** a
        calc.check("Biaxial: (M_Ed,h/M_Rd,h)^a + (M_Ed,b/M_Rd,b)^a ≤ 1", u, 1.0, "",
                   "EN 1992-1-1 Eq. 5.39", hint=HINT_COL)

        calc.heading("Shear")
        d = h - cb
        z = 0.9 * d
        k = min(1 + math.sqrt(200 / d), 2.0)
        rho = min(nb * bar_area(dia) / (b * d), 0.02)
        scp = min(NEd / Ac, 0.2 * fcd)
        VRdc = calc.formula("V_Rd,c", "[C_Rd,c k(100ρ_l f_ck)^(1/3) + 0.15σ_cp] b d",
                            max(0.18 / na.gamma_c * k * (100 * rho * fck) ** (1 / 3),
                                0.035 * k**1.5 * math.sqrt(fck)) * b * d + 0.15 * scp * b * d,
                            "kN", ref="Eq. 6.2", dp=1)
        Asw = 2 * bar_area(dl)
        VRds = calc.formula("V_Rd,s", "A_sw/s z f_ywd cot θ (cot θ = 2.5)",
                            Asw / inp["s"] * z * fyd * 2.5, "kN", ref="Eq. 6.8", dp=1)
        nu1 = 0.6 * (1 - fck / 250)
        VRdmax = b * z * nu1 * fcd / (2.5 + 1 / 2.5)
        calc.check("Shear: V_Ed ≤ max(V_Rd,c, min(V_Rd,s, V_Rd,max))", inp["VEd"],
                   max(VRdc, min(VRds, VRdmax)), "kN", "6.2",
                   hint="Reduce the link spacing or use larger links.")

        calc.heading("Detailing (9.5)")
        Asmin = max(0.10 * NEd / fyd, 0.002 * Ac)
        calc.check_min("A_s ≥ A_s,min = max(0.10 N_Ed/f_yd, 0.002 A_c)", As, Asmin, "mm²",
                       "9.5.2(2)", hint=HINT_COL)
        calc.check_limit("A_s ≤ 0.04 A_c", As, 0.04 * Ac, "mm²", "9.5.2(3)",
                         hint="Increase the column size.")
        smax = min(20 * dia, min(b, h), 400.0)
        calc.check_limit("Link spacing ≤ min(20φ, b_min, 400)", inp["s"], smax, "mm", "9.5.3(3)",
                         hint="Reduce the link spacing.")
        if inp["seismic"]:
            calc.heading("Seismic detailing — EN 1998-1 (DCM)")
            nud = calc.formula("ν_d", "N_Ed / (A_c f_cd)", n, "", ref="5.4.3.2.1(3)", dp=3)
            calc.check_limit("Axial load ratio ν_d ≤ 0.65", nud, 0.65, "", "EN 1998-1 5.4.3.2.1(3)",
                             hint="Increase the column size.")
            rho_l = As / Ac
            calc.check_min("ρ_l ≥ 1 %", rho_l, 0.01, "", "5.4.3.2.2(1)", hint=HINT_COL)
            calc.check_limit("ρ_l ≤ 4 %", rho_l, 0.04, "", "5.4.3.2.2(1)",
                             hint="Increase the column size.")
            b0 = min(b, h) - 2 * c - dl
            scrit = min(b0 / 2, 175.0, 8 * dia)
            calc.check_limit("Critical region links: s ≤ min(b_0/2, 175, 8d_bL)", inp["s"], scrit,
                             "mm", "5.4.3.2.2(11)",
                             hint="Use closer links in the critical regions at both ends.")
            calc.note("Capacity design of the beam–column joints (ΣM_Rc ≥ 1.3 ΣM_Rb, 4.4.2.3) "
                      "requires the beam resistances and is not checked here.")
        calc.model3d = cls._scene(calc, inp, cb, n_bars)

    @staticmethod
    def _scene(calc, inp, cb, n_bars) -> dict:
        m = lambda v: from_base(v, "m")  # noqa: E731
        b, h, L = m(inp["b"]), m(inp["h"]), m(inp["L"])
        sc = Scene3D("rc_column", calc.tr)
        sc.layer("concrete", "Concrete", visible=True)
        sc.layer("bars", "Reinforcement")
        sc.layer("dims", "Dimensions")
        sc.box("concrete", (0, L / 2, 0), (b, L, h), PALETTE["concrete"], opacity=0.35)
        r = m(float(inp["dia"])) / 2
        e = m(cb)
        nb, nh = inp["nb"], inp["nh"]
        pts = set()
        for i in range(nb):
            x = -b / 2 + e + (b - 2 * e) * i / (nb - 1)
            pts.add((round(x, 4), round(-h / 2 + e, 4)))
            pts.add((round(x, 4), round(h / 2 - e, 4)))
        for j in range(nh):
            z = -h / 2 + e + (h - 2 * e) * j / (nh - 1)
            pts.add((round(-b / 2 + e, 4), round(z, 4)))
            pts.add((round(b / 2 - e, 4), round(z, 4)))
        for x, z in pts:
            sc.cylinder("bars", (x, 0.02, z), (x, L - 0.02, z), r, "#5a6b7d")
        s = m(inp["s"])
        y = s / 2
        while y < L:
            sc.line("bars", [(-b / 2 + e * 0.7, y, -h / 2 + e * 0.7), (b / 2 - e * 0.7, y, -h / 2 + e * 0.7),
                             (b / 2 - e * 0.7, y, h / 2 - e * 0.7), (-b / 2 + e * 0.7, y, h / 2 - e * 0.7)],
                    "#8a5a2b", closed=True)
            y += s
        sc.label("dims", f"{inp['b']:g} × {inp['h']:g} mm, {n_bars}Ø{inp['dia']}",
                 (b / 2 + 0.1, L, 0), "dim")
        sc.label("dims", f"L = {L:.2f} m", (b / 2 + 0.1, L / 2, h / 2), "dim")
        return sc.to_dict()
