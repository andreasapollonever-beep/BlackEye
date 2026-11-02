"""EN 1992-1-1 rectangular reinforced concrete beam section design."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, register
from ..report.svg import rc_section

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "C45/55", "C50/60"]
BARS = ["8", "10", "12", "14", "16", "20", "25", "32"]


def bar_area(dia: float) -> float:
    return math.pi * dia**2 / 4


@register
class RCBeamEC2(DesignModule):
    id = "ec2_rc_beam"
    title = "RC beam section design"
    category = "Concrete"
    standard = "EN 1992-1-1:2004"
    description = ("Rectangular singly reinforced section: flexure (rectangular stress block), "
                   "minimum/maximum reinforcement and shear with variable strut inclination.")

    fields = [
        Field("b", "Width b", "mm", 300.0, min=100, group="Geometry"),
        Field("h", "Overall depth h", "mm", 500.0, min=150, group="Geometry"),
        Field("cnom", "Nominal cover to links", "mm", 30.0, min=10, group="Geometry"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE,
              default="C25/30", group="Materials"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=200, max=600, group="Materials"),
        Field("gamma_c", "γc", "", 1.5, min=1, group="Materials"),
        Field("gamma_s", "γs", "", 1.15, min=1, group="Materials"),
        Field("alpha_cc", "αcc", "", 1.0, min=0.8, max=1.0, group="Materials",
              help="1.0 recommended (Greek NA); 0.85 UK NA."),
        Field("MEd", "Design moment MEd", "kNm", 140.0, min=0, group="Actions"),
        Field("VEd", "Design shear VEd", "kN", 120.0, min=0, group="Actions"),
        Field("n_bars", "Number of tension bars", kind="int", default=4, min=2,
              group="Reinforcement"),
        Field("dia", "Tension bar diameter", kind="choice", choices=BARS, default="16",
              group="Reinforcement"),
        Field("link_dia", "Link diameter", kind="choice", choices=BARS[:4], default="8",
              group="Reinforcement"),
        Field("link_legs", "Link legs", kind="int", default=2, min=2, group="Reinforcement"),
        Field("link_s", "Link spacing", "mm", 200.0, min=50, group="Reinforcement"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        b, h, c = inp["b"], inp["h"], inp["cnom"]
        fck = float(inp["concrete"].split("/")[0][1:])
        dia, dl = float(inp["dia"]), float(inp["link_dia"])
        n, legs, s = inp["n_bars"], inp["link_legs"], inp["link_s"]

        calc.heading("Geometry and materials")
        calc.input("b", b, "mm", "Section width")
        calc.input("h", h, "mm", "Overall depth")
        calc.input("c_nom", c, "mm", "Nominal cover to links")
        d = calc.formula("d", "h − c_nom − φ_link − φ/2", h - c - dl - dia / 2, "mm",
                         "Effective depth")
        calc.label("Concrete", inp["concrete"])
        calc.input("f_ck", fck, "N/mm²", "Characteristic cylinder strength")
        fcd = calc.formula("f_cd", "α_cc f_ck / γ_c", inp["alpha_cc"] * fck / inp["gamma_c"],
                           "N/mm²", ref="EN 1992-1-1 3.1.6(1)")
        fctm = calc.formula("f_ctm", "0.30 f_ck^(2/3)", 0.30 * fck ** (2 / 3), "N/mm²",
                            ref="Table 3.1")
        fyk = calc.input("f_yk", inp["fyk"], "N/mm²", "Reinforcement yield strength")
        fyd = calc.formula("f_yd", "f_yk / γ_s", fyk / inp["gamma_s"], "N/mm²", ref="3.2.7")
        As_prov = n * bar_area(dia)
        calc.figure(rc_section(b, h, c, dl, dia, n),
                    f"Section {b:g}×{h:g} - {n}Ø{dia:g} bottom, Ø{dl:g} links")

        # ---------------------------------------------------------- flexure
        calc.heading("Flexure")
        MEd = calc.input("M_Ed", inp["MEd"], "kNm", "Design bending moment")
        mu = calc.formula("μ", "M_Ed / (b d² f_cd)", MEd / (b * d**2 * fcd), "", dp=4)
        xi_lim = 0.45
        mu_lim = 0.8 * xi_lim * (1 - 0.4 * xi_lim)
        calc.formula("μ_lim", "0.8ξ_lim(1 − 0.4ξ_lim), ξ_lim = 0.45", mu_lim, "",
                     "Limit for singly reinforced section (ductility, 5.6.3)", dp=4)
        if mu > mu_lim:
            calc.warn("μ > μ_lim - compression reinforcement is required; increase the "
                      "section depth or design as doubly reinforced.")
            calc.check("Singly reinforced: μ ≤ μ_lim", mu, mu_lim, "", "5.6.3")
            return
        xi = calc.formula("ξ", "1.25(1 − √(1 − 2μ))", 1.25 * (1 - math.sqrt(1 - 2 * mu)), "",
                          "Neutral axis depth ratio x/d (λ = 0.8, η = 1.0)", ref="3.1.7", dp=4)
        z = calc.formula("z", "d(1 − 0.4ξ) ≤ 0.95d", min(d * (1 - 0.4 * xi), 0.95 * d), "mm",
                         "Lever arm")
        As_req = calc.formula("A_s,req", "M_Ed / (f_yd z)", MEd / (fyd * z), "mm²",
                              "Required tension reinforcement")
        As_min = calc.formula("A_s,min", "max(0.26 f_ctm/f_yk b d, 0.0013 b d)",
                              max(0.26 * fctm / fyk * b * d, 0.0013 * b * d), "mm²",
                              ref="9.2.1.1(1)")
        As_max = calc.formula("A_s,max", "0.04 b h", 0.04 * b * h, "mm²", ref="9.2.1.1(3)")
        calc.formula("A_s,prov", f"{n} × π × {dia:g}² / 4", As_prov, "mm²",
                     f"Provided: {n}Ø{dia:g}")
        calc.check_min("Flexural reinforcement: A_s,prov ≥ A_s,req", As_prov, As_req, "mm²",
                       "6.1")
        calc.check_min("Minimum reinforcement: A_s,prov ≥ A_s,min", As_prov, As_min, "mm²",
                       "9.2.1.1(1)")
        calc.check_limit("Maximum reinforcement: A_s,prov ≤ A_s,max", As_prov, As_max, "mm²",
                         "9.2.1.1(3)")
        clear = (b - 2 * (c + dl) - n * dia) / (n - 1)
        s_min = max(dia, 20.0 + 5.0, 20.0)  # dg = 20 mm assumed
        calc.formula("s_clear", "(b − 2(c_nom + φ_link) − nφ) / (n − 1)", clear, "mm",
                     "Clear spacing between bars")
        calc.check_min("Bar spacing: s_clear ≥ max(φ, d_g + 5, 20)", clear, s_min, "mm",
                       "8.2(2)")
        MRd = As_prov * fyd * z
        if As_prov * fyd / (0.8 * b * fcd) <= xi_lim * d:
            x_p = As_prov * fyd / (0.8 * b * fcd)
            MRd = As_prov * fyd * min(d - 0.4 * x_p, 0.95 * d)
        calc.formula("M_Rd", "A_s,prov f_yd (d − 0.4x)", MRd, "kNm",
                     "Moment resistance of provided reinforcement")

        # ------------------------------------------------------------ shear
        calc.heading("Shear")
        VEd = calc.input("V_Ed", inp["VEd"], "kN", "Design shear force")
        k = calc.formula("k", "1 + √(200/d) ≤ 2.0", min(1 + math.sqrt(200 / d), 2.0), "",
                         ref="6.2.2(1)", dp=3)
        rho = calc.formula("ρ_l", "A_s,prov / (b d) ≤ 0.02", min(As_prov / (b * d), 0.02), "",
                           ref="6.2.2(1)", dp=4)
        CRdc = 0.18 / inp["gamma_c"]
        vmin = calc.formula("v_min", "0.035 k^1.5 f_ck^0.5", 0.035 * k**1.5 * math.sqrt(fck),
                            "N/mm²", ref="Eq. 6.3N", dp=3)
        VRdc = calc.formula("V_Rd,c", "max(C_Rd,c k(100ρ_l f_ck)^(1/3), v_min) b d",
                            max(CRdc * k * (100 * rho * fck) ** (1 / 3), vmin) * b * d, "kN",
                            "Resistance without shear reinforcement", ref="Eq. 6.2")
        if VEd <= VRdc:
            calc.text("V_Ed ≤ V_Rd,c - only minimum shear reinforcement is required.")
        zv = calc.formula("z_v", "0.9d", 0.9 * d, "mm", "Lever arm for shear", ref="6.2.3(1)")
        nu1 = calc.formula("ν_1", "0.6(1 − f_ck/250)", 0.6 * (1 - fck / 250), "",
                           ref="Eq. 6.6N", dp=3)
        fcd_s = fck / inp["gamma_c"]  # αcw = 1, uses αcc = 1 for strut
        # strut angle: smallest θ (largest cotθ ≤ 2.5) for which VRd,max ≥ VEd
        ratio = 2 * VEd / (b * zv * nu1 * fcd_s)
        if ratio <= 2 / (2.5 + 1 / 2.5):
            cot = 2.5
        elif ratio <= 1.0:
            cot = 1 / math.tan(0.5 * math.asin(ratio))
            cot = max(min(cot, 2.5), 1.0)
        else:
            cot = 1.0
        cot = calc.formula("cot θ", "1.0 ≤ cot θ ≤ 2.5 (VRd,max ≥ VEd)", cot, "",
                           "Strut inclination", ref="Eq. 6.7N", dp=3)
        VRdmax = calc.formula("V_Rd,max", "α_cw b z ν_1 f_cd / (cot θ + tan θ)",
                              b * zv * nu1 * fcd_s / (cot + 1 / cot), "kN", ref="Eq. 6.9")
        calc.check("Concrete strut: V_Ed ≤ V_Rd,max", VEd, VRdmax, "kN", "6.2.3(3)")
        Asw = legs * bar_area(dl)
        calc.formula("A_sw", f"{legs} × π × {dl:g}² / 4", Asw, "mm²", "Link area")
        fywd = fyd
        VRds = calc.formula("V_Rd,s", "(A_sw / s) z f_ywd cot θ", Asw / s * zv * fywd * cot,
                            "kN", ref="Eq. 6.8")
        calc.check("Shear reinforcement: V_Ed ≤ V_Rd,s", VEd, VRds, "kN", "6.2.3(3)")
        rho_w_min = calc.formula("ρ_w,min", "0.08√f_ck / f_yk", 0.08 * math.sqrt(fck) / fyk, "",
                                 ref="Eq. 9.5N", dp=5)
        calc.check_min("Minimum links: A_sw/(s b) ≥ ρ_w,min", Asw / (s * b), rho_w_min, "",
                       "9.2.2(5)")
        calc.check_limit("Link spacing: s ≤ 0.75d", s, 0.75 * d, "mm", "9.2.2(6)")
