"""Strip footing under a wall and seismic tie beams.

EN 1997-1 (bearing with inclination, sliding, eccentricity), EN 1992-1-1 (transverse bending
and shear per metre run) and EN 1998-5 §5.4.1.2 / EN 1998-1 §5.8.2 (tie beams).
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import APPROACH_CHOICES, check_approach, get_annex
from ..design.ec2 import bar_area, design_flexure, section_capacity, shear_no_links
from ..design.geotech import bearing_factors
from ..report.scene3d import PALETTE, Scene3D, heat_color

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45"]
BARS = ["10", "12", "14", "16", "20", "25"]
TIE_K = {"B": 0.3, "C": 0.4, "D": 0.6}  # EN 1998-5 5.4.1.2(6)
HINT_BEAR = "Increase the footing width B or the founding depth D."
HINT_SLIDE = "Increase the footing width or the founding depth, or add a shear key."
HINT_ECC = "Widen the footing on the side of the moment or offset the wall."
HINT_BARS = "Use larger bars or reduce the spacing (or increase the thickness h)."
HINT_TIE = "Add longitudinal bars or use larger bars in the tie beam."
HINT_TIE_DIM = "Increase the tie beam section (EN 1998-1 5.8.2(4))."


@register
class StripFootingEC7(DesignModule):
    id = "ec7_strip_footing"
    title = "Strip footing and tie beams"
    category = "Geotechnical"
    has_3d = True
    uses_annex = True
    standard = "EN 1997-1, EN 1992-1-1, EN 1998-5"
    description = ("Continuous footing under a wall (per metre run): bearing with load "
                   "inclination, sliding, eccentricity, transverse bending and shear. Optional "
                   "seismic tie beams between footings (EN 1998-5 5.4.1.2).")

    fields = [
        Field("B", "Footing width B", "m", 1.40, min=0.4, group="Geometry"),
        Field("h", "Footing thickness h", "m", 0.45, min=0.2, group="Geometry"),
        Field("D", "Founding depth D (ground to underside)", "m", 1.00, min=0.3,
              group="Geometry"),
        Field("bw", "Wall thickness b_w", "m", 0.25, min=0.1, group="Geometry"),
        Field("NG", "Line load — permanent G", "kN/m", 180.0, min=0,
              group="Characteristic loads per metre",
              help="At the top of the footing (base of the wall), downward positive."),
        Field("NQ", "Line load — variable Q", "kN/m", 60.0, min=0,
              group="Characteristic loads per metre"),
        Field("MG", "Moment — permanent", "kNm/m", 5.0, group="Characteristic loads per metre",
              help="Moment about the footing axis (across the width B)."),
        Field("MQ", "Moment — variable", "kNm/m", 5.0, group="Characteristic loads per metre"),
        Field("HG", "Horizontal load — permanent", "kN/m", 0.0,
              group="Characteristic loads per metre"),
        Field("HQ", "Horizontal load — variable", "kN/m", 5.0,
              group="Characteristic loads per metre"),
        Field("seismic", "Include seismic combination", kind="bool", default=False,
              group="Seismic (design values)"),
        Field("NE", "Line load N_E", "kN/m", 200.0, min=0, group="Seismic (design values)",
              show_if="seismic", help="G + ψ2Q + E from the seismic analysis."),
        Field("ME", "Moment M_E", "kNm/m", 30.0, group="Seismic (design values)",
              show_if="seismic"),
        Field("HE", "Horizontal H_E", "kN/m", 25.0, group="Seismic (design values)",
              show_if="seismic"),
        Field("phi", "Soil φ'k", "°", 30.0, min=10, max=45, group="Soil"),
        Field("c", "Soil c'k", "kN/m²", 5.0, min=0, group="Soil"),
        Field("gamma", "Soil γ", "kN/m³", 19.0, min=10, group="Soil"),
        Field("approach", "Design approach", kind="choice", choices=APPROACH_CHOICES,
              default="National Annex", group="Soil"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C25/30",
              group="Concrete"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Concrete"),
        Field("cover", "Cover (bottom)", "mm", 50.0, min=25, group="Concrete"),
        Field("dia", "Transverse bars Ø", kind="choice", choices=BARS, default="12",
              group="Reinforcement"),
        Field("s", "Spacing of transverse bars", "mm", 200.0, min=75, max=400,
              group="Reinforcement"),
        Field("tie", "Design tie beams (seismic)", kind="bool", default=True,
              group="Tie beams",
              help="Tie beams connect the footings so they move together in an earthquake."),
        Field("ag", "Reference ground acceleration a_gR", "", 0.25, min=0, max=0.6,
              group="Tie beams", show_if="tie", help="In g. Use the zone buttons."),
        Field("ground", "Ground type", kind="choice", choices=list(TIE_K), default="C",
              group="Tie beams", show_if="tie",
              help="Ground type A: tie beams may be omitted (EN 1998-5 5.4.1.2(5))."),
        Field("importance", "Importance class", kind="choice", choices=["I", "II", "III", "IV"],
              default="II", group="Tie beams", show_if="tie"),
        Field("N1", "Design axial load of column/wall 1", "kN", 900.0, min=0, group="Tie beams",
              show_if="tie", help="Seismic design situation, the two elements the beam joins."),
        Field("N2", "Design axial load of column/wall 2", "kN", 700.0, min=0, group="Tie beams",
              show_if="tie"),
        Field("tb", "Tie beam width", "m", 0.30, min=0.15, group="Tie beams", show_if="tie"),
        Field("th", "Tie beam depth", "m", 0.50, min=0.2, group="Tie beams", show_if="tie"),
        Field("storeys", "Storeys above the basement", "", 3, kind="int", min=1, max=40,
              group="Tie beams", show_if="tie"),
        Field("tn", "Bars top + bottom (total)", "", 8, kind="int", min=4, max=16,
              group="Tie beams", show_if="tie", help="Half at the top, half at the bottom."),
        Field("tdia", "Tie beam bars Ø", kind="choice", choices=BARS, default="16",
              group="Tie beams", show_if="tie"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        B, h, D, bw = inp["B"], inp["h"], inp["D"], inp["bw"]
        if D < h:
            raise InputError("Founding depth must be at least the footing thickness", "D")
        if bw >= B:
            raise InputError("The wall must be narrower than the footing", "bw")
        na = get_annex(calc.project.annex)
        gc, gs = 25e-6, inp["gamma"]
        calc.heading("Geometry and self weight (per metre run)")
        calc.input("B", B, "m", "Footing width")
        calc.input("h", h, "m", "Footing thickness")
        calc.input("D", D, "m", "Founding depth")
        calc.input("b_w", bw, "m", "Wall thickness")
        Wf = calc.formula("W_f", "γ_c B h", gc * B * h, "kN/m", "Footing self weight")
        Ws = calc.formula("W_s", "γ (B − b_w)(D − h)", gs * (B - bw) * (D - h), "kN/m",
                          "Soil above the footing")

        check_approach(calc, na, inp["approach"])
        gov = {"u": -1.0}
        for name in na.combinations(inp["approach"]):
            gu, gf, gq, gphi, gcf, gRv, gRh = na.combos[name]
            calc.heading(calc.tr("Geotechnical design — {name}", name=name))
            calc.text("Partial factors: γ_G = {gu} (unfav.) / {gf} (fav.), γ_Q = {gq}, "
                      "γ_φ' = {gphi}, γ_c' = {gc}, γ_R,v = {gRv}, γ_R,h = {gRh}.",
                      gu=gu, gf=gf, gq=gq, gphi=gphi, gc=gcf, gRv=gRv, gRh=gRh)
            M = gu * (inp["MG"] + inp["HG"] * h) + gq * (inp["MQ"] + inp["HQ"] * h)
            H = gu * inp["HG"] + gq * inp["HQ"]
            cases = [("max V", gu * (inp["NG"] + Wf + Ws) + gq * inp["NQ"]),
                     ("min V", gf * (inp["NG"] + Wf + Ws))]
            cls._geo(calc, inp, name, cases, M, H, gphi, gcf, gRv, gRh, gov)
        if inp["seismic"]:
            calc.heading("Seismic design situation (EN 1998-5 §5.4.1)")
            calc.text("Design action effects from the seismic analysis; soil strength with "
                      "γ_φ' = γ_c' = 1.25 (EN 1998-5 3.1(3)); γ_R = 1.0.")
            cls._geo(calc, inp, calc.tr("Seismic"), [("E", inp["NE"] + Wf + Ws)],
                     inp["ME"] + inp["HE"] * h, inp["HE"], na.seismic_gamma_phi,
                     na.seismic_gamma_c, 1.0, 1.0, gov)

        # ------------------------------------------------------------ STR
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyk = na.alpha_cc * fck / na.gamma_c, inp["fyk"]
        fyd = fyk / na.gamma_s
        calc.heading("Structural design — transverse bending (EN 1992-1-1)")
        calc.text("Net soil pressure from the wall loads (self weight and soil above cause no "
                  "bending); linear distribution, no tension. Cantilever from the wall face.")
        cases = [(1.35 * inp["NG"] + 1.5 * inp["NQ"],
                  1.35 * (inp["MG"] + inp["HG"] * h) + 1.5 * (inp["MQ"] + inp["HQ"] * h))]
        if inp["seismic"]:
            cases.append((inp["NE"], inp["ME"] + inp["HE"] * h))
        dia = float(inp["dia"])
        d = h - inp["cover"] - dia / 2
        As = bar_area(dia) * 1000 / inp["s"]
        a = (B - bw) / 2
        MEd = VEd = 0.0
        for N, M in cases:
            m, v = cls._cantilever(N, M, B, bw, d)
            MEd, VEd = max(MEd, m), max(VEd, v)
        calc.formula("a", "(B − b_w) / 2", a, "m", "Cantilever length")
        calc.formula("M_Ed", "∫ σ_net (x − b_w/2) dx at the wall face", MEd / 1000, "kNm/m")
        dd = calc.formula("d", "h − c − φ/2", d, "mm", "Effective depth")
        res = design_flexure(calc, 1000, dd, MEd, fck, fcd, fyk, fyd, h,
                             allow_compression=False, per_metre=True)
        calc.formula("A_s,prov", f"Ø{dia:g} @ {inp['s']:g} mm", As * 1e-3, "mm²/m")
        if math.isfinite(res["As"]):
            calc.check_min("Reinforcement: A_s,prov ≥ A_s,req", As * 1e-3, res["As"] * 1e-3,
                           "mm²/m", "6.1", hint=HINT_BARS)
        calc.check_min("Minimum reinforcement: A_s,prov ≥ A_s,min", As * 1e-3,
                       res["As_min"] * 1e-3, "mm²/m", "9.2.1.1", hint=HINT_BARS)
        MRd, _ = section_capacity(1000, dd, As, fcd, fyd)
        calc.formula("M_Rd", "A_s f_yd (d − 0.4x)", MRd / 1000, "kNm/m")
        calc.check("Bending: M_Ed ≤ M_Rd", MEd / 1000, MRd / 1000, "kNm/m", "6.1",
                   hint=HINT_BARS)
        calc.text("Beam shear at distance d from the wall face:")
        shear_no_links(calc, 1000, dd, As, fck, na.gamma_c, VEd, per_metre=True)
        calc.formula("A_s,dist", "0.2 A_s,prov", 0.2 * As * 1e-3, "mm²/m",
                     "Longitudinal distribution bars (minimum)", ref="9.3.1.1(2)")

        tie = cls._tie_beams(calc, inp, na, fck, fcd, fyd) if inp["tie"] else None
        calc.model3d = cls._scene(calc, inp, gov, tie)

    @staticmethod
    def _cantilever(N, M, B, bw, d):
        xs = np.linspace(bw / 2, B / 2, 201)
        q = np.maximum(N / B + 12 * abs(M) * xs / B**3, 0.0)
        Mx = float(np.trapezoid(q * (xs - bw / 2), xs)) * 1000
        msk = xs >= bw / 2 + d
        V = float(np.trapezoid(q[msk], xs[msk])) * 1000 if msk.sum() > 1 else 0.0
        return Mx, V

    # ------------------------------------------------------------ geotech
    @staticmethod
    def _geo(calc, inp, name, cases, M, H, gphi, gcf, gRv, gRh, gov) -> None:
        B, D = inp["B"], inp["D"]
        phid = math.atan(math.tan(math.radians(inp["phi"])) / gphi)
        cd = inp["c"] / gcf
        calc.formula("φ'_d", "atan(tan φ'_k / γ_φ')", math.degrees(phid), "°", dp=2)
        calc.formula("M_d", "γ (M + H h)", M, "kNm/m", "Design moment at the underside")
        Hd = calc.formula("H_d", "γ H", abs(H), "kN/m", "Design horizontal load")
        Nq, Nc, Ng = bearing_factors(phid)
        worst = None
        for label, V in cases:
            e = abs(M) / V
            Bp = B - 2 * e
            if Bp <= 0:
                cand = (float("inf"), label, V, e, Bp, float("inf"), 0.0, None)
            else:
                m = 2.0  # strip, load inclined across B (D.4, L' → ∞)
                r = max(1 - abs(H) / (V + Bp * cd / math.tan(phid)), 0.0)
                iq, ig = r**m, r ** (m + 1)
                ic = iq - (1 - iq) / (Nc * math.tan(phid))
                qRd = (cd * Nc * ic + inp["gamma"] * D * Nq * iq
                       + 0.5 * inp["gamma"] * Bp * Ng * ig) / gRv
                qEd = V / Bp
                cand = (qEd / qRd, label, V, e, Bp, qEd, qRd, (iq, ig, ic))
            if worst is None or cand[0] > worst[0]:
                worst = cand
        u, label, V, e, Bp, qEd, qRd, parts = worst
        calc.text("Governing sub-case: **{label}**, V_d = {V:.1f} kN/m.", label=label, V=V)
        calc.formula("e", "M_d / V_d", e, "m", "Eccentricity", dp=3)
        calc.check_limit(calc.tr("{name} eccentricity: e/B ≤ 1/3", name=name), e / B, 1 / 3, "",
                         "EN 1997-1 6.5.4", hint=HINT_ECC)
        calc.formula("B'", "B − 2e", max(Bp, 0), "m", "Effective width", dp=3)
        if parts:
            iq, ig, ic = parts
            calc.formula("N_q", "e^(π tan φ') tan²(45° + φ'/2)", Nq, "",
                         calc.tr("Bearing factors: Nc = {Nc:.2f}, Nγ = {Ng:.2f}", Nc=Nc, Ng=Ng),
                         dp=2)
            calc.formula("i_q", "(1 − H/(V + B'c' cot φ'))^m, m = 2", iq, "",
                         calc.tr("Inclination: iγ = {ig:.3f}, ic = {ic:.3f}", ig=ig, ic=ic),
                         ref="D.4", dp=3)
        calc.formula("q_Rd", "(c'N_c i_c + q'N_q i_q + ½γB'N_γ i_γ) / γ_R,v", qRd, "kN/m²",
                     "Design bearing resistance (strip, shape factors = 1)",
                     ref="EN 1997-1 Annex D.4")
        calc.formula("q_Ed", "V_d / B'", qEd, "kN/m²", "Design bearing pressure")
        calc.check(calc.tr("{name} bearing: q_Ed ≤ q_Rd", name=name), qEd, qRd, "kN/m²",
                   "EN 1997-1 6.5.2", hint=HINT_BEAR)
        Vmin = min(v for _, v in cases)
        Rh = calc.formula("R_h,d", "V_d,min tan φ'_d / γ_R,h", Vmin * math.tan(phid) / gRh,
                          "kN/m", "Sliding resistance (cast in situ, δ = φ')", ref="Eq. 6.3a")
        calc.check(calc.tr("{name} sliding: H_d ≤ R_h,d", name=name), Hd, Rh, "kN/m",
                   "EN 1997-1 6.5.3", hint=HINT_SLIDE)
        if u > gov["u"]:
            gov.update({"u": u, "name": f"{name} ({label})", "V": V, "e": e, "Bp": Bp,
                        "qEd": qEd, "qRd": qRd})

    # ------------------------------------------------------------ tie beams
    @staticmethod
    def _tie_beams(calc, inp, na, fck, fcd, fyd) -> dict:
        calc.heading("Tie beams (EN 1998-5 §5.4.1.2, EN 1998-1 §5.8.2)")
        gI = na.gamma_I[inp["importance"]]
        S = na.spectrum[inp["ground"]][0]
        agR = calc.input("a_gR", inp["ag"], "", "Reference peak ground acceleration [g]", dp=3)
        alpha = calc.formula("α", "γ_I a_gR / g", gI * agR, "",
                             calc.tr("Design ground acceleration ratio (γ_I = {g:g})", g=gI),
                             dp=3)
        calc.input("S", S, "", calc.tr("Soil factor (ground type {t})", t=inp["ground"]), dp=2)
        k = TIE_K[inp["ground"]]
        Nm = calc.formula("N_Ed,m", "(N_1 + N_2) / 2", (inp["N1"] + inp["N2"]) / 2, "kN",
                          "Mean design axial load of the connected elements")
        NT = calc.formula("N_tie", f"±{k:g} α S N_Ed,m", k * alpha * S * Nm, "kN",
                          "Tie beam axial force (tension and compression)",
                          ref="EN 1998-5 5.4.1.2(6)")
        b, hh = inp["tb"], inp["th"]
        hmin = 400.0 if inp["storeys"] <= 3 else 500.0
        calc.check_min("Tie beam width b ≥ 0.25 m", b, 250.0, "m", "EN 1998-1 5.8.2(4)",
                       hint=HINT_TIE_DIM)
        calc.check_min(calc.tr("Tie beam depth h ≥ {h:g} m ({n} storeys)", h=hmin / 1000,
                               n=inp["storeys"]), hh, hmin, "m",
                       "EN 1998-1 5.8.2(4)", hint=HINT_TIE_DIM)
        dia = float(inp["tdia"])
        n = int(inp["tn"])
        As = calc.formula("A_s", f"{n} Ø{dia:g}", n * bar_area(dia), "mm²",
                          "Longitudinal reinforcement (total)")
        rho = calc.formula("ρ_b", "(A_s/2) / (b h)", As / 2 / (b * hh), "", "Ratio top or bottom",
                           dp=4)
        calc.check_min("Minimum ratio top and bottom ρ_b ≥ 0.4 %", rho, 0.004, "%",
                       "EN 1998-1 5.8.2(5)", hint=HINT_TIE)
        NtRd = calc.formula("N_t,Rd", "A_s f_yd", As * fyd, "kN", "Tension resistance")
        calc.check("Tie beam in tension: N_tie ≤ N_t,Rd", NT, NtRd, "kN",
                   "EN 1992-1-1 6.1", hint=HINT_TIE)
        NcRd = calc.formula("N_c,Rd", "b h f_cd + A_s f_yd", b * hh * fcd + As * fyd, "kN",
                            "Compression resistance (beam restrained by the soil)")
        calc.check("Tie beam in compression: N_tie ≤ N_c,Rd", NT, NcRd, "kN", "EN 1992-1-1 6.1",
                   hint=HINT_TIE_DIM)
        calc.note("Ground type A: tie beams may be omitted; at low seismicity on ground type B "
                  "they may also be omitted (EN 1998-5 5.4.1.2(5)).")
        return {"N": NT, "b": b, "h": hh}

    # ---------------------------------------------------------------- 3D
    @staticmethod
    def _scene(calc, inp, gov, tie) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        B, h, D, bw = m(inp["B"]), m(inp["h"]), m(inp["D"]), m(inp["bw"])
        L = 4.0
        sc = Scene3D("strip_footing", calc.tr)
        for key, label in (("concrete", "Footing and wall"), ("soil", "Soil"),
                           ("bearing", "Base pressure"), ("ties", "Tie beams"),
                           ("loads", "Loads")):
            sc.layer(key, label, toggle=key != "concrete")
        top = -D + h
        sc.box("concrete", (0, -D + h / 2, 0), (B, h, L), PALETTE["concrete"])
        sc.box("concrete", (0, (top + 1.2) / 2, 0), (bw, 1.2 - top, L), "#9aa0a8")
        if D > h:
            sc.box("soil", (0, top / 2, 0), (B + 2.0, D - h, L), PALETTE["soil"], opacity=0.18,
                   edges=False)
        if gov.get("V"):
            V, e, Bf = gov["V"], m(gov["e"]), B
            xs = np.linspace(-Bf / 2, Bf / 2, 17)
            q = np.maximum(V / Bf * (1 + 12 * e * xs / Bf**2), 0)
            qmax = float(q.max()) or 1.0
            s = 0.5 / qmax
            verts, cols, faces = [], [], []
            for z in (-L / 2, L / 2):
                for x, qi in zip(xs, q):
                    verts.append((x, -D - 0.02 - qi * s, z))
                    cols.append(heat_color(qi / qmax))
            n = len(xs)
            for i in range(n - 1):
                faces += [(i, i + 1, n + i + 1), (i, n + i + 1, n + i)]
            sc.mesh("bearing", verts, faces, opacity=0.85, colors=cols)
            sc.label("bearing", calc.tr("q_Ed = {q:.0f} kN/m² ({name})", q=gov["qEd"] * 1000,
                                        name=gov["name"]), (B / 2 + 0.3, -D - 0.4, 0), "result")
            sc.arrow("loads", (0, 1.2 + 1.0, 0), (0, -1, 0), 1.0, PALETTE["load"], 0.2)
            sc.label("loads", calc.tr("V_d = {v:.0f} kN/m", v=V), (0, 2.35, 0), "result")
        if tie:
            tb, th = m(tie["b"]), m(tie["h"])
            for zc in (-L / 2 + 0.6, L / 2 - 0.6):
                sc.box("ties", (B / 2 + 1.5, top - th / 2 + h, zc), (3.0, th, tb), "#7d8794")
            sc.label("ties", calc.tr("N_tie = ±{n:.0f} kN", n=tie["N"] / 1000),
                     (B / 2 + 1.5, top + 0.4, L / 2 - 0.6), "force")
        sc.views["default"] = {"pos": [B + 3.5, 2.5, L + 2.5], "target": [0.5, -D / 2, 0]}
        return sc.to_dict()
