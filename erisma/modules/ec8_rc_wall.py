"""Ductile RC shear wall, DCM — EN 1998-1 §5.4.1.2.3, §5.4.2.4, §5.4.3.4 with EN 1992-1-1."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec2 import bar_area, moment_resistance
from ..report.scene3d import PALETTE, Scene3D

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45"]
BARS = ["10", "12", "14", "16", "20", "25"]
HINT_M = "Add bars in the boundary elements or lengthen the wall."
HINT_V = "Use closer or larger horizontal web bars, or a thicker wall."
HINT_G = "Increase the wall thickness."
HINT_C = "Use closer / larger hoops in the boundary elements (confinement, Eq. 5.20)."


@register
class RCWallEC8(DesignModule):
    id = "ec8_rc_wall"
    title = "RC shear wall (EC8 DCM)"
    category = "Concrete"
    has_3d = True
    uses_annex = True
    standard = "EN 1998-1 §5.4, EN 1992-1-1"
    description = ("Ductile cantilever wall of ductility class DCM: geometry, normalised axial "
                   "load, critical region, flexure with boundary elements, shear with the "
                   "amplification ε = 1.5, web reinforcement and confinement of the boundary "
                   "elements (Eq. 5.20). Interactive 3D model.")

    fields = [
        Field("lw", "Wall length l_w", "m", 4.0, min=1.0, max=12, group="Geometry"),
        Field("bw", "Wall thickness b_w", "mm", 250.0, min=150, max=600, group="Geometry"),
        Field("hs", "Clear storey height h_s", "m", 3.0, min=2, max=6, group="Geometry"),
        Field("Hw", "Total wall height H_w", "m", 18.0, min=3, max=120, group="Geometry"),
        Field("storeys", "Number of storeys", "", 6, kind="int", min=1, max=40, group="Geometry"),
        Field("NEd", "Axial force N_Ed (seismic, compression +)", "kN", 2500.0, min=0,
              group="Design actions (base, from the analysis)"),
        Field("MEd", "Moment M_Ed", "kNm", 9000.0, min=0,
              group="Design actions (base, from the analysis)"),
        Field("VEd", "Shear V'_Ed (from the analysis)", "kN", 700.0, min=0,
              group="Design actions (base, from the analysis)"),
        Field("q0", "Basic behaviour factor q_0", "", 3.0, min=1.5, max=4.5,
              group="Design actions (base, from the analysis)",
              help="DCM wall systems: q_0 = 3.0 (Table 5.1)."),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C30/37",
              group="Materials"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Materials"),
        Field("cover", "Cover to the hoops", "mm", 30.0, min=20, group="Materials"),
        Field("lc", "Boundary element length l_c", "mm", 700.0, min=200, group="Boundary elements"),
        Field("nbe", "Bars in each boundary element", "", 8, kind="int", min=4, max=30,
              group="Boundary elements"),
        Field("dbe", "Boundary bar Ø", kind="choice", choices=BARS, default="20",
              group="Boundary elements"),
        Field("dh", "Boundary hoop Ø", kind="choice", choices=["8", "10", "12"], default="10",
              group="Boundary elements"),
        Field("sh", "Boundary hoop spacing", "mm", 85.0, min=50, max=250,
              group="Boundary elements"),
        Field("dv", "Web vertical bars Ø (each face)", kind="choice", choices=BARS, default="10",
              group="Web"),
        Field("sv", "Web vertical spacing", "mm", 200.0, min=75, max=400, group="Web"),
        Field("dhw", "Web horizontal bars Ø (each face)", kind="choice", choices=BARS,
              default="12", group="Web"),
        Field("shw", "Web horizontal spacing", "mm", 150.0, min=75, max=400, group="Web"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        lw, bw, hs, Hw = inp["lw"], inp["bw"], inp["hs"], inp["Hw"]
        lc = inp["lc"]
        if 2 * lc >= lw:
            raise InputError("The boundary elements overlap — shorten l_c", "lc")
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyd = na.alpha_cc * fck / na.gamma_c, inp["fyk"] / na.gamma_s
        N, M, V1 = inp["NEd"], inp["MEd"], inp["VEd"]
        Ac = lw * bw
        calc.heading("Geometry (5.4.1.2.3, 5.4.3.4.2)")
        calc.check_min("Thickness b_w ≥ max(150 mm, h_s/20)", bw, max(150.0, hs / 20), "mm",
                       "5.4.1.2.3(1)", hint=HINT_G)
        hcr = max(lw, Hw / 6)
        hlim = min(2 * lw, hs if inp["storeys"] <= 6 else 2 * hs)
        hcr = calc.formula("h_cr", "max(l_w, H_w/6) ≤ min(2l_w, h_s or 2h_s)", min(hcr, hlim),
                           "m", "Height of the critical region", ref="Eq. 5.19a", dp=2)
        nud = calc.formula("ν_d", "N_Ed / (A_c f_cd)", N / (Ac * fcd), "", ref="5.4.3.4.1(2)", dp=3)
        calc.check_limit("Normalised axial load ν_d ≤ 0.4", nud, 0.4, "", "5.4.3.4.1(2)",
                         hint=HINT_G)
        calc.heading("Flexure at the base (5.4.3.4.1)")
        cb = inp["cover"] + float(inp["dh"]) + float(inp["dbe"]) / 2
        Abe = inp["nbe"] * bar_area(float(inp["dbe"]))
        Asv1 = 2 * bar_area(float(inp["dv"])) / inp["sv"]  # mm²/mm both faces
        layers = [(Abe, lc / 2), (Abe, lw - lc / 2)]
        nweb = max(int((lw - 2 * lc) / inp["sv"]), 1)
        for k in range(nweb):
            y = lc + (lw - 2 * lc) * (k + 0.5) / nweb
            layers.append((Asv1 * (lw - 2 * lc) / nweb, y))
        MRd, x = moment_resistance(bw, lw, layers, fcd, fyd, N)
        calc.formula("A_s,be", f"{inp['nbe']} Ø{inp['dbe']}", Abe, "mm²",
                     "Reinforcement of one boundary element")
        MRd = calc.formula("M_Rd", "strain compatibility with web bars, at N_Ed", MRd, "kNm",
                           calc.tr("Moment resistance (x = {x:.0f} mm)", x=x), ref="EN 1992-1-1 6.1")
        calc.check("Flexure: M_Ed ≤ M_Rd", M, MRd, "kNm", "5.4.3.4.1", hint=HINT_M)
        calc.check_min("Boundary element ρ ≥ 0.5 %", Abe / (lc * bw), 0.005, "%", "5.4.3.4.2(8)",
                       hint=HINT_M)
        calc.check_min("Boundary length l_c ≥ max(0.15 l_w, 1.5 b_w)", lc, max(0.15 * lw, 1.5 * bw),
                       "mm", "5.4.3.4.2(6)", hint=HINT_M)
        calc.heading("Shear (5.4.2.4(7), 5.4.3.4.2)")
        VEd = calc.formula("V_Ed", "ε V'_Ed, ε = 1.5 (DCM)", 1.5 * V1, "kN", ref="5.4.2.4(7)")
        z = 0.8 * lw
        nu1 = 0.6 * (1 - fck / 250)
        VRdmax = calc.formula("V_Rd,max", "b_w z ν_1 f_cd / (cot θ + tan θ), cot θ = 1", bw * z * nu1 *
                              fcd / 2, "kN", ref="EN 1992-1-1 Eq. 6.9", dp=0)
        calc.check("Web crushing: V_Ed ≤ V_Rd,max", VEd, VRdmax, "kN", "6.2.3", hint=HINT_G)
        Ash = 2 * bar_area(float(inp["dhw"]))
        VRds = calc.formula("V_Rd,s", "(A_sh/s_h) z f_yd cot θ", Ash / inp["shw"] * z * fyd, "kN",
                            ref="Eq. 6.8", dp=0)
        calc.check("Shear: V_Ed ≤ V_Rd,s", VEd, VRds, "kN", "6.2.3", hint=HINT_V)
        rv = Asv1 / bw
        rh = Ash / (inp["shw"] * bw)
        calc.check_min("Web vertical ρ_v ≥ 0.2 %", rv, 0.002, "%", "EN 1992-1-1 9.6.2", hint=HINT_V)
        calc.check_min("Web horizontal ρ_h ≥ max(0.25 ρ_v, 0.1 %)", rh, max(0.25 * rv, 0.001), "%",
                       "EN 1992-1-1 9.6.3", hint=HINT_V)
        calc.heading("Confinement of the boundary elements (5.4.3.4.2(4))")
        mu_phi = calc.formula("μ_φ", "2q_0 − 1 (T_1 ≥ T_C)", 2 * inp["q0"] - 1, "", ref="5.2.3.4(3)",
                              dp=2)
        b0 = bw - 2 * inp["cover"] - float(inp["dh"])
        h0 = lc - inp["cover"] - float(inp["dh"])
        dh = float(inp["dh"])
        legs = 2 + max(int(h0 / 200), 0)
        Vh = (2 * (b0 + h0) + legs * b0) * bar_area(dh)
        wwd = calc.formula("ω_wd", "(V_hoops / V_core) f_yd / f_cd", Vh / (b0 * h0 * inp["sh"]) * fyd /
                           fcd, "", ref="5.4.3.2.2(8)", dp=3)
        nb = max(inp["nbe"] // 2, 2)
        sb = 2 * (nb - 1) * (h0 / (nb - 1)) ** 2 + 2 * (b0 / 1) ** 2
        an = max(1 - sb / (6 * b0 * h0), 0.0)
        as_ = (1 - inp["sh"] / (2 * b0)) * (1 - inp["sh"] / (2 * h0))
        alpha = calc.formula("α", "α_n α_s", an * as_, "", "Confinement effectiveness", dp=3)
        wv = rv * fyd / fcd
        need = 30 * mu_phi * (nud + wv) * fyd / 200000 * bw / b0 - 0.035
        calc.check_min("Confinement: α ω_wd ≥ 30 μ_φ (ν_d + ω_v) ε_sy,d b_c/b_0 − 0.035",
                       alpha * wwd, max(need, 1e-6), "", "Eq. 5.20", hint=HINT_C)
        calc.check_min("Boundary ω_wd ≥ 0.08", wwd, 0.08, "", "5.4.3.4.2(4)", hint=HINT_C)
        calc.check_limit("Hoop spacing ≤ min(b_0/2, 175, 8 d_bL)", inp["sh"],
                         min(b0 / 2, 175.0, 8 * float(inp["dbe"])), "mm", "5.4.3.2.2(11)",
                         hint=HINT_C)
        sc = Scene3D("rc_wall", calc.tr)
        for key, label in (("concrete", "Wall"), ("bars", "Boundary elements"),
                           ("loads", "Actions")):
            sc.layer(key, label, toggle=key != "concrete")
        L, B, H = lw / 1000, bw / 1000, min(Hw / 1000, 3 * hs / 1000)
        sc.box("concrete", (0, H / 2, 0), (L, H, B), PALETTE["concrete"], opacity=0.45)
        for sx in (-1, 1):
            xc = sx * (L / 2 - lc / 2000)
            sc.box("bars", (xc, H / 2, 0), (lc / 1000, H, B * 1.02), "#e3a008", opacity=0.35)
            for k in range(min(inp["nbe"] // 2, 8)):
                x = xc - lc / 2000 + 0.05 + k * (lc / 1000 - 0.1) / max(inp["nbe"] // 2 - 1, 1)
                for zz in (-B / 2 + cb / 1000, B / 2 - cb / 1000):
                    sc.cylinder("bars", (x, 0, zz), (x, H, zz), float(inp["dbe"]) / 2000, "#8a5a2b")
        sc.box("concrete", (0, hcr / 1000, 0), (L + 0.05, 0.02, B + 0.05), "#e03b3b", opacity=0.7)
        sc.label("concrete", calc.tr("h_cr = {h:.2f} m", h=hcr / 1000), (L / 2 + 0.3, hcr / 1000, 0),
                 "result")
        sc.arrow("loads", (-L / 2 - 1.5, H, 0), (1, 0, 0), 1.3, PALETTE["seismic"], 0.2)
        sc.label("loads", calc.tr("V_Ed = {v:.0f} kN", v=VEd / 1000), (-L / 2 - 1.0, H + 0.3, 0),
                 "force")
        calc.model3d = sc.to_dict()
