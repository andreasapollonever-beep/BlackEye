"""Unreinforced masonry wall — EN 1996-1-1 §6.1 (vertical load) and §6.2 (in-plane shear)."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..report.scene3d import Scene3D

# EN 1996-1-1 Table 3.3, general purpose mortar: unit type -> group -> K
K_TABLE = {
    "Clay": {"Group 1": 0.55, "Group 2": 0.45, "Group 3": 0.35, "Group 4": 0.35},
    "Calcium silicate": {"Group 1": 0.55, "Group 2": 0.45},
    "Aggregate concrete": {"Group 1": 0.55, "Group 2": 0.52, "Group 3": 0.45,
                           "Group 4": 0.45},
    "Autoclaved aerated concrete": {"Group 1": 0.55},
    "Manufactured stone": {"Group 1": 0.45},
    "Dimensioned natural stone": {"Group 1": 0.45},
}
MORTAR = {"M2.5": 2.5, "M5": 5.0, "M10": 10.0, "M15": 15.0, "M20": 20.0}
HINT_N = "Use a stronger unit (higher f_b), a stronger mortar or a thicker wall."
HINT_SL = "Increase the wall thickness or add restraint (piers / cross walls)."
HINT_V = "Increase the wall length or thickness, or use a stronger mortar."


def fvk0(unit: str, mortar: float) -> float:
    """Initial shear strength — Table 3.4 (EN) / Table 3 (CYS), general purpose mortar."""
    if unit == "Clay":
        return 0.30 if mortar >= 10 else 0.20
    if unit == "Calcium silicate":
        return 0.20 if mortar >= 10 else 0.15
    return 0.20 if mortar >= 10 else 0.15


def phi_m(emk_t: float, lam: float) -> float:
    """EN 1996-1-1 Annex G, Eq. G.1–G.2 (E = 1000 f_k)."""
    A1 = 1 - 2 * emk_t
    u = (lam - 0.063) / (0.73 - 1.17 * emk_t)
    return max(A1 * math.exp(-u * u / 2), 0.0)


@register
class MasonryWallEC6(DesignModule):
    id = "ec6_masonry_wall"
    title = "Masonry wall"
    category = "Masonry"
    has_3d = True
    uses_annex = True
    standard = "EN 1996-1-1"
    description = ("Load-bearing unreinforced masonry wall: f_k from units and mortar, γ_M by "
                   "category and class, effective height and thickness, slenderness, "
                   "reduction factors at top/bottom/mid-height (Annex G) and in-plane shear "
                   "of a shear wall. Interactive 3D model.")

    fields = [
        Field("unit", "Masonry unit", kind="choice", choices=list(K_TABLE), default="Clay",
              group="Masonry"),
        Field("group", "Unit group", kind="choice", choices=["Group 1", "Group 2", "Group 3",
                                                             "Group 4"],
              default="Group 2", group="Masonry",
              help="Group 1 solid (voids ≤ 25 %), 2 vertically perforated ≤ 55 %, "
                   "3 ≤ 70 %, 4 horizontally perforated."),
        Field("fb", "Normalised unit strength f_b", "N/mm²", 10.0, min=2, max=60,
              group="Masonry"),
        Field("mortar", "Mortar class", kind="choice", choices=list(MORTAR), default="M10",
              group="Masonry"),
        Field("gM_row", "Units and mortar", kind="choice",
              choices=["Category I units, designed mortar", "Category I units, prescribed "
                       "mortar", "Category II units, any mortar"],
              default="Category I units, designed mortar", group="Masonry"),
        Field("exec", "Execution control class", kind="choice", choices=["1", "2", "3", "4", "5"],
              default="2", group="Masonry", help="1 = best supervision … 5 = least."),
        Field("phi_inf", "Final creep coefficient φ∞", "", 1.0, min=0.3, max=3.0,
              group="Masonry", help="Clay 0.5–1.5, concrete/calcium silicate 1.0–2.0 "
                                    "(Table 6 CYS)."),
        Field("t", "Wall thickness t", "mm", 250.0, min=90, max=600, group="Wall"),
        Field("h", "Clear storey height h", "m", 3.0, min=1, max=8, group="Wall"),
        Field("lw", "Wall length l_w", "m", 4.0, min=0.3, group="Wall"),
        Field("restraint", "Restraint of the wall", kind="choice",
              choices=["Top and bottom (RC floors)", "Top and bottom (timber floors)",
                       "Top, bottom and one vertical edge", "Top, bottom and both vertical edges"],
              default="Top and bottom (RC floors)", group="Wall"),
        Field("NEd", "Design vertical load at the top N_Ed", "kN/m", 180.0, min=0,
              group="Design actions"),
        Field("e_top", "Eccentricity of the floor load at the top", "mm", 15.0, min=0,
              group="Design actions", help="From the floor bearing (e.g. t/6 for a slab "
                                           "bearing on part of the wall)."),
        Field("VEd", "In-plane shear on the wall V_Ed", "kN", 60.0, min=0,
              group="Design actions", help="0 = not a shear wall."),
        Field("gamma_m", "Unit weight of masonry", "kN/m³", 18.0, min=5, max=25,
              group="Design actions"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        unit, group = inp["unit"], inp["group"]
        if group not in K_TABLE[unit]:
            raise InputError(calc.tr("{g} is not available for {u} units (Table 3.3)",
                                     g=calc.tr(group), u=calc.tr(unit)), "group")
        t, h, lw = inp["t"], inp["h"], inp["lw"]
        fb, fm = inp["fb"], MORTAR[inp["mortar"]]
        calc.heading("Masonry strength")
        K = calc.formula("K", calc.tr("Table 3.3 ({u}, {g})", u=calc.tr(unit), g=calc.tr(group)),
                         K_TABLE[unit][group], "", dp=2)
        fm_c = min(fm, 2 * fb, 20.0)
        fk = calc.formula("f_k", "K f_b^0.7 f_m^0.3 (f_m ≤ min(2f_b, 20))",
                          K * fb**0.7 * fm_c**0.3, "N/mm²", "Characteristic compressive strength",
                          ref="Eq. 3.2", dp=2)
        gM = na.masonry_gM[inp["gM_row"]][int(inp["exec"]) - 1]
        calc.input("γ_M", gM, "", calc.tr("{r}, class {c} (National Annex)",
                                          r=calc.tr(inp["gM_row"]), c=inp["exec"]), dp=2)
        fd = calc.formula("f_d", "f_k / γ_M", fk / gM, "N/mm²", dp=3)
        if t * lw < 1e5:
            fd = calc.formula("f_d,red", "f_d (0.7 + 3A), A < 0.1 m²", fd * (0.7 + 3 * t * lw / 1e6),
                              "N/mm²", "Small cross-section", ref="6.1.2.1(3)", dp=3)
        E = na.masonry_KE * fk

        calc.heading("Effective height and slenderness (5.5.1)")
        r = inp["restraint"]
        if r.startswith("Top and bottom (RC"):
            rho = 0.75 if inp["e_top"] <= 0.25 * t else 1.0
            rexpr = "ρ_2 = 0.75 (RC floors, e ≤ 0.25t)" if rho == 0.75 else "ρ_2 = 1.0 (e > 0.25t)"
        elif r.startswith("Top and bottom"):
            rho, rexpr = 1.0, "ρ_2 = 1.0"
        else:
            rho2 = 0.75
            if "one" in r:
                rho = (rho2 / (1 + (rho2 * h / (3 * lw)) ** 2) if h <= 3.5 * lw
                       else max(1.5 * lw / h, 0.3))
                rexpr = "ρ_3 (Eq. 5.6 / 5.7)"
            else:
                rho = (rho2 / (1 + (rho2 * h / lw) ** 2) if h <= 1.15 * lw else 0.5 * lw / h)
                rexpr = "ρ_4 (Eq. 5.8 / 5.9)"
        rho = calc.formula("ρ_n", rexpr, rho, "", "Reduction factor", ref="5.5.1.2", dp=3)
        hef = calc.formula("h_ef", "ρ_n h", rho * h, "m", "Effective height")
        tef = calc.input("t_ef", t, "mm", "Effective thickness (single-leaf wall)")
        sl = calc.formula("h_ef / t_ef", "slenderness ratio", hef / tef, "", dp=1)
        calc.check_limit("Slenderness: h_ef/t_ef ≤ 27", sl, 27.0, "", "5.5.1.4", hint=HINT_SL)

        calc.heading("Vertical load resistance (6.1.2)")
        w_self = inp["gamma_m"] * t  # N/mm per mm height
        N_top = inp["NEd"]
        N_mid = N_top + 1.35 * w_self * h / 2
        N_bot = N_top + 1.35 * w_self * h
        calc.formula("N_m,d", "N_Ed + 1.35 γ t h/2", N_mid, "kN/m", "Load at mid-height")
        einit = calc.formula("e_init", "h_ef / 450", hef / 450, "mm", ref="5.5.1.1(4)", dp=1)
        M_top = N_top * inp["e_top"]
        ei_top = calc.formula("e_i,top", "M_top/N_top + e_init ≥ 0.05t",
                              max(M_top / N_top + einit if N_top else einit, 0.05 * t), "mm",
                              ref="Eq. 6.5", dp=1)
        ei_bot = calc.formula("e_i,bot", "e_init ≥ 0.05t (bottom moment ≈ 0)", max(einit, 0.05 * t),
                              "mm", dp=1)
        phi_t = calc.formula("Φ_top", "1 − 2e_i/t", 1 - 2 * ei_top / t, "", ref="Eq. 6.4", dp=3)
        phi_b = 1 - 2 * ei_bot / t
        em = 0.5 * M_top / N_mid + einit
        lam_c = na.masonry_lambda_c
        ek = 0.0 if sl <= lam_c else 0.002 * inp["phi_inf"] * sl * math.sqrt(t * em)
        calc.formula("e_k", "0.002 φ∞ (h_ef/t_ef) √(t e_m) (0 if h_ef/t_ef ≤ λ_c)", ek, "mm",
                     calc.tr("Creep eccentricity (λ_c = {l:g})", l=lam_c), ref="Eq. 6.8", dp=2)
        emk = calc.formula("e_mk", "M_m/N_m + e_init + e_k ≥ 0.05t", max(em + ek, 0.05 * t),
                           "mm", "Mid-height eccentricity (M_m = M_top/2)", ref="Eq. 6.6", dp=1)
        lam = calc.formula("λ", "(h_ef/t_ef) √(f_k/E), E = K_E f_k", sl * math.sqrt(fk / E), "",
                           ref="Eq. G.4", dp=3)
        phim = calc.formula("Φ_m", "A_1 e^(−u²/2), Annex G", phi_m(emk / t, lam), "", dp=3)
        for lab, N, ph in (("top", N_top, phi_t), ("mid-height", N_mid, phim),
                           ("bottom", N_bot, phi_b)):
            NRd = ph * t * fd
            calc.check(calc.tr("Vertical load at {w}: N_Ed ≤ Φ t f_d", w=calc.tr(lab)), N, NRd,
                       "kN/m", "Eq. 6.2", hint=HINT_N)

        if inp["VEd"] > 0:
            calc.heading("In-plane shear (6.2)")
            sd = N_mid / t
            f0 = fvk0(unit, fm)
            calc.formula("f_vk0", calc.tr("Table 3 (CYS) / 3.4, {u}, {m}", u=calc.tr(unit),
                                          m=inp["mortar"]), f0, "N/mm²", dp=2)
            fvk = calc.formula("f_vk", f"f_vk0 + 0.4σ_d ≤ {na.masonry_fvk_max:g} f_b",
                               min(f0 + 0.4 * sd, na.masonry_fvk_max * fb), "N/mm²",
                               ref="Eq. 3.5", dp=3)
            VRd = calc.formula("V_Rd", "f_vk / γ_M t l_c (l_c = l_w, no tension)",
                               fvk / gM * t * lw, "kN", ref="Eq. 6.13")
            calc.check("In-plane shear: V_Ed ≤ V_Rd", inp["VEd"], VRd, "kN", "6.2", hint=HINT_V)
        calc.note("Concentrated loads under beams (6.1.3) and out-of-plane lateral loads (6.3) "
                  "need separate checks; seismic design to EN 1998-1 §9.")
        calc.model3d = cls._scene(calc, inp)

    @staticmethod
    def _scene(calc, inp) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        t, h, lw = m(inp["t"]), m(inp["h"]), m(inp["lw"])
        sc = Scene3D("masonry_wall", calc.tr)
        sc.layer("wall", "Wall", toggle=False)
        sc.layer("floors", "Floors")
        sc.layer("loads", "Loads")
        brick = "#b5653e" if inp["unit"] == "Clay" else "#a7a9ac"
        sc.box("wall", (0, h / 2, 0), (lw, h, t), brick)
        course = 0.25 if inp["unit"] != "Clay" else 0.2
        n = int(h / course)
        for i in range(1, n):
            y = i * course
            sc.line("wall", [(-lw / 2, y, t / 2 + 0.002), (lw / 2, y, t / 2 + 0.002)], "#e6e0d6")
            off = 0.0 if i % 2 else 0.2
            x = -lw / 2 + off
            while x < lw / 2 - 0.01:
                if x > -lw / 2 + 0.01:
                    sc.line("wall", [(x, y - course, t / 2 + 0.002), (x, y, t / 2 + 0.002)],
                            "#e6e0d6")
                x += 0.4
        for y in (-0.1, h + 0.1):
            sc.box("floors", (0, y, 0), (lw + 0.6, 0.2, 1.4), "#9aa0a8", opacity=0.6)
        for i in range(5):
            x = -lw / 2 + lw * (i + 0.5) / 5
            sc.arrow("loads", (x, h + 0.9, inp["e_top"] / 1000), (0, -1, 0), 0.6, "#1d2433", 0.1)
        sc.label("loads", calc.tr("N_Ed = {n:.0f} kN/m", n=inp["NEd"]), (0, h + 1.0, 0), "result")
        if inp["VEd"] > 0:
            sc.arrow("loads", (-lw / 2 - 1.0, h, 0), (1, 0, 0), 0.9, "#e03b3b", 0.15)
            sc.label("loads", calc.tr("V_Ed = {v:.0f} kN", v=inp["VEd"] / 1000),
                     (-lw / 2 - 0.6, h + 0.25, 0), "force")
        sc.views["default"] = {"pos": [lw * 0.8, h * 0.9, lw * 1.3], "target": [0, h / 2, 0]}
        return sc.to_dict()
