"""Seismic assessment and strengthening of an existing RC column or beam — EN 1998-3.

Limit states (2.1): Near Collapse θ_E ≤ θ_um, Significant Damage θ_E ≤ ¾ θ_um, Damage
Limitation θ_E ≤ θ_y; brittle shear V_E ≤ V_R.  Capacities from Annex A with mean material
strengths divided by the confidence factor CF of the knowledge level; shear (brittle) also
divided by the partial factors of EN 1998-1 (Cyprus NA 2.3).  Strengthening by RC jacketing
(A.4.2) or FRP wrapping (A.4.4).
"""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec2 import bar_area
from ..design.ec8_3 import RCSection, shear_VR, theta_um, theta_y
from ..report.scene3d import Scene3D

KL = {"KL1 — limited knowledge": "KL1", "KL2 — normal knowledge": "KL2",
      "KL3 — full knowledge": "KL3"}
STRENGTHEN = ["None (assessment only)", "RC jacket", "FRP wrapping"]
HINT_NC = "Strengthen the member: RC jacket (more ductility and strength) or FRP wrapping."
HINT_V = "Shear is brittle — add an RC jacket with closely spaced links or FRP wrapping."
HINT_DL = "Stiffen the building (new RC walls, jackets) to reduce the drift demand."


@register
class AssessmentEC83(DesignModule):
    id = "ec8_3_assessment"
    title = "Assessment and strengthening of RC members"
    category = "Existing buildings"
    has_3d = True
    uses_annex = True
    standard = "EN 1998-3 Annex A"
    description = ("Existing RC column or beam: knowledge level and confidence factor, chord "
                   "rotation at yield and ultimate (A.10a, A.1), cyclic shear resistance (A.12), "
                   "checks for the limit states NC, SD and DL, and strengthening with an RC "
                   "jacket or FRP wrapping. Interactive 3D model.")

    fields = [
        Field("kl", "Knowledge level", kind="choice", choices=list(KL),
              default="KL2 — normal knowledge", group="Knowledge",
              help="KL1: simulated design + limited in-situ tests; KL2: extended inspection "
                   "and testing; KL3: comprehensive (Table 3.1)."),
        Field("primary", "Primary seismic element", kind="bool", default=True,
              group="Knowledge", help="γ_el = 1.5 (deformation) and 1.15 (shear) for primary "
                                      "elements, 1.0 for secondary."),
        Field("detailing", "Detailed for earthquake resistance", kind="bool", default=False,
              group="Knowledge", help="Off for older buildings (no seismic detailing): θ_um is "
                                      "divided by 1.2 (A.3.2.2)."),
        Field("ribbed", "Ribbed (deformed) bars", kind="bool", default=True, group="Knowledge"),
        Field("b", "Width b", "mm", 300.0, min=150, group="Existing section"),
        Field("h", "Depth h (in the direction of bending)", "mm", 400.0, min=150,
              group="Existing section"),
        Field("cover", "Cover to bar centre", "mm", 35.0, min=15, group="Existing section"),
        Field("nb", "Bars along b (each face, incl. corners)", "", 3, kind="int", min=2,
              group="Existing section"),
        Field("nh", "Bars along h (each face, incl. corners)", "", 3, kind="int", min=2,
              group="Existing section"),
        Field("dia", "Longitudinal bar Ø", "mm", 16.0, min=8, max=32,
              group="Existing section"),
        Field("dh", "Hoop Ø", "mm", 8.0, min=6, max=14, group="Existing section"),
        Field("sh", "Hoop spacing", "mm", 200.0, min=50, max=400, group="Existing section"),
        Field("legs", "Hoop legs parallel to the shear", "", 2, kind="int", min=2, max=6,
              group="Existing section"),
        Field("fcm", "Concrete mean strength f_cm (tests)", "N/mm²", 16.0, min=8, max=60,
              group="Materials (mean, from tests)"),
        Field("fym", "Steel mean yield strength f_ym", "N/mm²", 450.0, min=220, max=700,
              group="Materials (mean, from tests)"),
        Field("Lv", "Shear span L_V = M/V", "m", 1.5, min=0.3, group="Member and demand",
              help="Half the clear height for a column in double curvature."),
        Field("N", "Axial force in the seismic situation", "kN", 600.0, min=0,
              group="Member and demand", help="Compression positive (G + ψ2Q)."),
        Field("thE_NC", "Chord rotation demand θ_E — NC", "", 0.020, min=0, max=0.2,
              group="Member and demand", help="rad, from the analysis for the NC seismic action."),
        Field("thE_SD", "Chord rotation demand θ_E — SD", "", 0.012, min=0, max=0.2,
              group="Member and demand"),
        Field("thE_DL", "Chord rotation demand θ_E — DL", "", 0.004, min=0, max=0.2,
              group="Member and demand"),
        Field("VE", "Shear demand V_E", "kN", 150.0, min=0, group="Member and demand",
              help="From capacity design: ΣM_y / L_cl of the member, or from the analysis."),
        Field("strengthen", "Strengthening", kind="choice", choices=STRENGTHEN,
              default="RC jacket", group="Strengthening"),
        Field("tj", "Jacket thickness", "mm", 100.0, min=60, max=250, group="Strengthening",
              show_if="strengthen=RC jacket",
              help="≥ 75 mm cast, ≥ 50 mm shotcrete."),
        Field("fcj", "Jacket concrete mean strength", "N/mm²", 33.0, min=20, max=60,
              group="Strengthening", show_if="strengthen=RC jacket"),
        Field("nbj", "Jacket bars along each face (incl. corners)", "", 3, kind="int", min=2,
              group="Strengthening", show_if="strengthen=RC jacket"),
        Field("diaj", "Jacket bar Ø", "mm", 16.0, min=10, max=32, group="Strengthening",
              show_if="strengthen=RC jacket"),
        Field("dhj", "Jacket hoop Ø", "mm", 10.0, min=8, max=14, group="Strengthening",
              show_if="strengthen=RC jacket"),
        Field("shj", "Jacket hoop spacing", "mm", 100.0, min=50, max=200,
              group="Strengthening", show_if="strengthen=RC jacket"),
        Field("fyj", "Jacket steel mean yield strength", "N/mm²", 550.0, min=400, max=700,
              group="Strengthening", show_if="strengthen=RC jacket"),
        Field("nf", "FRP layers", "", 2, kind="int", min=1, max=10, group="Strengthening",
              show_if="strengthen=FRP wrapping"),
        Field("tf", "Thickness per layer", "mm", 0.17, min=0.05, max=2.0,
              group="Strengthening", show_if="strengthen=FRP wrapping"),
        Field("Ef", "FRP modulus E_f", "GPa", 230.0, min=20, max=650, group="Strengthening",
              show_if="strengthen=FRP wrapping"),
        Field("euf", "FRP ultimate strain ε_u,f", "", 0.015, min=0.003, max=0.05,
              group="Strengthening", show_if="strengthen=FRP wrapping"),
        Field("R", "Corner radius", "mm", 25.0, min=10, max=60, group="Strengthening",
              show_if="strengthen=FRP wrapping",
              help="Round the corners before wrapping (≥ 20–25 mm)."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        kl = KL[inp["kl"]]
        CF = na.CF[kl]
        g_def = 1.5 if inp["primary"] else 1.0
        g_v = 1.15 if inp["primary"] else 1.0
        gc, gs = (na.gamma_c, na.gamma_s) if (na.ec83_brittle_partial and inp["primary"]) \
            else (1.0, 1.0)
        b, h, c = inp["b"], inp["h"], inp["cover"]
        dia, Lv, N = inp["dia"], inp["Lv"], inp["N"]
        if 2 * c >= h - 40 or 2 * c >= b - 40:
            raise InputError("The cover is too large for the section", "cover")

        calc.note("Method: EN 1998-3 with Annex A and the selected National Annex. The Greek "
                  "KANEPE is not implemented in this version.")
        calc.heading("Knowledge level and material values")
        calc.label("Knowledge level", inp["kl"])
        calc.input("CF", CF, "", "Confidence factor (Table 3.1 / National Annex)", dp=2)
        calc.text("Return periods (National Annex): NC {nc} years, SD {sd} years, DL {dl} "
                  "years.", nc=na.ec83_return["NC"], sd=na.ec83_return["SD"],
                  dl=na.ec83_return["DL"])
        fc = calc.formula("f_c", "f_cm / CF", inp["fcm"] / CF, "N/mm²",
                          "Concrete (ductile mechanisms)", dp=2)
        fy = calc.formula("f_y", "f_ym / CF", inp["fym"] / CF, "N/mm²", "Steel (ductile)", dp=1)
        fcv = calc.formula("f_c,V", "f_cm / (CF γ_c)", inp["fcm"] / (CF * gc), "N/mm²",
                           "Concrete for shear (brittle, National Annex 2.3)", dp=2)
        fyv = calc.formula("f_yw,V", "f_ym / (CF γ_s)", inp["fym"] / (CF * gs), "N/mm²",
                           "Hoops for shear (brittle)", dp=1)
        if not inp["ribbed"]:
            calc.warn("Smooth (plain) bars: Annex A gives reduced deformation capacities and "
                      "lap-splice/anchorage effects — check them separately; the values below "
                      "assume ribbed bars.")
        sec = cls._section(b, h, c, inp["nb"], inp["nh"], dia, inp["dh"], inp["sh"],
                           inp["legs"])
        calc.heading("Existing member — capacities (EN 1998-3 Annex A)")
        res0 = cls._capacities(calc, sec, fc, fy, fy, fcv, fyv, N, Lv, g_def, g_v,
                               inp["detailing"], inp)
        st = inp["strengthen"]
        cls._checks(calc, inp, res0, calc.tr("existing"), record=st == STRENGTHEN[0])

        res = res0
        if st == "RC jacket":
            res = cls._jacket(calc, inp, na, CF, gc, gs, g_def, g_v)
        elif st == "FRP wrapping":
            res = cls._frp(calc, inp, sec, fc, fy, fcv, fyv, N, Lv, g_def, g_v, res0)
        calc.model3d = cls._scene(calc, inp, res)

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _section(b, h, c, nb, nh, dia, dh, sh, legs) -> RCSection:
        a1 = bar_area(dia)
        return RCSection(b=b, h=h, d1=c, As=nb * a1, As2=nb * a1,
                         Asv=2 * max(nh - 2, 0) * a1, db=dia, Asw=legs * bar_area(dh), sh=sh,
                         nb=nb, nh=nh, dh=dh)

    @staticmethod
    def _capacities(calc, sec, fc, fy, fyw, fcv, fyv, N, Lv, g_def, g_v, detailing, inp,
                    frp=0.0, Vwf=0.0, fact=(1.0, 1.0, 1.0)) -> dict:
        ky, ku, kv = fact
        # a_v = 1 if shear cracking precedes flexural yielding (V_Rc < M_y/L_V)
        d = sec.d
        k = min(1 + math.sqrt(200 / d), 2.0)
        rho = min(sec.As / (sec.b * d), 0.02)
        VRc = max(0.18 * k * (100 * rho * fc) ** (1 / 3), 0.035 * k**1.5 * math.sqrt(fc)) \
            * sec.b * d + 0.15 * min(N / (sec.b * sec.h), 0.2 * fc) * sec.b * d
        th_y0, parts, yp = theta_y(sec, fc, fy, N, Lv, 0.0)
        av = 1.0 if VRc < yp["My"] / Lv else 0.0
        th_y, parts, yp = theta_y(sec, fc, fy, N, Lv, av)
        calc.formula("φ_y", "f_y / (E_s (1 − ξ_y) d)", yp["phi_y"] * 1000, "",
                     calc.tr("Yield curvature [1/m] (ξ_y = {x:.3f})", x=yp["xi"]),
                     ref="A.3.2.4", dp=2)
        My = calc.formula("M_y", "Annex A (yield of the tension steel)", yp["My"], "kNm",
                          "Yield moment")
        calc.formula("a_v", "1 if V_Rc < M_y/L_V", av, "", calc.tr(
            "Shear cracking before yielding: V_Rc = {v:.0f} kN", v=VRc / 1000), dp=0)
        th_y = calc.formula("θ_y", "φ_y (L_V + a_v z)/3 + 0.0014(1 + 1.5h/L_V) + "
                            "ε_y d_b f_y / (6(d − d')√f_c)", th_y * ky, "",
                            calc.tr("Chord rotation at yield (terms {a:.4f} + {b:.4f} + "
                                    "{c:.4f}){f}", a=parts[0], b=parts[1], c=parts[2],
                                    f=calc.tr(" × {k:g}", k=ky) if ky != 1 else ""),
                            ref="Eq. A.10a", dp=5)
        th_u, pr = theta_um(sec, fc, fy, fyw, N, Lv, g_def, detailing, frp)
        th_u = calc.formula("θ_um", "(1/γ_el) 0.016 (0.3^ν) [max(0.01,ω')/max(0.01,ω) f_c]^0.225"
                            " (L_V/h)^0.35 25^(α ρ_sx f_yw/f_c)", th_u * ku, "",
                            calc.tr("ν = {n:.3f}, ω = {w:.3f}, ω' = {w2:.3f}, α = {a:.3f}, "
                                    "ρ_sx = {r:.4f}, γ_el = {g:g}{d}", n=pr["nu"], w=pr["w"],
                                    w2=pr["w2"], a=pr["alpha"], r=pr["rsx"], g=g_def,
                                    d=calc.tr("; ÷ 1.2 (no seismic detailing)")
                                    if not detailing else ""), ref="Eq. A.1", dp=5)
        calc.formula("θ_SD", "¾ θ_um", 0.75 * th_u, "", "Significant damage capacity",
                     ref="A.3.3", dp=5)
        mu = max(inp["thE_NC"] / th_y - 1, 0.0)
        VR, vp = shear_VR(sec, fcv, fyv, N, Lv, yp["x"], mu, g_v, Vwf)
        VR = calc.formula("V_R", "(1/γ_el)[(h − x)/(2L_V) min(N, 0.55A_c f_c) + (1 − 0.05 min(5, "
                          "μ_Δ,pl))(0.16 max(0.5, 100ρ_tot)(1 − 0.16 min(5, L_V/h))√f_c A_c + "
                          "V_w)]", VR * kv, "kN", calc.tr(
                              "Cyclic shear resistance at μ_Δ,pl = {m:.2f} (V_w = {w:.0f} kN)",
                              m=mu, w=vp["Vw"] / 1000), ref="Eq. A.12", dp=1)
        Vy = My / Lv
        calc.formula("V_My", "M_y / L_V", Vy, "kN", "Shear at flexural yielding", dp=1)
        mode = "flexure" if VR >= Vy else "shear"
        calc.text("Expected failure mode: **{m}** (V_R {c} M_y/L_V).", m=calc.tr(mode),
                  c="≥" if VR >= Vy else "<")
        return {"thy": th_y, "thu": th_u, "VR": VR, "My": My, "mode": mode, "sec": sec}

    @staticmethod
    def _checks(calc, inp, r, label, record: bool = True) -> None:
        calc.heading(calc.tr("Limit state checks — {w}", w=label), 2)
        if not record:  # existing member before strengthening: reference table only
            rows = []
            for ls, dem, cap in (("NC", inp["thE_NC"], r["thu"]),
                                 ("SD", inp["thE_SD"], 0.75 * r["thu"]),
                                 ("DL", inp["thE_DL"], r["thy"])):
                rows.append([ls, f"{dem:.4f}", f"{cap:.4f}", f"{dem / cap:.2f}",
                             calc.tr("OK" if dem <= cap else "Not OK")])
            u = inp["VE"] / r["VR"]
            rows.append([calc.tr("Shear"), f"{inp['VE'] / 1000:.0f} kN",
                         f"{r['VR'] / 1000:.0f} kN", f"{u:.2f}",
                         calc.tr("OK" if u <= 1 else "Not OK")])
            calc.table(["Limit state", "Demand", "Capacity", "Ratio", "Status"], rows,
                       caption="Existing member — the strengthened member is checked below")
            return
        calc.check(calc.tr("NC ({w}): θ_E ≤ θ_um", w=label), inp["thE_NC"], r["thu"], "",
                   "EN 1998-3 A.3.2.2", hint=HINT_NC)
        calc.check(calc.tr("SD ({w}): θ_E ≤ ¾ θ_um", w=label), inp["thE_SD"], 0.75 * r["thu"],
                   "", "EN 1998-3 A.3.2.3", hint=HINT_NC)
        calc.check(calc.tr("DL ({w}): θ_E ≤ θ_y", w=label), inp["thE_DL"], r["thy"], "",
                   "EN 1998-3 A.3.2.4", hint=HINT_DL)
        calc.check(calc.tr("Shear ({w}): V_E ≤ V_R", w=label), inp["VE"], r["VR"], "kN",
                   "EN 1998-3 A.3.3.1", hint=HINT_V)

    @classmethod
    def _jacket(cls, calc, inp, na, CF, gc, gs, g_def, g_v) -> dict:
        calc.heading("Strengthening with an RC jacket (A.4.2)")
        tj = inp["tj"]
        b2, h2 = inp["b"] + 2 * tj, inp["h"] + 2 * tj
        calc.formula("b* × h*", "(b + 2t_j) × (h + 2t_j)", b2, "mm",
                     calc.tr("Jacketed section {b:.0f} × {h:.0f} mm", b=b2, h=h2))
        calc.text("Monolithic behaviour (A.4.2.2): the jacket concrete is assumed over the "
                  "whole section, the axial load is taken by the full composite section and "
                  "the jacket bars are the longitudinal reinforcement (original bars "
                  "conservatively neglected). Interfaces roughened, dowels per A.4.2.")
        fc = calc.formula("f_c*", "f_cm,j / CF", inp["fcj"] / CF, "N/mm²", dp=2)
        fy = inp["fyj"] / CF
        fcv, fyv = inp["fcj"] / (CF * gc), inp["fyj"] / (CF * gs)
        cj = 30 + inp["dhj"] + inp["diaj"] / 2
        sec = cls._section(b2, h2, cj, inp["nbj"], inp["nbj"], inp["diaj"], inp["dhj"],
                           inp["shj"], 2)
        r = cls._capacities(calc, sec, fc, fy, fy, fcv, fyv, inp["N"], inp["Lv"], g_def, g_v,
                            True, inp, fact=(1.05, 1.0, 0.9))
        calc.text("Monolithic-member factors applied: θ_y* = 1.05 θ_y, θ_u* = θ_u, "
                  "V_R* = 0.9 V_R, M_y* = M_y (A.4.2.2(4)).")
        cls._checks(calc, inp, r, calc.tr("with RC jacket"))
        return {**r, "jacket": (b2, h2)}

    @classmethod
    def _frp(cls, calc, inp, sec, fc, fy, fcv, fyv, N, Lv, g_def, g_v, r0) -> dict:
        calc.heading("Strengthening with FRP wrapping (A.4.4)")
        b, h, R = inp["b"], inp["h"], inp["R"]
        tf = inp["nf"] * inp["tf"]
        Ef = inp["Ef"]  # already N/mm² (field unit GPa)
        euf = inp["euf"]
        rho_f = calc.formula("ρ_f", "2 t_f / b_w (full wrapping)", 2 * tf / b, "", dp=5)
        fuf = Ef * euf
        xr = fuf * rho_f / fc
        if xr > 1 / 1.4:
            calc.note("ρ_f f_u,f / f_c = {x:.2f} exceeds 1/1.4: more FRP gives no further "
                      "confinement benefit in A.4.4.3, so the effective term is capped at its "
                      "maximum (use fewer layers for confinement).", x=xr)
            rho_c = 1 / 1.4 * fc / fuf
        else:
            rho_c = rho_f
        ffe = calc.formula("f_f,e", "f_u,f (1 − 0.7 f_u,f ρ_f / f_c)",
                           fuf * (1 - 0.7 * fuf * rho_c / fc), "N/mm²",
                           "Effective FRP stress for confinement", ref="A.4.4.3", dp=0)
        af = calc.formula("α_f", "1 − ((b − 2R)² + (h − 2R)²)/(3bh)",
                          1 - ((b - 2 * R) ** 2 + (h - 2 * R) ** 2) / (3 * b * h), "",
                          "Confinement effectiveness of the wrap", dp=3)
        frp = af * rho_c * ffe / fc
        calc.formula("α_f ρ_f f_f,e / f_c", "added to the exponent of 25 in Eq. A.1", frp, "",
                     dp=4)
        efe = calc.formula("ε_f,e", "min(0.004, 0.5 ε_u,f)", min(0.004, 0.5 * euf), "",
                           "Effective FRP strain for shear (full wrapping, fib Bulletin 14)",
                           dp=4)
        z = sec.d - sec.d1
        Vwf = calc.formula("V_w,f", "ρ_f b_w z E_f ε_f,e (θ = 45°)", rho_f * b * z * Ef * efe,
                           "kN", "FRP contribution to the shear resistance", ref="A.4.4.2",
                           dp=1)
        r = cls._capacities(calc, sec, fc, fy, fy, fcv, fyv, N, Lv, g_def, g_v,
                            inp["detailing"], inp, frp=frp, Vwf=Vwf)
        cls._checks(calc, inp, r, calc.tr("with FRP"))
        return {**r, "frp": tf}

    # ---------------------------------------------------------------- 3D
    @staticmethod
    def _scene(calc, inp, res) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        b, h, L = m(inp["b"]), m(inp["h"]), 2 * m(inp["Lv"])
        sc = Scene3D("assessment", calc.tr)
        for key, label in (("member", "Existing member"), ("bars", "Reinforcement"),
                           ("strength", "Strengthening"), ("state", "Results")):
            sc.layer(key, label, toggle=key != "member")
        ok = all(ch.passed for ch in calc.checks[-4:])
        col = "#2e9b5f" if ok else "#e03b3b"
        sc.box("member", (0, L / 2, 0), (b, L, h), "#b4b8bf",
               opacity=0.35 if res.get("jacket") or res.get("frp") else 1.0)
        c = m(inp["cover"])
        for i in range(inp["nb"]):
            x = -b / 2 + c + i * (b - 2 * c) / (inp["nb"] - 1)
            for zz in (-h / 2 + c, h / 2 - c):
                sc.cylinder("bars", (x, 0, zz), (x, L, zz), m(inp["dia"]) / 2, "#8a5a2b")
        if res.get("jacket"):
            b2, h2 = (m(v) for v in res["jacket"])
            sc.box("strength", (0, L / 2, 0), (b2, L, h2), "#9aa0a8", opacity=0.45)
            s = m(inp["shj"])
            y = s / 2
            while y < L:
                sc.line("strength", [(-b2 / 2 + 0.03, y, -h2 / 2 + 0.03),
                                     (b2 / 2 - 0.03, y, -h2 / 2 + 0.03),
                                     (b2 / 2 - 0.03, y, h2 / 2 - 0.03),
                                     (-b2 / 2 + 0.03, y, h2 / 2 - 0.03)], "#5a6b7d", closed=True)
                y += s
        if res.get("frp"):
            t = 0.006
            sc.box("strength", (0, L / 2, 0), (b + t, L * 0.9, h + t), "#20242b", opacity=0.75)
        sc.label("state", calc.tr("θ_um = {t:.4f} rad · V_R = {v:.0f} kN", t=res["thu"],
                                  v=res["VR"] / 1000), (b, L * 0.75, 0), "result")
        sc.label("state", calc.tr("Failure mode: {m}", m=calc.tr(res["mode"])),
                 (b, L * 0.6, 0), "force")
        sc.box("state", (0, -0.15, 0), (b * 3, 0.3, h * 3), col, opacity=0.5)
        return sc.to_dict()
