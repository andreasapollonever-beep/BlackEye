"""Mass concrete / masonry gravity retaining wall — EN 1997-1, EN 1998-5, EN 1992-1-1 §12."""

from __future__ import annotations

import math

from ..core import Calculation, Field, InputError, register
from ..core.units import from_base
from ..design.geotech import clip_z, ka_coulomb, poly_props  # noqa: F401
from ..design.walls import GAMMA_W, WallGeometry, WallModule, soil_fields

CONCRETE = ["C12/15", "C16/20", "C20/25", "C25/30", "C30/37"]


class GravityGeometry(WallGeometry):
    def __init__(self, inp: dict) -> None:
        super().__init__(inp)
        self.H, self.bt, self.Bw = inp["H"], inp["b_top"], inp["B_body"]
        self.f = inp["front_batter"]
        self.tb = inp["t_footing"]
        self.ptoe = inp["toe"] if self.tb > 0 else 0.0
        self.pheel = inp["heel"] if self.tb > 0 else 0.0
        self.df = inp["d_front"]
        self.B = self.ptoe + self.Bw + self.pheel
        self.top = self.tb + self.H
        self.x_front = self.ptoe
        self.x0 = self.ptoe + self.f + self.bt
        self.xbb = self.ptoe + self.Bw
        body = [(self.ptoe, self.tb), (self.xbb, self.tb), (self.x0, self.top),
                (self.ptoe + self.f, self.top)]
        self.body = body
        self.concrete = [("Wall body", body)]
        if self.tb > 0:
            self.concrete.append(("Footing", [(0, 0), (self.B, 0), (self.B, self.tb),
                                              (0, self.tb)]))
        self.finish()

    def x_faces(self, z: float) -> tuple[float, float]:
        """Front and back face x at level z (within the body)."""
        t = (z - self.tb) / self.H
        return self.ptoe + self.f * t, self.xbb + (self.x0 - self.xbb) * t


@register
class GravityWallEC7(WallModule):
    id = "ec7_gravity_wall"
    title = "Gravity retaining wall"
    category = "Geotechnical"
    standard = "EN 1997-1, EN 1998-5, EN 1992-1-1 §12"
    description = ("Mass concrete or masonry gravity wall with optional footing: Coulomb and "
                   "Mononobe-Okabe thrust, groundwater, sliding, overturning, bearing and "
                   "plain-concrete section checks. Interactive 3D model.")

    fields = [
        Field("H", "Wall height (above footing)", "m", 3.0, min=0.5, max=10, group="Geometry"),
        Field("b_top", "Top width", "m", 0.50, min=0.2, group="Geometry"),
        Field("B_body", "Width at base of wall body", "m", 1.90, min=0.3, group="Geometry"),
        Field("front_batter", "Front face batter (horizontal offset)", "m", 0.20, min=0,
              group="Geometry", help="0 = vertical front face."),
        Field("t_footing", "Footing thickness (0 = no footing)", "m", 0.40, min=0,
              group="Geometry"),
        Field("toe", "Footing toe projection", "m", 0.50, min=0, group="Geometry"),
        Field("heel", "Footing heel projection", "m", 0.30, min=0, group="Geometry"),
        Field("d_front", "Soil depth over toe", "m", 0.50, min=0, group="Geometry"),
        Field("length", "Wall length (3D view)", "m", 8.0, min=1, group="Geometry"),
    ] + soil_fields() + [
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C20/25",
              group="Material"),
        Field("gamma_c", "Unit weight of wall", "kN/m³", 24.0, min=15, group="Material",
              help="24 plain concrete, 22 stone masonry, 20 gabions (approx.)."),
    ]

    @classmethod
    def make_geometry(cls, inp: dict) -> GravityGeometry:
        if inp["B_body"] < inp["front_batter"] + inp["b_top"] - 1e-6:
            raise InputError("Base width of the wall body must be ≥ front batter + top width",
                             "B_body")
        return GravityGeometry(inp)

    @classmethod
    def record_geometry(cls, calc: Calculation, g: GravityGeometry, inp: dict) -> None:
        calc.heading("Geometry")
        calc.input("H", g.H, "m", "Wall height")
        calc.input("b_top", g.bt, "m", "Top width")
        calc.input("B_w", g.Bw, "m", "Width at base of wall body")
        calc.input("f", g.f, "m", "Front face batter")
        if g.tb > 0:
            calc.input("t_f", g.tb, "m", "Footing thickness")
            calc.formula("B", "b_toe + B_w + b_heel", g.B, "m", "Footing width")
        else:
            calc.formula("B", "B_w", g.B, "m", "Base width")
        calc.input("β", inp["beta"], "°", "Backfill slope")
        calc.formula("h_v", "t_f + H + (B − x_back,top) tan β", g.hv, "m",
                     "Height of virtual back (through rear edge of base)")

    @classmethod
    def structural(cls, calc, g: GravityGeometry, inp, weights, seis, gov=None) -> None:
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd = calc.formula("f_cd,pl", "α_cc,pl f_ck / γ_c", 0.8 * fck / 1.5, "N/mm²",
                           "Design compressive strength, plain concrete", ref="EN 1992-1-1 12.3.1")
        calc.heading("Wall body — plain concrete sections (EN 1992-1-1 §12)")
        calc.text("Sections through the wall body are checked at the base of the body and at "
                  "mid-height for the persistent STR case (γ_G = 1.35, γ_Q = 1.50). Earth "
                  "pressure acts on the vertical plane through the back face at each level.")
        beta = math.radians(inp["beta"])
        Kh = ka_coulomb(math.radians(inp["phi_b"]), beta, beta) * math.cos(beta)
        for frac, label in ((0.0, "base of wall body"), (0.5, "mid-height")):
            z = g.tb + frac * g.H
            xf, xb = g.x_faces(z)
            w = xb - xf
            above = clip_z(g.body, z, keep_below=False)
            A, cx, _ = poly_props(above)
            N = 1.35 * inp["gamma_c"] * A
            Mst = N * (cx - xf)
            # soil resting on the back batter above this level
            wedge = [(xb, z), (xb, g.zs(xb)), (g.x0, g.top)] if xb > g.x0 + 1e-6 else []
            if wedge:
                Aw, cxw, _ = poly_props(wedge)
                Nw = 1.35 * g.gb * Aw
                N += Nw
                Mst += Nw * (cxw - xf)
            h = g.zs(xb) - z
            Ph = 1.35 * 0.5 * Kh * g.gb * h**2 + 1.5 * Kh * inp["q"] * h
            Mdst = 1.35 * 0.5 * Kh * g.gb * h**2 * h / 3 + 1.5 * Kh * inp["q"] * h**2 / 2
            if g.hw > z:
                hwz = g.hw - z
                Ph += 1.35 * GAMMA_W * hwz**2 / 2
                Mdst += 1.35 * GAMMA_W * hwz**3 / 6
            calc.heading(calc.tr("Section at {where} (z = {z:.2f} m)", where=calc.tr(label),
                                 z=from_base(z, "m")), 2)
            calc.formula("b_w", "x_back − x_front", w, "m", "Section width")
            calc.formula("N_Ed", "1.35 Σ W", N, "kN/m", "Axial force (weights above section)")
            calc.formula("H_Ed", "1.35 P_a + 1.5 P_q (+ water)", Ph, "kN/m", "Shear force")
            e = calc.formula("e", "b_w/2 − (M_stb − M_dst)/N_Ed", w / 2 - (Mst - Mdst) / N,
                             "m", "Eccentricity of the resultant", dp=3)
            NRd = calc.formula("N_Rd", "f_cd,pl b_w (1 − 2e/b_w)",
                               max(fcd * w * (1 - 2 * abs(e) / w), 0.0), "kN/m",
                               ref="EN 1992-1-1 Eq. 12.10")
            calc.check(calc.tr("Body at {where}: N_Ed ≤ N_Rd", where=calc.tr(label)), N, NRd,
                       "kN/m", "12.6.1",
                       hint="Widen the wall body (larger base width or top width).")
            calc.check_limit(calc.tr("Body at {where}: |e| ≤ 0.3 b_w", where=calc.tr(label)),
                             abs(e), 0.3 * w, "m", "12.6.5.1",
                             hint="Increase the back batter so that the resultant stays near "
                                  "the centre of the section.")
            sliding_R = N * math.tan(math.radians(35))
            calc.check(calc.tr("Body at {where}: H_Ed ≤ N_Ed tan 35° (joint)",
                               where=calc.tr(label)), Ph, sliding_R, "kN/m", "12.6.3",
                       hint="Increase the wall weight or provide shear keys at joints.")
