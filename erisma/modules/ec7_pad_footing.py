"""Isolated RC pad footing — EN 1997-1 (bearing, sliding) and EN 1992-1-1 (bending, punching)."""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..design.ec2 import bar_area, design_flexure, section_capacity, shear_no_links
from ..design.geotech import bearing_factors
from ..design.walls import APPROACHES, COMBOS
from ..report.scene3d import PALETTE, Scene3D, heat_color
from ..report.svg import footing_plan

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45"]
BARS = ["10", "12", "14", "16", "20", "25"]
HINT_BEAR = "Increase the footing plan size (Bx, By) or the founding depth D."
HINT_SLIDE = "Increase the footing size or founding depth, or add a shear key."
HINT_ECC = "Enlarge the footing in the direction of the moment or offset the column."
HINT_PUNCH = "Increase the footing thickness h (most effective) or the column size."
HINT_BARS = "Use larger bars or reduce the bar spacing (or increase the thickness h)."
HINT_SHEAR = "Increase the footing thickness h."


def _k_ratio(r: float) -> float:
    """EN 1992-1-1 Table 6.1 (interpolated)."""
    return float(np.interp(r, [0.5, 1.0, 2.0, 3.0], [0.45, 0.60, 0.70, 0.80]))


@register
class PadFootingEC7(DesignModule):
    id = "ec7_pad_footing"
    title = "Pad footing"
    category = "Geotechnical"
    has_3d = True
    standard = "EN 1997-1, EN 1992-1-1, EN 1998-5"
    description = ("Isolated reinforced concrete footing under a column with biaxial moments: "
                   "effective-area bearing (Annex D, shape and inclination factors), sliding, "
                   "eccentricity, bending, beam shear and punching. Interactive 3D model.")

    fields = [
        Field("Bx", "Footing length Bx", "m", 2.40, min=0.5, group="Geometry"),
        Field("By", "Footing width By", "m", 2.40, min=0.5, group="Geometry"),
        Field("h", "Footing thickness h", "m", 0.60, min=0.25, group="Geometry"),
        Field("D", "Founding depth D (ground to underside)", "m", 1.20, min=0.3,
              group="Geometry"),
        Field("cx", "Column size cx", "m", 0.40, min=0.15, group="Geometry"),
        Field("cy", "Column size cy", "m", 0.40, min=0.15, group="Geometry"),
        Field("NG", "Axial load — permanent G", "kN", 700.0, min=0, group="Characteristic loads",
              help="Loads at the top of the footing (column base), downward positive."),
        Field("NQ", "Axial load — variable Q", "kN", 300.0, min=0,
              group="Characteristic loads"),
        Field("MxG", "Moment Mx — permanent", "kNm", 30.0, group="Characteristic loads",
              help="Mx causes eccentricity along X (rotation about the Y axis)."),
        Field("MxQ", "Moment Mx — variable", "kNm", 20.0, group="Characteristic loads"),
        Field("MyG", "Moment My — permanent", "kNm", 0.0, group="Characteristic loads",
              help="My causes eccentricity along Y."),
        Field("MyQ", "Moment My — variable", "kNm", 10.0, group="Characteristic loads"),
        Field("HxG", "Horizontal load Hx — permanent", "kN", 10.0, group="Characteristic loads"),
        Field("HxQ", "Horizontal load Hx — variable", "kN", 10.0, group="Characteristic loads"),
        Field("seismic", "Include seismic combination", kind="bool", default=True,
              group="Seismic (design values)"),
        Field("NE", "Axial load N_E", "kN", 750.0, min=0, group="Seismic (design values)",
              help="Design values from the seismic analysis (G + ψ2Q + E), capacity design "
                   "as required by EN 1998-1 4.4.2.6."),
        Field("MxE", "Moment Mx,E", "kNm", 150.0, group="Seismic (design values)"),
        Field("MyE", "Moment My,E", "kNm", 50.0, group="Seismic (design values)"),
        Field("HxE", "Horizontal Hx,E", "kN", 80.0, group="Seismic (design values)"),
        Field("phi", "Soil φ'k", "°", 30.0, min=10, max=45, group="Soil"),
        Field("c", "Soil c'k", "kN/m²", 5.0, min=0, group="Soil"),
        Field("gamma", "Soil γ", "kN/m³", 19.0, min=10, group="Soil"),
        Field("approach", "Design approach", kind="choice", choices=list(APPROACHES),
              default="DA1", group="Soil"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C25/30",
              group="Concrete"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Concrete"),
        Field("cover", "Cover (bottom)", "mm", 50.0, min=25, group="Concrete"),
        Field("dia_x", "Bars in X Ø", kind="choice", choices=BARS, default="14",
              group="Reinforcement"),
        Field("s_x", "Spacing in X", "mm", 150.0, min=75, max=400, group="Reinforcement"),
        Field("dia_y", "Bars in Y Ø", kind="choice", choices=BARS, default="14",
              group="Reinforcement"),
        Field("s_y", "Spacing in Y", "mm", 150.0, min=75, max=400, group="Reinforcement"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        Bx, By, h, D = inp["Bx"], inp["By"], inp["h"], inp["D"]
        cx, cy = inp["cx"], inp["cy"]
        if D < h:
            raise InputError("Founding depth must be at least the footing thickness", "D")
        if cx >= Bx or cy >= By:
            raise InputError("The column must be smaller than the footing", "cx")
        gc, gs = 25e-6, inp["gamma"]

        calc.heading("Geometry and self weight")
        calc.input("B_x", Bx, "m", "Footing length")
        calc.input("B_y", By, "m", "Footing width")
        calc.input("h", h, "m", "Footing thickness")
        calc.input("D", D, "m", "Founding depth")
        calc.input("c_x", cx, "m", "Column size in X")
        calc.input("c_y", cy, "m", "Column size in Y")
        Wf = calc.formula("W_f", "γ_c B_x B_y h", gc * Bx * By * h, "kN", "Footing self weight")
        Ws = calc.formula("W_s", "γ (B_x B_y − c_x c_y)(D − h)", gs * (Bx * By - cx * cy) * (D - h),
                          "kN", "Soil above footing")
        fig_index = len(calc.items)

        gov = {"u": -1.0}
        for name in APPROACHES[inp["approach"]]:
            gu, gf, gq, gphi, gcf, gRv, gRh = COMBOS[name]
            calc.heading(calc.tr("Geotechnical design — {name}", name=name))
            calc.text("Partial factors: γ_G = {gu} (unfav.) / {gf} (fav.), γ_Q = {gq}, "
                      "γ_φ' = {gphi}, γ_c' = {gc}, γ_R,v = {gRv}, γ_R,h = {gRh}.",
                      gu=gu, gf=gf, gq=gq, gphi=gphi, gc=gcf, gRv=gRv, gRh=gRh)
            Mx = gu * (inp["MxG"] + inp["HxG"] * h) + gq * (inp["MxQ"] + inp["HxQ"] * h)
            My = gu * inp["MyG"] + gq * inp["MyQ"]
            H = gu * inp["HxG"] + gq * inp["HxQ"]
            cases = [("max V", gu * (inp["NG"] + Wf + Ws) + gq * inp["NQ"]),
                     ("min V", gf * (inp["NG"] + Wf + Ws))]
            cls._geo_case(calc, inp, name, cases, Mx, My, H, gphi, gcf, gRv, gRh, gov)

        if inp["seismic"]:
            calc.heading("Seismic design situation (EN 1998-5 §5.4.1)")
            calc.text("Design action effects from the seismic analysis; soil strength with "
                      "γ_φ' = γ_c' = 1.25 (EN 1998-5 3.1(3)); γ_R = 1.0.")
            Mx = inp["MxE"] + inp["HxE"] * h
            cls._geo_case(calc, inp, calc.tr("Seismic"), [("E", inp["NE"] + Wf + Ws)], Mx,
                          inp["MyE"], inp["HxE"], 1.25, 1.25, 1.0, 1.0, gov)

        # ------------------------------------------------------------ STR
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyk = fck / 1.5, inp["fyk"]
        fyd = fyk / 1.15
        calc.heading("Structural design — STR (EN 1992-1-1)")
        str_cases = [("Persistent (1.35G + 1.5Q)",
                      1.35 * inp["NG"] + 1.5 * inp["NQ"],
                      1.35 * (inp["MxG"] + inp["HxG"] * h) + 1.5 * (inp["MxQ"] + inp["HxQ"] * h),
                      1.35 * inp["MyG"] + 1.5 * inp["MyQ"])]
        if inp["seismic"]:
            str_cases.append(("Seismic", inp["NE"], inp["MxE"] + inp["HxE"] * h, inp["MyE"]))
        calc.text("Footing self weight and soil above do not cause bending; the net soil "
                  "pressure from the column loads is used. Linear and effective-area "
                  "distributions are both evaluated and the larger effect governs.")
        dx_bar, dy_bar = float(inp["dia_x"]), float(inp["dia_y"])
        dxe = h - inp["cover"] - dx_bar / 2
        dye = h - inp["cover"] - dx_bar - dy_bar / 2
        Asx = bar_area(dx_bar) * 1000 / inp["s_x"]
        Asy = bar_area(dy_bar) * 1000 / inp["s_y"]

        def cantilever(N, M, B, Bo, c, d):
            """Max moment / beam shear per metre at the column face in one direction."""
            a = (B - c) / 2
            xs = np.linspace(c / 2, B / 2, 201)
            lin = N / (B * Bo) + 12 * abs(M) * xs / (Bo * B**3)
            e = abs(M) / N if N > 0 else 0
            Bp = max(B - 2 * e, 1e-6)
            eff = np.where(B / 2 - xs <= Bp, N / (Bp * Bo), 0.0) if e > 0 else lin
            Ms, Vs = [], []
            for q in (lin, eff):
                Ms.append(np.trapezoid(q * (xs - c / 2), xs) * 1000)
                msk = xs >= c / 2 + d
                Vs.append(np.trapezoid(q[msk], xs[msk]) * 1000 if msk.sum() > 1 else 0.0)
            return max(Ms), max(Vs), a

        Mx_ed = My_ed = Vx_ed = Vy_ed = 0.0
        Ngov, Mxg, Myg = 0.0, 0.0, 0.0
        for lab, N, Mx, My in str_cases:
            m1, v1, _ = cantilever(N, Mx, Bx, By, cx, dxe)
            m2, v2, _ = cantilever(N, My, By, Bx, cy, dye)
            My_add = 6 * abs(My) / (Bx * By**2)  # pressure from the other moment
            Mx_ed = max(Mx_ed, m1 + My_add * 1000 * ((Bx - cx) / 2) ** 2 / 2)
            My_ed = max(My_ed, m2)
            Vx_ed, Vy_ed = max(Vx_ed, v1), max(Vy_ed, v2)
            if N > Ngov:
                Ngov, Mxg, Myg = N, Mx, My
        for label, M, V, d, As, dia, s in (
                ("Bending in X (bars parallel to X)", Mx_ed, Vx_ed, dxe, Asx, dx_bar, inp["s_x"]),
                ("Bending in Y (bars parallel to Y)", My_ed, Vy_ed, dye, Asy, dy_bar, inp["s_y"])):
            calc.heading(label, 2)
            calc.formula("M_Ed", "∫ σ_net (x − c/2) dx at column face", M / 1000, "kNm/m")
            dd = calc.formula("d", "h − c − φ/2 (−φ_x for Y)", d, "mm", "Effective depth")
            res = design_flexure(calc, 1000, dd, M, fck, fcd, fyk, fyd, h,
                                 allow_compression=False, per_metre=True)
            calc.formula("A_s,prov", f"Ø{dia:g} @ {s:g} mm", As * 1e-3, "mm²/m")
            if math.isfinite(res["As"]):
                calc.check_min("Reinforcement: A_s,prov ≥ A_s,req", As * 1e-3, res["As"] * 1e-3,
                               "mm²/m", "6.1", hint=HINT_BARS)
            calc.check_min("Minimum reinforcement: A_s,prov ≥ A_s,min", As * 1e-3,
                           res["As_min"] * 1e-3, "mm²/m", "9.2.1.1", hint=HINT_BARS)
            MRd, _ = section_capacity(1000, dd, As, fcd, fyd)
            calc.formula("M_Rd", "A_s f_yd (d − 0.4x)", MRd / 1000, "kNm/m")
            calc.check("Bending: M_Ed ≤ M_Rd", M / 1000, MRd / 1000, "kNm/m", "6.1",
                       hint=HINT_BARS)
            calc.text("Beam shear at distance d from the column face:")
            shear_no_links(calc, 1000, dd, As, fck, 1.5, V, per_metre=True)
            calc.checks[-1].hint = calc.tr(HINT_SHEAR)

        punch = cls._punching(calc, Ngov, Mxg, Myg, Bx, By, cx, cy, (dxe + dye) / 2, Asx, Asy,
                              fck, fcd)

        calc.model3d = cls._scene(calc, inp, gov, punch, Wf, Ws)
        calc.figure(footing_plan(Bx / 1e3, By / 1e3, cx / 1e3, cy / 1e3,
                                 gov.get("Bp", Bx) / 1e3, gov.get("Lp", By) / 1e3,
                                 gov.get("ex", 0) / 1e3, gov.get("ey", 0) / 1e3,
                                 punch["a"] / 1e3, calc.tr("effective area"),
                                 calc.tr("punching perimeter")),
                    "Plan: footing, column, governing effective area and critical punching "
                    "perimeter")
        calc.items.insert(fig_index, calc.items.pop())

    # ------------------------------------------------------------ geotech
    @classmethod
    def _geo_case(cls, calc, inp, name, cases, Mx, My, H, gphi, gcf, gRv, gRh, gov) -> None:
        Bx, By, D = inp["Bx"], inp["By"], inp["D"]
        phid = math.atan(math.tan(math.radians(inp["phi"])) / gphi)
        cd = inp["c"] / gcf
        calc.formula("φ'_d", "atan(tan φ'_k / γ_φ')", math.degrees(phid), "°", dp=2)
        calc.formula("M_x,d", "γ (M_x + H_x h)", Mx, "kNm", "Design moment at underside (X)")
        calc.formula("M_y,d", "γ M_y", My, "kNm", "Design moment at underside (Y)")
        Hd = calc.formula("H_d", "γ H_x", abs(H), "kN", "Design horizontal load")
        Nq, Nc, Ng = bearing_factors(phid)
        worst = None
        Vmin = min(v for _, v in cases)
        for label, V in cases:
            ex, ey = abs(Mx) / V, abs(My) / V
            Bp, Lp = Bx - 2 * ex, By - 2 * ey
            ecc = (ex / Bx) ** 2 + (ey / By) ** 2
            if Bp <= 0 or Lp <= 0:
                u, qEd, qRd = float("inf"), float("inf"), 0.0
                parts = None
            else:
                b, l = min(Bp, Lp), max(Bp, Lp)
                sq = 1 + b / l * math.sin(phid)
                sg = 1 - 0.3 * b / l
                sc = (sq * Nq - 1) / (Nq - 1)
                along_b = Bp <= Lp  # Hx acts along the B' direction?
                m = (2 + b / l) / (1 + b / l) if along_b else (2 + l / b) / (1 + l / b)
                r = max(1 - abs(H) / (V + Bp * Lp * cd / math.tan(phid)), 0.0)
                iq, ig = r**m, r ** (m + 1)
                ic = iq - (1 - iq) / (Nc * math.tan(phid))
                qv = inp["gamma"] * D
                qRd = (cd * Nc * sc * ic + qv * Nq * sq * iq + 0.5 * inp["gamma"] * b * Ng * sg
                       * ig) / gRv
                qEd = V / (Bp * Lp)
                u = qEd / qRd
                parts = (sq, sg, sc, iq, ig, ic, m)
            if worst is None or u > worst[0]:
                worst = (u, label, V, ex, ey, Bp, Lp, qEd, qRd, parts, ecc)
        u, label, V, ex, ey, Bp, Lp, qEd, qRd, parts, ecc = worst
        calc.text("Governing sub-case: **{label}**, V_d = {V:.1f} kN.", label=label,
                  V=from_base(V, "kN"))
        calc.formula("e_x", "M_x,d / V_d", ex, "m", "Eccentricity along X", dp=3)
        calc.formula("e_y", "M_y,d / V_d", ey, "m", "Eccentricity along Y", dp=3)
        calc.check_limit(calc.tr("{name} eccentricity: (e_x/B_x)² + (e_y/B_y)² ≤ 1/9", name=name),
                         ecc, 1 / 9, "", "EN 1997-1 6.5.4", hint=HINT_ECC)
        calc.formula("B'", "B_x − 2e_x", max(Bp, 0), "m", "Effective length", dp=3)
        calc.formula("L'", "B_y − 2e_y", max(Lp, 0), "m", "Effective width", dp=3)
        if parts:
            sq, sg, sc, iq, ig, ic, m = parts
            calc.formula("N_q", "e^(π tan φ') tan²(45° + φ'/2)", Nq, "",
                         calc.tr("Bearing factors: Nc = {Nc:.2f}, Nγ = {Ng:.2f}", Nc=Nc, Ng=Ng),
                         dp=2)
            calc.formula("s_q", "1 + (B'/L') sin φ'", sq, "",
                         calc.tr("Shape factors: sγ = {sg:.3f}, sc = {sc:.3f}", sg=sg, sc=sc),
                         ref="D.4", dp=3)
            calc.formula("i_q", "(1 − H/(V + A'c' cot φ'))^m", iq, "",
                         calc.tr("Inclination: m = {m:.2f}, iγ = {ig:.3f}, ic = {ic:.3f}",
                                 m=m, ig=ig, ic=ic), ref="D.4", dp=3)
        calc.formula("q_Rd", "(c'N_c s_c i_c + q'N_q s_q i_q + ½γB'N_γ s_γ i_γ) / γ_R,v", qRd,
                     "kN/m²", "Design bearing resistance", ref="EN 1997-1 Annex D.4")
        calc.formula("q_Ed", "V_d / (B' L')", qEd, "kN/m²", "Design bearing pressure")
        calc.check(calc.tr("{name} bearing: q_Ed ≤ q_Rd", name=name), qEd, qRd, "kN/m²",
                   "EN 1997-1 6.5.2", hint=HINT_BEAR)
        Rh = calc.formula("R_h,d", "V_d,min tan φ'_d / γ_R,h", Vmin * math.tan(phid) / gRh, "kN",
                          "Sliding resistance (cast in situ, δ = φ')", ref="Eq. 6.3a")
        calc.check(calc.tr("{name} sliding: H_d ≤ R_h,d", name=name), Hd, Rh, "kN",
                   "EN 1997-1 6.5.3", hint=HINT_SLIDE)
        if u > gov["u"]:
            gov.update({"u": u, "name": f"{name} ({label})", "V": V, "ex": ex, "ey": ey,
                        "Bp": Bp, "Lp": Lp, "qEd": qEd, "qRd": qRd,
                        "Mx": Mx, "My": My})

    # ------------------------------------------------------------ punching
    @staticmethod
    def _punching(calc, V, Mx, My, Bx, By, cx, cy, d, Asx, Asy, fck, fcd) -> dict:
        calc.heading("Punching shear (EN 1992-1-1 6.4.4)")
        calc.input("V_Ed", V, "kN", "Column design axial load (governing STR case)")
        calc.input("d_eff", d, "mm", "Mean effective depth")
        sigma = V / (Bx * By)
        calc.formula("σ_net", "V_Ed / (B_x B_y)", sigma, "kN/m²", "Net soil pressure")
        rho = math.sqrt(min(Asx / (1000 * d), 0.02) * min(Asy / (1000 * d), 0.02))
        k = min(1 + math.sqrt(200 / d), 2.0)
        vmin = 0.035 * k**1.5 * math.sqrt(fck)
        crc = 0.18 / 1.5 * k * (100 * rho * fck) ** (1 / 3)
        kx, ky = _k_ratio(cx / cy), _k_ratio(cy / cx)
        best = None
        for a in np.linspace(0.25 * d, 2 * d, 36):
            a = min(a, (min(Bx - cx, By - cy)) / 2 - 1)
            if a <= 0:
                continue
            u = 2 * (cx + cy) + 2 * math.pi * a
            A = cx * cy + 2 * a * (cx + cy) + math.pi * a**2
            Vred = max(V - sigma * A, 0.0)
            if Vred <= 0:
                continue
            W1x = cx**2 / 2 + cx * cy + 2 * cy * a + 4 * a**2 + math.pi * a * cx
            W1y = cy**2 / 2 + cx * cy + 2 * cx * a + 4 * a**2 + math.pi * a * cy
            beta = 1 + kx * abs(Mx) / Vred * u / W1x + ky * abs(My) / Vred * u / W1y
            vEd = beta * Vred / (u * d)
            vRd = max(crc, vmin) * 2 * d / a
            if best is None or vEd / vRd > best["r"]:
                best = {"r": vEd / vRd, "a": a, "u": u, "A": A, "Vred": Vred, "beta": beta,
                        "vEd": vEd, "vRd": vRd}
        if best is None:
            calc.text("The whole footing lies within 2d of the column face — punching is not "
                      "critical; beam shear governs.")
            best = {"a": 0.0, "r": 0.0, "u": 0.0}
        else:
            calc.formula("a_crit", "critical distance, 0 < a ≤ 2d (6.4.4(2))", best["a"], "mm",
                         "Distance of governing control perimeter")
            calc.formula("u", "2(c_x + c_y) + 2πa", best["u"], "mm", "Control perimeter")
            calc.formula("V_Ed,red", "V_Ed − σ_net A(a)", best["Vred"], "kN", ref="Eq. 6.48")
            calc.formula("β", "1 + k_x (M_x/V) u/W_1x + k_y (M_y/V) u/W_1y", best["beta"], "",
                         ref="Eq. 6.51", dp=3)
            calc.formula("v_Ed", "β V_Ed,red / (u d)", best["vEd"], "N/mm²", ref="Eq. 6.51", dp=3)
            calc.formula("v_Rd", "C_Rd,c k (100ρ_l f_ck)^(1/3) 2d/a ≥ v_min 2d/a", best["vRd"],
                         "N/mm²", ref="Eq. 6.50", dp=3)
            calc.check("Punching: v_Ed ≤ v_Rd", best["vEd"], best["vRd"], "N/mm²", "6.4.4(2)",
                       hint=HINT_PUNCH)
        u0 = 2 * (cx + cy)
        nu = 0.6 * (1 - fck / 250)
        vmax = calc.formula("v_Rd,max", "0.4 ν f_cd", 0.4 * nu * fcd, "N/mm²", ref="6.4.5(3)",
                            dp=3)
        beta0 = best.get("beta", 1.0)
        v0 = calc.formula("v_Ed,0", "β V_Ed / (u_0 d)", beta0 * V / (u0 * d), "N/mm²",
                          "Shear stress at the column face", dp=3)
        calc.check("Punching at column face: v_Ed,0 ≤ v_Rd,max", v0, vmax, "N/mm²", "6.4.5(3)",
                   hint=HINT_PUNCH)
        return best

    # ---------------------------------------------------------------- 3D
    @staticmethod
    def _scene(calc, inp, gov, punch, Wf, Ws) -> dict:
        m = lambda v: from_base(v, "m")  # noqa: E731
        Bx, By, h, D, cx, cy = (m(inp[k]) for k in ("Bx", "By", "h", "D", "cx", "cy"))
        sc = Scene3D("pad_footing", calc.tr)
        for key, label in (("concrete", "Footing and column"), ("soil", "Soil"),
                           ("loads", "Loads"), ("bearing", "Base pressure"),
                           ("effective", "Effective area"), ("punch", "Punching perimeter"),
                           ("dims", "Dimensions")):
            sc.layer(key, label, toggle=key != "concrete")
        top = -D + h
        sc.box("concrete", (0, -D + h / 2, 0), (Bx, h, By), PALETTE["concrete"])
        sc.box("concrete", (0, (top + 0.8) / 2, 0), (cx, 0.8 - top, cy), "#9aa0a8")
        if D > h:
            sc.box("soil", (0, top / 2, 0), (Bx + 2.4, D - h, By + 2.4), PALETTE["soil"],
                   opacity=0.18, edges=False)
        sc.box("soil", (0, -D - 0.3, 0), (Bx + 2.4, 0.6, By + 2.4), PALETTE["rock"],
               opacity=0.12, edges=False)
        # loads (governing GEO case, design values)
        V = from_base(gov["V"], "kN")
        sc.arrow("loads", (0, 0.8 + 1.2, 0), (0, -1, 0), 1.2, PALETTE["load"], 0.25)
        sc.label("loads", calc.tr("V_d = {v:.0f} kN ({name})", v=V, name=gov["name"]),
                 (0, 0.8 + 1.35, 0), "result")
        Mx, My = from_base(gov["Mx"], "kNm"), from_base(gov["My"], "kNm")
        if abs(Mx) > 0:
            sc.label("loads", f"M_x,d = {Mx:.0f} kNm", (cx / 2 + 0.3, 0.6, 0), "force")
        if abs(My) > 0:
            sc.label("loads", f"M_y,d = {My:.0f} kNm", (0, 0.4, cy / 2 + 0.3), "force")
        # linear contact pressure under the footing (governing case, no-tension clipped)
        ex, ey = m(gov["ex"]), m(gov["ey"])
        n = 16
        xs = np.linspace(-Bx / 2, Bx / 2, n + 1)
        zs = np.linspace(-By / 2, By / 2, n + 1)
        A = Bx * By
        q = np.array([[V / A * (1 + 12 * ex * x / Bx**2 + 12 * ey * z / By**2)
                       for x in xs] for z in zs])
        q = np.maximum(q, 0)
        qmax = float(q.max()) or 1.0
        s = max(0.6, 0.35 * max(Bx, By)) / qmax
        verts, cols, faces = [], [], []
        for j, z in enumerate(zs):
            for i, x in enumerate(xs):
                verts.append((x, -D - 0.02 - q[j, i] * s, z))
                cols.append(heat_color(q[j, i] / qmax))
        for j in range(n):
            for i in range(n):
                a0 = j * (n + 1) + i
                faces += [(a0, a0 + 1, a0 + n + 2), (a0, a0 + n + 2, a0 + n + 1)]
        sc.mesh("bearing", verts, faces, opacity=0.85, colors=cols)
        for j in range(0, n + 1, 4):
            for i in range(0, n + 1, 4):
                ln = q[j, i] * s
                if ln > 0.03:
                    sc.arrow("bearing", (xs[i], -D - 0.02 - ln, zs[j]), (0, 1, 0), ln,
                             heat_color(q[j, i] / qmax), 0.08)
        sc.label("bearing", calc.tr("linear contact pressure, max {q:.0f} kN/m²", q=qmax),
                 (Bx / 2, -D - qmax * s - 0.15, By / 2), "bearing")
        sc.legend_item(heat_color(1.0), calc.tr("Contact pressure max {q:.0f} kN/m²", q=qmax))
        sc.legend_item(heat_color(0.0), calc.tr("Contact pressure min {q:.0f} kN/m²",
                                                q=float(q.min())))
        # effective area (centred on the load)
        Bp, Lp = m(gov["Bp"]), m(gov["Lp"])
        cxp, czp = ex, ey  # the effective area is centred on the load
        y0 = -D - 0.005
        sc.line("effective", [(cxp - Bp / 2, y0, czp - Lp / 2), (cxp + Bp / 2, y0, czp - Lp / 2),
                              (cxp + Bp / 2, y0, czp + Lp / 2), (cxp - Bp / 2, y0, czp + Lp / 2)],
                "#1d2433", dashed=True, closed=True)
        sc.label("effective", calc.tr("B' × L' = {b:.2f} × {l:.2f} m", b=Bp, l=Lp),
                 (cxp, y0 - 0.05, czp + Lp / 2), "dim")
        sc.legend_item("#1d2433", calc.tr("Effective area ({name}), q_Ed/q_Rd = {u:.2f}",
                                          name=gov["name"], u=gov["u"]))
        # punching control perimeter on the top face
        a = m(punch["a"])
        if a > 0:
            pts = []
            for k in range(73):
                t = 2 * math.pi * k / 72
                px = (cx / 2) * np.sign(math.cos(t)) + a * math.cos(t)
                pz = (cy / 2) * np.sign(math.sin(t)) + a * math.sin(t)
                pts.append((px, top + 0.01, pz))
            sc.line("punch", pts, PALETTE["punch"], closed=True)
            sc.label("punch", calc.tr("punching: a = {a:.2f} m, v_Ed/v_Rd = {r:.2f}", a=a,
                                      r=punch["r"]), (cx / 2 + a, top + 0.15, 0), "force")
            sc.legend_item(PALETTE["punch"], calc.tr("Critical punching perimeter"))
        sc.label("dims", f"B_x = {Bx:.2f} m", (0, top + 0.05, By / 2 + 0.2), "dim")
        sc.label("dims", f"B_y = {By:.2f} m", (Bx / 2 + 0.2, top + 0.05, 0), "dim")
        sc.label("dims", f"h = {h:.2f} m, D = {D:.2f} m", (-Bx / 2 - 0.2, -D + h / 2, By / 2),
                 "dim")
        return sc.to_dict()
