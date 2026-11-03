"""Rectangular RC water tank / pool wall and base — EN 1992-3 (liquid retaining), EN 1992-1-1,
EN 1997-1 (uplift, UPL).

The long walls are designed as vertical one-way strips fixed into the base slab, free at the
top (open tank) or pinned to a roof slab.  Load cases: (A) full, no backfill (water test);
(B) empty with backfill, surcharge and groundwater outside.  Crack widths are checked in the
quasi-permanent combination against w_k1 of the tightness class 1 (EN 1992-3 7.3.1).
"""

from __future__ import annotations

import math

import numpy as np

from ..analysis import UDL, Beam, Support
from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec2 import bar_area, concrete_props, design_flexure, section_capacity
from ..report.scene3d import PALETTE, Scene3D
from ..report.svg import vertical_diagrams

GW = 9.81e-6
ES = 200000.0
CONCRETE = ["C30/37", "C35/45", "C40/50"]
BARS = ["10", "12", "14", "16", "20"]
HINT_CRACK = "Use more, smaller bars at closer spacing (e.g. Ø12/100) or a thicker wall."
HINT_M = "Increase the wall thickness or the reinforcement."
HINT_UPL = ("Increase the base slab thickness or its projection (toe) carrying soil, add "
            "tension piles/anchors, or provide pressure relief (with care).")


def wk1(na, hD: float, h: float) -> float:
    r1, w1, r2, w2 = na.wk1
    return float(np.interp(hD / h, [r1, r2], [w1, w2]))


def crack_width(M: float, b: float, h: float, d: float, As: float, dia: float, s: float,
                cover: float, fck: float, alpha_long: float = 15.0) -> dict:
    """EN 1992-1-1 7.3.4 for a rectangular section in bending (per metre, b = 1000)."""
    p = concrete_props(fck)
    fct, Ecm = p["fctm"], p["Ecm"]
    ae = alpha_long
    rho = As / (b * d)
    xi = -ae * rho + math.sqrt((ae * rho) ** 2 + 2 * ae * rho)
    x = xi * d
    ss = M / (As * (d - x / 3)) if As > 0 else float("inf")
    hc = min(2.5 * (h - d), (h - x) / 3, h / 2)
    rpe = As / (b * hc)
    aE = ES / Ecm
    de = max((ss - 0.4 * fct / rpe * (1 + aE * rpe)) / ES, 0.6 * ss / ES)
    if s <= 5 * (cover + dia / 2):
        sr = 3.4 * cover + 0.425 * 0.8 * 0.5 * dia / rpe
    else:
        sr = 1.3 * (h - x)
    return {"x": x, "ss": ss, "hc": hc, "rpe": rpe, "de": de, "sr": sr, "wk": sr * de}


@register
class TankEC2(DesignModule):
    id = "ec2_tank"
    title = "Water tank / pool"
    category = "Concrete"
    has_3d = True
    uses_annex = True
    standard = "EN 1992-3, EN 1992-1-1, EN 1997-1"
    description = ("Rectangular reinforced concrete tank or swimming pool: wall bending for "
                   "the full (water test) and empty (backfill + groundwater) cases, crack "
                   "width to EN 1992-3 tightness class 1, minimum thickness and "
                   "reinforcement, and flotation (UPL) of the empty tank. Interactive 3D.")

    fields = [
        Field("Lx", "Internal length", "m", 10.0, min=1, group="Geometry"),
        Field("Ly", "Internal width", "m", 5.0, min=1, group="Geometry"),
        Field("H", "Wall height (above base)", "m", 2.5, min=0.5, max=12, group="Geometry"),
        Field("hw", "Maximum water depth", "m", 2.3, min=0.1, group="Geometry"),
        Field("t", "Wall thickness", "mm", 250.0, min=120, max=1000, group="Geometry"),
        Field("tb", "Base slab thickness", "mm", 300.0, min=150, max=1500, group="Geometry"),
        Field("toe", "Base projection beyond the walls", "m", 0.3, min=0, group="Geometry",
              help="Soil resting on the projection helps against flotation."),
        Field("top", "Wall support at the top", kind="choice",
              choices=["Free (open tank / pool)", "Pinned (roof slab)"],
              default="Free (open tank / pool)", group="Geometry"),
        Field("hs", "Backfill height outside (above base)", "m", 2.5, min=0, group="Ground"),
        Field("gamma", "Backfill γ", "kN/m³", 19.0, min=10, group="Ground"),
        Field("phi", "Backfill φ'k", "°", 30.0, min=20, max=45, group="Ground"),
        Field("q", "Surcharge on the backfill", "kN/m²", 5.0, min=0, group="Ground"),
        Field("hgw", "Groundwater outside (above base underside)", "m", 1.0, min=0,
              group="Ground", help="Highest expected level — governs flotation of the empty "
                                   "tank."),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C30/37",
              group="Concrete"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Concrete"),
        Field("cover", "Cover to bars", "mm", 40.0, min=25, max=75, group="Concrete"),
        Field("dia_i", "Vertical bars, inside face Ø", kind="choice", choices=BARS,
              default="12", group="Reinforcement"),
        Field("s_i", "Spacing, inside face", "mm", 125.0, min=75, max=300, group="Reinforcement"),
        Field("dia_o", "Vertical bars, outside face Ø", kind="choice", choices=BARS,
              default="12", group="Reinforcement"),
        Field("s_o", "Spacing, outside face", "mm", 125.0, min=75, max=300,
              group="Reinforcement"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        H, hw, t, tb = inp["H"], inp["hw"], inp["t"], inp["tb"]
        if hw > H:
            raise InputError("Water depth cannot exceed the wall height", "hw")
        if inp["hs"] > H:
            raise InputError("Backfill cannot be higher than the wall", "hs")
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyk = na.alpha_cc * fck / na.gamma_c, inp["fyk"]
        fyd = fyk / na.gamma_s
        cover = inp["cover"]
        propped = inp["top"].startswith("Pinned")
        K0 = 1 - math.sin(math.radians(inp["phi"]))

        calc.heading("Tank, materials and tightness")
        calc.input("H", H, "m", "Wall height")
        calc.input("h_w", hw, "m", "Water depth")
        calc.input("t", t, "mm", "Wall thickness")
        calc.label("Top support", inp["top"])
        tmin = na.tank_tmin[1]
        calc.check_min("Minimum wall thickness (EN 1992-3 9.11.1, classes 1–2)", t, tmin, "mm",
                       "EN 1992-3 9.11.1(102)",
                       hint=calc.tr("Use a wall at least {t:g} mm thick.", t=tmin))
        w_lim = calc.formula("w_k1", "linear 0.2 mm (h_D/h ≤ 5) → 0.05 mm (h_D/h ≥ 35)",
                             wk1(na, hw, t), "mm",
                             calc.tr("Tightness class 1, h_D/h = {r:.1f} (National Annex)",
                                     r=hw / t), ref="EN 1992-3 7.3.1(111)", dp=3)
        calc.formula("K_0", "1 − sin φ'", K0, "", "Earth pressure at rest (walls do not yield)",
                     dp=3)
        gL = na.gamma_liquid
        calc.text("ULS: liquid pressure × γ_F = {g:g} (EN 1991-4 Annex B); earth pressure × "
                  "1.35, surcharge × 1.5. SLS quasi-permanent: water × 1.0, earth × 1.0, "
                  "surcharge × ψ2 = 0.3.", g=gL)

        n = 40
        zs = np.linspace(0, H, n + 1)  # height above base

        def strip(pressure):  # pressure(z) [N/mm²] → beam with stepwise UDL (x = z)
            udls = [UDL(z1, z2, pressure(0.5 * (z1 + z2)) * 1000)
                    for z1, z2 in zip(zs[:-1], zs[1:])]
            sup = [Support(0.0, "fixed")] + ([Support(H, "pinned")] if propped else [])
            return Beam(H, 30000.0, 1000 * t**3 / 12, sup, udls=udls).solve()

        def p_water(z):
            return GW * max(hw - z, 0.0)

        def p_soil(z, gs=1.0, gq=1.0, ps=1.0):
            hs, hg = inp["hs"], inp["hgw"]
            if z >= hs:
                return 0.0
            depth = hs - z
            dw = max(hg - z, 0.0) if hg > 0 else 0.0
            dry = depth - dw
            sv = inp["gamma"] * dry + (inp["gamma"] - GW) * dw
            return gs * K0 * sv + gs * GW * dw + gq * ps * K0 * inp["q"]

        cases = {
            "A": ("Full, no backfill (water test)", lambda z: gL * p_water(z),
                  lambda z: p_water(z)),
            "B": ("Empty with backfill and groundwater",
                  lambda z: p_soil(z, 1.35, 1.5), lambda z: p_soil(z, 1.0, 1.0, 0.3)),
        }
        res = {}
        faces = {"inside": (float(inp["dia_i"]), inp["s_i"]),
                 "outside": (float(inp["dia_o"]), inp["s_o"])}
        need = {"inside": [0.0, 0.0, 0.0], "outside": [0.0, 0.0, 0.0]}  # M_uls, M_sls, hD
        Vmax = 0.0
        for key, (label, pu, ps) in cases.items():
            if key == "B" and inp["hs"] <= 0 and inp["hgw"] <= 0:
                continue
            ru, rs = strip(pu), strip(ps)
            res[key] = (label, ru, rs)
            # case A: hogging → inside face, sagging → outside; case B the reverse
            hog_u, sag_u = -ru.max_hogging[0], ru.max_sagging[0]
            hog_s, sag_s = -rs.max_hogging[0], rs.max_sagging[0]
            a, b_ = ("inside", "outside") if key == "A" else ("outside", "inside")
            for face, mu, ms in ((a, hog_u, hog_s), (b_, sag_u, sag_s)):
                if mu > need[face][0]:
                    need[face] = [mu, ms, hw]
            Vmax = max(Vmax, abs(ru.max_shear[0]))
            calc.heading(calc.tr("Load case {k}: {l}", k=key, l=calc.tr(label)))
            calc.formula("M_Ed,base", "fixed-end moment (strip analysis)", hog_u, "kNm",
                         "Design moment at the base per metre run")
            if sag_u > 1e3:
                calc.formula("M_Ed,span", "maximum span moment", sag_u, "kNm",
                             "Design span moment per metre run")
            calc.formula("M_qp,base", "same, quasi-permanent", hog_s, "kNm",
                         "SLS moment at the base per metre run")

        for face, (dia, s) in faces.items():
            Mu, Ms, hD = need[face]
            if Mu <= 0:
                continue
            calc.heading(calc.tr("Vertical reinforcement — {f} face", f=calc.tr(face)))
            d = t - cover - dia / 2
            As = bar_area(dia) * 1000 / s
            calc.formula("d", "t − c − φ/2", d, "mm", "Effective depth")
            calc.formula("M_Ed", "governing", Mu / 1000, "kNm/m")
            r = design_flexure(calc, 1000, d, Mu, fck, fcd, fyk, fyd, t,
                               allow_compression=False, per_metre=True)
            calc.formula("A_s,prov", f"Ø{dia:g} @ {s:g} mm", As * 1e-3, "mm²/m")
            if math.isfinite(r["As"]):
                calc.check_min("Reinforcement: A_s,prov ≥ A_s,req", As * 1e-3, r["As"] * 1e-3,
                               "mm²/m", "6.1", hint=HINT_M)
            MRd, _ = section_capacity(1000, d, As, fcd, fyd)
            calc.check("Bending: M_Ed ≤ M_Rd", Mu / 1000, MRd / 1000, "kNm/m", "6.1",
                       hint=HINT_M)
            p = concrete_props(fck)
            k = float(np.interp(t, [300, 800], [1.0, 0.65]))
            Asmin = 0.4 * k * p["fctm"] * (1000 * t / 2) / fyk
            calc.check_min("A_s ≥ A_s,min = k_c k f_ct,eff A_ct / f_yk (k_c = 0.4)", As * 1e-3,
                           Asmin * 1e-3, "mm²/m", "EN 1992-1-1 7.3.2", hint=HINT_CRACK)
            cw = crack_width(Ms, 1000, t, d, As, dia, s, cover, fck)
            calc.formula("σ_s", "M_qp / (A_s (d − x/3)), α_e = 15 (long-term)", cw["ss"],
                         "N/mm²", calc.tr("Steel stress, x = {x:.0f} mm", x=cw["x"]), dp=0)
            calc.formula("ρ_p,eff", "A_s / (b h_c,eff)", cw["rpe"], "",
                         calc.tr("h_c,eff = {h:.0f} mm", h=cw["hc"]), ref="7.3.2(3)", dp=4)
            calc.formula("s_r,max", "3.4c + 0.425 k_1 k_2 φ/ρ_p,eff", cw["sr"], "mm",
                         "Maximum crack spacing (k_1 = 0.8, k_2 = 0.5)", ref="Eq. 7.11", dp=0)
            calc.formula("ε_sm − ε_cm", "(σ_s − k_t f_ct,eff/ρ_p,eff (1 + α_e ρ_p,eff))/E_s ≥ "
                         "0.6σ_s/E_s", cw["de"] * 1000, "", "Mean strain difference [‰] "
                         "(k_t = 0.4)", ref="Eq. 7.9", dp=4)
            wl = wk1(na, hD, t)
            calc.check(calc.tr("Crack width {f}: w_k ≤ w_k1", f=calc.tr(face)), cw["wk"], wl,
                       "mm", "EN 1992-3 7.3.1", hint=HINT_CRACK)
            xmin = min(50.0, 0.2 * t)
            calc.check_min("Compression zone x ≥ x_min = min(50 mm, 0.2t) (no through-cracks)",
                           cw["x"], xmin, "mm", "EN 1992-3 7.3.1(112)", hint=HINT_CRACK)

        calc.heading("Shear at the base of the wall")
        d = t - cover - float(inp["dia_i"]) / 2
        As = bar_area(float(inp["dia_i"])) * 1000 / inp["s_i"]
        kk = min(1 + math.sqrt(200 / d), 2.0)
        rho = min(As / (1000 * d), 0.02)
        VRdc = max(0.18 / na.gamma_c * kk * (100 * rho * fck) ** (1 / 3),
                   0.035 * kk**1.5 * math.sqrt(fck)) * 1000 * d
        calc.formula("V_Rd,c", "C_Rd,c k (100ρ_l f_ck)^(1/3) b d", VRdc / 1000, "kN/m",
                     ref="Eq. 6.2")
        calc.check("Shear: V_Ed ≤ V_Rd,c", Vmax / 1000, VRdc / 1000, "kN/m", "6.2.2",
                   hint="Increase the wall thickness.")

        cls._uplift(calc, inp, na, t, tb)
        z = zs
        series = []
        for key, (label, ru, rs) in res.items():
            Mz = np.interp(z, ru.x, ru.moment) / 1e6
            series.append((calc.tr("M_Ed case {k} [kNm/m]", k=key), Mz,
                           "#2a6f97" if key == "A" else "#c47a2c"))
        if series:
            calc.figure(vertical_diagrams(H / 1000 - z[::-1] / 1000, H / 1000, 0.0,
                                          [(n_, v[::-1], c) for n_, v, c in series]),
                        "Design bending moment along the wall height (depth from the top)")
        calc.model3d = cls._scene(calc, inp)

    @staticmethod
    def _uplift(calc, inp, na, t, tb) -> None:
        hg = inp["hgw"]
        if hg <= 0:
            return
        calc.heading("Flotation of the empty tank — UPL (EN 1997-1 2.4.7.4)")
        Gdst, Gstb, _ = na.upl
        Bx = inp["Lx"] + 2 * t + 2 * inp["toe"]
        By = inp["Ly"] + 2 * t + 2 * inp["toe"]
        Ab = Bx * By
        U = calc.formula("U", "γ_w h_gw A_base", GW * hg * Ab, "kN", "Uplift on the base")
        gc = 25e-6
        Wb = gc * Ab * tb
        Ww = gc * t * inp["H"] * 2 * (inp["Lx"] + inp["Ly"] + 2 * t)
        Atoe = Ab - (inp["Lx"] + 2 * t) * (inp["Ly"] + 2 * t)
        Ws = inp["gamma"] * Atoe * min(inp["hs"], inp["H"])
        G = calc.formula("G_stb", "W_base + W_walls + W_soil on projection", Wb + Ww + Ws, "kN",
                         "Stabilising permanent weight (friction on the walls ignored)")
        calc.check(calc.tr("UPL: γ_G,dst U ≤ γ_G,stb G ({a:g} / {b:g})", a=Gdst, b=Gstb),
                   Gdst * U, Gstb * G, "kN", "EN 1997-1 Eq. 2.8", hint=HINT_UPL)

    @staticmethod
    def _scene(calc, inp) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        Lx, Ly, H, hw = m(inp["Lx"]), m(inp["Ly"]), m(inp["H"]), m(inp["hw"])
        t, tb, toe = m(inp["t"]), m(inp["tb"]), m(inp["toe"])
        sc = Scene3D("tank", calc.tr)
        for key, label in (("concrete", "Tank"), ("water", "Water"), ("soil", "Backfill"),
                           ("gw", "Groundwater")):
            sc.layer(key, label, toggle=key != "concrete")
        col = PALETTE["concrete"]
        Bx, By = Lx + 2 * t + 2 * toe, Ly + 2 * t + 2 * toe
        sc.box("concrete", (0, -tb / 2, 0), (Bx, tb, By), col)
        for sx in (-1, 1):
            sc.box("concrete", (sx * (Lx / 2 + t / 2), H / 2, 0), (t, H, Ly + 2 * t), col)
        for sz in (-1, 1):
            sc.box("concrete", (0, H / 2, sz * (Ly / 2 + t / 2)), (Lx, H, t), col)
        sc.box("water", (0, hw / 2, 0), (Lx, hw, Ly), PALETTE["water"], opacity=0.35,
               edges=False)
        hs = m(inp["hs"])
        if hs > 0:
            W = Bx + 3
            sc.box("soil", (0, (hs - tb) / 2, -(Ly / 2 + t) - 0.75), (W, hs + tb, 1.5),
                   PALETTE["soil"], opacity=0.25, edges=False)
        hg = m(inp["hgw"])
        if hg > 0:
            sc.box("gw", (0, -tb + hg, 0), (Bx + 3, 0.01, By + 3), PALETTE["water"],
                   opacity=0.25, edges=False)
        sc.views["default"] = {"pos": [Lx * 0.9, H * 3, Ly * 2.2], "target": [0, H / 3, 0]}
        return sc.to_dict()
