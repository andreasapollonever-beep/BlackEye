"""EN 1993-1-1 simply supported steel I-beam design."""

from __future__ import annotations

import math

from ..analysis import UDL, Beam, PointLoad, Support
from ..core import Calculation, DesignModule, Field, register
from ..report.svg import beam_diagrams
from ..sections.steel import get_section, section_names

STEEL_GRADES = {"S235": 235.0, "S275": 275.0, "S355": 355.0, "S460": 460.0}


def _fy(grade: str, t: float) -> float:
    """Nominal yield strength, EN 1993-1-1 Table 3.1 (t ≤ 40 mm / 40 < t ≤ 80 mm)."""
    base = STEEL_GRADES[grade]
    if t <= 40:
        return base
    return {"S235": 215.0, "S275": 255.0, "S355": 335.0, "S460": 430.0}[grade]


@register
class SteelBeamEC3(DesignModule):
    id = "ec3_steel_beam"
    title = "Steel beam design"
    category = "Steel"
    standard = "EN 1993-1-1:2005"
    description = ("Simply supported rolled I-beam: classification, bending, shear, "
                   "bending-shear interaction, lateral-torsional buckling and deflection.")

    fields = [
        Field("section", "Section", kind="choice", choices=section_names(), default="IPE 300",
              group="Section"),
        Field("grade", "Steel grade", kind="choice", choices=list(STEEL_GRADES),
              default="S275", group="Section"),
        Field("L", "Span", "m", 6.0, min=0.1, group="Geometry"),
        Field("Lcr", "LTB effective length (0 = unrestrained span)", "m", 2.0, min=0,
              group="Geometry",
              help="Distance between lateral restraints to the compression flange."),
        Field("gk", "Permanent UDL (excl. self weight)", "kN/m", 8.0, min=0, group="Loads"),
        Field("qk", "Variable UDL", "kN/m", 10.0, min=0, group="Loads"),
        Field("Gk_pt", "Permanent point load at midspan", "kN", 0.0, min=0, group="Loads"),
        Field("Qk_pt", "Variable point load at midspan", "kN", 0.0, min=0, group="Loads"),
        Field("gamma_G", "γG", "", 1.35, min=0, group="Partial factors"),
        Field("gamma_Q", "γQ", "", 1.50, min=0, group="Partial factors"),
        Field("gamma_M0", "γM0", "", 1.00, min=0.5, group="Partial factors"),
        Field("gamma_M1", "γM1", "", 1.00, min=0.5, group="Partial factors"),
        Field("defl_limit", "Variable load deflection limit L/…", "", 360.0, min=1,
              group="Serviceability"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        sec = get_section(inp["section"])
        L = inp["L"]
        E, G = 210000.0, 81000.0

        # ----------------------------------------------------------- section
        calc.heading("Section and material")
        calc.label("Section", sec.name, "Hot rolled I-section")
        calc.table(
            ["h", "b", "tw", "tf", "r", "A", "Iy", "Iz", "Wel,y", "Wpl,y", "It", "Iw"],
            [[f"{sec.h:g} mm", f"{sec.b:g} mm", f"{sec.tw:g} mm", f"{sec.tf:g} mm",
              f"{sec.r:g} mm", f"{sec.A / 1e2:.1f} cm²", f"{sec.Iy / 1e4:.0f} cm⁴",
              f"{sec.Iz / 1e4:.1f} cm⁴", f"{sec.Wel_y / 1e3:.1f} cm³",
              f"{sec.Wpl_y / 1e3:.1f} cm³", f"{sec.It / 1e4:.2f} cm⁴",
              f"{sec.Iw / 1e6:.0f} cm⁶"]],
            caption="Section properties (derived from nominal dimensions)",
        )
        calc.label("Grade", inp["grade"])
        fy = calc.formula("f_y", "Table 3.1", _fy(inp["grade"], sec.tf), "N/mm²",
                          "Yield strength", ref="EN 1993-1-1 Table 3.1")
        eps = calc.formula("ε", "√(235 / f_y)", math.sqrt(235 / fy), "",
                           ref="Table 5.2", dp=3)
        calc.input("E", E, "N/mm²", "Modulus of elasticity")
        calc.input("G", G, "N/mm²", "Shear modulus")

        # ---------------------------------------------------- classification
        calc.heading("Section classification")
        c_f = (sec.b - sec.tw - 2 * sec.r) / 2
        cf_t = calc.formula("c_f/t_f", "(b − t_w − 2r) / 2 / t_f", c_f / sec.tf, "",
                            "Outstand flange in compression", ref="Table 5.2 (sheet 2)", dp=2)
        f_class = 1 if cf_t <= 9 * eps else 2 if cf_t <= 10 * eps else 3 if cf_t <= 14 * eps else 4
        cw_t = calc.formula("c_w/t_w", "d / t_w", sec.d / sec.tw, "",
                            "Internal web in bending", ref="Table 5.2 (sheet 1)", dp=2)
        w_class = 1 if cw_t <= 72 * eps else 2 if cw_t <= 83 * eps else 3 if cw_t <= 124 * eps else 4
        sec_class = max(f_class, w_class)
        calc.text("Flange: Class {fc} (limits 9ε = {a:.2f}, 10ε = {b:.2f}, 14ε = {c:.2f}); "
                  "web: Class {wc} (limits 72ε = {d:.1f}, 83ε = {e:.1f}, 124ε = {f:.1f}).",
                  fc=f_class, a=9 * eps, b=10 * eps, c=14 * eps, wc=w_class, d=72 * eps,
                  e=83 * eps, f=124 * eps)
        calc.text("**Section is Class {n}.**", n=sec_class)
        if sec_class == 4:
            calc.warn("Class 4 sections require effective properties (EN 1993-1-5) - "
                      "not covered by this module.")
        Wy = sec.Wpl_y if sec_class <= 2 else sec.Wel_y
        calc.formula("W_y", "W_pl,y" if sec_class <= 2 else "W_el,y", Wy, "cm³",
                     "Section modulus used for design")

        # ------------------------------------------------------------ loading
        calc.heading("Actions and analysis")
        sw = calc.formula("g_sw", "A × ρ × g", sec.mass * 9.81e-3, "kN/m",
                          "Self weight", dp=3)
        gk = calc.input("g_k", inp["gk"] + sw, "kN/m", "Total permanent UDL (incl. self weight)")
        qk = calc.input("q_k", inp["qk"], "kN/m", "Variable UDL")
        Gp, Qp = inp["Gk_pt"], inp["Qk_pt"]
        if Gp or Qp:
            calc.input("G_k", Gp, "kN", "Permanent point load at midspan")
            calc.input("Q_k", Qp, "kN", "Variable point load at midspan")
        gG, gQ = inp["gamma_G"], inp["gamma_Q"]
        wEd = calc.formula("w_Ed", "γ_G × g_k + γ_Q × q_k", gG * gk + gQ * qk, "kN/m",
                           "ULS design UDL", ref="EN 1990 Eq. 6.10")
        PEd = gG * Gp + gQ * Qp
        if PEd:
            calc.formula("P_Ed", "γ_G × G_k + γ_Q × Q_k", PEd, "kN", "ULS point load")

        def analyse(w: float, P: float):
            beam = Beam(L, E, sec.Iy, [Support(0.0), Support(L)],
                        point_loads=[PointLoad(L / 2, P)] if P else [],
                        udls=[UDL(0.0, L, w)] if w else [])
            return beam.solve()

        uls = analyse(wEd, PEd)
        MEd = calc.formula("M_Ed", "max M(x)", uls.max_sagging[0], "kNm",
                           "Maximum design moment (stiffness analysis)")
        VEd = calc.formula("V_Ed", "max |V(x)|", abs(uls.max_shear[0]), "kN",
                           "Maximum design shear")
        calc.figure(beam_diagrams(uls, title="ULS"), "ULS shear force and bending moment")

        # ------------------------------------------------------------ bending
        calc.heading("Bending resistance", 1)
        McRd = calc.formula("M_c,Rd", "W_y × f_y / γ_M0", Wy * fy / inp["gamma_M0"], "kNm",
                            ref="EN 1993-1-1 6.2.5")
        calc.check("Bending: M_Ed ≤ M_c,Rd", MEd, McRd, "kNm", "6.2.5(1)", hint="Choose a deeper section or a higher steel grade.")

        # -------------------------------------------------------------- shear
        calc.heading("Shear resistance")
        Av = calc.formula("A_v", "A − 2bt_f + (t_w + 2r)t_f ≥ h_w t_w", sec.Av_z, "cm²",
                          "Shear area", ref="6.2.6(3)")
        VplRd = calc.formula("V_pl,Rd", "A_v × (f_y / √3) / γ_M0",
                             Av * fy / math.sqrt(3) / inp["gamma_M0"], "kN", ref="6.2.6(2)")
        calc.check("Shear: V_Ed ≤ V_pl,Rd", VEd, VplRd, "kN", "6.2.6(1)", hint="Choose a section with a thicker or deeper web.")
        calc.check_limit("Shear buckling: h_w/t_w ≤ 72ε/η", sec.hw / sec.tw, 72 * eps, "",
                         "6.2.6(6)")

        # Bending-shear interaction: for a simply supported UDL beam max M and
        # max V do not coincide; we conservatively check V at the M_max location.
        V_at_M = abs(float(uls.shear[abs(uls.x - uls.max_sagging[1]).argmin()]))
        if V_at_M > 0.5 * VplRd:
            rho = (2 * V_at_M / VplRd - 1) ** 2
            calc.formula("ρ", "(2V_Ed / V_pl,Rd − 1)²", rho, "", ref="6.2.8(3)", dp=3)
            MvRd = calc.formula("M_v,Rd", "(W_pl,y − ρA_w²/(4t_w)) f_y / γ_M0",
                                min((sec.Wpl_y - rho * (sec.hw * sec.tw) ** 2 / (4 * sec.tw))
                                    * fy / inp["gamma_M0"], McRd), "kNm", ref="6.2.8(5)")
            calc.check("Bending + shear: M_Ed ≤ M_v,Rd", MEd, MvRd, "kNm", "6.2.8", hint="Choose a heavier section.")
        else:
            calc.text("V_Ed at the position of maximum moment ≤ 0.5 V_pl,Rd - no reduction "
                      "for shear is required (6.2.8(2)).")

        # --------------------------------------------------------------- LTB
        calc.heading("Lateral-torsional buckling")
        Lcr = inp["Lcr"] if inp["Lcr"] > 0 else L
        calc.input("L_cr", Lcr, "m", "Effective length between lateral restraints")
        if PEd and wEd:
            C1 = 1.13 if wEd * L >= PEd else 1.35
        else:
            C1 = 1.35 if PEd and not wEd else 1.13
        calc.input("C_1", C1, "", "Moment-gradient factor (load at shear centre)", dp=2)
        Mcr = calc.formula(
            "M_cr", "C_1 π²EI_z/L_cr² × √(I_w/I_z + L_cr²GI_t/(π²EI_z))",
            C1 * math.pi**2 * E * sec.Iz / Lcr**2
            * math.sqrt(sec.Iw / sec.Iz + Lcr**2 * G * sec.It / (math.pi**2 * E * sec.Iz)),
            "kNm", "Elastic critical moment", ref="NCCI SN003")
        lam = calc.formula("λ̄_LT", "√(W_y f_y / M_cr)", math.sqrt(Wy * fy / Mcr), "",
                           ref="6.3.2.2(1)", dp=3)
        curve = "b" if sec.h / sec.b <= 2 else "c"
        alpha = {"b": 0.34, "c": 0.49}[curve]
        calc.text("h/b = {r:.2f} → buckling curve **{c}** for rolled sections (Table 6.5), "
                  "α_LT = {a}.", r=sec.h / sec.b, c=curve, a=alpha)
        lam0, beta = 0.4, 0.75
        phi = calc.formula("Φ_LT", "0.5[1 + α_LT(λ̄_LT − λ̄_LT,0) + βλ̄_LT²]",
                           0.5 * (1 + alpha * (lam - lam0) + beta * lam**2), "",
                           ref="6.3.2.3(1)", dp=3)
        chi = 1 / (phi + math.sqrt(max(phi**2 - beta * lam**2, 0)))
        chi = min(chi, 1.0, 1 / lam**2 if lam > 0 else 1.0)
        if lam <= lam0:
            chi = 1.0
            calc.text("λ̄_LT ≤ λ̄_LT,0 = 0.4 - lateral-torsional buckling may be ignored "
                      "(6.3.2.2(4)).")
        chi = calc.formula("χ_LT", "1 / (Φ_LT + √(Φ_LT² − βλ̄_LT²)) ≤ min(1, 1/λ̄_LT²)",
                           chi, "", ref="6.3.2.3(1)", dp=3)
        MbRd = calc.formula("M_b,Rd", "χ_LT W_y f_y / γ_M1", chi * Wy * fy / inp["gamma_M1"],
                            "kNm", ref="6.3.2.1(3)")
        calc.check("LTB: M_Ed ≤ M_b,Rd", MEd, MbRd, "kNm", "6.3.2.1(1)", hint="Add lateral restraints to the compression flange (reduce L_cr) or choose a wider section (HEA/HEB).")

        # -------------------------------------------------------- deflection
        calc.heading("Serviceability - deflection")
        sls = analyse(qk, Qp)
        dq = calc.formula("δ_q", "max δ(x) under variable loads", sls.max_deflection[0], "mm",
                          "Variable load deflection")
        dlim = calc.formula("δ_lim", f"L / {inp['defl_limit']:g}", L / inp["defl_limit"], "mm")
        calc.check("Deflection: δ_q ≤ δ_lim", dq, dlim, "mm", "EN 1990 A1.4", hint="Choose a deeper (stiffer) section or reduce the span.")
        tot = analyse(gk + qk, Gp + Qp)
        calc.formula("δ_tot", "max δ(x) under g_k + q_k", tot.max_deflection[0], "mm",
                     "Total characteristic deflection (for information)")
