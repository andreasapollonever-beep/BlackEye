"""Slope stability — Bishop's simplified method of slices (EN 1997-1 §11, EN 1998-5 §4.1.3).

Geometry (metres in the UI, mm internally): the crest is on the left at
height H, the slope face descends to the toe at (L_s, 0), and the slip mass
moves to the right.  A grid of circle centres is searched, then refined.
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..design.annex import get_annex
from ..report.scene3d import PALETTE, Scene3D, heat_color
from ..report.svg import slope_section

HINT_SLOPE = ("Flatten the slope (smaller angle), reduce the surcharge or move it away from "
              "the crest, lower the groundwater (drainage) or add a toe berm / retaining "
              "structure.")


class SlopeModel:
    def __init__(self, inp: dict) -> None:
        self.H = inp["H"]
        self.beta = math.radians(inp["slope"])
        self.Ls = self.H / math.tan(self.beta)
        self.gamma = inp["gamma"]
        self.ru = inp["ru"]
        self.q, self.q_off, self.q_w = inp["q"], inp["q_offset"], inp["q_width"]
        self.y_min = -inp["depth_firm"]
        self.x_left = -max(3 * self.H, self.q_off + self.q_w + self.H)
        self.x_right = self.Ls + 2.5 * self.H
        # nails / anchors: (x_head, y_head, dx, dy, L, T_d per m, bond per m per m)
        self.nails = []
        for r in inp.get("nails") or []:
            zh = min(max(r["z"], 0.0), self.H)
            a = math.radians(r["angle"])
            self.nails.append((self.Ls * (1 - zh / self.H), zh, -math.cos(a), -math.sin(a),
                               r["L"], r["Td"] / r["sh"], r["bond"] / r["sh"]))

    def nail_force(self, xc, yc, R):
        """Σ T·r / R of the nails crossing the circle (per metre of slope)."""
        tot, used = 0.0, []
        for xh, yh, dx, dy, L, Td, bond in self.nails:
            fx, fy = xh - xc, yh - yc
            b = 2 * (fx * dx + fy * dy)
            cc = fx * fx + fy * fy - R * R
            disc = b * b - 4 * cc
            if disc <= 0 or cc >= 0:  # head must lie inside the circle (in the moving mass)
                continue
            s_int = (-b + math.sqrt(disc)) / 2
            if s_int <= 0 or s_int >= L:
                continue
            T = min(Td, bond * (L - s_int))
            lever = abs(fx * dy - fy * dx)
            tot += T * lever / R
            used.append(T)
        return tot, used

    def ground(self, x):
        x = np.asarray(x, dtype=float)
        return np.where(x <= 0, self.H, np.where(x >= self.Ls, 0.0,
                                                 self.H * (1 - x / self.Ls)))

    def surcharge(self, x):
        x = np.asarray(x, dtype=float)
        return np.where((x <= -self.q_off) & (x >= -self.q_off - self.q_w), self.q, 0.0)

    def factor(self, xc, yc, R, tanphi, c, gq=1.0, kh=0.0, kv=0.0, n=40):
        """Bishop factor of safety of one circle, or None if the circle is invalid."""
        xs = np.linspace(xc - R, xc + R, 400)
        ys = yc - np.sqrt(np.maximum(R**2 - (xs - xc) ** 2, 0))
        inside = self.ground(xs) - ys > 1e-6
        if not inside.any():
            return None
        idx = np.where(inside)[0]
        if (np.diff(idx) > 1).any():  # must be one contiguous mass
            return None
        x1, x2 = xs[idx[0]], xs[idx[-1]]
        if x1 <= self.x_left or x2 >= self.x_right or (yc - R) < self.y_min - 1e-6:
            return None
        edges = np.linspace(x1, x2, n + 1)
        xm = 0.5 * (edges[1:] + edges[:-1])
        b = edges[1] - edges[0]
        yb = yc - np.sqrt(np.maximum(R**2 - (xm - xc) ** 2, 0))
        hgt = np.maximum(self.ground(xm) - yb, 0)
        if hgt.max() < 500.0:  # ignore skin slips shallower than 0.5 m
            return None
        W = self.gamma * b * hgt + gq * self.surcharge(xm) * b
        sina = (xc - xm) / R
        cosa = np.sqrt(np.maximum(1 - sina**2, 1e-9))
        u = self.ru * self.gamma * hgt
        Wv = W * (1 - kv)
        drive = np.sum(Wv * sina) + np.sum(kh * W * (yc - (yb + hgt / 2)) / R)
        if drive <= 0:
            return None
        num0 = c * b + np.maximum(Wv - u * b, 0) * tanphi
        Tn, used = self.nail_force(xc, yc, R) if self.nails else (0.0, [])
        F = 1.5
        for _ in range(60):
            m = cosa * (1 + sina / cosa * tanphi / F)
            m = np.maximum(m, 0.2)  # guard against negative mα at steep exit
            Fn = (np.sum(num0 / m) + Tn) / drive
            if abs(Fn - F) < 1e-5:
                F = Fn
                break
            F = Fn
        return {"F": float(F), "xc": xc, "yc": yc, "R": R, "x1": x1, "x2": x2,
                "edges": edges, "yb": yb, "W": float(W.sum()), "T": used}

    def search(self, tanphi, c, gq=1.0, kh=0.0, kv=0.0):
        H, Ls = self.H, self.Ls
        best, grid = None, []

        def scan(xcs, ycs, nr=14, keep=False):
            nonlocal best
            for xc in xcs:
                for yc in ycs:
                    Rmax = yc - self.y_min
                    # shortest distance to the slope face line
                    nx, ny = H, Ls
                    dist = abs(nx * xc + ny * yc - H * Ls) / math.hypot(nx, ny)
                    Rmin = max(dist + 300.0, 600.0)
                    if Rmax <= Rmin:
                        continue
                    fmin = None
                    for R in np.linspace(Rmin, Rmax, nr):
                        r = self.factor(xc, yc, R, tanphi, c, gq, kh, kv)
                        if r and (best is None or r["F"] < best["F"]):
                            best = r
                        if r and (fmin is None or r["F"] < fmin):
                            fmin = r["F"]
                    if keep and fmin is not None:
                        grid.append((xc, yc, fmin))

        scan(np.linspace(-0.6 * H, Ls + 0.6 * H, 13), np.linspace(H + 0.3 * H, H + 2.2 * H, 11),
             keep=True)
        if best:
            for _ in range(2):  # local refinement
                dx = 0.25 * H
                scan(np.linspace(best["xc"] - dx, best["xc"] + dx, 7),
                     np.linspace(best["yc"] - dx, best["yc"] + dx, 7), nr=20)
        return best, grid


@register
class SlopeStabilityEC7(DesignModule):
    id = "ec7_slope_stability"
    title = "Slope stability (Bishop)"
    category = "Geotechnical"
    has_3d = True
    uses_annex = True
    standard = "EN 1997-1 §11, EN 1998-5 §4.1.3"
    description = ("Circular slip surfaces by Bishop's simplified method with automatic search "
                   "of the critical circle; pore pressure ratio, crest surcharge and seismic "
                   "pseudo-static action. Interactive 3D model.")

    fields = [
        Field("H", "Slope height", "m", 6.0, min=1, max=50, group="Geometry"),
        Field("slope", "Slope angle", "°", 30.0, min=5, max=75, group="Geometry",
              help="Angle of the slope face to the horizontal (1:√3 ≈ 30°, 1:2 ≈ 26.6°)."),
        Field("depth_firm", "Depth to firm stratum below toe", "m", 6.0, min=0, group="Geometry",
              help="Slip circles are not allowed below this level."),
        Field("length", "Slope length (3D view)", "m", 20.0, min=4, group="Geometry"),
        Field("phi", "Soil φ'k", "°", 30.0, min=0, max=45, group="Soil"),
        Field("c", "Soil c'k", "kN/m²", 8.0, min=0, group="Soil"),
        Field("gamma", "Soil γ", "kN/m³", 19.0, min=10, group="Soil"),
        Field("ru", "Pore pressure ratio r_u", "", 0.0, min=0, max=0.6, group="Soil",
              help="u = r_u·γ·h. 0 = dry/drained, 0.2–0.3 typical with a high water table."),
        Field("q", "Crest surcharge (variable)", "kN/m²", 10.0, min=0, group="Loads"),
        Field("q_offset", "Distance of surcharge from crest", "m", 1.0, min=0, group="Loads"),
        Field("q_width", "Surcharge width", "m", 5.0, min=0, group="Loads"),
        Field("nails", "Soil nails / anchors (optional)", kind="table", group="Reinforcement",
              default=[], columns=[
                  Field("z", "Head height above the toe", "m", 3.0, min=0),
                  Field("angle", "Inclination below horizontal", "°", 15.0, min=0, max=60),
                  Field("L", "Length", "m", 8.0, min=1),
                  Field("sh", "Horizontal spacing", "m", 1.5, min=0.3),
                  Field("Td", "Design tensile resistance T_d", "kN", 150.0, min=1),
                  Field("bond", "Design pull-out resistance per metre", "kN/m", 40.0, min=1)],
              help="Leave empty for an unreinforced slope. Each row adds T = min(T_d, bond × "
                   "length behind the slip surface) with its lever arm about the circle centre."),
        Field("seismic", "Include seismic (pseudo-static)", kind="bool", default=True,
              group="Seismic"),
        Field("ag", "Design ground acceleration αgR·γI", "", 0.16, min=0, max=0.6,
              group="Seismic",
              help="In g (a_gR × γI). Pick a zone with the buttons of the selected National "
                   "Annex."),
        Field("S", "Soil factor S", "", 1.2, min=1.0, max=1.8, group="Seismic"),
        Field("ST", "Topography factor S_T", "", 1.0, min=1.0, max=1.4, group="Seismic",
              help="EN 1998-5 Annex A: 1.0 for slopes < 15°, up to 1.2–1.4 for high ridges."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        sm = SlopeModel(inp)
        if inp["phi"] <= 0 and inp["c"] <= 0:
            raise InputError("The soil needs strength: give φ' > 0 or c' > 0", "phi")
        calc.heading("Geometry and soil")
        calc.input("H", sm.H, "m", "Slope height")
        calc.input("β", inp["slope"], "°", "Slope angle")
        calc.formula("L_s", "H / tan β", sm.Ls, "m", "Horizontal length of slope face")
        calc.input("φ'_k", inp["phi"], "°", "Angle of shearing resistance")
        calc.input("c'_k", inp["c"], "kN/m²", "Effective cohesion")
        calc.input("γ", inp["gamma"], "kN/m³", "Unit weight")
        calc.input("r_u", inp["ru"], "", "Pore pressure ratio", dp=2)
        if inp["q"] > 0:
            calc.input("q_k", inp["q"], "kN/m²", "Crest surcharge")
        fig_index = len(calc.items)
        calc.heading("Method")
        calc.text("Bishop's simplified method: F = Σ[c'b + (W − ub) tan φ'] / m_α / "
                  "Σ W sin α, with m_α = cos α (1 + tan α tan φ' / F). A grid of centres "
                  "is searched with several radii per centre and then refined locally.")

        tphi = math.tan(math.radians(inp["phi"]))
        cases = []
        calc.heading("Characteristic factor of safety (information)")
        rk, grid = sm.search(tphi, inp["c"], 1.0)
        if not rk:
            raise InputError("No valid slip circle found — check the geometry", "H")
        calc.formula("F_k", "min F (characteristic parameters)", rk["F"], "",
                     "Lowest factor of safety", dp=3)
        cases.append(("char", rk))

        na = get_annex(calc.project.annex)
        if na.slope_mode == "DA2":
            gG, gQ = na.combos["DA2"][0], na.combos["DA2"][2]
            calc.heading("Persistent design situation — GEO (Design Approach 2)")
            calc.text("Design Approach 2 (A1 + M1 + R2), factors applied to the effects of "
                      "actions: E_d = γ_G E_G,k + γ_Q E_Q,k and R_d = R_k / γ_R,e with "
                      "γ_G = {g}, γ_Q = {q}, γ_R,e = {re}. Characteristic soil strength is "
                      "used; the surcharge is scaled by γ_Q/γ_G so that F' = R_k/(E_G,k + "
                      "(γ_Q/γ_G) E_Q,k), and F_d = F' / (γ_G γ_R,e) ≥ 1.0.",
                      g=gG, q=gQ, re=na.slope_gRe)
            rd0, _ = sm.search(tphi, inp["c"], gQ / gG)
            calc.formula("F'", "R_k / (E_G,k + γ_Q/γ_G E_Q,k)", rd0["F"], "", dp=3)
            rd = dict(rd0, F=rd0["F"] / (gG * na.slope_gRe))
            calc.formula("F_d", "F' / (γ_G γ_R,e)", rd["F"], "", "Over-design factor",
                         ref="EN 1997-1 2.4.7.3 / A.14 (NA)", dp=3)
        else:
            calc.heading("Persistent design situation — GEO (DA1-C2 / DA3: A2 + M2)")
            gp, gcc, gq = na.slope_factors
            calc.text("Design parameters: tan φ'_d = tan φ'_k / {gp}, c'_d = c'_k / {gc}, "
                      "surcharge × {gq}. The slope is stable when the design factor F_d ≥ 1.0 "
                      "(over-design factor, EN 1997-1 2.4.7.3).", gp=gp, gc=gcc, gq=gq)
            rd, _ = sm.search(tphi / gp, inp["c"] / gcc, gq)
            calc.formula("F_d", "min F (design parameters)", rd["F"], "", "Over-design factor",
                         dp=3)
        calc.check("Persistent: E_d ≤ R_d (1 ≤ F_d)", 1.0, rd["F"], "", "EN 1997-1 Eq. 2.5",
                   hint=HINT_SLOPE)
        cases.append(("design", rd))

        rs = None
        if inp["seismic"] and inp["ag"] > 0:
            calc.heading("Seismic design situation (EN 1998-5 §4.1.3.3)")
            kh = calc.formula("k_h", "0.5 α S S_T", 0.5 * inp["ag"] * inp["S"] * inp["ST"], "",
                              ref="EN 1998-5 Eq. 4.1", dp=4)
            kv = calc.formula("k_v", "±0.5 k_h", 0.5 * kh, "", ref="Eq. 4.2", dp=4)
            sp, sc_ = na.seismic_gamma_phi, na.seismic_gamma_c
            calc.text("Soil strength with γ_φ' = {gp}, γ_c' = {gc}; surcharge × ψ2 = 0.3; both "
                      "signs of k_v analysed.", gp=sp, gc=sc_)
            for kvs in (kv, -kv):
                r, _ = sm.search(tphi / sp, inp["c"] / sc_, 0.3, kh, kvs)
                if r and (rs is None or r["F"] < rs["F"]):
                    rs = r
            if rs:
                calc.formula("F_d,E", "min F (seismic)", rs["F"], "", "Seismic over-design factor",
                             dp=3)
                calc.check("Seismic: E_d ≤ R_d (1 ≤ F_d,E)", 1.0, rs["F"], "",
                           "EN 1998-5 4.1.3.3", hint=HINT_SLOPE)
                cases.append(("seismic", rs))

        if sm.nails:
            calc.heading("Soil nails / anchors")
            calc.text("Each row crossing the slip circle adds the resisting moment T·r about the "
                      "centre, T = min(T_d, R_pull,d × L_behind) per metre (s_h). Design values "
                      "of T_d and pull-out resistance are given by the user (EN 1997-1 §8).")
            calc.table(["Row", "z [m]", "α [°]", "L [m]", "s_h [m]", "T_d [kN]", "T in design case [kN/m]"],
                       [[str(k + 1), f"{r['z'] / 1000:g}", f"{r['angle']:g}", f"{r['L'] / 1000:g}",
                         f"{r['sh'] / 1000:g}", f"{r['Td'] / 1000:g}",
                         f"{rd['T'][k] / 1:.1f}" if k < len(rd.get('T', [])) else "—"]
                        for k, r in enumerate(inp["nails"])], caption="Reinforcement rows")
        calc.heading("Critical slip circles")
        calc.table(["Case", "F", "x_c [m]", "y_c [m]", "R [m]", "W [kN/m]"],
                   [[calc.tr({"char": "Characteristic", "design": "Persistent (design)",
                              "seismic": "Seismic (design)"}[k]), f"{r['F']:.3f}",
                     f"{from_base(r['xc'], 'm'):.2f}", f"{from_base(r['yc'], 'm'):.2f}",
                     f"{from_base(r['R'], 'm'):.2f}", f"{from_base(r['W'], 'kN/m'):.1f}"]
                    for k, r in cases], caption="Origin at the toe of the slope crest edge (x = 0)")
        calc.figure(slope_section(sm, rd, rs, grid, calc.tr), "Section with critical circles and "
                    "factor of safety of the centre grid (persistent design)")
        calc.items.insert(fig_index, calc.items.pop())
        calc.model3d = cls._scene(calc, sm, inp, rd, rs)

    @staticmethod
    def _scene(calc, sm: SlopeModel, inp, rd, rs) -> dict:
        m = lambda v: from_base(v, "m")  # noqa: E731
        L = m(inp["length"])
        sc = Scene3D("slope", calc.tr)
        sc.layer("soil", "Soil", toggle=True)
        sc.layer("slip", "Critical slip mass (persistent)")
        if rs:
            sc.layer("slip_e", "Critical slip mass (seismic)", visible=False)
        sc.layer("loads", "Surcharge")
        sc.layer("dims", "Dimensions")
        H, Ls, y0 = m(sm.H), m(sm.Ls), m(sm.y_min) - 1.0
        xl, xr = m(sm.x_left), m(sm.x_right)
        ground = [(xl, y0), (xr, y0), (xr, 0), (Ls, 0), (0, H), (xl, H)]
        sc.prism("soil", ground, L, PALETTE["soil"], opacity=0.22)
        sc.views = {"default": "front"}

        def mass(r, layer, col, label):
            xs = np.linspace(r["x1"], r["x2"], 60)
            ys = r["yc"] - np.sqrt(np.maximum(r["R"] ** 2 - (xs - r["xc"]) ** 2, 0))
            top = [(m(x), m(float(sm.ground(x)))) for x in xs[::-1]]
            bot = [(m(x), m(y)) for x, y in zip(xs, ys)]
            sc.prism(layer, bot + top, L * 0.6, col, opacity=0.7)
            cx, cy = m(r["xc"]), m(r["yc"])
            for zz in (-L * 0.3, L * 0.3):
                sc.line(layer, [(cx, cy, zz)] + [(x, y, zz) for x, y in bot[:: max(len(bot) // 6, 1)]],
                        "#555555", dashed=True)
            sc.label(layer, label, (cx, cy + 0.3, L * 0.3), "result")
            xm = m(0.5 * (r["x1"] + r["x2"]))
            ym = m(float(sm.ground(0.5 * (r["x1"] + r["x2"])))) + 0.6
            sc.arrow(layer, (xm - 0.8, ym + 0.4, 0), (1, -math.tan(sm.beta), 0), 1.6, col, 0.3)

        mass(rd, "slip", PALETTE["slip"], calc.tr("F_d = {f:.2f} (persistent)", f=rd["F"]))
        sc.legend_item(PALETTE["slip"], calc.tr("Persistent design F_d = {f:.2f}", f=rd["F"]))
        if rs:
            mass(rs, "slip_e", "#8e6cc4", calc.tr("F_d,E = {f:.2f} (seismic)", f=rs["F"]))
            sc.legend_item("#8e6cc4", calc.tr("Seismic design F_d,E = {f:.2f}", f=rs["F"]))
        if inp["q"] > 0 and inp["q_width"] > 0:
            x1, x2 = -m(sm.q_off + sm.q_w), -m(sm.q_off)
            sc.box("loads", ((x1 + x2) / 2, H + 0.05, 0), (x2 - x1, 0.1, L * 0.9),
                   PALETTE["surcharge"], opacity=0.6)
            for xa in np.linspace(x1, x2, 5):
                for za in np.linspace(-L * 0.4, L * 0.4, 4):
                    sc.arrow("loads", (xa, H + 1.0, za), (0, -1, 0), 0.9, PALETTE["surcharge"],
                             0.15)
            sc.label("loads", f"q = {from_base(inp['q'], 'kN/m²'):.0f} kN/m²",
                     ((x1 + x2) / 2, H + 1.2, L * 0.45), "surcharge")
        if sm.nails:
            sc.layer("nails", "Soil nails / anchors")
            for xh, yh, dx, dy, Ln, _, _ in sm.nails:
                for zz in np.linspace(-L * 0.4, L * 0.4, 7):
                    sc.cylinder("nails", (m(xh), m(yh), zz),
                                (m(xh + dx * Ln), m(yh + dy * Ln), zz), 0.05, "#5a6b7d")
                sc.box("nails", (m(xh), m(yh), 0), (0.08, 0.5, L * 0.85), "#9aa0a8")
        sc.label("dims", f"H = {H:.1f} m", (Ls + 0.4, H / 2, L / 2), "dim")
        sc.label("dims", f"β = {inp['slope']:.1f}°", (Ls * 0.6, H * 0.2, L / 2), "dim")
        return sc.to_dict()


__all__ = ["SlopeStabilityEC7", "SlopeModel", "heat_color"]
