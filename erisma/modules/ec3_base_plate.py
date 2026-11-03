"""Column base plate with anchor bolts — EN 1993-1-8 §6.2.5, 6.2.6.5, 6.2.8 and §6.2.2(6)."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec3_bolts import BOLT_AS, BOLT_CLASSES, PLATE, tension_resistance
from ..report.scene3d import PALETTE, Scene3D
from ..sections.steel import get_section, section_names
from .ec3_steel_beam import _fy

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45"]
HINT_C = "Use a larger or thicker base plate, or a stronger concrete / grout."
HINT_T = "Use larger or more anchor bolts, a thicker plate, or increase the lever arm."
HINT_V = "Add a shear nib (shear key) below the plate or use more anchor bolts."


@register
class BasePlateEC3(DesignModule):
    id = "ec3_base_plate"
    title = "Column base plate"
    category = "Steel"
    has_3d = True
    uses_annex = True
    standard = "EN 1993-1-8 §6.2.5–6.2.8, EN 1992-1-1 §6.7"
    description = ("Base plate of an I/H column on a concrete foundation under axial force, "
                   "strong-axis moment and shear: bearing strength f_jd, effective width c, "
                   "compression T-stubs, tension T-stubs with anchor bolts, moment resistance "
                   "and shear by friction and bolts. Interactive 3D model.")

    fields = [
        Field("section", "Column section", kind="choice", choices=section_names(),
              default="HEB 240", group="Column"),
        Field("NEd", "Axial compression N_Ed", "kN", 600.0, min=0, group="Design actions"),
        Field("MEd", "Moment M_y,Ed", "kNm", 100.0, min=0, group="Design actions"),
        Field("VEd", "Shear V_Ed", "kN", 40.0, min=0, group="Design actions"),
        Field("bp", "Plate width b_p (along the flanges)", "mm", 400.0, min=150,
              group="Base plate"),
        Field("lp", "Plate length l_p (along the web)", "mm", 500.0, min=150,
              group="Base plate"),
        Field("tp", "Plate thickness t_p", "mm", 25.0, min=8, max=80, group="Base plate"),
        Field("grade", "Plate steel grade", kind="choice", choices=list(PLATE), default="S275",
              group="Base plate"),
        Field("bolt_cls", "Anchor bolt class", kind="choice", choices=list(BOLT_CLASSES),
              default="8.8", group="Anchor bolts"),
        Field("d", "Anchor bolt diameter", kind="choice", choices=[f"M{k}" for k in BOLT_AS
                                                                 if k >= 16],
              default="M24", group="Anchor bolts"),
        Field("nt", "Bolts per side (in each tension row)", "", 2, kind="int", min=1, max=4,
              group="Anchor bolts"),
        Field("ex", "Bolt distance from plate end e_x", "mm", 50.0, min=25, group="Anchor bolts"),
        Field("w", "Bolt gauge across w", "mm", 240.0, min=60, group="Anchor bolts"),
        Field("concrete", "Foundation concrete", kind="choice", choices=CONCRETE,
              default="C25/30", group="Foundation"),
        Field("af", "Foundation width", "m", 1.2, min=0.3, group="Foundation"),
        Field("bf", "Foundation length", "m", 1.2, min=0.3, group="Foundation"),
        Field("weld", "Flange weld throat a", "mm", 8.0, min=3, max=20, group="Base plate"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        gM0, gM2 = na.gamma_M0, na.gamma_M2
        sec = get_section(inp["section"])
        bp, lp, tp = inp["bp"], inp["lp"], inp["tp"]
        h, b, tf, tw = sec.h, sec.b, sec.tf, sec.tw
        if lp < h + 2 * inp["ex"] + 40 or bp < b:
            raise InputError("The plate must be larger than the column with room for the "
                             "anchor bolts", "lp")
        if inp["w"] >= bp - 40:
            raise InputError("Bolt gauge w is too large for the plate width", "w")
        fy = _fy(inp["grade"], tp)
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd = na.alpha_cc * fck / na.gamma_c
        d = float(inp["d"][1:])

        calc.heading("Bearing strength of the foundation (6.2.5)")
        Ac0 = bp * lp
        Ac1 = min(inp["af"] * inp["bf"], 9 * Ac0)
        kj = calc.formula("k_j", "√(A_c1 / A_c0) ≤ 3", min(math.sqrt(max(Ac1 / Ac0, 1.0)), 3.0),
                          "", "Concentration factor (EN 1992-1-1 6.7)", dp=3)
        fjd = calc.formula("f_jd", "β_j k_j f_cd, β_j = 2/3", 2 / 3 * kj * fcd, "N/mm²",
                           "Design bearing strength of the joint", ref="6.2.5(7)", dp=2)
        c = calc.formula("c", "t_p √(f_y / (3 f_jd γ_M0))", tp * math.sqrt(fy / (3 * fjd * gM0)),
                         "mm", "Additional bearing width", ref="Eq. 6.5", dp=1)

        calc.heading("Compression T-stub under a flange (6.2.5, 6.2.6.9)")
        over_l = (lp - h) / 2
        beff = min(b + 2 * c, bp)
        leff = tf + min(c, over_l) + min(c, (h - 2 * tf) / 2)
        FC = calc.formula("F_C,Rd", "f_jd b_eff l_eff", fjd * beff * leff, "kN",
                          calc.tr("b_eff = {b:.0f} mm, l_eff = {l:.0f} mm", b=beff, l=leff),
                          ref="6.2.6.9")
        Aeff = (2 * beff * leff
                + max(h - 2 * leff, 0.0) * min(tw + 2 * c, bp))
        NjRd = calc.formula("N_j,Rd", "f_jd A_eff (I-shaped effective area)", fjd * Aeff, "kN",
                            "Axial resistance in pure compression")
        calc.check("Pure compression: N_Ed ≤ N_j,Rd", inp["NEd"], NjRd, "kN", "6.2.8.2",
                   hint=HINT_C)

        calc.heading("Tension T-stub: plate in bending with anchor bolts (6.2.6.11)")
        ex, w = inp["ex"], inp["w"]
        e = (bp - w) / 2
        mx = calc.formula("m_x", "(l_p − h)/2 − e_x − 0.8 a √2", over_l - ex - 0.8 *
                          inp["weld"] * math.sqrt(2), "mm", "Bolt to weld toe")
        if mx <= 0:
            raise InputError("Anchor bolts are too close to the column flange (m_x ≤ 0)", "ex")
        leff_cp = min(2 * math.pi * mx, math.pi * mx + w, math.pi * mx + 2 * e)
        leff_nc = min(4 * mx + 1.25 * ex, e + 2 * mx + 0.625 * ex, 0.5 * bp,
                      0.5 * w + 2 * mx + 0.625 * ex)
        leff1 = calc.formula("l_eff,1", "min(l_eff,cp, l_eff,nc) (Table 6.6, row outside "
                             "the flange)", min(leff_cp, leff_nc), "mm", dp=0)
        Mpl = 0.25 * leff1 * tp**2 * fy / gM0
        calc.formula("M_pl,1,Rd", "0.25 l_eff,1 t_p² f_y / γ_M0", Mpl, "kNm", dp=2)
        F12 = calc.formula("F_T,1-2,Rd", "2 M_pl,1,Rd / m_x", 2 * Mpl / mx, "kN",
                           "Plate yielding without prying (anchor bolts, 6.2.4.1(2))")
        nt = inp["nt"]
        FtRd = tension_resistance(inp["bolt_cls"], d, gM2)
        F3 = calc.formula("F_T,3,Rd", "n_t 0.9 f_ub A_s / γ_M2", nt * FtRd, "kN",
                          "Anchor bolt failure")
        FT = calc.formula("F_T,Rd", "min(F_T,1-2, F_T,3)", min(F12, F3), "kN",
                          "Tension T-stub resistance")

        calc.heading("Moment with axial force (6.2.8.3)")
        N, M = inp["NEd"], inp["MEd"]
        zC = (h - tf) / 2
        zT = lp / 2 - ex
        z = zC + zT
        calc.formula("z", "z_C + z_T", z, "mm",
                     calc.tr("Lever arm (z_C = {c:.0f} mm to the flange, z_T = {t:.0f} mm to "
                             "the bolts)", c=zC, t=zT))
        if N > 0 and M / N < zC:
            calc.text("e = M/N < z_C — both flanges in compression.")
            Fc1 = N / 2 + M / (2 * zC)
            calc.formula("F_c,max", "N/2 + M/(2z_C)", Fc1, "kN")
            calc.check("Compressed flange: F_c ≤ F_C,Rd", Fc1, FC, "kN", "Table 6.7",
                       hint=HINT_C)
            Ft = 0.0
        else:
            Ft = calc.formula("F_t,Ed", "(M − N z_C) / z", max((M - N * zC) / z, 0.0), "kN",
                              "Tension in the bolt row (moments about the compressed flange)")
            Fc = calc.formula("F_c,Ed", "N + F_t", N + Ft, "kN", "Compression under the flange")
            calc.check("Tension side: F_t,Ed ≤ F_T,Rd", Ft, FT, "kN", "Table 6.7", hint=HINT_T)
            calc.check("Compression side: F_c,Ed ≤ F_C,Rd", Fc, FC, "kN", "Table 6.7",
                       hint=HINT_C)
            if N > 0:
                eN = M / N
                MjRd = min(FT * z / (1 - zC / eN), FC * z / (1 + zT / eN))
            else:
                MjRd = min(FT * z, FC * z)
            calc.formula("M_j,Rd", "Table 6.7 (for e = M/N)", MjRd, "kNm",
                         "Moment resistance of the base for this axial force")

        calc.heading("Shear (6.2.2(6)–(8))")
        fyb, fub = BOLT_CLASSES[inp["bolt_cls"]]
        ab = 0.44 - 0.0003 * fyb
        Fvb = ab * fub * BOLT_AS[int(d)] / gM2
        nb = 2 * nt
        Ff = calc.formula("F_f,Rd", "C_f,d N_c,Ed, C_f,d = 0.2", 0.2 * N, "kN", "Friction")
        Fvb_t = calc.formula("F_vb,Rd", "n α_b f_ub A_s / γ_M2, α_b = 0.44 − 0.0003 f_yb",
                             nb * Fvb, "kN", calc.tr("Anchor bolts in shear ({n} bolts)", n=nb))
        calc.check("Shear: V_Ed ≤ F_f,Rd + F_vb,Rd", inp["VEd"], Ff + Fvb_t, "kN", "6.2.2(8)",
                   hint=HINT_V)
        calc.note("Anchorage of the bolts in the concrete (pull-out, cone failure) must be "
                  "verified to EN 1992-4; the column-to-plate welds are not checked here.")
        calc.model3d = cls._scene(calc, inp, sec, c, Ft)

    @staticmethod
    def _scene(calc, inp, sec, c, Ft) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        bp, lp, tp = m(inp["bp"]), m(inp["lp"]), m(inp["tp"])
        h, b, tf, tw = m(sec.h), m(sec.b), m(sec.tf), m(sec.tw)
        sc = Scene3D("base_plate", calc.tr)
        for key, label in (("steel", "Column and plate"), ("concrete", "Foundation"),
                           ("bolts", "Anchor bolts"), ("bearing", "Compression zone"),
                           ("loads", "Loads")):
            sc.layer(key, label, toggle=key != "steel")
        Hc = 0.8
        col = PALETTE["steel"]
        sc.box("steel", (0, tp + Hc / 2, (h - tf) / 2), (b, Hc, tf), col)
        sc.box("steel", (0, tp + Hc / 2, -(h - tf) / 2), (b, Hc, tf), col)
        sc.box("steel", (0, tp + Hc / 2, 0), (tw, Hc, h - 2 * tf), col)
        sc.box("steel", (0, tp / 2, 0), (bp, tp, lp), "#7d8794")
        sc.box("concrete", (0, -0.03, 0), (bp + 0.06, 0.06, lp + 0.06), "#8f949b")
        sc.box("concrete", (0, -0.06 - 0.4, 0), (m(inp["af"]), 0.8, m(inp["bf"])), PALETTE["concrete"],
               opacity=0.35)
        ex, w = m(inp["ex"]), m(inp["w"])
        nt = inp["nt"]
        xs = [(-w / 2 + i * w / (nt - 1)) if nt > 1 else 0.0 for i in range(nt)]
        d = m(float(inp["d"][1:]))
        for zc in (lp / 2 - ex, -(lp / 2 - ex)):
            for x in xs:
                sc.cylinder("bolts", (x, tp + 0.06, zc), (x, -0.5, zc), d / 2, "#333a44")
        cc = m(c)
        sc.box("bearing", (0, -0.005, -(h - tf) / 2), (min(b + 2 * cc, bp), 0.012,
                                                       tf + 2 * cc), "#2e9b5f", opacity=0.6)
        sc.arrow("loads", (0, tp + Hc + 0.6, 0), (0, -1, 0), 0.5, PALETTE["load"], 0.08)
        sc.label("loads", calc.tr("N_Ed = {n:.0f} kN, M_Ed = {mm:.0f} kNm",
                                  n=inp["NEd"] / 1000, mm=inp["MEd"] / 1e6),
                 (0, tp + Hc + 0.7, 0), "result")
        if Ft > 0:
            sc.label("bolts", calc.tr("F_t,Ed = {f:.0f} kN", f=Ft / 1000),
                     (bp / 2 + 0.05, 0.1, lp / 2 - ex), "force")
        sc.views["default"] = {"pos": [1.3, 1.1, 1.4], "target": [0, 0.2, 0]}
        return sc.to_dict()
