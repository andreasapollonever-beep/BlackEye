"""Steel column (beam-column) — EN 1993-1-1 §6.2, §6.3.1–6.3.3 and Annex B (Method 2)."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..report.scene3d import PALETTE, Scene3D
from ..sections.steel import get_section, section_names
from .ec3_steel_beam import STEEL_GRADES, _fy

E, G = 210000.0, 81000.0
ALPHA = {"a0": 0.13, "a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}
HINT_N = "Choose a heavier section, a higher steel grade or reduce the buckling length."
HINT_BUCK = ("Reduce the buckling length (add bracing about the weak axis) or choose a wider "
             "section (HEB / HEM).")
HINT_INT = "Choose a heavier section or add bracing to reduce the buckling lengths."


def chi_curve(lam: float, alpha: float) -> float:
    if lam <= 0.2:
        return 1.0
    phi = 0.5 * (1 + alpha * (lam - 0.2) + lam**2)
    return min(1.0, 1 / (phi + math.sqrt(phi**2 - lam**2)))


def curves(sec) -> tuple[str, str]:
    """EN 1993-1-1 Table 6.2, rolled I-sections, S235–S420."""
    if sec.h / sec.b > 1.2:
        return ("a", "b") if sec.tf <= 40 else ("b", "c")
    return ("b", "c") if sec.tf <= 100 else ("d", "d")


@register
class SteelColumnEC3(DesignModule):
    id = "ec3_steel_column"
    title = "Steel column"
    category = "Steel"
    has_3d = True
    uses_annex = True
    standard = "EN 1993-1-1 §6.3, Annex B"
    description = ("Rolled I/H column under axial force and biaxial end moments: "
                   "classification, cross-section resistance, flexural buckling about both "
                   "axes, lateral-torsional buckling and the interaction of Eq. 6.61/6.62 "
                   "(Annex B). Interactive 3D model with buckled shape.")

    fields = [
        Field("section", "Section", kind="choice", choices=section_names(), default="HEB 240",
              group="Section"),
        Field("grade", "Steel grade", kind="choice", choices=list(STEEL_GRADES),
              default="S355", group="Section"),
        Field("L", "Column height L", "m", 4.0, min=0.5, max=30, group="Buckling"),
        Field("ky", "Buckling length factor about y-y", "", 1.0, min=0.5, max=3.0,
              group="Buckling", help="1.0 pinned–pinned, 0.7 fixed–pinned, 0.5 fixed–fixed, "
                                     "2.0 cantilever; sway frames > 1.0."),
        Field("kz", "Buckling length factor about z-z", "", 1.0, min=0.3, max=3.0,
              group="Buckling", help="Bracing at mid-height about the weak axis → 0.5."),
        Field("kLT", "LTB length factor", "", 1.0, min=0.3, max=3.0, group="Buckling"),
        Field("NEd", "Axial compression N_Ed", "kN", 1200.0, min=0, group="Design actions"),
        Field("My_top", "M_y,Ed at top", "kNm", 80.0, group="Design actions",
              help="Strong-axis moment; same sign at both ends = single curvature."),
        Field("My_bot", "M_y,Ed at bottom", "kNm", -40.0, group="Design actions"),
        Field("Mz_top", "M_z,Ed at top", "kNm", 5.0, group="Design actions"),
        Field("Mz_bot", "M_z,Ed at bottom", "kNm", 0.0, group="Design actions"),
        Field("VEd", "Shear V_z,Ed", "kN", 30.0, min=0, group="Design actions"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        g0, g1 = na.gamma_M0, na.gamma_M1
        sec = get_section(inp["section"])
        L, NEd = inp["L"], inp["NEd"]
        calc.heading("Section and material")
        calc.label("Section", sec.name)
        calc.table(["h", "b", "t_w", "t_f", "A", "I_y", "I_z", "W_pl,y", "W_pl,z", "i_y", "i_z"],
                   [[f"{sec.h:g}", f"{sec.b:g}", f"{sec.tw:g}", f"{sec.tf:g}",
                     f"{sec.A / 1e2:.1f}", f"{sec.Iy / 1e4:.0f}", f"{sec.Iz / 1e4:.0f}",
                     f"{sec.Wpl_y / 1e3:.0f}", f"{sec.Wpl_z / 1e3:.0f}",
                     f"{sec.iy / 10:.2f}", f"{sec.iz / 10:.2f}"]],
                   caption="mm, cm², cm⁴, cm³, cm")
        fy = calc.formula("f_y", "Table 3.1", _fy(inp["grade"], sec.tf), "N/mm²",
                          ref="EN 1993-1-1 Table 3.1")
        eps = calc.formula("ε", "√(235 / f_y)", math.sqrt(235 / fy), "", dp=3)
        calc.text("γ_M0 = {a:g}, γ_M1 = {b:g} (National Annex).", a=g0, b=g1)

        calc.heading("Classification (Table 5.2)")
        cf = (sec.b - sec.tw - 2 * sec.r) / 2 / sec.tf
        cw = sec.d / sec.tw
        fcl = 1 if cf <= 9 * eps else 2 if cf <= 10 * eps else 3 if cf <= 14 * eps else 4
        wcl = 1 if cw <= 33 * eps else 2 if cw <= 38 * eps else 3 if cw <= 42 * eps else 4
        calc.formula("c/t (flange)", "(b − t_w − 2r)/(2t_f)", cf, "",
                     calc.tr("Class {c} (9ε / 10ε / 14ε)", c=fcl), dp=2)
        calc.formula("c/t (web)", "d / t_w (pure compression)", cw, "",
                     calc.tr("Class {c} (33ε / 38ε / 42ε)", c=wcl), dp=2)
        cl = max(fcl, wcl)
        calc.text("**Section is Class {n}** (web conservatively in pure compression).", n=cl)
        Aeff = sec.A
        if fcl == 4:
            raise InputError("Class 4 flanges — choose a section with stockier flanges", "section")
        if wcl == 4:
            lp = cw / (28.4 * eps * 2.0)
            rho = min((lp - 0.055 * 4) / lp**2, 1.0)
            Aeff = calc.formula("A_eff", "A − (1 − ρ) d t_w", sec.A - (1 - rho) * sec.d * sec.tw,
                                "cm²", calc.tr("Class 4 web: effective width, λ̄_p = {l:.3f}, "
                                               "ρ = {r:.3f} (EN 1993-1-5 4.4)", l=lp, r=rho))
            calc.text("Bending uses the elastic moduli (the effective web loss lies at the "
                      "centroid of the doubly symmetric section, e_N = 0).")
            cl = 3
        Wy = sec.Wpl_y if cl <= 2 else sec.Wel_y
        Wz = sec.Wpl_z if cl <= 2 else sec.Wel_z

        calc.heading("Cross-section resistance (6.2)")
        NRk = Aeff * fy
        NRd = calc.formula("N_c,Rd", "A_eff f_y / γ_M0" if Aeff < sec.A else "A f_y / γ_M0", NRk / g0, "kN", ref="6.2.4")
        My = max(abs(inp["My_top"]), abs(inp["My_bot"]))
        Mz = max(abs(inp["Mz_top"]), abs(inp["Mz_bot"]))
        MyRd = calc.formula("M_y,Rd", "W_y f_y / γ_M0", Wy * fy / g0, "kNm", ref="6.2.5")
        MzRd = calc.formula("M_z,Rd", "W_z f_y / γ_M0", Wz * fy / g0, "kNm")
        calc.check("Cross-section: N/N_Rd + M_y/M_y,Rd + M_z/M_z,Rd ≤ 1",
                   NEd / NRd + My / MyRd + Mz / MzRd, 1.0, "", "Eq. 6.2", hint=HINT_N)
        Vpl = sec.Av_z * fy / math.sqrt(3) / g0
        calc.formula("V_pl,z,Rd", "A_v f_y / (√3 γ_M0)", Vpl, "kN", ref="6.2.6")
        calc.check("Shear: V_Ed ≤ V_pl,Rd", inp["VEd"], Vpl, "kN", "6.2.6", hint=HINT_N)
        if inp["VEd"] > 0.5 * Vpl:
            calc.warn("V_Ed > 0.5 V_pl,Rd: the moment resistance must be reduced (6.2.8).")

        calc.heading("Flexural buckling (6.3.1)")
        lam1 = 93.9 * eps
        cy, cz = curves(sec)
        res = {}
        for ax, k, i, c in (("y", inp["ky"], sec.iy, cy), ("z", inp["kz"], sec.iz, cz)):
            Lcr = calc.formula(f"L_cr,{ax}", f"k_{ax} L", k * L, "m")
            lam = calc.formula(f"λ̄_{ax}", f"L_cr / (i_{ax} λ_1) √(A_eff/A), λ_1 = 93.9ε",
                               Lcr / (i * lam1) * math.sqrt(Aeff / sec.A),
                               "", ref="Eq. 6.50", dp=3)
            chi = calc.formula(f"χ_{ax}", calc.tr("curve {c}, α = {a:g}", c=c, a=ALPHA[c]),
                               chi_curve(lam, ALPHA[c]), "", ref="Eq. 6.49", dp=3)
            Nb = calc.formula(f"N_b,{ax},Rd", f"χ_{ax} A f_y / γ_M1", chi * NRk / g1, "kN")
            calc.check(calc.tr("Buckling about {ax}-{ax}: N_Ed ≤ N_b,Rd", ax=ax), NEd, Nb, "kN",
                       "6.3.1", hint=HINT_BUCK)
            res[ax] = (lam, chi)

        calc.heading("Lateral-torsional buckling (6.3.2)")
        Mt, Mb = inp["My_top"], inp["My_bot"]
        Mmax = Mt if abs(Mt) >= abs(Mb) else Mb
        Mmin = Mb if Mmax is Mt else Mt
        psi = Mmin / Mmax if abs(Mmax) > 1e-9 else 1.0
        C1 = calc.formula("C_1", "1.88 − 1.40ψ + 0.52ψ² ≤ 2.7",
                          min(1.88 - 1.40 * psi + 0.52 * psi**2, 2.7), "",
                          calc.tr("Moment gradient, ψ = {p:.2f}", p=psi), dp=3)
        Lt = inp["kLT"] * L
        Mcr = calc.formula("M_cr", "C_1 π²EI_z/L² √(I_w/I_z + L²GI_t/(π²EI_z))",
                           C1 * math.pi**2 * E * sec.Iz / Lt**2 * math.sqrt(
                               sec.Iw / sec.Iz + Lt**2 * G * sec.It / (math.pi**2 * E * sec.Iz)),
                           "kNm", "Elastic critical moment")
        lamLT = calc.formula("λ̄_LT", "√(W_y f_y / M_cr)", math.sqrt(Wy * fy / Mcr), "", dp=3)
        cLT = "b" if sec.h / sec.b <= 2 else "c"
        aLT, lam0, beta = ALPHA[cLT], 0.4, 0.75
        if lamLT <= lam0:
            chiLT = 1.0
        else:
            ph = 0.5 * (1 + aLT * (lamLT - lam0) + beta * lamLT**2)
            chiLT = min(1.0, 1 / lamLT**2, 1 / (ph + math.sqrt(ph**2 - beta * lamLT**2)))
        chiLT = calc.formula("χ_LT", calc.tr("6.3.2.3, curve {c}, λ̄_LT,0 = 0.4, β = 0.75",
                                             c=cLT), chiLT, "", dp=3)
        MbRd = calc.formula("M_b,Rd", "χ_LT W_y f_y / γ_M1", chiLT * Wy * fy / g1, "kNm")
        calc.check("LTB: M_y,Ed ≤ M_b,Rd", My, MbRd, "kNm", "6.3.2.1", hint=HINT_BUCK)

        calc.heading("Interaction — Annex B, Method 2 (members susceptible to torsion)")
        lam_y, chi_y = res["y"]
        lam_z, chi_z = res["z"]

        def cm(a, b):
            mx = a if abs(a) >= abs(b) else b
            mn = b if mx is a else a
            ps = mn / mx if abs(mx) > 1e-9 else 1.0
            return max(0.6 + 0.4 * ps, 0.4)
        Cmy = cm(inp["My_top"], inp["My_bot"])
        Cmz = cm(inp["Mz_top"], inp["Mz_bot"])
        CmLT = Cmy
        ny = NEd / (chi_y * NRk / g1)
        nz = NEd / (chi_z * NRk / g1)
        if cl <= 2:
            kyy = Cmy * min(1 + (lam_y - 0.2) * ny, 1 + 0.8 * ny)
            kzz = Cmz * min(1 + (2 * lam_z - 0.6) * nz, 1 + 1.4 * nz)
            kyz = 0.6 * kzz
            lim = 1 - 0.1 * nz / (CmLT - 0.25)
            kzy = (max(1 - 0.1 * lam_z * nz / (CmLT - 0.25), lim) if lam_z >= 0.4
                   else min(0.6 + lam_z, 1 - 0.1 * lam_z * nz / (CmLT - 0.25)))
        else:
            kyy = Cmy * min(1 + 0.6 * lam_y * ny, 1 + 0.6 * ny)
            kzz = Cmz * min(1 + 0.6 * lam_z * nz, 1 + 0.6 * nz)
            kyz = kzz
            kzy = max(1 - 0.05 * lam_z * nz / (CmLT - 0.25), 1 - 0.05 * nz / (CmLT - 0.25))
        calc.table(["C_my", "C_mz", "C_mLT", "k_yy", "k_yz", "k_zy", "k_zz"],
                   [[f"{v:.3f}" for v in (Cmy, Cmz, CmLT, kyy, kyz, kzy, kzz)]],
                   caption="Equivalent uniform moment factors (Table B.3) and interaction "
                           "factors (Table B.2)")
        MyRk, MzRk = Wy * fy, Wz * fy
        u61 = ny + kyy * My / (chiLT * MyRk / g1) + kyz * Mz / (MzRk / g1)
        u62 = nz + kzy * My / (chiLT * MyRk / g1) + kzz * Mz / (MzRk / g1)
        calc.check("Eq. 6.61: N/(χ_y N_Rk/γ_M1) + k_yy M_y/(χ_LT M_y,Rk/γ_M1) + k_yz M_z/M_z,Rd "
                   "≤ 1", u61, 1.0, "", "6.3.3(4)", hint=HINT_INT)
        calc.check("Eq. 6.62: N/(χ_z N_Rk/γ_M1) + k_zy M_y/(χ_LT M_y,Rk/γ_M1) + k_zz M_z/M_z,Rd "
                   "≤ 1", u62, 1.0, "", "6.3.3(4)", hint=HINT_INT)
        calc.model3d = cls._scene(calc, inp, sec, chi_z)

    @staticmethod
    def _scene(calc, inp, sec, chi_z) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        h, b, tw, tf, L = m(sec.h), m(sec.b), m(sec.tw), m(sec.tf), m(inp["L"])
        sc = Scene3D("steel_column", calc.tr)
        for key, label in (("steel", "Column"), ("buckle", "Buckled shape (weak axis)"),
                           ("loads", "Loads")):
            sc.layer(key, label, toggle=key != "steel")
        col = PALETTE["steel"]
        sc.box("steel", (0, L / 2, (h - tf) / 2), (b, L, tf), col)
        sc.box("steel", (0, L / 2, -(h - tf) / 2), (b, L, tf), col)
        sc.box("steel", (0, L / 2, 0), (tw, L, h - 2 * tf), col)
        for y in (0.0, L):
            sc.box("steel", (0, y + (0.01 if y == 0 else -0.01), 0), (b + 0.15, 0.02, h + 0.15),
                   "#7d8794")
        amp = 0.05 * L
        pts = [(amp * math.sin(math.pi * i / 20) * (1 if inp["kz"] >= 0.7 else
                                                     math.sin(math.pi * i / 10)),
                i / 20 * L, h / 2 + 0.05) for i in range(21)]
        sc.line("buckle", pts, "#e03b3b", dashed=True)
        sc.arrow("loads", (0, L + 1.2, 0), (0, -1, 0), 1.1, PALETTE["load"], 0.2)
        sc.label("loads", calc.tr("N_Ed = {n:.0f} kN", n=inp["NEd"] / 1000), (0, L + 1.35, 0),
                 "result")
        sc.label("loads", f"{sec.name}", (b, L / 2, 0), "")
        sc.views["default"] = {"pos": [L * 0.9, L * 0.7, L * 0.9], "target": [0, L / 2, 0]}
        return sc.to_dict()
