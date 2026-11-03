"""Gabion retaining wall — stacked courses of stone-filled wire baskets.

Global stability (sliding, overturning, bearing, seismic) comes from the shared wall engine
(EN 1997-1, EN 1998-5).  In addition every joint between courses is checked for sliding,
eccentricity and compression with the earth pressure on the virtual back of the courses above.
"""

from __future__ import annotations

import math

from ..core import Calculation, Field, InputError, register
from ..design.geotech import clip_z, ka_coulomb, poly_props
from ..design.walls import GAMMA_W, WallGeometry, WallModule, soil_fields

STONE = "#9c9486"
HINT_JOINT = ("Widen the courses above this joint or step the courses back into the "
              "backfill (larger set-back).")


def clip_x(pts, xc: float, keep_left: bool):
    """Clip a polygon by the vertical line x = xc (reuses clip_z on swapped coordinates)."""
    sw = [(z, x) for x, z in pts]
    out = clip_z(sw, xc, keep_below=keep_left)
    return [(x, z) for z, x in out]


class GabionGeometry(WallGeometry):
    def __init__(self, inp: dict) -> None:
        super().__init__(inp)
        rows = inp["courses"]
        x, z = 0.0, 0.0
        self.courses = []  # (x_front, x_back, z_bottom, z_top)
        for i, r in enumerate(rows):
            if i > 0:
                x += r["setback"]
            self.courses.append((x, x + r["b"], z, z + r["h"]))
            z += r["h"]
        self.B = self.courses[0][1]
        self.tb = 0.0
        self.top = z
        self.x_front = 0.0
        self.x0 = self.courses[-1][1]
        self.xbb = self.B
        self.df = inp["d_front"]
        self.concrete = [(f"Course {i + 1}", [(a, zb), (b, zb), (b, zt), (a, zt)])
                         for i, (a, b, zb, zt) in enumerate(self.courses)]
        self.finish()

    @property
    def back_face(self) -> list:
        pts = []
        for a, b, zb, zt in reversed(self.courses):
            pts += [(b, zt), (b, zb)]
        out = []
        for p in pts:
            if not out or abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > 1e-9:
                out.append(p)
        return out


@register
class GabionWallEC7(WallModule):
    id = "ec7_gabion_wall"
    title = "Gabion wall"
    category = "Geotechnical"
    standard = "EN 1997-1, EN 1998-5, EN 10223-3"
    description = ("Gravity wall of stacked gabion courses with set-backs: Coulomb and "
                   "Mononobe-Okabe thrust, sliding, overturning, bearing and the stability of "
                   "every joint between courses. Interactive 3D model.")

    fields = [
        Field("courses", "Gabion courses (from the bottom up)", kind="table", group="Geometry",
              default=[{"b": 3.0, "h": 1.0, "setback": 0.0},
                       {"b": 2.5, "h": 1.0, "setback": 0.25},
                       {"b": 1.5, "h": 1.0, "setback": 0.25}],
              columns=[Field("b", "Width", "m", 1.0, min=0.5),
                       Field("h", "Height", "m", 1.0, min=0.3, max=1.0),
                       Field("setback", "Front set-back from the course below", "m", 0.0,
                             min=0)],
              help="Standard baskets are 0.5 m or 1.0 m high and 1.0–1.5 m wide modules."),
        Field("d_front", "Embedment of the base below ground in front", "m", 0.50, min=0,
              group="Geometry"),
        Field("length", "Wall length (3D view)", "m", 8.0, min=1, group="Geometry"),
    ] + soil_fields() + [
        Field("gamma_s", "Unit weight of the stone", "kN/m³", 26.0, min=18, max=30,
              group="Gabions", help="Limestone 24–26, basalt/granite 26–28 kN/m³."),
        Field("n", "Porosity of the fill n", "", 0.35, min=0.25, max=0.45, group="Gabions",
              help="0.30–0.40 for hand-placed, well-graded stone."),
        Field("phi_j", "Friction angle between courses", "°", 35.0, min=20, max=45,
              group="Gabions", help="Stone-on-stone contact through the mesh; 30–40°."),
    ]

    @classmethod
    def make_geometry(cls, inp: dict) -> GabionGeometry:
        rows = inp["courses"]
        if not rows:
            raise InputError("Add at least one gabion course", "courses")
        x = 0.0
        for i, r in enumerate(rows):
            if i == 0:
                xb = r["b"]
                continue
            x += r["setback"]
            if x >= xb - 1e-6:
                raise InputError("Each course must sit on the course below (set-back smaller "
                                 "than the width below)", "courses")
            xb = x + r["b"]
        return GabionGeometry(inp)

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        inp = dict(inp)
        inp["gamma_c"] = inp["gamma_s"] * (1 - inp["n"])
        super().run(calc, inp)
        if calc.model3d:
            for o in calc.model3d["objects"]:
                if o.get("layer") == "concrete":
                    o["color"] = STONE

    @classmethod
    def record_geometry(cls, calc: Calculation, g: GabionGeometry, inp: dict) -> None:
        calc.heading("Geometry and gabion fill")
        calc.table(["Course", "x_front [m]", "Width [m]", "Height [m]"],
                   [[str(i + 1), f"{a / 1000:.2f}", f"{(b - a) / 1000:.2f}",
                     f"{(zt - zb) / 1000:.2f}"] for i, (a, b, zb, zt) in enumerate(g.courses)],
                   caption="Courses from the bottom up (x from the front edge of the base)")
        calc.formula("H", "Σ h_i", g.top, "m", "Wall height")
        calc.formula("B", "b_1", g.B, "m", "Base width")
        calc.input("γ_s", inp["gamma_s"], "kN/m³", "Unit weight of the stone")
        calc.input("n", inp["n"], "", "Porosity of the fill", dp=2)
        calc.formula("γ_g", "γ_s (1 − n)", inp["gamma_c"], "kN/m³", "Unit weight of the gabions",
                     dp=2)
        calc.input("β", inp["beta"], "°", "Backfill slope")
        calc.formula("h_v", "H + (B − x_back,top) tan β", g.hv, "m",
                     "Height of virtual back (through rear edge of base)")

    @classmethod
    def structural(cls, calc, g: GabionGeometry, inp, weights, seis, gov=None) -> None:
        calc.heading("Internal stability — joints between courses")
        calc.text("At each joint the courses above act as a gravity wall on the virtual back "
                  "through the rear edge of the course below (STR: γ_G = 1.35, γ_Q = 1.50 on "
                  "the thrust; weights favourable 1.0 for sliding and eccentricity).")
        beta = math.radians(inp["beta"])
        Ka = ka_coulomb(math.radians(inp["phi_b"]), beta, beta)
        Kh, Kv = Ka * math.cos(beta), Ka * math.sin(beta)
        gg = inp["gamma_c"]
        mu = math.tan(math.radians(inp["phi_j"]))
        soil = g.back_soil
        for k in range(1, len(g.courses)):
            a_k, b_k, _, zj = g.courses[k - 1]
            above = [c for c in g.courses[k:]]
            W = Mw = 0.0
            for a, b, zb, zt in above:
                w = gg * (b - a) * (zt - zb)
                W += w
                Mw += w * ((a + b) / 2 - a_k)
            ws = clip_x(clip_z(soil, zj, keep_below=False), b_k, keep_left=True)
            A, cx, _ = poly_props(ws) if len(ws) >= 3 else (0.0, 0.0, 0.0)
            Ws = g.gb * A
            W += Ws
            Mw += Ws * (cx - a_k)
            h = g.zs(b_k) - zj
            P_e, P_q = 0.5 * Kh * g.gb * h**2, Kh * inp["q"] * h
            V_e, V_q = 0.5 * Kv * g.gb * h**2, Kv * inp["q"] * h
            Hd = 1.35 * P_e + 1.5 * P_q
            Md = 1.35 * P_e * h / 3 + 1.5 * P_q * h / 2
            if g.hw > zj:
                hw = g.hw - zj
                Hd += 1.35 * GAMMA_W * hw**2 / 2
                Md += 1.35 * GAMMA_W * hw**3 / 6
            bw = b_k - a_k
            N = W + 1.35 * V_e + 1.5 * V_q
            Ms = Mw + (1.35 * V_e + 1.5 * V_q) * bw
            Nf = W + V_e  # favourable: weights 1.0, no variable
            calc.heading(calc.tr("Joint on top of course {k} (z = {z:.2f} m)", k=k,
                                 z=zj / 1000), 2)
            calc.formula("b_j", "width of course below", bw, "m", "Joint width")
            calc.formula("h", "height of the virtual back above the joint", h, "m")
            calc.formula("H_Ed", "1.35 P_a + 1.5 P_q (+ water)", Hd, "kN/m",
                         "Shear force on the joint")
            calc.formula("N_Ed", "Σ W + P_a,v", N, "kN/m", "Normal force on the joint")
            calc.check(calc.tr("Joint {k} sliding: H_Ed ≤ N_fav tan φ_j", k=k), Hd, Nf * mu,
                       "kN/m", "EN 1997-1 6.5.3", hint=HINT_JOINT)
            e = bw / 2 - (Ms - Md) / N
            calc.formula("e", "b_j/2 − (M_stb − M_dst)/N_Ed", e, "m",
                         "Eccentricity of the resultant", dp=3)
            calc.check_limit(calc.tr("Joint {k} eccentricity: |e| ≤ b_j/3", k=k), abs(e),
                             bw / 3, "m", "EN 1997-1 6.5.4", hint=HINT_JOINT)
            sig = N / max(bw - 2 * abs(e), 1e-6)
            calc.formula("σ_max", "N_Ed / (b_j − 2e)", sig, "kN/m²",
                         "Mean compressive stress on the effective joint width")
        calc.note("Mesh, lacing and stone grading per EN 10223-3; a geotextile filter between "
                  "backfill and gabions prevents loss of fines.")
