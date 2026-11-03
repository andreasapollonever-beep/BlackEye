"""Timber beam — EN 1995-1-1 (solid timber EN 338, glulam EN 14080)."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, register
from ..design.annex import get_annex
from ..report.scene3d import Scene3D

# class: (type, f_m,k, f_v,k, f_c,90,k, E_0,mean [kN/mm²], E_0,05, G_mean, ρ_k)
TIMBER = {
    "C16": ("Solid timber", 16, 3.2, 2.2, 8.0, 5.4, 0.50, 310),
    "C20": ("Solid timber", 20, 3.6, 2.3, 9.5, 6.4, 0.59, 330),
    "C24": ("Solid timber", 24, 4.0, 2.5, 11.0, 7.4, 0.69, 350),
    "C30": ("Solid timber", 30, 4.0, 2.7, 12.0, 8.0, 0.75, 380),
    "GL24h": ("Glulam", 24, 3.5, 2.5, 11.5, 9.6, 0.65, 385),
    "GL28h": ("Glulam", 28, 3.5, 2.5, 12.6, 10.5, 0.65, 425),
    "GL32h": ("Glulam", 32, 3.5, 2.5, 14.2, 11.8, 0.65, 440),
    "GL24c": ("Glulam", 24, 3.5, 2.5, 11.0, 9.1, 0.65, 365),
}
# EN 1995-1-1 Table 3.1 (solid & glulam): service class -> duration -> k_mod
KMOD = {1: {"Permanent": 0.6, "Long-term": 0.7, "Medium-term": 0.8, "Short-term": 0.9,
            "Instantaneous": 1.1},
        3: {"Permanent": 0.5, "Long-term": 0.55, "Medium-term": 0.65, "Short-term": 0.7,
            "Instantaneous": 0.9}}
KMOD[2] = KMOD[1]
KDEF = {1: 0.6, 2: 0.8, 3: 2.0}  # Table 3.2
HINT_B = "Use a deeper section or a higher strength class (e.g. glulam GL28h)."
HINT_LTB = "Add lateral restraints to the compression edge or use a wider section."
HINT_D = "Use a deeper section (stiffness grows with h³) or a stiffer class."
HINT_BRG = "Increase the support length or the beam width."


@register
class TimberBeamEC5(DesignModule):
    id = "ec5_timber_beam"
    title = "Timber beam"
    category = "Timber"
    has_3d = True
    uses_annex = True
    standard = "EN 1995-1-1, EN 338, EN 14080"
    description = ("Simply supported solid timber or glulam beam: k_mod by service class "
                   "and load duration, size factor, bending with lateral-torsional buckling "
                   "(k_crit), shear (k_cr), bearing (k_c,90) and instantaneous/final "
                   "deflection with creep (k_def). Interactive 3D model.")

    fields = [
        Field("cls", "Strength class", kind="choice", choices=list(TIMBER), default="GL24h",
              group="Section"),
        Field("b", "Width b", "mm", 140.0, min=38, max=400, group="Section"),
        Field("h", "Depth h", "mm", 400.0, min=75, max=2000, group="Section"),
        Field("L", "Span L", "m", 6.0, min=0.5, max=40, group="Geometry"),
        Field("lef_f", "Lateral restraint spacing (0 = span)", "m", 0.0, min=0,
              group="Geometry", help="Distance between restraints of the compression edge "
                                     "(e.g. purlins, floor joists)."),
        Field("top", "Load on the compression (top) edge", kind="bool", default=True,
              group="Geometry", help="Destabilising: l_ef + 2h (Table 6.1)."),
        Field("lb", "Support length", "mm", 120.0, min=40, group="Geometry"),
        Field("sc", "Service class", kind="choice", choices=["1", "2", "3"], default="1",
              group="Use", help="1 heated interior, 2 covered unheated, 3 exposed outdoors."),
        Field("g", "Permanent load g_k (excl. self weight)", "kN/m", 2.0, min=0, group="Loads"),
        Field("q", "Variable load q_k", "kN/m", 3.0, min=0, group="Loads"),
        Field("dur", "Duration of the variable load", kind="choice",
              choices=list(KMOD[1]), default="Medium-term", group="Loads",
              help="Imposed floor load: medium; snow: short (Cyprus); wind: short/instant."),
        Field("psi2", "ψ2 of the variable load", "", 0.3, min=0, max=1, group="Loads"),
        Field("w_inst", "Limit w_inst (variable) = L / …", "", 300.0, min=100,
              group="Serviceability"),
        Field("w_fin", "Limit w_net,fin = L / …", "", 250.0, min=100, group="Serviceability"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        typ, fmk, fvk, fc90k, E0, E05, Gm, rho = TIMBER[inp["cls"]]
        E0, E05, Gm = E0 * 1000, E05 * 1000, Gm * 1000
        b, h, L = inp["b"], inp["h"], inp["L"]
        sc_ = int(inp["sc"])
        gM = na.timber_gM[typ]
        calc.heading("Material and section")
        if not na.timber_na:
            calc.note("No National Annex for EN 1995-1-1 is available for the selected country "
                      "in Erisma — EN recommended values are used (γ_M, k_mod, k_def, "
                      "deflection limits).")
        calc.table(["Class", "f_m,k", "f_v,k", "f_c,90,k", "E_0,mean", "E_0,05", "G_mean", "ρ_k"],
                   [[inp["cls"], f"{fmk:g}", f"{fvk:g}", f"{fc90k:g}", f"{E0:g}", f"{E05:g}",
                     f"{Gm:g}", f"{rho:g}"]],
                   caption=calc.tr("{t} — N/mm², kg/m³ ({s})", t=calc.tr(typ),
                                   s="EN 338" if typ == "Solid timber" else "EN 14080"))
        calc.input("γ_M", gM, "", calc.tr("Partial factor ({t}, Table 2.3)", t=calc.tr(typ)),
                   dp=2)
        A, W, I = b * h, b * h**2 / 6, b * h**3 / 12
        sw = calc.formula("g_sw", "ρ_k g b h (≈ 1.1 ρ_k)", 1.1 * rho * 9.81e-9 * A, "kN/m",
                          "Self weight", dp=3)
        gk = inp["g"] + sw
        qk = inp["q"]

        calc.heading("Load combinations and k_mod")
        cases = [("1.35 G (permanent)", 1.35 * gk, KMOD[sc_]["Permanent"])]
        if qk > 0:
            cases.append((calc.tr("1.35 G + 1.5 Q ({d})", d=calc.tr(inp["dur"])),
                          1.35 * gk + 1.5 * qk, KMOD[sc_][inp["dur"]]))
        calc.table(["Combination", "w_d [kN/m]", "k_mod", "w_d / k_mod"],
                   [[lab, f"{w:.2f}", f"{k:g}", f"{w / k:.2f}"] for lab, w, k in cases],
                   caption="The governing combination has the largest w_d / k_mod (EN 1995-1-1 "
                           "3.1.3)")
        lab, wd, kmod = max(cases, key=lambda x: x[1] / x[2])
        calc.text("Governing: **{l}**, k_mod = {k:g}.", l=lab, k=kmod)
        MEd = calc.formula("M_Ed", "w_d L² / 8", wd * L**2 / 8, "kNm")
        VEd = calc.formula("V_Ed", "w_d L / 2", wd * L / 2, "kN")

        calc.heading("Bending (6.1.6) and lateral-torsional buckling (6.3.3)")
        if typ == "Solid timber":
            kh = min((150 / h) ** 0.2, 1.3) if h < 150 else 1.0
            khe = "(150/h)^0.2 ≤ 1.3 (h < 150 mm)"
        else:
            kh = min((600 / h) ** 0.1, 1.1) if h < 600 else 1.0
            khe = "(600/h)^0.1 ≤ 1.1 (h < 600 mm)"
        kh = calc.formula("k_h", khe, kh, "", "Size factor", ref="3.2 / 3.3", dp=3)
        fmd = calc.formula("f_m,d", "k_mod k_h f_m,k / γ_M", kmod * kh * fmk / gM, "N/mm²", dp=2)
        sm = calc.formula("σ_m,d", "M_Ed / W, W = bh²/6", MEd / W, "N/mm²", dp=2)
        lr = inp["lef_f"] if inp["lef_f"] > 0 else L
        lef = 0.9 * lr + (2 * h if inp["top"] else -0.5 * h)
        lef = calc.formula("l_ef", "0.9 l + 2h (top edge) / − 0.5h", lef, "m",
                           "Effective length (Table 6.1, UDL)", dp=2)
        scrit = calc.formula("σ_m,crit", "0.78 b² E_0,05 / (h l_ef)", 0.78 * b**2 * E05 / (h * lef),
                             "N/mm²", ref="Eq. 6.32", dp=1)
        lrel = calc.formula("λ_rel,m", "√(f_m,k / σ_m,crit)", math.sqrt(fmk / scrit), "",
                            ref="Eq. 6.30", dp=3)
        kcrit = 1.0 if lrel <= 0.75 else (1.56 - 0.75 * lrel if lrel <= 1.4 else 1 / lrel**2)
        kcrit = calc.formula("k_crit", "Eq. 6.34", kcrit, "", dp=3)
        calc.check("Bending: σ_m,d ≤ f_m,d", sm, fmd, "N/mm²", "Eq. 6.11", hint=HINT_B)
        calc.check("LTB: σ_m,d ≤ k_crit f_m,d", sm, kcrit * fmd, "N/mm²", "Eq. 6.33",
                   hint=HINT_LTB)

        calc.heading("Shear (6.1.7)")
        kcr = 0.67
        tau = calc.formula("τ_d", "1.5 V_Ed / (k_cr b h), k_cr = 0.67", 1.5 * VEd / (kcr * b * h),
                           "N/mm²", ref="Eq. 6.60 / 6.1.7(2)", dp=3)
        fvd = calc.formula("f_v,d", "k_mod f_v,k / γ_M", kmod * fvk / gM, "N/mm²", dp=3)
        calc.check("Shear: τ_d ≤ f_v,d", tau, fvd, "N/mm²", "Eq. 6.13", hint=HINT_B)

        calc.heading("Bearing at the supports (6.1.5)")
        kc90 = 1.5 if typ == "Solid timber" else 1.75
        kc90 = calc.formula("k_c,90", "discrete supports, l_1 ≥ 2h", kc90 if L >= 2 * h else 1.0, "",
                            dp=2)
        Aef = b * (inp["lb"] + 30)
        sc90 = calc.formula("σ_c,90,d", "V_Ed / (b (l_b + 30))", VEd / Aef, "N/mm²",
                            "Effective contact length + 30 mm (one side at the end)", dp=3)
        fc90d = kmod * fc90k / gM
        calc.check("Bearing: σ_c,90,d ≤ k_c,90 f_c,90,d", sc90, kc90 * fc90d, "N/mm²", "Eq. 6.3",
                   hint=HINT_BRG)

        calc.heading("Deflection (7.2)")
        kdef = calc.input("k_def", KDEF[sc_], "", calc.tr("Creep factor (service class {s})",
                                                          s=sc_), dp=2)

        def defl(w):
            return 5 * w * L**4 / (384 * E0 * I) + 1.2 * w * L**2 / (8 * Gm * A)
        wG = defl(gk)
        wQ = calc.formula("w_inst,Q", "5qL⁴/(384EI) + 1.2qL²/(8GA)", defl(qk), "mm",
                          "Instantaneous deflection, variable load (incl. shear)", dp=1)
        calc.check_limit(calc.tr("w_inst,Q ≤ L/{n:g}", n=inp["w_inst"]), wQ, L / inp["w_inst"],
                         "mm", "Table 7.2", hint=HINT_D)
        wfin = calc.formula("w_net,fin", "w_G (1 + k_def) + w_Q (1 + ψ_2 k_def)",
                            wG * (1 + kdef) + wQ * (1 + inp["psi2"] * kdef), "mm",
                            "Final deflection (no precamber)", ref="Eq. 2.2–2.5", dp=1)
        calc.check_limit(calc.tr("w_net,fin ≤ L/{n:g}", n=inp["w_fin"]), wfin, L / inp["w_fin"],
                         "mm", "Table 7.2", hint=HINT_D)
        calc.model3d = cls._scene(calc, inp, wfin)

    @staticmethod
    def _scene(calc, inp, wfin) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        b, h, L = m(inp["b"]), m(inp["h"]), m(inp["L"])
        sc = Scene3D("timber_beam", calc.tr)
        for key, label in (("beam", "Beam"), ("supports", "Supports"),
                           ("defl", "Final deflection (×20)"), ("loads", "Loads")):
            sc.layer(key, label, toggle=key != "beam")
        wood = "#c8955a" if TIMBER[inp["cls"]][0] == "Glulam" else "#d2a56d"
        sc.box("beam", (L / 2, h / 2, 0), (L, h, b), wood)
        if TIMBER[inp["cls"]][0] == "Glulam":
            nl = max(int(h / 0.04), 2)
            for i in range(1, nl):
                y = i * h / nl
                sc.line("beam", [(0, y, b / 2 + 0.001), (L, y, b / 2 + 0.001)], "#8a5a2b")
        lb = m(inp["lb"])
        for x in (lb / 2, L - lb / 2):
            sc.box("supports", (x, -0.1, 0), (lb, 0.2, b + 0.1), "#9aa0a8")
        w = m(wfin) * 20
        pts = [(L * i / 30, -w * math.sin(math.pi * i / 30), b / 2 + 0.05) for i in range(31)]
        sc.line("defl", pts, "#e03b3b", dashed=True)
        for i in range(1, 8):
            x = L * i / 8
            sc.arrow("loads", (x, h + 0.5, 0), (0, -1, 0), 0.45, "#1d2433", 0.08)
        sc.label("loads", calc.tr("g_k + q_k = {w:.1f} kN/m", w=(inp["g"] + inp["q"])),
                 (L / 2, h + 0.65, 0), "force")
        sc.label("defl", calc.tr("w_net,fin = {w:.1f} mm", w=wfin), (L / 2, -0.4, b / 2),
                 "result")
        sc.views["default"] = {"pos": [L / 2 + 1.5, 1.5, L * 0.9], "target": [L / 2, 0, 0]}
        return sc.to_dict()
