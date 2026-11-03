"""Fire resistance — EN 1993-1-2 (steel), EN 1995-1-2 (timber), EN 1992-1-2 (concrete tables).

Standard fire exposure (ISO 834 curve, EN 1991-1-2 3.2.1).  Steel: critical temperature
(Eq. 4.22) and incremental heating of unprotected (Eq. 4.25) or protected (Eq. 4.27) members.
Timber: reduced cross-section method (4.2.2).  Concrete: tabulated data (Tables 5.5, 5.8).
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..report.scene3d import PALETTE, Scene3D, heat_color
from ..report.svg import line_plot
from ..sections.steel import get_section, section_names
from .ec5_timber_beam import TIMBER

R_CHOICES = ["R30", "R60", "R90", "R120", "R180", "R240"]
HINT_S = "Add (more) fire protection, or lower the utilisation (heavier section)."
HINT_T = "Use a larger section, glulam, or fire-protective boards."
HINT_C = "Increase the member width/thickness or the axis distance (cover)."


def iso834(t_min):
    return 20 + 345 * np.log10(8 * np.asarray(t_min, float) + 1)


def c_steel(th: float) -> float:
    """Specific heat of carbon steel, EN 1993-1-2 3.4.1.2 [J/kgK]."""
    if th < 600:
        return 425 + 0.773 * th - 1.69e-3 * th**2 + 2.22e-6 * th**3
    if th < 735:
        return 666 + 13002 / (738 - th)
    if th < 900:
        return 545 + 17820 / (th - 731)
    return 650.0


def theta_cr(mu0: float) -> float:
    mu0 = min(max(mu0, 0.013), 0.99)
    return 39.19 * math.log(1 / (0.9674 * mu0**3.833) - 1) + 482


def heat_steel(AmV: float, ksh: float, prot: dict | None, t_end: float = 240.0):
    """Steel temperature history (minutes, °C); AmV in 1/m."""
    dt = 5.0
    ta, out_t, out_a = 20.0, [0.0], [20.0]
    t = 0.0
    sig, eps = 5.67e-8, 0.7
    tg_prev = 20.0
    while t < t_end * 60:
        t += dt
        tg = float(iso834(t / 60))
        ca = c_steel(ta)
        if prot is None:
            hnet = 25 * (tg - ta) + eps * sig * ((tg + 273) ** 4 - (ta + 273) ** 4)
            ta += ksh * AmV / (ca * 7850) * hnet * dt
        else:
            lp, dp, cp, rp = prot["lp"], prot["dp"], prot["cp"], prot["rp"]
            phi = cp * rp / (ca * 7850) * dp * AmV
            d = lp / dp * AmV / (ca * 7850) * (tg - ta) / (1 + phi / 3) * dt \
                - (math.exp(phi / 10) - 1) * (tg - tg_prev)
            ta += max(d, 0.0)
        tg_prev = tg
        if int(t) % 30 == 0:
            out_t.append(t / 60)
            out_a.append(ta)
    return np.array(out_t), np.array(out_a)


@register
class SteelFireEC3(DesignModule):
    id = "ec3_fire"
    title = "Fire resistance — steel member"
    category = "Fire"
    has_3d = True
    standard = "EN 1993-1-2, EN 1991-1-2"
    description = ("Steel I/H member in the standard fire: degree of utilisation, critical "
                   "temperature, section factor with shadow effect, heating of the unprotected "
                   "or protected member and the fire resistance time against the requirement.")

    fields = [
        Field("section", "Section", kind="choice", choices=section_names(), default="HEB 240",
              group="Member"),
        Field("exposure", "Fire exposure", kind="choice",
              choices=["4 sides (column)", "3 sides (beam under a slab)"],
              default="3 sides (beam under a slab)", group="Member"),
        Field("U", "Utilisation at normal temperature E_d / R_d", "", 0.8, min=0.05, max=1.0,
              group="Loading", help="From the cold design (e.g. the steel beam calculation)."),
        Field("eta", "Reduction factor for fire η_fi", "", 0.65, min=0.2, max=1.0, group="Loading",
              help="E_fi,d = η_fi E_d; EN 1993-1-2 2.4.2(3): 0.65 recommended (0.7 for "
                   "storage areas)."),
        Field("R", "Required fire resistance", kind="choice", choices=R_CHOICES, default="R60",
              group="Requirement"),
        Field("protection", "Fire protection", kind="choice",
              choices=["None", "Board / spray (λ_p, d_p)"], default="Board / spray (λ_p, d_p)",
              group="Protection"),
        Field("lp", "Thermal conductivity λ_p", "", 0.12, min=0.02, max=1.0, group="Protection",
              show_if="protection=Board / spray (λ_p, d_p)", help="W/mK — from the product data."),
        Field("dp", "Protection thickness d_p", "mm", 20.0, min=2, max=100, group="Protection",
              show_if="protection=Board / spray (λ_p, d_p)"),
        Field("cp", "Specific heat c_p", "", 1200.0, min=100, max=3000, group="Protection",
              show_if="protection=Board / spray (λ_p, d_p)", help="J/kgK"),
        Field("rp", "Density ρ_p", "kN/m³", 3.0, min=0.5, max=20, group="Protection",
              show_if="protection=Board / spray (λ_p, d_p)", help="e.g. 3 kN/m³ ≈ 300 kg/m³"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        sec = get_section(inp["section"])
        h, b, tw = sec.h, sec.b, sec.tw
        three = inp["exposure"].startswith("3")
        calc.heading("Section factor (4.2.5.1)")
        P = 2 * h + 4 * b - 2 * tw - (b if three else 0)
        AmV = calc.formula("A_m/V", "exposed perimeter / A", P / sec.A * 1000, "",
                           "Section factor [1/m]", dp=0)
        box = (2 * h + b if three else 2 * (b + h)) / sec.A * 1000
        calc.formula("[A_m/V]_b", "box perimeter / A", box, "", "Box value [1/m]", dp=0)
        ksh = calc.formula("k_sh", "0.9 [A_m/V]_b / [A_m/V]", 0.9 * box / AmV, "",
                           "Shadow effect", ref="Eq. 4.26a", dp=3)
        calc.heading("Critical temperature (4.2.4)")
        mu0 = calc.formula("μ_0", "η_fi E_d / R_d (γ_M,fi = γ_M = 1.0)", inp["eta"] * inp["U"], "",
                           "Degree of utilisation in fire", ref="Eq. 4.24", dp=3)
        tcr = calc.formula("θ_a,cr", "39.19 ln[1/(0.9674 μ_0^3.833) − 1] + 482", theta_cr(mu0),
                           "°", "Critical steel temperature", ref="Eq. 4.22", dp=0)
        calc.note("Eq. 4.22 applies to members without instability (laterally restrained beams, "
                  "tension members); for slender columns check buckling in fire (4.2.3.2).")
        prot = None
        if inp["protection"] != "None":
            calc.heading("Fire protection (4.2.5.2)")
            ApV = (2 * h + b if three else 2 * (b + h)) / sec.A * 1000  # board: box
            calc.formula("A_p/V", "box perimeter / A (boards)", ApV, "", "[1/m]", dp=0)
            prot = {"lp": inp["lp"], "dp": inp["dp"] / 1000, "cp": inp["cp"],
                    "rp": inp["rp"] * 1e6 / 9.81}
            calc.input("λ_p", inp["lp"], "", "Thermal conductivity [W/mK]", dp=3)
            calc.input("d_p", inp["dp"], "mm", "Thickness")
            AmV_used = ApV
        else:
            AmV_used = AmV
        t, ta = heat_steel(AmV_used, ksh if prot is None else 1.0, prot)
        reach = np.where(ta >= tcr)[0]
        t_fi = float(t[reach[0]]) if len(reach) else 240.0
        req = float(inp["R"][1:])
        calc.heading("Fire resistance (ISO 834)")
        calc.formula("t_fi,d", "time when θ_a = θ_a,cr", t_fi, "", calc.tr(
            "Fire resistance [min]{s}", s=" (> 240)" if not len(reach) else ""), dp=0)
        calc.check_min(calc.tr("Fire resistance ≥ {r}", r=inp["R"]), t_fi, req, "",
                       "EN 1993-1-2 2.4.2", hint=HINT_S)
        tg = iso834(t)
        calc.figure(line_plot([(calc.tr("Gas (ISO 834)"), t, tg, "#e03b3b"),
                               (calc.tr("Steel"), t, ta, "#2a6f97")], calc.tr("time [min]"),
                              "θ [°C]", [(tcr, "θ_cr")], [(req, inp["R"])]),
                    "Gas and steel temperature in the standard fire")
        theta_req = float(np.interp(req, t, ta))
        calc.values["θ_req"] = theta_req
        sc = Scene3D("fire_steel", calc.tr)
        sc.layer("steel", "Member", toggle=False)
        sc.layer("notes", "Results")
        col = heat_color(min(theta_req / 900, 1))
        L = 4.0
        hm, bm, tf = h / 1000, b / 1000, sec.tf / 1000
        sc.box("steel", (L / 2, hm - tf / 2, 0), (L, tf, bm), col)
        sc.box("steel", (L / 2, tf / 2, 0), (L, tf, bm), col)
        sc.box("steel", (L / 2, hm / 2, 0), (L, hm - 2 * tf, tw / 1000), col)
        if prot:
            sc.box("steel", (L / 2, hm / 2, 0), (L, hm + 0.04, bm + 0.04), "#d9d4c7", opacity=0.35)
        if three:
            sc.box("steel", (L / 2, hm + 0.1, 0), (L, 0.2, 1.2), PALETTE["concrete"])
        sc.label("notes", calc.tr("θ_a at {r} = {th:.0f} °C, θ_cr = {c:.0f} °C", r=inp["R"],
                                  th=theta_req, c=tcr), (L / 2, hm + 0.5, 0), "result")
        calc.model3d = sc.to_dict()


@register
class TimberFireEC5(DesignModule):
    id = "ec5_fire"
    title = "Fire resistance — timber beam"
    category = "Fire"
    has_3d = True
    standard = "EN 1995-1-2 §4.2.2"
    description = ("Reduced cross-section method: charring depth, effective section, strength "
                   "in fire (k_fi, k_mod,fi = 1) and bending, lateral buckling and shear under the "
                   "fire load combination.")

    fields = [
        Field("cls", "Strength class", kind="choice", choices=list(TIMBER), default="GL24h",
              group="Member"),
        Field("b", "Width b", "mm", 160.0, min=60, group="Member"),
        Field("h", "Depth h", "mm", 480.0, min=100, group="Member"),
        Field("L", "Span L", "m", 6.0, min=0.5, group="Member"),
        Field("sides", "Exposure", kind="choice",
              choices=["3 sides (top protected)", "4 sides"], default="3 sides (top protected)",
              group="Member"),
        Field("g", "Permanent load g_k (incl. self weight)", "kN/m", 3.0, min=0, group="Loads"),
        Field("q", "Variable load q_k", "kN/m", 3.0, min=0, group="Loads"),
        Field("psi", "ψ for the fire situation", "", 0.3, min=0, max=1, group="Loads",
              help="EN 1991-1-2 4.3.1: ψ2,1 recommended (or ψ1,1 per the National Annex)."),
        Field("R", "Required fire resistance", kind="choice", choices=R_CHOICES[:4], default="R30",
              group="Requirement"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        typ, fmk, fvk, _, E0, E05, _, rho = TIMBER[inp["cls"]]
        glulam = typ == "Glulam"
        t = float(inp["R"][1:])
        b, h, L = inp["b"], inp["h"], inp["L"]
        calc.heading("Charring and effective section (4.2.2)")
        bn = calc.formula("β_n", "Table 3.1", 0.7 if glulam else 0.8, "",
                          "Notional charring rate [mm/min]", dp=2)
        dchar = calc.formula("d_char,n", "β_n t", bn * t, "mm", dp=1)
        def_ = calc.formula("d_ef", "d_char,n + k_0 d_0, d_0 = 7 mm, k_0 = 1", dchar + 7, "mm",
                            ref="Eq. 4.1", dp=1)
        four = inp["sides"].startswith("4")
        bf = calc.formula("b_fi", "b − 2 d_ef", b - 2 * def_, "mm", dp=0)
        hf = calc.formula("h_fi", "h − d_ef" + (" × 2" if four else ""), h - (2 if four else 1) * def_,
                          "mm", dp=0)
        if bf <= 20 or hf <= 20:
            raise InputError("The section burns away within the required time — enlarge it", "b")
        calc.heading("Design in fire")
        kfi = calc.formula("k_fi", "Table 2.1", 1.15 if glulam else 1.25, "", dp=2)
        fmd = calc.formula("f_m,d,fi", "k_mod,fi k_fi f_m,k / γ_M,fi (1.0, 1.0)", kfi * fmk,
                           "N/mm²", dp=1)
        wfi = calc.formula("w_fi", "g_k + ψ q_k", inp["g"] + inp["psi"] * inp["q"], "kN/m", dp=2)
        M = wfi * L**2 / 8
        V = wfi * L / 2
        W = bf * hf**2 / 6
        sm = calc.formula("σ_m,fi", "M_fi / W_fi", M / W, "N/mm²", dp=2)
        lef = 0.9 * L + 2 * hf
        scrit = 0.78 * bf**2 * kfi * E05 * 1000 / (hf * lef)
        lrel = math.sqrt(kfi * fmk / scrit)
        kcrit = 1.0 if lrel <= 0.75 else (1.56 - 0.75 * lrel if lrel <= 1.4 else 1 / lrel**2)
        calc.formula("k_crit,fi", "EN 1995-1-1 6.3.3 with the residual section", kcrit, "", dp=3)
        calc.check("Bending in fire: σ_m,fi ≤ k_crit f_m,d,fi", sm, kcrit * fmd, "N/mm²",
                   "EN 1995-1-2 4.2.2", hint=HINT_T)
        tau = 1.5 * V / (0.67 * bf * hf)
        calc.check("Shear in fire: τ_fi ≤ k_fi f_v,k", tau, kfi * fvk, "N/mm²", "EN 1995-1-2 4.2.2",
                   hint=HINT_T)
        sc = Scene3D("fire_timber", calc.tr)
        sc.layer("wood", "Residual section", toggle=False)
        sc.layer("char", "Char layer")
        Lm, bm, hm = L / 1000, b / 1000, h / 1000
        sc.box("char", (Lm / 2, hm / 2, 0), (Lm, hm, bm), "#2b2522", opacity=0.55)
        sc.box("wood", (Lm / 2, (hf / 2 + (def_ if four else 0)) / 1000 * 1 + 0, 0),
               (Lm * 0.999, hf / 1000, bf / 1000), "#c8955a")
        sc.label("char", calc.tr("d_ef = {d:.0f} mm after {t:.0f} min", d=def_, t=t),
                 (Lm / 2, hm + 0.3, 0), "result")
        calc.model3d = sc.to_dict()


# EN 1992-1-2 Table 5.5 (simply supported beams): R -> [(b_min, a)], b_w,min
T55 = {"R30": ([(80, 25), (120, 20), (160, 15), (200, 15)], 80),
       "R60": ([(120, 40), (160, 35), (200, 30), (300, 25)], 100),
       "R90": ([(150, 55), (200, 45), (300, 40), (400, 35)], 110),
       "R120": ([(200, 65), (240, 60), (300, 55), (500, 50)], 130),
       "R180": ([(240, 80), (300, 70), (400, 65), (600, 60)], 150),
       "R240": ([(280, 90), (350, 80), (500, 75), (700, 70)], 170)}
# Table 5.8 (simply supported slabs): R -> (h_s, a one-way, a two-way ≤1.5, a two-way ≤2)
T58 = {"R30": (60, 10, 10, 10), "R60": (80, 20, 10, 15), "R90": (100, 30, 15, 20),
       "R120": (120, 40, 20, 25), "R180": (150, 55, 30, 40), "R240": (175, 65, 40, 50)}


@register
class ConcreteFireEC2(DesignModule):
    id = "ec2_fire"
    title = "Fire resistance — RC beam / slab"
    category = "Fire"
    has_3d = True
    standard = "EN 1992-1-2 §5 (tabulated data)"
    description = ("Tabulated data for simply supported beams (Table 5.5) and slabs "
                   "(Table 5.8): minimum width / thickness and axis distance of the "
                   "reinforcement for the required fire resistance.")

    fields = [
        Field("member", "Member", kind="choice",
              choices=["Simply supported beam", "One-way slab", "Two-way slab (l_y/l_x ≤ 1.5)",
                       "Two-way slab (1.5 < l_y/l_x ≤ 2)"], default="Simply supported beam",
              group="Member"),
        Field("R", "Required fire resistance", kind="choice", choices=R_CHOICES, default="R90",
              group="Member"),
        Field("b", "Beam width b / slab thickness h", "mm", 300.0, min=60, group="Member"),
        Field("cover", "Nominal cover to the links (beam) / bars (slab)", "mm", 35.0, min=10,
              group="Reinforcement"),
        Field("link", "Link Ø (beam)", "mm", 8.0, min=0, max=16, group="Reinforcement"),
        Field("dia", "Main bar Ø", "mm", 20.0, min=8, max=40, group="Reinforcement"),
        Field("layers", "One layer of bars (beam: corner bars need a + 10 mm)", kind="bool",
              default=True, group="Reinforcement"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        R = inp["R"]
        beam = inp["member"].startswith("Simply")
        a = inp["cover"] + (inp["link"] if beam else 0) + inp["dia"] / 2
        calc.heading("Axis distance")
        calc.formula("a", "c + φ_link + φ/2" if beam else "c + φ/2", a, "mm",
                     "Axis distance of the main bars", dp=0)
        if beam:
            combos, bw = T55[R]
            bmins = [x for x, _ in combos]
            if inp["b"] < bmins[0]:
                calc.check_min(calc.tr("Beam width b ≥ b_min ({r})", r=R), inp["b"], bmins[0],
                               "mm", "EN 1992-1-2 Table 5.5", hint=HINT_C)
                areq = combos[0][1]
            else:
                areq = float(np.interp(inp["b"], bmins, [y for _, y in combos]))
                calc.check_min(calc.tr("Beam width b ≥ b_min ({r})", r=R), inp["b"], bmins[0],
                               "mm", "EN 1992-1-2 Table 5.5", hint=HINT_C)
            calc.table(["b_min [mm]", "a [mm]"], [[str(x), str(y)] for x, y in combos],
                       caption=calc.tr("EN 1992-1-2 Table 5.5, {r} (web b_w ≥ {w} mm)", r=R, w=bw))
            areq = calc.formula("a_req", "Table 5.5 interpolated for b", areq, "mm", dp=0)
            if inp["layers"]:
                calc.formula("a_sd", "a_req + 10 mm (corner bars, one layer)", areq + 10, "mm",
                             ref="5.6.3(5)", dp=0)
                areq += 10
            calc.check_min(calc.tr("Axis distance a ≥ a_req ({r})", r=R), a, areq, "mm",
                           "EN 1992-1-2 5.6", hint=HINT_C)
        else:
            hs, a1, a2, a3 = T58[R]
            areq = {"One-way slab": a1}.get(inp["member"], a2 if "≤ 1.5" in inp["member"] else a3)
            calc.check_min(calc.tr("Slab thickness h ≥ h_s,min ({r})", r=R), inp["b"], hs, "mm",
                           "EN 1992-1-2 Table 5.8", hint=HINT_C)
            calc.check_min(calc.tr("Axis distance a ≥ a_min ({r})", r=R), a, areq, "mm",
                           "EN 1992-1-2 Table 5.8", hint=HINT_C)
        calc.note("Tabulated data apply to normal-weight concrete with siliceous aggregate and "
                  "the reinforcement stress level of EN 1992-1-2 5.2(5); continuous members: "
                  "Tables 5.6 / 5.8 continuous columns.")
        sc = Scene3D("fire_concrete", calc.tr)
        sc.layer("concrete", "Member", toggle=False)
        sc.layer("bars", "Reinforcement")
        bm = inp["b"] / 1000
        if beam:
            hb = max(bm * 1.8, 0.4)
            sc.box("concrete", (0, hb / 2, 0), (bm, hb, 2.0), PALETTE["concrete"], opacity=0.4)
            for k in range(3):
                x = -bm / 2 + a / 1000 + k * (bm - 2 * a / 1000) / 2
                sc.cylinder("bars", (x, a / 1000, -1), (x, a / 1000, 1), inp["dia"] / 2000, "#8a5a2b")
            sc.box("concrete", (0, -0.05, 0), (bm + 0.2, 0.1, 2.0), heat_color(0.9), opacity=0.5)
        else:
            sc.box("concrete", (0, bm / 2, 0), (2.0, bm, 2.0), PALETTE["concrete"], opacity=0.4)
            for k in range(7):
                z = -0.9 + k * 0.3
                sc.cylinder("bars", (-1, a / 1000, z), (1, a / 1000, z), inp["dia"] / 2000, "#8a5a2b")
            sc.box("concrete", (0, -0.05, 0), (2.2, 0.1, 2.2), heat_color(0.9), opacity=0.5)
        sc.label("bars", f"a = {a:.0f} mm", (bm, 0.1, 1), "result")
        calc.model3d = sc.to_dict()
