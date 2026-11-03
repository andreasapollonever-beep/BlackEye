"""Cantilever RC retaining wall — EN 1997-1, EN 1998-5 and EN 1992-1-1."""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, Field, InputError, register
from ..core.units import from_base
from ..design.ec2 import bar_area, design_flexure, section_capacity, shear_no_links
from ..design.geotech import ka_coulomb, poly_props
from ..design.walls import (GAMMA_W, Totals, WallGeometry, WallModule, factored,
                            soil_fields)

CONCRETE = ["C25/30", "C30/37", "C35/45", "C40/50"]
BARS = ["10", "12", "14", "16", "20", "25", "32"]
HINT_BARS = "Use larger bars or reduce the bar spacing (or increase the thickness)."


class CantileverGeometry(WallGeometry):
    def __init__(self, inp: dict) -> None:
        super().__init__(inp)
        self.Hs, self.t_top, self.t_bot = inp["H_stem"], inp["t_top"], inp["t_bot"]
        self.tb, self.toe, self.heel = inp["t_base"], inp["toe"], inp["heel"]
        self.df = inp["d_front"]
        self.B = self.toe + self.t_bot + self.heel
        self.top = self.tb + self.Hs
        self.x0 = self.toe + self.t_top
        self.xb = self.xbb = self.toe + self.t_bot
        self.x_front = self.toe
        self.gc = inp["gamma_c"]
        self.concrete = [("Stem", self.stem_poly), ("Base", self.base_poly)]
        self.finish()

    @property
    def stem_poly(self):
        return [(self.toe, self.tb), (self.xb, self.tb), (self.x0, self.tb + self.Hs),
                (self.toe, self.tb + self.Hs)]

    @property
    def base_poly(self):
        return [(0, 0), (self.B, 0), (self.B, self.tb), (0, self.tb)]

    def base_moments(self, t: Totals, fG: float, fQ: float, f_up: float, q: float):
        """Cantilever moments/shears of heel and toe at the stem faces."""
        pts = self.base_pressure(t)
        xq = np.array([p[0] for p in pts])
        qq = np.array([p[1] for p in pts])
        # heel
        xh = np.linspace(self.xb, self.B, 201)
        hs = np.array([self.zs(x) for x in xh]) - self.tb
        if self.hw > self.tb:
            above = np.maximum(hs - (self.hw - self.tb), 0)
            soil = self.gb * above + self.gsat * (hs - above)
        else:
            soil = self.gb * hs
        uplift = GAMMA_W * self.hw * xh / self.B if self.hw > 0 else 0 * xh
        w = fG * (self.gc * self.tb + soil) + fQ * q - f_up * uplift
        net = w - np.interp(xh, xq, qq)
        M_heel = np.trapezoid(net * (xh - self.xb), xh)
        V_heel = np.trapezoid(net, xh)
        # toe
        if self.toe > 0:
            xt = np.linspace(0, self.toe, 201)
            wt = self.gc * self.tb + self.gf * self.df  # favourable, γ = 1.0
            uplift_t = GAMMA_W * self.hw * xt / self.B if self.hw > 0 else 0 * xt
            nt = np.interp(xt, xq, qq) + uplift_t - wt
            M_toe = np.trapezoid(nt * (self.toe - xt), xt)
            V_toe = np.trapezoid(nt, xt)
        else:
            M_toe = V_toe = 0.0
        return M_heel, V_heel, M_toe, V_toe


@register
class RetainingWallEC7(WallModule):
    id = "ec7_retaining_wall"
    title = "Cantilever retaining wall"
    category = "Geotechnical"
    standard = "EN 1997-1, EN 1998-5, EN 1992-1-1"
    description = ("Reinforced concrete cantilever wall: active earth pressure (Coulomb), "
                   "surcharge, groundwater, seismic thrust (Mononobe-Okabe), sliding, "
                   "overturning, bearing (Annex D), and EC2 design of stem, heel and toe. "
                   "Includes an interactive 3D model.")

    fields = [
        Field("H_stem", "Stem height above base", "m", 4.0, min=0.5, max=15, group="Geometry"),
        Field("t_top", "Stem thickness at top", "m", 0.25, min=0.15, group="Geometry"),
        Field("t_bot", "Stem thickness at base", "m", 0.40, min=0.15, group="Geometry"),
        Field("t_base", "Base thickness", "m", 0.50, min=0.2, group="Geometry"),
        Field("toe", "Toe length", "m", 1.00, min=0, group="Geometry"),
        Field("heel", "Heel length (behind stem)", "m", 2.20, min=0.2, group="Geometry"),
        Field("d_front", "Soil depth over toe", "m", 0.50, min=0, group="Geometry",
              help="Depth of soil in front of the wall above the top of the base."),
        Field("length", "Wall length (3D view)", "m", 8.0, min=1, group="Geometry"),
    ] + soil_fields() + [
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C30/37",
              group="Concrete"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Concrete"),
        Field("gamma_c", "Concrete unit weight", "kN/m³", 25.0, min=20, group="Concrete"),
        Field("cover_stem", "Cover — stem (earth face)", "mm", 50.0, min=20, group="Concrete"),
        Field("cover_base", "Cover — base", "mm", 75.0, min=25, group="Concrete"),
        Field("stem_dia", "Stem bars Ø", kind="choice", choices=BARS, default="16",
              group="Reinforcement"),
        Field("stem_s", "Stem bar spacing", "mm", 150.0, min=75, max=400, group="Reinforcement"),
        Field("heel_dia", "Heel top bars Ø", kind="choice", choices=BARS, default="16",
              group="Reinforcement"),
        Field("heel_s", "Heel bar spacing", "mm", 150.0, min=75, max=400, group="Reinforcement"),
        Field("toe_dia", "Toe bottom bars Ø", kind="choice", choices=BARS, default="12",
              group="Reinforcement"),
        Field("toe_s", "Toe bar spacing", "mm", 150.0, min=75, max=400, group="Reinforcement"),
    ]

    @classmethod
    def make_geometry(cls, inp: dict) -> CantileverGeometry:
        if inp["t_bot"] < inp["t_top"]:
            raise InputError("Stem thickness at base must be ≥ thickness at top", "t_bot")
        return CantileverGeometry(inp)

    @classmethod
    def record_geometry(cls, calc: Calculation, g: CantileverGeometry, inp: dict) -> None:
        calc.heading("Geometry")
        calc.input("H_stem", g.Hs, "m", "Stem height")
        calc.input("t_top", g.t_top, "m", "Stem thickness at top")
        calc.input("t_bot", g.t_bot, "m", "Stem thickness at base")
        calc.input("t_b", g.tb, "m", "Base thickness")
        calc.input("b_toe", g.toe, "m", "Toe length")
        calc.input("b_heel", g.heel, "m", "Heel length")
        calc.formula("B", "b_toe + t_bot + b_heel", g.B, "m", "Base width")
        calc.input("β", inp["beta"], "°", "Backfill slope")
        calc.formula("h_v", "t_b + H_stem + (B − b_toe − t_top) tan β", g.hv, "m",
                     "Height of virtual back (through heel)")

    @classmethod
    def structural(cls, calc, g, inp, weights, seis) -> None:
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd = fck / 1.5
        fyk = inp["fyk"]
        fyd = fyk / 1.15
        beta = math.radians(inp["beta"])
        phi = math.radians(inp["phi_b"])
        Ka_s = ka_coulomb(phi, beta, beta) * math.cos(beta)
        calc.heading("Structural design — STR (EN 1992-1-1)")
        calc.text("{c}: f_cd = {fcd:.2f} N/mm², f_yd = {fyd:.1f} N/mm². "
                  "Persistent design forces use set A1 (γ_G = 1.35, γ_Q = 1.50) with "
                  "characteristic soil strength; the seismic situation (if included) uses "
                  "γ = 1.0 and the Mononobe-Okabe thrust. The larger governs.",
                  c=inp["concrete"], fcd=fcd, fyd=fyd)
        calc.formula("K_a,h", "K_a(φ'_k, β) cos β", Ka_s, "", "Horizontal active coefficient "
                     "on stem", dp=4)

        # ---- stem forces at the top of the base
        def stem_forces(Kh, fG, fQ, q, extra=None):
            zs = np.linspace(g.tb, g.tb + g.Hs, 401)
            depth = g.tb + g.Hs - zs
            if g.hw > g.tb:
                dw = max(g.tb + g.Hs - g.hw, 0)
                sv = np.where(zs >= g.hw, g.gb * depth,
                              g.gb * dw + (g.gsat - GAMMA_W) * (depth - dw))
                pw = np.where(zs < g.hw, GAMMA_W * (g.hw - zs), 0.0)
            else:
                sv = g.gb * depth
                pw = np.zeros_like(zs)
            p = fG * (Kh * sv + pw) + fQ * Kh * q
            lever = zs - g.tb
            V = np.trapezoid(p, zs)
            M = np.trapezoid(p * lever, zs)
            if extra:
                V += extra[0]
                M += extra[1]
            return M, V

        M_p, V_p = stem_forces(Ka_s, 1.35, 1.5, inp["q"])
        M_s = V_s = 0.0
        if seis:
            kvs, Kae, kh = seis["kvs"], seis["Kae"], seis["kh"]
            Ka_d = seis["Ka"]
            dE = max(0.5 * g.gb * (1 + kvs) * Kae * g.Hs**2 - 0.5 * g.gb * Ka_d * g.Hs**2, 0)
            Ws, _, zc = poly_props(g.stem_poly)
            Ws *= g.gc
            dE *= math.cos(beta)
            extra = (dE + kh * Ws + Kae * inp["psi2"] * inp["q"] * g.Hs,
                     dE * g.Hs / 2 + kh * Ws * (zc - g.tb)
                     + Kae * inp["psi2"] * inp["q"] * g.Hs**2 / 2)
            M_s, V_s = stem_forces(Ka_d * math.cos(beta), 1.0, 0.0, 0.0, extra)

        cls._member(calc, "Stem (at top of base, earth face in tension)", g.t_bot,
                    inp["cover_stem"], float(inp["stem_dia"]), inp["stem_s"],
                    max(M_p, M_s), max(V_p, V_s), M_p, M_s, fck, fcd, fyk, fyd)

        # ---- heel and toe from linear base pressure
        thrust, _ = cls._thrust(None, g, inp, 1.0, record=False)
        t_p = factored(weights + thrust, 1.35, 1.0, 1.5, max_vertical=True)
        heel_p, vheel_p, toe_p, vtoe_p = g.base_moments(t_p, 1.35, 1.5, 1.0, inp["q"])
        heel_s = vheel_s = toe_s = vtoe_s = 0.0
        if seis:
            f = 1 + seis["kvs"]
            heel_s, vheel_s, toe_s, vtoe_s = g.base_moments(seis["t"], f, inp["psi2"], 1.0,
                                                           inp["q"])
        cls._member(calc, "Heel (at back of stem, top face in tension)", g.tb,
                    inp["cover_base"], float(inp["heel_dia"]), inp["heel_s"],
                    max(heel_p, heel_s), max(abs(vheel_p), abs(vheel_s)), heel_p, heel_s,
                    fck, fcd, fyk, fyd)
        cls._member(calc, "Toe (at front of stem, bottom face in tension)", g.tb,
                    inp["cover_base"], float(inp["toe_dia"]), inp["toe_s"],
                    max(toe_p, toe_s), max(abs(vtoe_p), abs(vtoe_s)), toe_p, toe_s,
                    fck, fcd, fyk, fyd)

    @staticmethod
    def _member(calc, title, h, cover, dia, s, M, V, M_p, M_s, fck, fcd, fyk, fyd) -> None:
        calc.heading(title, 2)
        title = calc.tr(title)
        calc.formula("M_Ed", "max(persistent, seismic)", max(M, 0.0), "kNm/m",
                     calc.tr("persistent {p:.1f}, seismic {s:.1f} kNm/m",
                             p=from_base(M_p, "kNm/m"), s=from_base(M_s, "kNm/m")))
        calc.formula("V_Ed", "at the face of the stem", abs(V), "kN/m", "Design shear")
        d = calc.formula("d", "h − c − φ/2", h - cover - dia / 2, "mm", "Effective depth")
        b = 1000.0
        Mt = max(M, 0.0) * b
        res = design_flexure(calc, b, d, Mt, fck, fcd, fyk, fyd, h, allow_compression=False,
                             per_metre=True)
        As_prov = bar_area(dia) * b / s
        calc.formula("A_s,prov", f"Ø{dia:g} @ {s:g} mm", As_prov * 1e-3, "mm²/m")
        if math.isfinite(res["As"]):
            calc.check_min("Reinforcement: A_s,prov ≥ A_s,req", As_prov * 1e-3,
                           res["As"] * 1e-3, "mm²/m", "6.1", hint=HINT_BARS)
        calc.check_min("Minimum reinforcement: A_s,prov ≥ A_s,min", As_prov * 1e-3,
                       res["As_min"] * 1e-3, "mm²/m", "9.2.1.1", hint=HINT_BARS)
        MRd, _ = section_capacity(b, d, As_prov, fcd, fyd)
        calc.formula("M_Rd", "A_s f_yd (d − 0.4x)", MRd / b, "kNm/m", "Moment resistance")
        calc.check("Bending: M_Ed ≤ M_Rd", Mt / b, MRd / b, "kNm/m", "6.1", hint=HINT_BARS)
        shear_no_links(calc, b, d, As_prov, fck, 1.5, abs(V) * b, per_metre=True)
        calc.check_limit("Bar spacing: s ≤ min(3h, 400)", s, min(3 * h, 400.0), "mm",
                         "9.3.1.1(3)", hint="Reduce the bar spacing.")

