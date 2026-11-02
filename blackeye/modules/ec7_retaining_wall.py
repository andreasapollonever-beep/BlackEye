"""Cantilever RC retaining wall — EN 1997-1, EN 1998-5 and EN 1992-1-1.

Coordinate system (per unit length of wall, base units N and mm):
x is measured horizontally from the toe (front edge of the base) towards
the heel, z vertically upwards from the underside of the base.  Earth
pressures are evaluated on a *virtual back* — the vertical plane through the
heel — so the soil above the heel moves with the wall.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..design.ec2 import bar_area, design_flexure, section_capacity, shear_no_links
from ..design.geotech import (bearing_factors, clip_z, k_mononobe_okabe, ka_coulomb,
                              linear_resultant, poly_props)
from ..report.svg import wall_section

GAMMA_W = 9.81e-6  # N/mm³
CONCRETE = ["C25/30", "C30/37", "C35/45", "C40/50"]
BARS = ["10", "12", "14", "16", "20", "25", "32"]

# Partial factor sets, EN 1997-1 Annex A (recommended values)
#            γG,unf γG,fav  γQ    γφ'   γc'   γR,v  γR,h
COMBOS = {
    "DA1-C1": (1.35, 1.00, 1.50, 1.00, 1.00, 1.00, 1.00),
    "DA1-C2": (1.00, 1.00, 1.30, 1.25, 1.25, 1.00, 1.00),
    "DA2": (1.35, 1.00, 1.50, 1.00, 1.00, 1.40, 1.10),
    "DA3": (1.00, 1.00, 1.30, 1.25, 1.25, 1.00, 1.00),
}
APPROACHES = {"DA1": ["DA1-C1", "DA1-C2"], "DA2": ["DA2"], "DA3": ["DA3"]}
EQU = (1.10, 0.90, 1.50, 1.25, 1.25)  # γG,dst γG,stb γQ,dst γφ' γc' (Tables A.1, A.2)


@dataclass
class Comp:
    """A characteristic action on the wall (per unit length)."""
    name: str
    H: float = 0.0     # horizontal, positive towards the toe (destabilising)
    zH: float = 0.0
    V: float = 0.0     # vertical, positive downwards
    xV: float = 0.0
    kind: str = "G"    # G permanent | Q variable | A seismic (already factored)
    role: str = "weight"  # weight | thrust | water | uplift | inertia


@dataclass
class Totals:
    H: float
    V: float
    M_stb: float
    M_dst: float
    rows: list

    @property
    def x_R(self) -> float:
        return (self.M_stb - self.M_dst) / self.V if self.V > 0 else 0.0


def _factored(comps: list[Comp], g_unf: float, g_fav: float, gq: float,
              max_vertical: bool = False) -> Totals:
    """Apply partial factors. ``max_vertical`` makes vertical actions unfavourable."""
    H = V = Ms = Md = 0.0
    rows = []
    for c in comps:
        if c.kind == "A":
            fH = fV = 1.0
        elif c.role == "uplift":
            fH, fV = 0.0, (g_fav if max_vertical else g_unf)
        else:
            unf = g_unf if c.kind == "G" else gq
            fav = g_fav if c.kind == "G" else 0.0
            fH = unf
            fV = unf if max_vertical else fav
        h, v = fH * c.H, fV * c.V
        H += h
        V += v
        Md += h * c.zH
        if v >= 0:
            Ms += v * c.xV
        else:
            Md += -v * c.xV
        rows.append((c, fH, fV, h, v))
    return Totals(H, V, Ms, Md, rows)


@register
class RetainingWallEC7(DesignModule):
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
        Field("beta", "Backfill slope β", "°", 0.0, min=0, max=40, group="Retained soil"),
        Field("phi_b", "Backfill φ'k", "°", 30.0, min=15, max=45, group="Retained soil"),
        Field("gamma_b", "Backfill γ", "kN/m³", 18.0, min=10, group="Retained soil"),
        Field("gamma_sat", "Backfill γsat", "kN/m³", 20.0, min=10, group="Retained soil"),
        Field("q", "Surcharge on backfill (variable)", "kN/m²", 10.0, min=0,
              group="Retained soil"),
        Field("h_w", "Water level above base underside", "m", 0.0, min=0,
              group="Retained soil", help="0 = drained backfill (no water pressure)."),
        Field("phi_f", "Foundation φ'k", "°", 32.0, min=10, max=45, group="Foundation soil"),
        Field("c_f", "Foundation c'k", "kN/m²", 0.0, min=0, group="Foundation soil"),
        Field("gamma_f", "Foundation γ", "kN/m³", 19.0, min=10, group="Foundation soil"),
        Field("k_base", "Base friction factor k (tan δ = k tan φ')", "", 1.0, min=0.3, max=1.0,
              group="Foundation soil", help="1.0 cast in situ, 2/3 precast (EN 1997-1 6.5.3(10))."),
        Field("approach", "Design approach", kind="choice", choices=list(APPROACHES),
              default="DA1", group="Design basis",
              help="Check the National Annex (DA1 recommended in many countries)."),
        Field("seismic", "Include seismic design (EN 1998-5)", kind="bool", default=True,
              group="Seismic"),
        Field("ag", "Design ground acceleration αgR·γI", "", 0.16, min=0, max=0.6,
              group="Seismic", help="In g. Greece: Zone I 0.16, Zone II 0.24, Zone III 0.36."),
        Field("S", "Soil factor S", "", 1.2, min=1.0, max=1.8, group="Seismic"),
        Field("r", "Displacement factor r", kind="choice", choices=["1.0", "1.5", "2.0"],
              default="2.0", group="Seismic",
              help="EN 1998-5 Table 7.1: 2.0 free gravity walls allowing ~300α·S mm, "
                   "1.0 for walls that cannot move (e.g. propped)."),
        Field("psi2", "ψ2 for surcharge", "", 0.3, min=0, max=1, group="Seismic"),
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

    # ===================================================================== run
    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        g = _Wall(inp)
        if g.t_bot < g.t_top:
            raise InputError("Stem thickness at base must be ≥ thickness at top")
        if inp["h_w"] > g.hv + 1e-6:
            raise InputError("Water level is above the retained ground surface")
        if math.radians(inp["beta"]) >= math.radians(inp["phi_b"]) / 1.25:
            raise InputError("Backfill slope is too steep for the design angle of shearing "
                             "resistance (β must be < φ'd)")
        cls._geometry(calc, g, inp)
        weights = cls._weights(calc, g, inp)
        model = {"type": "retaining_wall", "geometry": g.to_dict(), "pressures": [],
                 "bearing": [], "forces": [], "checks": []}
        gov: dict = {"util": -1}

        # ---------------------------------------------- persistent GEO cases
        for name in APPROACHES[inp["approach"]]:
            gu, gf, gq, gphi, gc, gRv, gRh = COMBOS[name]
            calc.heading(f"Stability — {name} (EN 1997-1 Annex A)")
            calc.text(f"Partial factors: γ_G = {gu} (unfav.) / {gf} (fav.), γ_Q = {gq}, "
                      f"γ_φ' = {gphi}, γ_c' = {gc}, γ_R,v = {gRv}, γ_R,h = {gRh}.")
            thrust, info = cls._thrust(calc, g, inp, gphi, record=True)
            comps = weights + thrust
            cls._stability(calc, g, inp, name, comps, gu, gf, gq, gphi, gc, gRv, gRh, gov,
                           info)

        # ------------------------------------------------------------- EQU
        calc.heading("Overturning — EQU (EN 1997-1 2.4.7.2)")
        dst, stb, gq, gphi, _ = EQU
        calc.text(f"Partial factors: γ_G,dst = {dst}, γ_G,stb = {stb}, γ_Q,dst = {gq}, "
                  f"γ_φ' = {gphi}.")
        thrust, _ = cls._thrust(calc, g, inp, gphi, record=True)
        t = _factored(weights + thrust, dst, stb, gq)
        cls._table(calc, t, "EQU — design actions about the toe")
        Md = calc.formula("M_dst,d", "Σ H_d z + Σ U_d x", t.M_dst, "kNm/m",
                          "Destabilising moment about toe")
        Ms = calc.formula("M_stb,d", "Σ V_d x", t.M_stb, "kNm/m", "Stabilising moment about toe")
        calc.check("Overturning: M_dst,d ≤ M_stb,d", Md, Ms, "kNm/m", "EN 1997-1 Eq. 2.4")

        # ----------------------------------------------------------- seismic
        seis = None
        if inp["seismic"] and inp["ag"] > 0:
            seis = cls._seismic(calc, g, inp, weights, gov)

        # ------------------------------------------------------ structural
        cls._structural(calc, g, inp, weights, seis)

        # ----------------------------------------------------------- model
        chars, _ = cls._thrust(None, g, inp, 1.0, record=False)
        model["pressures"] = cls._pressure_profiles(g, inp, seis)
        model["forces"] = [
            {"name": c.name, "x": from_base(g.B if c.role != "weight" else c.xV, "m"),
             "z": from_base(c.zH, "m"), "H": from_base(c.H, "kN/m"),
             "V": from_base(c.V, "kN/m"), "role": c.role}
            for c in weights + chars if abs(c.H) + abs(c.V) > 0]
        model["bearing"] = gov.get("bearing", [])
        model["governing"] = {k: gov[k] for k in ("name", "e", "B_eff", "q_Ed", "q_Rd", "R_x")
                              if k in gov}
        model["checks"] = [{"description": c.description, "utilisation": c.utilisation,
                            "passed": c.passed} for c in calc.checks]
        calc.model3d = model
        calc.figure(wall_section(model), "Section with characteristic earth/water pressures "
                    "and governing design base pressure")
        # move the figure to just after the geometry heading for readability
        fig = calc.items.pop()
        calc.items.insert(g.fig_index, fig)

    # =========================================================== sections
    @staticmethod
    def _geometry(calc: Calculation, g: "_Wall", inp: dict) -> None:
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
        g.fig_index = len(calc.items)
        calc.heading("Soil and materials")
        calc.table(["", "φ'k [°]", "c'k [kN/m²]", "γ [kN/m³]", "γsat [kN/m³]"],
                   [["Retained backfill", f"{inp['phi_b']:g}", "0",
                     f"{from_base(g.gb, 'kN/m³'):g}", f"{from_base(g.gsat, 'kN/m³'):g}"],
                    ["Foundation soil", f"{inp['phi_f']:g}",
                     f"{from_base(inp['c_f'], 'kN/m²'):g}",
                     f"{from_base(g.gf, 'kN/m³'):g}", "—"]],
                   caption="Characteristic soil parameters")
        calc.input("q_k", inp["q"], "kN/m²", "Variable surcharge on retained surface")
        if g.hw > 0:
            calc.input("h_w", g.hw, "m", "Groundwater level above base underside")
            calc.note("Water is assumed behind the wall only; uplift varies linearly from "
                      "γ_w h_w at the heel to zero at the toe.")
        else:
            calc.note("Drained backfill — no water pressure (provide drainage/weep holes).")
        calc.text("Wall friction on the virtual back δ = β (EN 1997-1 Annex C). Passive "
                  "resistance in front of the wall is conservatively ignored.")

    @staticmethod
    def _weights(calc: Calculation, g: "_Wall", inp: dict) -> list[Comp]:
        calc.heading("Characteristic vertical actions")
        out: list[Comp] = []

        def add(name, pts, gamma, kind="G"):
            a, cx, cz = poly_props(pts)
            if a > 0:
                out.append(Comp(name, V=a * gamma, xV=cx, zH=cz, kind=kind, role="weight"))

        add("Stem", g.stem_poly, g.gc)
        add("Base", g.base_poly, g.gc)
        soil = g.heel_soil_poly
        if g.hw > g.tb:
            add("Backfill over heel (above water)", clip_z(soil, g.hw, False), g.gb)
            add("Backfill over heel (below water)", clip_z(soil, g.hw, True), g.gsat)
        else:
            add("Backfill over heel", soil, g.gb)
        if g.df > 0 and g.toe > 0:
            add("Soil over toe", g.toe_soil_poly, g.gf)
        qw = g.B - g.x0
        if inp["q"] > 0 and qw > 0:
            out.append(Comp("Surcharge over heel", V=inp["q"] * qw, xV=g.x0 + qw / 2,
                            zH=g.hv, kind="Q", role="weight"))
        if g.hw > 0:
            out.append(Comp("Uplift", V=-GAMMA_W * g.hw * g.B / 2, xV=2 * g.B / 3,
                            kind="G", role="uplift"))
        calc.table(["Action", "Type", "V [kN/m]", "x from toe [m]", "M [kNm/m]"],
                   [[c.name, c.kind, f"{from_base(c.V, 'kN/m'):.2f}",
                     f"{from_base(c.xV, 'm'):.3f}", f"{from_base(c.V * c.xV, 'kNm/m'):.2f}"]
                    for c in out], caption="Weights per metre run (G permanent, Q variable)")
        return out

    @staticmethod
    def _thrust(calc: Calculation | None, g: "_Wall", inp: dict, gphi: float,
                record: bool) -> tuple[list[Comp], dict]:
        phi_d = math.atan(math.tan(math.radians(inp["phi_b"])) / gphi)
        beta = math.radians(inp["beta"])
        delta = beta
        Ka = ka_coulomb(phi_d, beta, delta)
        cd = math.cos(delta)
        if calc is not None and record:
            calc.formula("φ'_d", "atan(tan φ'_k / γ_φ')", math.degrees(phi_d), "°",
                         "Design angle of shearing resistance (backfill)", dp=2)
            calc.formula("K_a", "cos²φ'_d / [cos δ (1 + √(sin(φ'_d+δ) sin(φ'_d−β) / "
                         "(cos δ cos β)))²]", Ka, "", "Coulomb active coefficient, δ = β",
                         ref="EN 1997-1 Annex C", dp=4)
        Ph, zP = g.earth_force(Ka * cd)
        out = [Comp("Active earth pressure", H=Ph, zH=zP, V=Ph * math.tan(delta), xV=g.B,
                    kind="G", role="thrust")]
        if inp["q"] > 0:
            pq = Ka * cd * inp["q"]
            out.append(Comp("Surcharge pressure", H=pq * g.hv, zH=g.hv / 2,
                            V=pq * g.hv * math.tan(delta), xV=g.B, kind="Q", role="thrust"))
        if g.hw > 0:
            out.append(Comp("Water pressure", H=GAMMA_W * g.hw**2 / 2, zH=g.hw / 3,
                            kind="G", role="water"))
        return out, {"phi_d": phi_d, "Ka": Ka}

    @staticmethod
    def _table(calc: Calculation, t: Totals, caption: str) -> None:
        rows = []
        for c, fH, fV, h, v in t.rows:
            rows.append([c.name, f"{fH:.2f}" if c.H else "", f"{from_base(h, 'kN/m'):.2f}"
                         if c.H else "", f"{from_base(c.zH, 'm'):.2f}" if c.H else "",
                         f"{fV:.2f}" if c.V else "", f"{from_base(v, 'kN/m'):.2f}"
                         if c.V else "", f"{from_base(c.xV, 'm'):.2f}" if c.V else ""])
        rows.append(["Total", "", f"{from_base(t.H, 'kN/m'):.2f}", "", "",
                     f"{from_base(t.V, 'kN/m'):.2f}", ""])
        calc.table(["Action", "γ_H", "H_d [kN/m]", "z [m]", "γ_V", "V_d [kN/m]", "x [m]"],
                   rows, caption=caption)

    @classmethod
    def _stability(cls, calc, g, inp, name, comps, gu, gf, gq, gphi, gc, gRv, gRh, gov,
                   info, seismic=False) -> None:
        # ---- sliding (vertical actions favourable)
        t = _factored(comps, gu, gf, gq)
        cls._table(calc, t, f"{name} — design actions (vertical actions favourable)")
        phi_fd = math.atan(math.tan(math.radians(inp["phi_f"])) / gphi)
        c_fd = inp["c_f"] / gc
        calc.formula("φ'_f,d", "atan(tan φ'_f,k / γ_φ')", math.degrees(phi_fd), "°",
                     "Design φ' of foundation soil", dp=2)
        tan_db = calc.formula("tan δ_d", "k tan φ'_f,d", inp["k_base"] * math.tan(phi_fd), "",
                              ref="EN 1997-1 6.5.3(10)", dp=4)
        Hd = calc.formula("H_d", "Σ H_d", t.H, "kN/m", "Design horizontal action")
        Rh = calc.formula("R_h,d", "V'_d tan δ_d / γ_R,h", max(t.V, 0) * tan_db / gRh, "kN/m",
                          "Sliding resistance", ref="Eq. 6.3a")
        calc.check(f"{name} sliding: H_d ≤ R_h,d", Hd, Rh, "kN/m", "EN 1997-1 6.5.3")
        # ---- bearing: two sub-cases
        Nq, Nc, Ng = bearing_factors(phi_fd)
        D = g.tb + g.df
        best = None
        for label, mv in (("max V", True), ("min V", False)):
            tt = _factored(comps, gu, gf, gq, max_vertical=mv)
            if tt.V <= 0:
                continue
            e = g.B / 2 - tt.x_R
            Bp = g.B - 2 * abs(e)
            if Bp <= 0:
                q_rd = 0.0
                q_ed = float("inf")
            else:
                ratio = 1 - tt.H / (tt.V + Bp * c_fd / math.tan(phi_fd))
                ratio = max(ratio, 0.0)
                iq, ig = ratio**2, ratio**3
                ic = iq - (1 - iq) / (Nc * math.tan(phi_fd))
                qv = g.gf * D
                q_rd = (c_fd * Nc * ic + qv * Nq * iq + 0.5 * g.gf * Bp * Ng * ig) / gRv
                q_ed = tt.V / Bp
            u = q_ed / q_rd if q_rd > 0 else float("inf")
            if best is None or u > best[0]:
                best = (u, label, tt, e, Bp, q_ed, q_rd, iq if Bp > 0 else 0,
                        ig if Bp > 0 else 0, ic if Bp > 0 else 0)
        u, label, tt, e, Bp, q_ed, q_rd, iq, ig, ic = best
        calc.text(f"Bearing — governing sub-case: vertical actions **{label}** "
                  f"(V_d = {from_base(tt.V, 'kN/m'):.1f} kN/m, H_d = "
                  f"{from_base(tt.H, 'kN/m'):.1f} kN/m).")
        calc.formula("e", "B/2 − (M_stb − M_dst)/V_d", e, "m",
                     "Eccentricity of resultant (+ towards toe)", dp=3)
        calc.check_limit(f"{name} eccentricity: |e| ≤ B/3", abs(e), g.B / 3, "m",
                         "EN 1997-1 6.5.4")
        calc.formula("B'", "B − 2|e|", Bp, "m", "Effective base width")
        calc.formula("N_q", "e^(π tan φ') tan²(45° + φ'/2)", Nq, "", f"Bearing factors: Nc = {Nc:.2f}, Nγ = {Ng:.2f}",
                     dp=2)
        calc.formula("i_q", "(1 − H/(V + B'c' cot φ'))^m, m = 2", iq, "",
                     f"iγ = {ig:.3f}, ic = {ic:.3f} (strip footing)", ref="D.4(7)", dp=3)
        calc.formula("q_Rd", "(c'N_c i_c + q'N_q i_q + 0.5γ'B'N_γ i_γ) / γ_R,v", q_rd, "kN/m²",
                     f"Design bearing resistance (q' = γ D, D = {from_base(D, 'm'):.2f} m)",
                     ref="EN 1997-1 Annex D.4")
        calc.formula("q_Ed", "V_d / B'", q_ed, "kN/m²", "Design bearing pressure")
        calc.check(f"{name} bearing: q_Ed ≤ q_Rd", q_ed, q_rd, "kN/m²", "EN 1997-1 6.5.2")
        if u > gov["util"]:
            gov.update({"util": u, "name": f"{name} ({label})",
                        "e": from_base(e, "m"), "B_eff": from_base(Bp, "m"),
                        "q_Ed": from_base(q_ed, "kN/m²"), "q_Rd": from_base(q_rd, "kN/m²"),
                        "R_x": from_base(tt.x_R, "m"),
                        "bearing": [[from_base(x, "m"), from_base(p, "kN/m²")]
                                    for x, p in g.base_pressure(tt)]})

    @classmethod
    def _seismic(cls, calc, g, inp, weights, gov) -> dict:
        calc.heading("Seismic design situation (EN 1998-5 §7.3 and Annex E)")
        alpha = calc.input("α", inp["ag"], "", "Design ground acceleration ratio a_g/g", dp=3)
        S = calc.input("S", inp["S"], "", "Soil factor", dp=2)
        r = calc.input("r", float(inp["r"]), "", "Displacement factor (Table 7.1)", dp=1)
        kh = calc.formula("k_h", "α S / r", alpha * S / r, "", ref="EN 1998-5 Eq. 7.1", dp=4)
        kv = calc.formula("k_v", "±0.5 k_h", 0.5 * kh, "", ref="Eq. 7.2", dp=4)
        gphi = 1.25
        phi_d = calc.formula("φ'_d", "atan(tan φ'_k / γ_φ'), γ_φ' = 1.25",
                             math.degrees(math.atan(math.tan(math.radians(inp["phi_b"]))
                                                    / gphi)), "°",
                             ref="EN 1998-5 3.1(3)", dp=2)
        phi_d = math.radians(phi_d)
        beta = math.radians(inp["beta"])
        delta = beta
        Ka = ka_coulomb(phi_d, beta, delta)
        if g.hw > 0:
            calc.warn("Seismic thrust is computed for dry backfill plus hydrostatic water "
                      "pressure (simplified; see EN 1998-5 E.6–E.8 for saturated soil).")
        result = None
        for sgn, label in ((-1, "k_v upwards"), (1, "k_v downwards")):
            kvs = sgn * kv
            theta = math.atan(kh / (1 + kvs))
            try:
                Kae = k_mononobe_okabe(phi_d, beta, delta, theta)
            except ValueError as exc:
                raise InputError(str(exc)) from exc
            E_tot = 0.5 * g.gb * (1 + kvs) * Kae * g.hv**2
            E_st = 0.5 * g.gb * Ka * g.hv**2
            dE = max(E_tot - E_st, 0.0)
            cd, sd = math.cos(delta), math.sin(delta)
            comps: list[Comp] = []
            for w in weights:
                if w.role == "weight" and w.kind == "G":
                    comps.append(Comp(w.name, V=w.V * (1 + kvs), xV=w.xV, kind="A"))
                    if not w.name.startswith("Soil over toe"):
                        comps.append(Comp(f"Inertia — {w.name.lower()}", H=kh * w.V, zH=w.zH,
                                          kind="A", role="inertia"))
                elif w.role == "weight" and w.kind == "Q":
                    comps.append(Comp(w.name + " (ψ2)", V=inp["psi2"] * w.V, xV=w.xV,
                                      kind="A"))
                elif w.role == "uplift":
                    comps.append(Comp(w.name, V=w.V, xV=w.xV, kind="A", role="uplift"))
            Ph, zP = g.earth_force(Ka * cd)
            comps.append(Comp("Static earth pressure", H=Ph, zH=zP, V=Ph * math.tan(delta),
                              xV=g.B, kind="A", role="thrust"))
            comps.append(Comp("Dynamic earth increment ΔE", H=dE * cd, zH=g.hv / 2,
                              V=dE * sd, xV=g.B, kind="A", role="thrust"))
            if inp["q"] > 0 and inp["psi2"] > 0:
                Eq = Kae * (1 + kvs) * inp["psi2"] * inp["q"] * g.hv
                comps.append(Comp("Surcharge ψ2q (seismic)", H=Eq * cd, zH=g.hv / 2,
                                  V=Eq * sd, xV=g.B, kind="A", role="thrust"))
            if g.hw > 0:
                comps.append(Comp("Water pressure", H=GAMMA_W * g.hw**2 / 2, zH=g.hw / 3,
                                  kind="A", role="water"))
            t = _factored(comps, 1, 1, 1)
            if result is None or t.H / max(t.V, 1e-9) > result["t"].H / max(result["t"].V, 1e-9):
                result = {"label": label, "kvs": kvs, "theta": theta, "Kae": Kae, "E": E_tot,
                          "dE": dE, "comps": comps, "t": t, "kh": kh, "Ka": Ka,
                          "phi_d": phi_d}
        calc.text(f"Both directions of the vertical seismic action were analysed; the "
                  f"governing case is **{result['label']}**.")
        calc.formula("θ", "atan(k_h / (1 ± k_v))", math.degrees(result["theta"]), "°",
                     ref="Eq. E.6", dp=2)
        calc.formula("K", "Mononobe-Okabe, β ≤ φ'_d − θ", result["Kae"], "",
                     "Seismic active earth pressure coefficient", ref="EN 1998-5 Eq. E.2",
                     dp=4)
        calc.formula("E_d", "½ γ (1 ± k_v) K h_v²", result["E"], "kN/m",
                     "Total design earth thrust (static + dynamic)", ref="Eq. E.1")
        calc.formula("ΔE_d", "E_d − ½ γ K_a h_v²", result["dE"], "kN/m",
                     "Dynamic increment, applied at mid-height of the virtual back",
                     ref="E.9(3)")
        cls._stability(calc, g, inp, "Seismic", result["comps"], 1, 1, 1, gphi, 1.25, 1.0, 1.0,
                       gov, result, seismic=True)
        t = result["t"]
        calc.check("Seismic overturning: M_dst ≤ M_stb", t.M_dst, t.M_stb, "kNm/m",
                   "EN 1998-5 7.3.1")
        return result

    # ------------------------------------------------------------ structure
    @classmethod
    def _structural(cls, calc, g, inp, weights, seis) -> None:
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd = fck / 1.5
        fyk = inp["fyk"]
        fyd = fyk / 1.15
        beta = math.radians(inp["beta"])
        phi = math.radians(inp["phi_b"])
        Ka_s = ka_coulomb(phi, beta, beta) * math.cos(beta)
        calc.heading("Structural design — STR (EN 1992-1-1)")
        calc.text(f"{inp['concrete']}: f_cd = {fcd:.2f} N/mm², f_yd = {fyd:.1f} N/mm². "
                  "Persistent design forces use set A1 (γ_G = 1.35, γ_Q = 1.50) with "
                  "characteristic soil strength; the seismic situation (if included) uses "
                  "γ = 1.0 and the Mononobe-Okabe thrust. The larger governs.")
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
        t_p = _factored(weights + thrust, 1.35, 1.0, 1.5, max_vertical=True)
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
        calc.formula("M_Ed", "max(persistent, seismic)", max(M, 0.0), "kNm/m",
                     f"persistent {from_base(M_p, 'kNm/m'):.1f}, seismic "
                     f"{from_base(M_s, 'kNm/m'):.1f} kNm/m")
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
                           res["As"] * 1e-3, "mm²/m", "6.1")
        calc.check_min("Minimum reinforcement: A_s,prov ≥ A_s,min", As_prov * 1e-3,
                       res["As_min"] * 1e-3, "mm²/m", "9.2.1.1")
        MRd, _ = section_capacity(b, d, As_prov, fcd, fyd)
        calc.formula("M_Rd", "A_s f_yd (d − 0.4x)", MRd / b, "kNm/m", "Moment resistance")
        calc.check("Bending: M_Ed ≤ M_Rd", Mt / b, MRd / b, "kNm/m", "6.1")
        shear_no_links(calc, b, d, As_prov, fck, 1.5, abs(V) * b, per_metre=True)
        calc.check_limit("Bar spacing: s ≤ min(3h, 400)", s, min(3 * h, 400.0), "mm",
                         "9.3.1.1(3)")

    # -------------------------------------------------------- 3D pressures
    @staticmethod
    def _pressure_profiles(g: "_Wall", inp: dict, seis) -> list[dict]:
        beta = math.radians(inp["beta"])
        Ka = ka_coulomb(math.radians(inp["phi_b"]), beta, beta) * math.cos(beta)
        zs = np.linspace(0, g.hv, 41)
        out = [{"name": "Active earth pressure (char.)", "key": "earth",
                "points": [[from_base(z, "m"), from_base(Ka * g.sigma_v(z), "kN/m²")]
                           for z in zs]}]
        if inp["q"] > 0:
            out.append({"name": "Surcharge pressure (char.)", "key": "surcharge",
                        "points": [[0, from_base(Ka * inp["q"], "kN/m²")],
                                   [from_base(g.hv, "m"), from_base(Ka * inp["q"], "kN/m²")]]})
        if g.hw > 0:
            out.append({"name": "Water pressure", "key": "water",
                        "points": [[from_base(z, "m"),
                                    from_base(GAMMA_W * max(g.hw - z, 0), "kN/m²")]
                                   for z in np.linspace(0, g.hv, 41)]})
        if seis:
            p = seis["dE"] * math.cos(beta) / g.hv
            out.append({"name": "Seismic increment ΔE (uniform equiv.)", "key": "seismic",
                        "points": [[0, from_base(p, "kN/m²")],
                                   [from_base(g.hv, "m"), from_base(p, "kN/m²")]]})
        return out


class _Wall:
    """Derived wall geometry (base units)."""

    def __init__(self, inp: dict) -> None:
        self.Hs, self.t_top, self.t_bot = inp["H_stem"], inp["t_top"], inp["t_bot"]
        self.tb, self.toe, self.heel = inp["t_base"], inp["toe"], inp["heel"]
        self.df, self.hw, self.L = inp["d_front"], inp["h_w"], inp["length"]
        self.beta = math.radians(inp["beta"])
        self.gb, self.gsat, self.gf, self.gc = (inp["gamma_b"], inp["gamma_sat"],
                                                inp["gamma_f"], inp["gamma_c"])
        self.B = self.toe + self.t_bot + self.heel
        self.x0 = self.toe + self.t_top   # stem back at top
        self.xb = self.toe + self.t_bot   # stem back at base
        self.hv = self.tb + self.Hs + (self.B - self.x0) * math.tan(self.beta)
        self.fig_index = 0

    def zs(self, x: float) -> float:
        return self.tb + self.Hs + max(x - self.x0, 0) * math.tan(self.beta)

    @property
    def stem_poly(self):
        return [(self.toe, self.tb), (self.xb, self.tb), (self.x0, self.tb + self.Hs),
                (self.toe, self.tb + self.Hs)]

    @property
    def base_poly(self):
        return [(0, 0), (self.B, 0), (self.B, self.tb), (0, self.tb)]

    @property
    def heel_soil_poly(self):
        return [(self.xb, self.tb), (self.B, self.tb), (self.B, self.zs(self.B)),
                (self.x0, self.tb + self.Hs)]

    @property
    def toe_soil_poly(self):
        return [(0, self.tb), (self.toe, self.tb), (self.toe, self.tb + self.df),
                (0, self.tb + self.df)]

    def sigma_v(self, z: float) -> float:
        """Effective vertical stress on the virtual back at height z."""
        depth = self.hv - z
        if self.hw > 0 and z < self.hw:
            dw = self.hv - self.hw
            return self.gb * dw + (self.gsat - GAMMA_W) * (depth - dw)
        return self.gb * depth

    def earth_force(self, K: float) -> tuple[float, float]:
        """Horizontal earth thrust K·σ'v on the virtual back and its height."""
        zk = sorted({0.0, min(self.hw, self.hv), self.hv})
        F = M = 0.0
        for z1, z2 in zip(zk[:-1], zk[1:]):
            f, zc = linear_resultant(z1, K * self.sigma_v(z1), z2, K * self.sigma_v(z2))
            F += f
            M += f * zc
        return F, (M / F if F else self.hv / 3)

    def base_pressure(self, t: Totals) -> list[tuple[float, float]]:
        """Linear (no tension) contact pressure q(x) for the given design totals."""
        V, xr, B = t.V, t.x_R, self.B
        e = B / 2 - xr
        xs = np.linspace(0, B, 41)
        if abs(e) <= B / 6:
            q = V / B * (1 + 12 * e * (B / 2 - xs) / B**2)
        elif e > 0:
            Lc = 3 * xr
            q = np.where(xs < Lc, 2 * V / Lc * (1 - xs / Lc), 0.0) if Lc > 0 else 0 * xs
        else:
            Lc = 3 * (B - xr)
            q = np.where(xs > B - Lc, 2 * V / Lc * (1 - (B - xs) / Lc), 0.0)
        return list(zip(xs.tolist(), np.maximum(q, 0).tolist()))

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

    def to_dict(self) -> dict:
        m = lambda v: from_base(v, "m")  # noqa: E731
        return {"H_stem": m(self.Hs), "t_top": m(self.t_top), "t_bot": m(self.t_bot),
                "t_base": m(self.tb), "toe": m(self.toe), "heel": m(self.heel), "B": m(self.B),
                "beta": math.degrees(self.beta), "h_w": m(self.hw), "d_front": m(self.df),
                "h_v": m(self.hv), "length": m(self.L)}
