"""Tower crane foundation — square RC base under the mast, EN 1997-1 and EN 1992-1-1.

The crane manufacturer gives the loads at the top of the base for the in-service and the
out-of-service cases: vertical load N, overturning moment M, horizontal load H and slewing
torque M_t.  The moment can act in any direction, so every case is checked with M along an
axis of the base and along its diagonal.

* GEO (EN 1997-1 6.5): eccentricity (6.5.4), bearing on the effective area (Annex D or a given
  q_Rd), sliding (Eq. 6.3a) with the slewing torque (friction over the effective area, linear
  interaction — engineering approach), for the combinations of the design approach.
* EQU (EN 1997-1 2.4.7.2, Table A.2): overturning about the edge of the base.
* STR (EN 1992-1-1): contact pressure without tension (lift-off allowed); bending at the leg
  centre line (bottom bars, sagging) and on the lifted side (top bars, hogging), beam shear at d
  from the mast base (6.2.2), punching of the mast base (6.4.4(2), Eq. 6.51) and of the most
  compressed leg, shear at the leg face (6.4.5(3)).
* The smallest base (B, h) that passes every check is searched for.
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import APPROACH_CHOICES, check_approach, get_annex
from ..design.ec2 import bar_area, design_flexure
from ..design.geotech import bearing_factors
from ..report.scene3d import PALETTE, Scene3D

CONCRETE = ["C25/30", "C30/37", "C35/45", "C40/50"]
BARS = ["12", "14", "16", "20", "25", "32"]
LOADS = ["Characteristic (factors applied here)", "Design values (factors already included)"]
SOILS = ["Soil parameters (EN 1997-1 Annex D)", "Given design bearing resistance q_Rd"]
DIRS = (("axis", 1.0, 0.0), ("diagonal", 1 / math.sqrt(2), 1 / math.sqrt(2)))
HINT_PUNCH = "Thicker base (most effective), larger leg base plates or a higher concrete class."
GC = 25e-6  # reinforced concrete, N/mm³ (EN 1991-1-1 Table A.1)


class _Quiet:
    """Stands in for a Calculation when only the utilisations are needed (sizing)."""

    def __init__(self):
        self.checks = []

    def formula(self, sym, expr, value, unit="", desc="", ref=None, dp=None):
        return value

    def input(self, sym, value, unit="", desc="", dp=None):
        return value

    def check(self, desc, dem, cap, unit="", ref=None, hint=""):
        self.checks.append(abs(dem) / cap if cap > 0 else math.inf)

    def check_min(self, desc, prov, req, unit="", ref=None, hint=""):
        self.checks.append(req / prov if prov > 0 else math.inf)

    def check_limit(self, desc, value, limit, unit="", ref=None, hint=""):
        self.check(desc, value, limit)

    def tr(self, text, quiet=False, **kw):
        return text.format(**kw) if kw else text

    def heading(self, *a, **k):
        pass

    text = note = warn = table = heading

    @property
    def ok(self):
        return all(u <= 1 + 1e-9 for u in self.checks)


def _grid(B, n):
    c = (np.arange(n) + 0.5) / n * B - B / 2
    X, Y = np.meshgrid(c, c, indexing="ij")
    return X, Y, (B / n) ** 2


def contact_pressure(V, M, fx, fy, B, n=40):
    """Linear contact pressure under a square B × B with no tension, for V and a moment M whose
    resultant lies at e = M/V in the direction (fx, fy).  Returns (X, Y, dA, q) on an n × n grid,
    or None when the resultant is outside the base.  Linear over the whole base for full
    contact; with lift-off the neutral line is found by bisection so that Σq dA = V and
    Σq s dA = M."""
    X, Y, dA = _grid(B, n)
    s = X * fx + Y * fy
    e = abs(M) / V
    if e < 1e-9:
        return X, Y, dA, np.full_like(X, V / (B * B))
    lo, hi = -100 * B, float(s.max())
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        p = np.clip(s - mid, 0, None)
        if p.sum() <= 0 or (p * s).sum() / p.sum() > e:
            hi = mid
        else:
            lo = mid
    p = np.clip(s - lo, 0, None)
    if p.sum() <= 0 or abs((p * s).sum() / p.sum() - e) > 0.01 * B:
        return None
    return X, Y, dA, p * V / (p.sum() * dA)


def mean_radius(Bp, Lp, n=24):
    """Mean distance of a B' × L' rectangle from its centroid (friction against torsion)."""
    c1 = (np.arange(n) + 0.5) / n * Bp - Bp / 2
    c2 = (np.arange(n) + 0.5) / n * Lp - Lp / 2
    X, Y = np.meshgrid(c1, c2)
    return float(np.hypot(X, Y).mean())


def rounded_square_length(cx, cy, c, r, B, m=800):
    """Length of the control perimeter at distance r around a square c × c centred at (cx, cy)
    that lies inside the square base B × B centred at the origin."""
    pts = []
    h = c / 2
    for k in range(4):
        ang0 = k * math.pi / 2
        ux, uy = math.cos(ang0), math.sin(ang0)          # outward normal of this side
        vx, vy = -uy, ux                                  # along the side
        for t in np.linspace(-h, h, m // 8 + 1)[:-1]:
            pts.append((cx + ux * (h + r) + vx * t, cy + uy * (h + r) + vy * t))
        corner = (cx + (ux + vx) * h, cy + (uy + vy) * h)
        for t in np.linspace(0, math.pi / 2, m // 8 + 1)[:-1]:
            a = ang0 + t
            pts.append((corner[0] + r * math.cos(a), corner[1] + r * math.sin(a)))
    pts.append(pts[0])
    L = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if max(abs(x1), abs(x2), abs(y1), abs(y2)) <= B / 2 + 1e-6:
            L += math.hypot(x2 - x1, y2 - y1)
    return L


@register
class CraneBaseEC7(DesignModule):
    id = "ec7_crane_base"
    title = "Tower crane foundation"
    category = "Geotechnical"
    standard = "EN 1997-1 §2.4.7, §6.5, EN 1992-1-1 §6.1, 6.2, 6.4"
    uses_annex = True
    has_3d = True
    description = ("Square RC base of a tower crane from the manufacturer's loads (in service / out "
                   "of service): overturning, eccentricity, bearing, sliding with slewing torque, "
                   "bending (bottom and top bars), beam shear and punching under the mast — with "
                   "the moment along the axis and the diagonal — and the smallest base B × h that "
                   "passes.")

    fields = [
        Field("cases", "Loads at the top of the base (from the crane manufacturer)",
              kind="table", group="Crane loads",
              default=[{"name": "In service", "N": 1100.0, "M": 2400.0, "H": 35.0, "Mt": 300.0},
                       {"name": "Out of service", "N": 950.0, "M": 2800.0, "H": 95.0,
                        "Mt": 0.0}],
              columns=[Field("name", "Case", kind="text", default="Case"),
                       Field("N", "Vertical N", "kN", 1000.0, min=0),
                       Field("M", "Overturning moment M", "kNm", 2000.0, min=0),
                       Field("H", "Horizontal H", "kN", 50.0, min=0),
                       Field("Mt", "Slewing torque M_t", "kNm", 0.0, min=0)],
              help="Copy them from the crane's foundation data sheet. M may act in any "
                   "direction: the base is checked with M along its axis and its diagonal."),
        Field("loadtype", "The loads are", kind="choice", choices=LOADS, default=LOADS[0],
              group="Crane loads",
              help="Characteristic: N and the self-weight × γ_G (unfavourable / favourable), M, "
                   "H, M_t × γ_Q of the National Annex. Design values: no further factors on "
                   "the actions (material and resistance factors still apply)."),
        Field("a", "Mast leg spacing a (centre to centre)", "m", 2.0, min=0.8, max=6,
              group="Mast", help="The four legs / anchors of the mast base at the corners of a "
                                 "square a × a."),
        Field("cl", "Leg base plate size", "m", 0.40, min=0.1, max=1.5, group="Mast",
              help="Square loaded area under each leg (punching, face shear)."),
        Field("B", "Base size B (square)", "m", 6.0, min=1.5, max=20, group="Base"),
        Field("h", "Base thickness h", "m", 1.40, min=0.4, max=4, group="Base"),
        Field("ts", "Soil above the base", "m", 0.0, min=0, max=5, group="Base",
              help="0 = top of the base at ground level; founding depth D = h + soil above."),
        Field("soil", "Ground", kind="choice", choices=SOILS, default=SOILS[0], group="Ground"),
        Field("phi", "Soil φ'_k", "°", 30.0, min=15, max=45, group="Ground",
              help="Also used for sliding (base cast in situ: δ = φ', EN 1997-1 6.5.3(10))."),
        Field("c", "Soil c'_k", "kN/m²", 0.0, min=0, group="Ground",
              show_if="soil=Soil parameters (EN 1997-1 Annex D)"),
        Field("gamma", "Soil γ", "kN/m³", 19.0, min=10, max=24, group="Ground"),
        Field("qRd", "Design bearing resistance q_Rd", "kN/m²", 400.0, min=20, group="Ground",
              show_if="soil=Given design bearing resistance q_Rd",
              help="From the geotechnical report, already divided by γ_R,v."),
        Field("approach", "Design approach", kind="choice", choices=APPROACH_CHOICES,
              default="National Annex", group="Ground"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C30/37",
              group="Concrete"),
        Field("fyk", "Reinforcement f_yk", "N/mm²", 500.0, min=400, max=600, group="Concrete"),
        Field("cover", "Cover", "mm", 50.0, min=30, max=100, group="Concrete"),
        Field("db", "Bottom bars Ø (both ways)", kind="choice", choices=BARS, default="25",
              group="Reinforcement"),
        Field("sb", "Bottom bar spacing", "mm", 150.0, min=75, max=300, group="Reinforcement"),
        Field("dt", "Top bars Ø (both ways)", kind="choice", choices=BARS, default="20",
              group="Reinforcement"),
        Field("st", "Top bar spacing", "mm", 200.0, min=75, max=300, group="Reinforcement"),
        Field("size", "Find the smallest base B × h", kind="bool", default=True,
              group="Sizing", help="Searches B (step 0.1 m) and h (step 0.05 m) for the least "
                                   "concrete volume that passes every check with the bars "
                                   "entered."),
        Field("hmin", "Minimum thickness in the search", "m", 1.0, min=0.5, max=3, group="Sizing",
              show_if="size", help="Lower bound for h — the embedment of the mast anchors or "
                                   "the manufacturer's minimum usually govern."),
    ]

    # ----------------------------------------------------------------------- run
    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        if not inp["cases"]:
            raise InputError("Add at least one load case", "cases")
        for cs in inp["cases"]:
            if cs["N"] <= 0:
                raise InputError("The vertical load N must be positive", "cases")
        if inp["a"] + inp["cl"] >= inp["B"]:
            raise InputError("The mast base does not fit on the base — increase B", "B")
        na = get_annex(calc.project.annex)
        check_approach(calc, na, inp["approach"])
        calc.note("The loads come from the crane manufacturer. Check also any limits the "
                  "manufacturer sets (minimum base size and weight, eccentricity, anchorage of "
                  "the mast anchors) — they may be stricter than the Eurocodes.")
        cls._analyse(calc, inp, inp["B"], inp["h"], na)
        if inp["size"]:
            cls._sizing(calc, inp, na)
        calc.model3d = cls._scene(calc, inp)

    # ------------------------------------------------------------------ sizing
    @classmethod
    def passes(cls, inp, B, h, na, part="all") -> bool:
        q = _Quiet()
        try:
            cls._analyse(q, inp, B, h, na, part=part)
        except InputError:
            return False
        return q.ok

    @classmethod
    def search(cls, inp, na, hs=None):
        """Least volume B × h.  For every h the smallest B that passes GEO and EQU is found by
        bisection (these checks only improve with B), then B is stepped up until STR passes."""
        Bmin = math.ceil((inp["a"] + inp["cl"] + 200) / 100) * 100
        best = None
        if hs is None:
            h0 = math.ceil(inp["hmin"] / 50 - 1e-9) * 50
            hs = [h0 + 50 * i for i in range(max(int(round((3500 - h0) / 50)) + 1, 1))]
        for h in hs:
            if best and Bmin ** 2 * h >= best[0]:
                break
            if not cls.passes(inp, 20000, h, na, "geo"):
                continue
            if cls.passes(inp, Bmin, h, na, "geo"):
                B = Bmin
            else:
                lo, hi = Bmin, 20000                     # lo fails, hi passes
                while hi - lo > 100:
                    mid = round((lo + hi) / 200) * 100
                    if cls.passes(inp, mid, h, na, "geo"):
                        hi = mid
                    else:
                        lo = mid
                B = hi
            for _ in range(20):
                if best and B * B * h >= best[0]:
                    break
                if cls.passes(inp, B, h, na):
                    best = (B * B * h, B, h)
                    break
                B += 100
        return best

    @classmethod
    def _sizing(cls, calc, inp, na) -> None:
        calc.heading("Smallest base that passes every check")
        best = cls.search(inp, na)
        if best is None:
            calc.warn("No base up to 20 × 20 m × 3.5 m passes with these bars and this ground — "
                      "check the loads and the ground, or use larger bars.")
            return
        vol, B, h = best
        calc.text("Searched: h from {h0:.2f} m to 3.50 m in steps of 0.05 m; for each h the "
                  "smallest B (step 0.1 m) that passes; kept the least concrete volume.",
                  h0=inp["hmin"] / 1000)
        calc.formula("B_min", "search, step 0.1 m", B, "m", "Smallest base size", dp=2)
        calc.formula("h_min", "search, step 0.05 m", h, "m", "Thickness for the least volume",
                     dp=2)
        calc.formula("V_c", "B² h", vol / 1e9, "", "Concrete volume [m³]", dp=1)
        calc.formula("W_c", "γ_c B² h", GC * vol, "kN", "Weight of the base", dp=0)
        calc.text("Every check of this calculation passes for B = {B:.2f} m, h = {h:.2f} m with "
                  "the reinforcement entered (bottom Ø{db}/{sb:.0f}, top Ø{dt}/{st:.0f}). Enter "
                  "these values in B and h to see the full calculation.",
                  db=inp["db"], sb=inp["sb"], dt=inp["dt"], st=inp["st"], B=B / 1000,
                  h=h / 1000)
        own = cls.search(inp, na, [inp["h"]])
        if own:
            calc.formula("B_min(h)", "search with the thickness entered", own[1], "m",
                         "Smallest base for the thickness entered", dp=2)
        else:
            calc.text("No base up to 20 m passes with the thickness entered.")

    # ----------------------------------------------------------------- analysis
    @staticmethod
    def _factors(na, inp, name):
        gu, gf, gq, gphi, gcf, gRv, gRh = na.combos[name]
        if inp["loadtype"] == LOADS[1]:
            gu = gf = gq = 1.0
        return gu, gf, gq, gphi, gcf, gRv, gRh

    @classmethod
    def _analyse(cls, calc, inp, B, h, na, part="all") -> None:
        quiet = isinstance(calc, _Quiet)
        if inp["a"] + inp["cl"] >= B:
            raise InputError("The mast base does not fit on the base — increase B", "B")
        D = h + inp["ts"]
        if not quiet:
            calc.heading("Base and self-weight")
            calc.input("B", B, "m", "Base size (square)")
            calc.input("h", h, "m", "Thickness")
            calc.formula("D", "h + soil above", D, "m", "Founding depth", dp=2)
        W = calc.formula("W", "γ_c B² h + γ B² t_s", GC * B * B * h + inp["gamma"] * B * B *
                         inp["ts"], "kN", "Base and soil above (γ_c = 25 kN/m³)", dp=1)
        cls._equ(calc, inp, B, h, W, na, quiet)
        for name in na.combinations(inp["approach"]):
            cls._geo(calc, inp, B, h, D, W, na, name, quiet)
        if part == "all":
            cls._str(calc, inp, B, h, W, na, quiet)

    # --------------------------------------------------------------------- EQU
    @staticmethod
    def _equ(calc, inp, B, h, W, na, quiet):
        dst, stb, qdst = (1.0, 1.0, 1.0) if inp["loadtype"] == LOADS[1] else na.equ[:3]
        if not quiet:
            calc.heading("Overturning — EQU (EN 1997-1 2.4.7.2)")
            calc.text("γ_G,stb = {s} on N and W, γ_Q,dst = {q} on M and H (Table A.2); tipping "
                      "about the edge of the base with lever B/2 (along the axis — the shorter "
                      "lever).", s=stb, q=qdst)
        for cs in inp["cases"]:
            Mdst = qdst * (cs["M"] + cs["H"] * h)
            Mstb = stb * (cs["N"] + W) * B / 2
            if not quiet:
                calc.formula("M_dst", f"{qdst:g} (M + H h) — {cs['name']}", Mdst, "kNm", dp=0)
                calc.formula("M_stb", f"{stb:g} (N + W) B/2 — {cs['name']}", Mstb, "kNm", dp=0)
            calc.check(calc.tr("EQU {c}: M_dst ≤ M_stb", c=cs["name"]), Mdst, Mstb, "kNm",
                       "EN 1997-1 2.4.7.2, Eq. 2.4",
                       hint="Enlarge the base (B) or make it heavier (h, soil above).")

    # --------------------------------------------------------------------- GEO
    @classmethod
    def _geo(cls, calc, inp, B, h, D, W, na, name, quiet):
        gu, gf, gq, gphi, gcf, gRv, gRh = cls._factors(na, inp, name)
        if not quiet:
            calc.heading(calc.tr("Geotechnical design — {name}", name=name))
            calc.text("γ_G = {gu} (unfav.) / {gf} (fav.) on N and W; γ_Q = {gq} on M, H and "
                      "M_t; γ_φ' = {gphi}; γ_c' = {gc}; γ_R,v = {gRv}; γ_R,h = {gRh}.",
                      gu=gu, gf=gf, gq=gq, gphi=gphi, gc=gcf, gRv=gRv, gRh=gRh)
        phid = math.atan(math.tan(math.radians(inp["phi"])) / gphi)
        cd = inp["c"] / gcf
        Nq, Nc, Ng = bearing_factors(phid)
        rows, worst = [], {}
        for cs in inp["cases"]:
            Md = gq * (cs["M"] + cs["H"] * h)
            Hd, Mtd = gq * cs["H"], gq * cs["Mt"]
            for Vlab, V in (("max V", gu * (cs["N"] + W)), ("min V", gf * (cs["N"] + W))):
                for dname, fx, fy in DIRS:
                    r = cls._geo_one(inp, V, Md, Hd, Mtd, fx, fy, B, D, phid, cd, Nq, Nc, Ng,
                                     gRv, gRh)
                    r.update(case=f"{cs['name']}, {calc.tr(Vlab)}, {calc.tr(dname)}", V=V, Md=Md,
                             Hd=Hd, Mtd=Mtd)
                    rows.append(r)
                    for k in ("ecc", "bear", "slide"):
                        if k not in worst or r["u_" + k] > worst[k]["u_" + k]:
                            worst[k] = r
        if not quiet:
            calc.table(["Case", "V_d [kN]", "M_d [kNm]", "e [m]", "A' [m²]", "q_Ed [kN/m²]",
                        "q_Rd [kN/m²]", "u slide"],
                       [[r["case"], f"{r['V'] / 1e3:.0f}", f"{r['Md'] / 1e6:.0f}",
                         f"{r['e'] / 1e3:.3f}", f"{r['A'] / 1e6:.2f}" if r["A"] > 0 else "—",
                         f"{r['qEd'] * 1e3:.0f}" if r["A"] > 0 else "—",
                         f"{r['qRd'] * 1e3:.0f}" if r["A"] > 0 else "—",
                         f"{r['u_slide']:.2f}"] for r in rows],
                       "Every case: M along the axis and the diagonal, maximum and minimum "
                       "vertical load")
            g = worst["bear"]
            calc.heading(calc.tr("Governing bearing case: {c}", c=g["case"]), 2)
            calc.formula("V_d", "γ_G (N + W)", g["V"], "kN", dp=1)
            calc.formula("M_d", "γ_Q (M + H h)", g["Md"], "kNm", "Moment at the underside", dp=1)
            calc.formula("e", "M_d / V_d", g["e"], "m", "Eccentricity of the resultant", dp=3)
            if g["A"] > 0:
                calc.formula("A'", "(B − 2e_x)(B − 2e_y)", g["A"], "m²", "Effective area",
                             ref="EN 1997-1 Annex D", dp=2)
                calc.formula("q_Ed", "V_d / A'", g["qEd"], "kN/m²", dp=1)
                if inp["soil"] == SOILS[0]:
                    calc.formula("φ'_d", "atan(tan φ'_k / γ_φ')", math.degrees(phid), "°", dp=2)
                    calc.text("N_q = {a:.2f}, N_c = {b:.2f}, N_γ = {c:.2f}; s_q = {sq:.3f}, "
                              "s_γ = {sg:.3f}, s_c = {sc:.3f}; i_q = {iq:.3f}, i_γ = {ig:.3f}, "
                              "i_c = {ic:.3f}; q' = γ D = {qv:.1f} kN/m².", a=Nq, b=Nc, c=Ng,
                              sq=g["sq"], sg=g["sg"], sc=g["sc"], iq=g["iq"], ig=g["ig"],
                              ic=g["ic"], qv=g["qv"] * 1e3)
                    calc.formula("q_Rd", "(c'N_c s_c i_c + q'N_q s_q i_q + ½γB'N_γ s_γ i_γ)/γ_R,v",
                                 g["qRd"], "kN/m²", ref="EN 1997-1 Annex D.4", dp=1)
                else:
                    calc.input("q_Rd", g["qRd"], "kN/m²", "Given design bearing resistance")
            g = worst["slide"]
            calc.heading(calc.tr("Governing sliding case: {c}", c=g["case"]), 2)
            calc.formula("R_h,d", "V_d tan φ'_d / γ_R,h", g["Rh"], "kN", "Sliding resistance",
                         ref="EN 1997-1 Eq. 6.3a", dp=1)
            calc.formula("r_m", "mean distance of A' from its centroid", g["rm"], "m", dp=3)
            calc.formula("R_t,d", "R_h,d r_m", g["Rt"], "kNm",
                         "Friction resistance to the slewing torque", dp=1)
            calc.formula("u_slide", "H_d/R_h,d + M_t,d/R_t,d", g["u_slide"], "",
                         "Linear interaction of sliding and torsion (conservative)", dp=3)
        g = worst["ecc"]
        calc.check_limit(calc.tr("{n} eccentricity (e_x/B)² + (e_y/B)² ≤ 1/9 — {c}", n=name,
                                 c=g["case"]), g["ecc"], 1 / 9, "", "EN 1997-1 6.5.4",
                         hint="Enlarge the base: the resultant must stay inside the middle-third "
                              "ellipse (e ≤ B/3 along an axis).")
        g = worst["bear"]
        calc.check(calc.tr("{n} bearing q_Ed ≤ q_Rd — {c}", n=name, c=g["case"]),
                   g["qEd"] if g["A"] > 0 else 1.0, g["qRd"] if g["A"] > 0 else 0.0, "kN/m²",
                   "EN 1997-1 6.5.2", hint="Enlarge the base or found it deeper.")
        g = worst["slide"]
        calc.check(calc.tr("{n} sliding with torque H/R_h + M_t/R_t ≤ 1 — {c}", n=name,
                           c=g["case"]), g["u_slide"], 1.0, "", "EN 1997-1 6.5.3",
                   hint="Enlarge the base, make it heavier or found it deeper.")

    @staticmethod
    def _geo_one(inp, V, Md, Hd, Mtd, fx, fy, B, D, phid, cd, Nq, Nc, Ng, gRv, gRh) -> dict:
        ex, ey = Md * fx / V, Md * fy / V
        Bp, Lp = B - 2 * ex, B - 2 * ey
        r = {"e": math.hypot(ex, ey), "ecc": (ex / B) ** 2 + (ey / B) ** 2, "A": 0.0}
        r["u_ecc"] = r["ecc"] * 9
        if Bp <= 0 or Lp <= 0:
            r.update(u_bear=math.inf, u_slide=math.inf, qEd=math.inf, qRd=0.0, Rh=0.0, rm=0.0,
                     Rt=0.0)
            return r
        A = Bp * Lp
        r.update(A=A, qEd=V / A)
        if inp["soil"] == SOILS[0]:
            b, l = min(Bp, Lp), max(Bp, Lp)
            sq = 1 + b / l * math.sin(phid)
            sg = 1 - 0.3 * b / l
            sc = (sq * Nq - 1) / (Nq - 1)
            m = (2 + b / l) / (1 + b / l)
            base = max(1 - Hd / (V + A * cd / math.tan(phid)), 0.0)
            iq, ig = base ** m, base ** (m + 1)
            ic = iq - (1 - iq) / (Nc * math.tan(phid))
            qv = inp["gamma"] * D
            qRd = (cd * Nc * sc * ic + qv * Nq * sq * iq + 0.5 * inp["gamma"] * b * Ng * sg * ig
                   ) / gRv
            r.update(sq=sq, sg=sg, sc=sc, iq=iq, ig=ig, ic=ic, qv=qv)
        else:
            qRd = inp["qRd"]
        Rh = V * math.tan(phid) / gRh
        rm = mean_radius(Bp, Lp, 16)
        Rt = Rh * rm
        r.update(qRd=qRd, u_bear=r["qEd"] / qRd if qRd > 0 else math.inf, Rh=Rh, rm=rm, Rt=Rt,
                 u_slide=Hd / Rh + Mtd / Rt)
        return r

    # ----------------------------------------------------------------------- STR
    @classmethod
    def _str(cls, calc, inp, B, h, W, na, quiet):
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd = na.alpha_cc * fck / na.gamma_c
        fyk = inp["fyk"]
        fyd = fyk / na.gamma_s
        if inp["loadtype"] == LOADS[1]:
            gG, gGf, gQ = 1.0, 1.0, 1.0
        else:
            gG, gGf, gQ = na.combos["DA2"][:3]   # set A1 = EN 1990 Table A1.2(B)
        a, cl = inp["a"], inp["cl"]
        c = a + cl                                # mast base taken as a square "column"
        db, dt = float(inp["db"]), float(inp["dt"])
        d = h - inp["cover"] - db                 # mean of the two bottom layers
        d_t = h - inp["cover"] - dt
        Asb = bar_area(db) * 1000 / inp["sb"]     # mm² per metre
        Ast = bar_area(dt) * 1000 / inp["st"]
        n = 24 if quiet else 40
        if not quiet:
            calc.heading("Structural design — STR (EN 1992-1-1)")
            calc.text("Contact pressure q from N + W and M without tension (lift-off allowed), "
                      "linear over the contact area; the self-weight w = W/B² acts downwards on "
                      "the whole base. Moments and shears per metre are averaged over the width "
                      "B. Bending at the leg centre line x = a/2 (conservative), beam shear at d "
                      "from the mast base (x = (a + c_l)/2 + d). γ_G = {g} / {gf}, γ_Q = {q} "
                      "(EN 1990 Table A1.2(B)).", g=gG, gf=gGf, q=gQ)
        x0 = a / 2
        xs = c / 2 + d
        gov = {"mb": (0.0, ""), "mt": (0.0, ""), "v": (0.0, ""), "leg": (0.0, ""),
               "ten": (-math.inf, ""), "pun": None}
        k = min(1 + math.sqrt(200 / d), 2.0)
        rho = min(Asb / (1000 * d), 0.02)
        vmin = 0.035 * k ** 1.5 * math.sqrt(fck)
        crc = 0.18 / na.gamma_c * k * (100 * rho * fck) ** (1 / 3)
        vrc = max(crc, vmin)
        for cs in inp["cases"]:
            Md = gQ * (cs["M"] + cs["H"] * h)
            for g in (gG, gGf):
                V = g * (cs["N"] + W)
                w = g * W / (B * B)
                for dname, fx, fy in DIRS:
                    lab = f"{cs['name']}, γ_G = {g:g}, {calc.tr(dname)}"
                    res = contact_pressure(V, Md, fx, fy, B, n)
                    if res is None:
                        calc.check(calc.tr("Contact pressure: resultant inside the base — {c}",
                                           c=lab), 1.0, 0.0, "", "EN 1997-1 6.5.4",
                                   hint="Enlarge the base.")
                        continue
                    X, Y, dA, q = res
                    net = q - w
                    coord = X                     # the diagonal case is symmetric in X and Y
                    sag = float((net * (coord - x0) * (coord > x0)).sum() * dA / B)
                    hog = float((-net * (-coord - x0) * (coord < -x0)).sum() * dA / B)
                    vv = float((net * (coord > xs)).sum() * dA / B)
                    if sag > gov["mb"][0]:
                        gov["mb"] = (sag, lab)
                    if hog > gov["mt"][0]:
                        gov["mt"] = (hog, lab)
                    if vv > gov["v"][0]:
                        gov["v"] = (vv, lab)
                    # leg forces: legs at (±a/2, ±a/2), Σs² = a² in both directions
                    lev = (a / 2) * (fx + fy)
                    F = g * cs["N"] / 4 + Md * lev / (a * a)
                    if F > gov["leg"][0]:
                        gov["leg"] = (F, lab)
                    T = Md * lev / (a * a) - g * cs["N"] / 4
                    if T > gov["ten"][0]:
                        gov["ten"] = (T, lab)
                    p = cls._punch_frame(g * cs["N"], Md, fx, fy, X, Y, dA, net, c, d, B, vrc)
                    if p and (gov["pun"] is None or p["r"] > gov["pun"]["r"]):
                        p["case"] = lab
                        gov["pun"] = p
        Mb, Mh, Vb = gov["mb"][0] * 1000, gov["mt"][0] * 1000, gov["v"][0] * 1000  # per 1 m
        # ---- bottom bars
        if not quiet:
            calc.heading("Bottom reinforcement — sagging at x = a/2", 2)
            calc.text("Governing: {c}.", c=gov["mb"][1])
            calc.formula("m_Ed", "Σ (q − w)(x − a/2) ΔA / B,  x > a/2", Mb / 1000, "kNm/m", dp=1)
            res = design_flexure(calc, 1000, d, Mb, fck, fcd, fyk, fyd, h,
                                 allow_compression=False, per_metre=True)
            calc.formula("A_s,prov", f"Ø{inp['db']} / {inp['sb']:g} mm", Asb * 1e-3, "mm²/m",
                         dp=0)
            As_req, As_min = res["As"], res["As_min"]
        else:
            As_req = _as_req(Mb, d, fcd, fyd)
            As_min = max(0.26 * 0.30 * fck ** (2 / 3) / fyk * 1000 * d, 0.0013 * 1000 * d)
        if math.isfinite(As_req):
            calc.check_min("Bottom bars: A_s,prov ≥ A_s,req", Asb * 1e-3, As_req * 1e-3, "mm²/m",
                           "6.1", hint="Larger or closer bottom bars, or a thicker base.")
        elif quiet:
            calc.check("Bottom bars", 1.0, 0.0)
        calc.check_min("Bottom bars: A_s,prov ≥ A_s,min", Asb * 1e-3, As_min * 1e-3, "mm²/m",
                       "9.2.1.1(1)", hint="Larger or closer bottom bars.")
        # ---- top bars
        if not quiet:
            calc.heading("Top reinforcement — hogging on the lifted side", 2)
        if Mh > 0:
            Asr = _as_req(Mh, d_t, fcd, fyd)
            if not quiet:
                calc.text("Governing: {c}.", c=gov["mt"][1])
                calc.formula("m_Ed,top", "Σ (w − q)(|x| − a/2) ΔA / B,  x < −a/2", Mh / 1000,
                             "kNm/m", dp=1)
                calc.formula("d_top", "h − c − Ø_top", d_t, "mm", dp=0)
                calc.formula("A_s,req,top", "m_Ed / (f_yd z), z = d(1 − 0.4ξ) ≤ 0.95d",
                             Asr * 1e-3, "mm²/m", ref="3.1.7", dp=0)
                calc.formula("A_s,prov,top", f"Ø{inp['dt']} / {inp['st']:g} mm", Ast * 1e-3,
                             "mm²/m", dp=0)
            if math.isfinite(Asr):
                calc.check_min("Top bars: A_s,prov ≥ A_s,req", Ast * 1e-3, Asr * 1e-3, "mm²/m",
                               "6.1", hint="Larger or closer top bars, or a thicker base.")
            else:
                calc.check("Top bars: section adequate", 1.0, 0.0, "", "6.1",
                           hint="Thicker base.")
        elif not quiet:
            calc.text("The self-weight never exceeds the contact pressure on the lifted side — the "
                      "top bars carry no bending; provide them for shrinkage and for the mast "
                      "anchors.")
        # ---- beam shear
        if not quiet:
            calc.heading("Beam shear at d from the mast base (6.2.2)", 2)
            calc.text("Governing: {c}.", c=gov["v"][1])
            calc.formula("v_Ed", "Σ (q − w) ΔA / B,  x > (a + c_l)/2 + d", Vb / 1000, "kN/m",
                         dp=1)
            calc.formula("k", "1 + √(200/d) ≤ 2", k, "", ref="6.2.2(1)", dp=3)
            calc.formula("ρ_l", "A_s / (b d) ≤ 0.02", rho, "", dp=4)
            calc.formula("v_min", "0.035 k^1.5 f_ck^0.5", vmin, "N/mm²", ref="Eq. 6.3N", dp=3)
            calc.formula("V_Rd,c", "max(0.18/γ_c k (100ρ_l f_ck)^(1/3), v_min) b d",
                         vrc * d, "kN/m", ref="Eq. 6.2", dp=1)
        calc.check("Beam shear: v_Ed ≤ V_Rd,c", Vb / 1000, vrc * d, "kN/m", "6.2.2",
                   hint="Thicker base.")
        # ---- punching: mast base as a column
        nu = 0.6 * (1 - fck / 250)
        vmax = na.punch_vmax * nu * fcd
        p = gov["pun"]
        if not quiet:
            calc.heading("Punching of the mast base (6.4.4(2))", 2)
            calc.text("The mast base is taken as a square column c = a + c_l. Control perimeters "
                      "0 < a_p ≤ 2d inside the base are searched; the net soil reaction inside "
                      "each one is deducted (Eq. 6.48) and the moment is taken with Eq. 6.51 "
                      "(k = 0.6, both components added — conservative).")
        if p:
            if not quiet:
                calc.text("Governing: {c}.", c=p["case"])
                calc.formula("a_crit", "critical distance, 0 < a_p ≤ 2d", p["a"], "mm", dp=0)
                calc.formula("u", "4c + 2πa_p", p["u"], "mm", "Control perimeter", dp=0)
                calc.formula("V_Ed,red", "γ N − Σ (q − w) ΔA inside u", p["Vred"], "kN",
                             ref="Eq. 6.48", dp=1)
                calc.formula("β", "1 + k (M_x + M_y)/V_Ed,red · u/W_1", p["beta"], "",
                             ref="Eq. 6.51", dp=3)
                calc.formula("v_Ed,p", "β V_Ed,red / (u d)", p["vEd"], "N/mm²", dp=3)
                calc.formula("v_Rd,p", "max(C_Rd,c k (100ρ f_ck)^(1/3), v_min) 2d/a_p", p["vRd"],
                             "N/mm²", ref="Eq. 6.50", dp=3)
            calc.check("Punching of the mast base: v_Ed ≤ v_Rd", p["vEd"], p["vRd"], "N/mm²",
                       "6.4.4(2)", hint=HINT_PUNCH)
        elif not quiet:
            calc.text("Every control perimeter within 2d of the mast base lies outside the base — "
                      "punching of the mast base is not critical; beam shear governs.")
        # ---- punching under the most compressed leg
        F = gov["leg"][0]
        ce = B / 2 - a / 2 - cl / 2                 # clear distance plate → base edge
        amax = min(2 * d, (a - cl) / 2)             # the perimeter must not reach the next leg
        u_leg = rounded_square_length(a / 2, a / 2, cl, amax, B)
        vEd_l = F / (u_leg * d)
        vRd_l = vrc * 2 * d / amax
        if not quiet:
            calc.heading("Punching under the most compressed leg", 2)
            calc.text("Governing: {c}. Control perimeter at a_p = min(2d, (a − c_l)/2) so that it "
                      "does not reach the next leg, clipped at the edge of the base when closer "
                      "(clear edge distance {ce:.2f} m); the soil reaction is ignored "
                      "(conservative), v_Rd enhanced by 2d/a_p (6.4.4(2)).",
                      c=gov["leg"][1], ce=ce / 1000)
            calc.formula("F_leg", "γ_G N/4 + M_d s_max / Σs²", F, "kN",
                         "Most compressed leg (M along the diagonal: M_d/(√2 a))", dp=1)
            calc.formula("a_p", "min(2d, (a − c_l)/2)", amax, "mm", dp=0)
            calc.formula("u_leg", "4c_l + 2πa_p (inside the base)", u_leg, "mm", dp=0)
            calc.formula("v_Ed,leg", "F_leg / (u_leg d)", vEd_l, "N/mm²", dp=3)
            calc.formula("v_Rd,leg", "max(C_Rd,c k (100ρ f_ck)^(1/3), v_min) 2d/a_p", vRd_l, "N/mm²",
                         ref="Eq. 6.50", dp=3)
        calc.check("Punching under a leg: v_Ed ≤ v_Rd", vEd_l, vRd_l, "N/mm²", "6.4.4(2)",
                   hint=HINT_PUNCH)
        v0 = F / (4 * cl * d)
        if not quiet:
            calc.formula("v_Ed,0", "F_leg / (4 c_l d)", v0, "N/mm²",
                         "Shear at the face of the leg base plate", dp=3)
            calc.formula("v_Rd,max", f"{na.punch_vmax:g} ν f_cd, ν = 0.6(1 − f_ck/250)", vmax,
                         "N/mm²", ref="6.4.5(3)", dp=3)
        calc.check("Leg face: v_Ed,0 ≤ v_Rd,max", v0, vmax, "N/mm²", "6.4.5(3)",
                   hint="Larger leg base plates or a higher concrete class.")
        # ---- anchors
        if not quiet:
            calc.heading("Mast anchors", 2)
            T = gov["ten"][0]
            if T > 0:
                calc.formula("T_leg", "M_d s_max / Σs² − γ_G,fav N/4", T, "kN",
                             "Design tension in the most stressed mast anchor", dp=1)
                calc.note("Anchor the mast anchors (manufacturer's anchor frame or cast-in "
                          "anchors) below the bottom bars, or tie them with hanger bars for "
                          "T_leg, following the manufacturer's details.")
            else:
                calc.text("No tension in the mast anchors.")

    @staticmethod
    def _punch_frame(VN, Md, fx, fy, X, Y, dA, net, c, d, B, vrc):
        best = None
        dx = np.clip(np.abs(X) - c / 2, 0, None)
        dy = np.clip(np.abs(Y) - c / 2, 0, None)
        dist = np.hypot(dx, dy)
        for ap in np.linspace(0.1 * d, 2 * d, 20):
            if c / 2 + ap > B / 2:
                break
            u = 4 * c + 2 * math.pi * ap
            Vred = VN - float((net * (dist <= ap)).sum() * dA)
            if Vred <= 0:
                continue
            W1 = c * c / 2 + c * c + 4 * c * ap + 4 * ap * ap + math.pi * ap * c
            beta = 1 + 0.6 * Md * (fx + fy) / Vred * u / W1
            vEd = beta * Vred / (u * d)
            vRd = vrc * 2 * d / ap
            if best is None or vEd / vRd > best["r"]:
                best = {"r": vEd / vRd, "a": ap, "u": u, "Vred": Vred, "beta": beta, "vEd": vEd,
                        "vRd": vRd}
        return best

    # ------------------------------------------------------------------- 3D
    @staticmethod
    def _scene(calc, inp) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        B, h, a, cl = m(inp["B"]), m(inp["h"]), m(inp["a"]), m(inp["cl"])
        sc = Scene3D("crane_base", calc.tr)
        for key, label in (("base", "Base"), ("bars", "Reinforcement"), ("mast", "Mast"),
                           ("soil", "Soil"), ("loads", "Loads")):
            sc.layer(key, label, toggle=key != "base")
        top = -m(inp["ts"])
        sc.box("base", (0, top - h / 2, 0), (B, h, B), PALETTE["concrete"], opacity=0.45)
        if inp["ts"] > 0:
            sc.box("soil", (0, top / 2, 0), (B + 2, -top, B + 2), PALETTE["soil"], opacity=0.15)
        sc.box("soil", (0, top - h - 0.3, 0), (B + 2, 0.6, B + 2), PALETTE["rock"], opacity=0.12)
        cov = m(inp["cover"])
        for dia, s, y in ((m(float(inp["db"])), m(inp["sb"]), top - h + cov),
                          (m(float(inp["dt"])), m(inp["st"]), top - cov)):
            nb = int((B - 2 * cov) / s) + 1
            step = max(nb // 16, 1)
            for i in range(0, nb, step):
                p = -B / 2 + cov + i * s
                sc.cylinder("bars", (-B / 2 + cov, y, p), (B / 2 - cov, y, p), dia / 2,
                            "#8a5a2b")
                sc.cylinder("bars", (p, y + dia, -B / 2 + cov), (p, y + dia, B / 2 - cov),
                            dia / 2, "#8a5a2b")
        H = 3.0
        for sx in (-1, 1):
            for sz in (-1, 1):
                sc.box("mast", (sx * a / 2, top + 0.03, sz * a / 2), (cl, 0.06, cl),
                       PALETTE["steel"])
                sc.cylinder("mast", (sx * a / 2, top, sz * a / 2),
                            (sx * a / 2, top + H, sz * a / 2), 0.07, "#e0a800")
        for y0 in range(int(H)):
            for (x1, z1), (x2, z2) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)),
                                       ((-1, 1), (-1, -1))):
                sc.line("mast", [(x1 * a / 2, top + y0, z1 * a / 2),
                                 (x2 * a / 2, top + y0 + 1, z2 * a / 2)], "#e0a800")
        cs = max(inp["cases"], key=lambda r: r["M"])
        sc.arrow("loads", (0, top + H + 1.5, 0), (0, -1, 0), 1.2, PALETTE["load"])
        sc.label("loads", f"{cs['name']}: N = {cs['N'] / 1e3:.0f} kN, M = {cs['M'] / 1e6:.0f} kNm",
                 (0, top + H + 1.8, 0), "force")
        sc.label("base", f"B = {B:.2f} m, h = {h:.2f} m", (B / 2 + 0.3, top - h / 2, B / 2),
                 "result")
        return sc.to_dict()


def _as_req(M, d, fcd, fyd):
    """Required area for M on a 1000 mm wide strip (rectangular block λ = 0.8, η = 1, 3.1.7)."""
    mu = M / (1000 * d * d * fcd)
    if mu >= 0.5:
        return math.inf
    xi = 1.25 * (1 - math.sqrt(1 - 2 * mu))
    z = min(d * (1 - 0.4 * xi), 0.95 * d)
    return M / (fyd * z)
