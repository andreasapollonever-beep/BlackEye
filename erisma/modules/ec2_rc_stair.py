"""RC stair flight (waist slab spanning between landings) — EN 1992-1-1, EN 1991-1-1."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec2 import bar_area, design_flexure, section_capacity, shear_no_links
from ..report.scene3d import PALETTE, Scene3D

CONCRETE = ["C20/25", "C25/30", "C30/37"]
BARS = ["8", "10", "12", "14", "16"]
HINT_M = "Increase the waist thickness or the reinforcement."
HINT_D = "Increase the waist thickness (deflection)."


@register
class StairEC2(DesignModule):
    id = "ec2_rc_stair"
    title = "RC stair flight"
    category = "Concrete"
    has_3d = True
    uses_annex = True
    standard = "EN 1992-1-1, EN 1991-1-1"
    description = ("Straight flight with a waist slab spanning between landings or beams: "
                   "geometry rules (2R + G), self weight of waist and steps, bending, shear, "
                   "minimum reinforcement and span/depth. Interactive 3D model.")

    fields = [
        Field("L", "Horizontal span (support to support)", "m", 3.08, min=1, max=8,
              group="Geometry"),
        Field("rise", "Total rise of the flight", "m", 2.04, min=0.3, max=4, group="Geometry"),
        Field("n", "Number of risers", "", 12, kind="int", min=2, max=25, group="Geometry"),
        Field("w", "Flight width", "m", 1.2, min=0.6, max=4, group="Geometry"),
        Field("t", "Waist thickness (perpendicular to the slope)", "mm", 200.0, min=100,
              max=350, group="Geometry"),
        Field("support", "Support condition", kind="choice",
              choices=["Simply supported", "Continuous with landings"], default="Simply supported",
              group="Geometry", help="Continuous: M = wL²/10 (end spans with landing slabs)."),
        Field("g", "Finishes (on plan)", "kN/m²", 1.5, min=0, group="Loads"),
        Field("q", "Imposed load", "kN/m²", 3.0, min=0, group="Loads",
              help="EN 1991-1-1 category A stairs: 2.0–4.0 kN/m² (national annex)."),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C25/30",
              group="Materials"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Materials"),
        Field("cover", "Cover", "mm", 25.0, min=15, group="Materials"),
        Field("dia", "Main bars Ø", kind="choice", choices=BARS, default="12",
              group="Reinforcement"),
        Field("s", "Main bar spacing", "mm", 150.0, min=75, max=300, group="Reinforcement"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        L, rise, n, t = inp["L"], inp["rise"], inp["n"], inp["t"]
        R = rise / n
        G = L / (n - 1) if n > 1 else L
        if G <= 0:
            raise InputError("The span is too short for the number of risers", "n")
        alpha = math.atan(rise / L)
        calc.heading("Geometry")
        calc.formula("R", "rise / n", R, "mm", "Riser height", dp=0)
        calc.formula("G", "L / (n − 1)", G, "mm", "Going (tread)", dp=0)
        calc.formula("α", "atan(rise / L)", math.degrees(alpha), "°", "Pitch", dp=1)
        calc.check_limit("Comfort: 2R + G ≤ 650 mm", 2 * R + G, 650.0, "mm",
                         "building regulations (600–650)", hint="Adjust the number of risers.")
        calc.check_min("Comfort: 2R + G ≥ 580 mm", 2 * R + G, 580.0, "mm",
                       "building regulations (600–650)", hint="Adjust the number of risers.")
        calc.check_limit("Riser R ≤ 190 mm", R, 190.0, "mm", "building regulations",
                         hint="Add risers.")

        calc.heading("Loads (per metre of width, on plan)")
        sw = calc.formula("g_sw", "25 (t/cos α + R/2)", 25e-6 * (t / math.cos(alpha) + R / 2),
                          "kN/m²", "Waist and steps", dp=2)
        gk = calc.formula("g_k", "g_sw + finishes", sw + inp["g"], "kN/m²", dp=2)
        wd = calc.formula("p_d", "1.35 g_k + 1.5 q_k", 1.35 * gk + 1.5 * inp["q"], "kN/m²", dp=2)
        k = 8 if inp["support"] == "Simply supported" else 10
        MEd = calc.formula("M_Ed", f"p_d L² / {k}", wd * L**2 / k, "kNm/m", dp=1) * 1000
        VEd = calc.formula("V_Ed", "p_d L / 2", wd * L / 2, "kN/m", dp=1) * 1000

        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyk = na.alpha_cc * fck / na.gamma_c, inp["fyk"]
        fyd = fyk / na.gamma_s
        dia = float(inp["dia"])
        d = t - inp["cover"] - dia / 2
        As = bar_area(dia) * 1000 / inp["s"]
        calc.heading("Bending (EN 1992-1-1 §6.1, section perpendicular to the waist)")
        calc.formula("d", "t − c − φ/2", d, "mm")
        r = design_flexure(calc, 1000, d, MEd, fck, fcd, fyk, fyd, t, allow_compression=False,
                           per_metre=True)
        calc.formula("A_s,prov", f"Ø{dia:g} @ {inp['s']:g} mm", As * 1e-3, "mm²/m")
        if math.isfinite(r["As"]):
            calc.check_min("Reinforcement: A_s,prov ≥ A_s,req", As * 1e-3, r["As"] * 1e-3,
                           "mm²/m", "6.1", hint=HINT_M)
        calc.check_min("Minimum reinforcement", As * 1e-3, r["As_min"] * 1e-3, "mm²/m",
                       "9.3.1.1", hint=HINT_M)
        MRd, _ = section_capacity(1000, d, As, fcd, fyd)
        calc.check("Bending: M_Ed ≤ M_Rd", MEd / 1000, MRd / 1000, "kNm/m", "6.1", hint=HINT_M)
        calc.check_limit("Bar spacing ≤ min(3t, 400)", inp["s"], min(3 * t, 400.0), "mm",
                         "9.3.1.1(3)", hint="Reduce the bar spacing.")
        calc.heading("Shear")
        shear_no_links(calc, 1000, d, As, fck, na.gamma_c, VEd * math.cos(alpha), per_metre=True)
        calc.formula("A_s,dist", "0.2 A_s", 0.2 * As * 1e-3, "mm²/m",
                     "Distribution bars across the flight", ref="9.3.1.1(2)")
        calc.heading("Deflection — span/depth (7.4.2)")
        rho = As / (1000 * d)
        rho0 = math.sqrt(fck) * 1e-3
        K = 1.0 if k == 8 else 1.3
        ld = K * (11 + 1.5 * math.sqrt(fck) * rho0 / rho + 3.2 * math.sqrt(fck) *
                  (rho0 / rho - 1) ** 1.5) if rho <= rho0 else K * (11 + 1.5 * math.sqrt(fck) *
                                                                    rho0 / rho)
        ld = calc.formula("(l/d)_lim", "Eq. 7.16", min(ld, 40 * K), "", dp=1)
        calc.check_limit("Span/depth: l/d ≤ (l/d)_lim (horizontal span)", L / d, ld, "", "7.4.2",
                         hint=HINT_D)
        calc.model3d = cls._scene(calc, inp, R, G)

    @staticmethod
    def _scene(calc, inp, R, G) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        n, w, t = inp["n"], m(inp["w"]), m(inp["t"])
        Rm, Gm = m(R), m(G)
        L, rise = m(inp["L"]), m(inp["rise"])
        sc = Scene3D("stair", calc.tr)
        for key, label in (("concrete", "Stair"), ("bars", "Reinforcement"), ("loads", "Loads")):
            sc.layer(key, label, toggle=key != "concrete")
        a = math.atan(rise / L)
        tv = t / math.cos(a)
        pts = [(0, -tv), (0, 0)]
        for i in range(n):
            x = i * Gm
            pts += [(x, (i + 1) * Rm), (min(x + Gm, L), (i + 1) * Rm)]
        pts = pts[:-1] + [(L, rise), (L, rise - tv)]
        sc.prism("concrete", pts, w, PALETTE["concrete"])
        sc.box("concrete", (-0.6, -tv / 2, 0), (1.2, tv, w), "#9aa0a8")
        sc.box("concrete", (L + 0.6, rise - tv / 2, 0), (1.2, tv, w), "#9aa0a8")
        c = m(inp["cover"])
        for z in [-w / 2 + 0.1 + k * (w - 0.2) / 6 for k in range(7)]:
            sc.cylinder("bars", (0, -tv + c, z), (L, rise - tv + c, z), 0.006, "#8a5a2b")
        for i in range(n):
            sc.arrow("loads", (i * Gm + Gm / 2, (i + 1) * Rm + 0.5, 0), (0, -1, 0), 0.4,
                     PALETTE["load"], 0.06)
        return sc.to_dict()
