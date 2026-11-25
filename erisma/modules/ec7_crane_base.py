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
INPUTS = ["Resultants N, M, H, M_t", "Forces on each leg"]
LUNITS = ["kN, kNm", "t, t·m"]
FIXING = ["Bolted to the top of the base (anchor bolts / base plates)",
          "Embedded anchor section (cast in, built-in mast)"]
LEGXY = ((1, 1), (-1, 1), (-1, -1), (1, -1))   # legs 1–4 at (±a/2, ±a/2), anticlockwise
HINT_PUNCH = ("Thicker base (most effective), allow punching links, larger leg base plates or a "
              "higher concrete class.")
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


def normalise(inp: dict) -> dict:
    """The selected load table as resultants {name, N, M, H, M_t} [N, Nmm]; with leg forces
    N = ΣF and M = √((ΣF x)² + (ΣF y)²), legs at (±a/2, ±a/2)."""
    if inp.get("_norm"):
        return inp
    tons = inp.get("lunit") == LUNITS[1]
    if inp.get("input", INPUTS[0]) == INPUTS[0]:
        key = "cases_t" if tons else "cases"
        cases = [dict(r) for r in inp[key]]
    else:
        key = "legs_t" if tons else "legs"
        cases = []
        for r in inp[key]:
            F = [r["F1"], r["F2"], r["F3"], r["F4"]]
            sx = sum(f * i * inp["a"] / 2 for f, (i, _) in zip(F, LEGXY))
            sy = sum(f * j * inp["a"] / 2 for f, (_, j) in zip(F, LEGXY))
            cases.append({"name": r["name"], "N": sum(F), "M": math.hypot(sx, sy), "H": r["H"],
                          "Mt": r["Mt"], "legs": F, "sx": sx, "sy": sy})
    if not cases:
        raise InputError("Add at least one load case", key)
    for cs in cases:
        if cs["N"] <= 0:
            raise InputError("The vertical load N must be positive", key)
    return {**inp, "cases": cases, "_norm": True, "_table": key}


def peak_pressure(V, M, fx, fy, B, n=60):
    """Peak contact pressure at the most compressed corner/edge (linear, no tension), from the
    neutral line of :func:`contact_pressure` extrapolated exactly to s_max."""
    res = contact_pressure(V, M, fx, fy, B, n)
    if res is None:
        return math.inf
    X, Y, dA, q = res
    s = X * fx + Y * fy
    i = np.unravel_index(np.argmax(q), q.shape)
    j = np.unravel_index(np.argmin(np.where(q > 0, s, np.inf)), q.shape)
    smax = B / 2 * (fx + fy)
    if q[i] == q[j] or s[i] == s[j]:
        return float(q.max())
    grad = (q[i] - q[j]) / (s[i] - s[j])
    return float(q[i] + grad * (smax - s[i]))


def mean_radius(Bp, Lp, n=24):
    """Mean distance of a B' × L' rectangle from its centroid (friction against torsion)."""
    c1 = (np.arange(n) + 0.5) / n * Bp - Bp / 2
    c2 = (np.arange(n) + 0.5) / n * Lp - Lp / 2
    X, Y = np.meshgrid(c1, c2)
    return float(np.hypot(X, Y).mean())


def rounded_rect_length(cx, cy, w, l, r, B, m=800):
    """Length of the perimeter at distance r around a w × l rectangle centred at (cx, cy) that
    lies inside the square base B × B centred at the origin."""
    pts = []
    hw, hl = w / 2, l / 2
    for k in range(4):
        ang0 = k * math.pi / 2
        ux, uy = round(math.cos(ang0)), round(math.sin(ang0))
        vx, vy = -uy, ux
        half_n = hw if ux else hl           # half-length of the side facing (ux, uy)
        half_t = hl if ux else hw           # half-length along the side
        for t in np.linspace(-half_t, half_t, m // 8 + 1)[:-1]:
            pts.append((cx + ux * (half_n + r) + vx * t, cy + uy * (half_n + r) + vy * t))
        corner = (cx + ux * half_n + vx * half_t, cy + uy * half_n + vy * half_t)
        for t in np.linspace(0, math.pi / 2, m // 8 + 1)[:-1]:
            a = ang0 + t
            pts.append((corner[0] + r * math.cos(a), corner[1] + r * math.sin(a)))
    pts.append(pts[0])
    L = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if max(abs(x1), abs(x2), abs(y1), abs(y2)) <= B / 2 + 1e-6:
            L += math.hypot(x2 - x1, y2 - y1)
    return L


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
        Field("input", "Crane loads given as", kind="choice", choices=INPUTS, default=INPUTS[0],
              group="Crane loads",
              help="Resultants at the top of the base, or the force on each of the four mast "
                   "legs — whichever the manufacturer's data sheet gives."),
        Field("lunit", "Units of the loads", kind="choice", choices=LUNITS, default=LUNITS[0],
              group="Crane loads", help="Many manufacturers (e.g. Saez) give t and t·m: "
                                        "1 t = 9.80665 kN."),
        Field("cases", "Loads at the top of the base (from the crane manufacturer)",
              kind="table", group="Crane loads", show_if=f"input={INPUTS[0]}&lunit={LUNITS[0]}",
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
        Field("cases_t", "Loads at the top of the base (from the crane manufacturer)",
              kind="table", group="Crane loads", show_if=f"input={INPUTS[0]}&lunit={LUNITS[1]}",
              default=[{"name": "H = 35.7 m", "N": 21.5, "M": 160.0, "H": 6.5, "Mt": 0.0}],
              columns=[Field("name", "Case", kind="text", default="Case"),
                       Field("N", "Vertical N (P)", "t", 20.0, min=0),
                       Field("M", "Overturning moment M", "t·m", 100.0, min=0),
                       Field("H", "Horizontal H (T)", "t", 5.0, min=0),
                       Field("Mt", "Slewing torque M_t", "t·m", 0.0, min=0)],
              help="As printed in the manufacturer's table, in t and t·m (e.g. Saez: P, M, T)."),
        Field("legs", "Force on each mast leg (compression +, tension −)", kind="table",
              group="Crane loads", show_if=f"input={INPUTS[1]}&lunit={LUNITS[0]}",
              default=[{"name": "Out of service", "F1": 1227.5, "F2": 237.5, "F3": -752.5,
                        "F4": 237.5, "H": 95.0, "Mt": 0.0}],
              columns=[Field("name", "Case", kind="text", default="Case"),
                       Field("F1", "Leg 1 (+x, +y)", "kN", 250.0),
                       Field("F2", "Leg 2 (−x, +y)", "kN", 250.0),
                       Field("F3", "Leg 3 (−x, −y)", "kN", 250.0),
                       Field("F4", "Leg 4 (+x, −y)", "kN", 250.0),
                       Field("H", "Horizontal H", "kN", 50.0, min=0),
                       Field("Mt", "Slewing torque M_t", "kNm", 0.0, min=0)],
              help="Legs numbered anticlockwise from the corner (+x, +y), at ±a/2. Gives N = ΣF "
                   "and M = √((ΣF x)² + (ΣF y)²). For the manufacturer's maximum compression C "
                   "and tension T along the diagonal: F1 = C, F3 = −T, F2 = F4 = (C − T)/2."),
        Field("legs_t", "Force on each mast leg (compression +, tension −)", kind="table",
              group="Crane loads", show_if=f"input={INPUTS[1]}&lunit={LUNITS[1]}",
              default=[{"name": "Case", "F1": 99.7, "F2": 5.4, "F3": -88.9, "F4": 5.4, "H": 6.5,
                        "Mt": 0.0}],
              columns=[Field("name", "Case", kind="text", default="Case"),
                       Field("F1", "Leg 1 (+x, +y)", "t", 25.0),
                       Field("F2", "Leg 2 (−x, +y)", "t", 25.0),
                       Field("F3", "Leg 3 (−x, −y)", "t", 25.0),
                       Field("F4", "Leg 4 (+x, −y)", "t", 25.0),
                       Field("H", "Horizontal H", "t", 5.0, min=0),
                       Field("Mt", "Slewing torque M_t", "t·m", 0.0, min=0)],
              help="Legs numbered anticlockwise from the corner (+x, +y), at ±a/2; in t."),
        Field("loadtype", "The loads are", kind="choice", choices=LOADS, default=LOADS[0],
              group="Crane loads",
              help="Characteristic: N and the self-weight × γ_G (unfavourable / favourable), M, "
                   "H, M_t × γ_Q of the National Annex. Design values: no further factors on "
                   "the actions (material and resistance factors still apply)."),
        Field("a", "Mast leg spacing a (centre to centre)", "m", 2.0, min=0.8, max=6,
              group="Mast", help="The four legs / anchors of the mast base at the corners of a "
                                 "square a × a."),
        Field("cl", "Leg base plate size", "m", 0.40, min=0.1, max=1.5, group="Mast",
              help="Square loaded area under each leg (punching, face shear); for an embedded "
                   "anchor, the foot plate of each leg."),
        Field("fixing", "Mast fixing", kind="choice", choices=FIXING, default=FIXING[0],
              group="Mast", help="Embedded: the manufacturer's anchor section (e.g. Saez S51) is "
                                 "cast into the base and the legs end near the bottom bars."),
        Field("hemb", "Embedment depth of the anchor section", "m", 1.1, min=0.3, max=3.5,
              group="Mast", show_if=f"fixing={FIXING[1]}",
              help="From the top of the base to the feet of the anchor (manufacturer's "
                   "drawing)."),
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
        Field("mfr", "Also check the manufacturer's criteria (unfactored)", kind="bool",
              default=False, group="Ground",
              help="Manufacturer-type check with the loads as given (no partial factors): "
                   "resultant within the middle-third ellipse (e ≤ B/3) and peak soil pressure "
                   "≤ the allowable value. For comparison with the manufacturer's data sheet; "
                   "not a Eurocode verification."),
        Field("qall", "Allowable soil pressure (manufacturer)", "kN/m²", 157.0, min=20,
              group="Ground", show_if="mfr",
              help="E.g. Saez: \"minimum land pressure 1.6 kg/cm²\" = 157 kN/m²."),
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
        Field("links", "Allow punching reinforcement (links)", kind="bool", default=True,
              group="Reinforcement", help="Where the concrete alone does not resist punching, "
                                          "vertical links are designed (EN 1992-1-1 6.4.5, "
                                          "9.4.3). Off: the base must pass without them."),
        Field("dsw", "Punching link Ø", kind="choice", choices=["8", "10", "12", "14", "16"],
              default="12", group="Reinforcement", show_if="links"),
        Field("hmin", "Minimum thickness in the search", "m", 1.0, min=0.5, max=3, group="Sizing",
              show_if="size", help="Lower bound for h — the embedment of the mast anchors or "
                                   "the manufacturer's minimum usually govern."),
    ]

    # ----------------------------------------------------------------------- run
    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        inp = normalise(inp)
        if inp["a"] + inp["cl"] >= inp["B"]:
            raise InputError("The mast base does not fit on the base — increase B", "B")
        na = get_annex(calc.project.annex)
        check_approach(calc, na, inp["approach"])
        calc.note("The loads come from the crane manufacturer. Check also any limits the "
                  "manufacturer sets (minimum base size and weight, eccentricity, anchorage of "
                  "the mast anchors) — they may be stricter than the Eurocodes.")
        if inp["input"] == INPUTS[1]:
            cls._leg_input(calc, inp)
        pos = len(calc.items)
        links = cls._analyse(calc, inp, inp["B"], inp["h"], na)
        cls._summary(calc, inp, links, pos)
        if inp["size"]:
            cls._sizing(calc, inp, na)
        calc.model3d = cls._scene(calc, inp, links)

    @staticmethod
    def _summary(calc, inp, links, pos) -> None:
        """Three answers at the top of the report: dimensions, reinforcement, punching."""
        start = len(calc.items)
        i0, i1, i2 = calc.crane_marks
        groups = (("Dimensions B × h (overturning, soil, sliding)", calc.checks[i0:i1]),
                  ("Bending reinforcement and beam shear", calc.checks[i1:i2]),
                  ("Punching and the concrete around the mast", calc.checks[i2:]))
        calc.heading("Summary")
        calc.text("Base {B:.2f} × {B:.2f} m, h = {h:.2f} m; bottom bars Ø{db}/{sb:.0f}, top bars "
                  "Ø{dt}/{st:.0f} (both ways).", B=inp["B"] / 1000, h=inp["h"] / 1000,
                  db=inp["db"], sb=inp["sb"], dt=inp["dt"], st=inp["st"])
        rows = []
        for label, chks in groups:
            if not chks:
                continue
            worst = max(chks, key=lambda c: c.utilisation)
            ok = all(c.passed for c in chks)
            rows.append([calc.tr(label), calc.tr("OK") if ok else calc.tr("NOT OK"),
                         f"{worst.utilisation:.2f}", worst.description])
        calc.table(["Check group", "Result", "Max. utilisation", "Governing check"], rows)
        key = getattr(calc, "crane_key", None)
        if key:
            name, Fk, Fd = key["legs"]
            calc.heading("Forces on each leg", 2)
            calc.table(["Leg", "1 (+x, +y)", "2 (−x, +y)", "3 (−x, −y)", "4 (+x, −y)"],
                       [[calc.tr("Characteristic [kN]"), *(f"{f / 1e3:+.1f}" for f in Fk)],
                        [calc.tr("Design [kN]"), *(f"{f / 1e3:+.1f}" for f in Fd)]],
                       calc.tr("{c}, M along the diagonal towards leg 1 (the most onerous); "
                               "compression +, tension −", c=name))
            o = calc.outputs
            val = lambda k: o[k]["value"] if k in o else None  # noqa: E731
            rows = [[calc.tr("Bending, bottom bars (sagging)"),
                     f"m_Ed = {key['mb'] / 1e6:.1f} kNm/m",
                     f"A_s,req = {max(key.get('Asb_req', 0), key.get('Asb_min', 0)):.0f} mm²/m",
                     f"A_s,prov = {key['Asb']:.0f} mm²/m"],
                    [calc.tr("Bending, top bars (hogging)"),
                     f"m_Ed = {key['mt'] / 1e6:.1f} kNm/m",
                     f"A_s,req = {key.get('Ast_req', 0):.0f} mm²/m",
                     f"A_s,prov = {key['Ast']:.0f} mm²/m"],
                    [calc.tr("Beam shear"), f"v_Ed = {key['vb'] / 1e3:.1f} kN/m",
                     f"V_Rd,c = {key['VRc'] / 1e3:.1f} kN/m", ""]]
            if val("v_Ed,p") is not None:
                rows.append([calc.tr("Punching of the mast base"),
                             f"v_Ed = {val('v_Ed,p'):.3f} N/mm²",
                             f"v_Rd = {val('v_Rd,p'):.3f} N/mm²", ""])
            if val("v_Ed,leg") is not None:
                rows.append([calc.tr("Punching under a leg"),
                             f"v_Ed = {val('v_Ed,leg'):.3f} N/mm²",
                             f"v_Rd = {val('v_Rd,leg'):.3f} N/mm²", ""])
            calc.heading("Moments and shear (design values)", 2)
            calc.table(["", "Action effect", "Resistance / required", "Provided"], rows,
                       "Per metre width of the base; details further below")
        frame, leg = (links or {}).get("frame"), (links or {}).get("leg")
        if not frame and not leg:
            calc.text("Punching reinforcement: not required — the concrete alone resists "
                      "punching." if all(c.passed for c in calc.checks[i2:]) else
                      "Punching: the concrete alone is not enough (see the checks below).")
        for lk, where in ((frame, "around the mast base"), (leg, "around each leg")):
            if lk:
                calc.text("Punching reinforcement REQUIRED {w}: {n} perimeters of vertical links "
                          "Ø{d:.0f}, {legs} legs per perimeter (details below).",
                          w=calc.tr(where), n=len(lk["radii"]), d=lk["dsw"],
                          legs=max(lk["legs"]))
        new = calc.items[start:]
        del calc.items[start:]
        calc.items[pos:pos] = new

    @staticmethod
    def _leg_input(calc, inp) -> None:
        calc.heading("Loads from the forces on each leg")
        u = "t" if inp["lunit"] == LUNITS[1] else "kN"
        um = "t·m" if u == "t" else "kNm"
        f = 9806.65 if u == "t" else 1e3
        rows = []
        for cs in inp["cases"]:
            rows.append([cs["name"], *(f"{x / f:.1f}" for x in cs["legs"]),
                         f"{cs['N'] / f:.1f}", f"{cs['sx'] / f / 1e3:.1f}",
                         f"{cs['sy'] / f / 1e3:.1f}", f"{cs['M'] / f / 1e3:.1f}"])
        calc.table(["Case", f"F1 [{u}]", f"F2 [{u}]", f"F3 [{u}]", f"F4 [{u}]", f"N [{u}]",
                    f"ΣF x [{um}]", f"ΣF y [{um}]", f"M [{um}]"], rows,
                   "N = ΣF_i, M = √((ΣF_i x_i)² + (ΣF_i y_i)²), legs at x_i, y_i = ±a/2")
        calc.text("The crane slews, so M is then checked along the axis and the diagonal of the "
                  "base, whatever its direction in the data sheet.")

    # ------------------------------------------------------------------ sizing
    @classmethod
    def passes(cls, inp, B, h, na, part="all") -> bool:
        inp = normalise(inp)
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
        inp = normalise(inp)
        Bmin = math.ceil((inp["a"] + inp["cl"] + 200) / 100) * 100
        best = None
        if hs is None:
            hlo = inp["hmin"]
            if inp["fixing"] == FIXING[1]:
                hlo = max(hlo, inp["hemb"] + inp["cover"] + 2 * float(inp["db"]))
            h0 = math.ceil(hlo / 50 - 1e-9) * 50
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
        if not quiet:
            calc.crane_marks = [len(calc.checks)]
        cls._equ(calc, inp, B, h, W, na, quiet)
        for name in na.combinations(inp["approach"]):
            cls._geo(calc, inp, B, h, D, W, na, name, quiet)
        if inp["mfr"]:
            cls._manufacturer(calc, inp, B, h, W, quiet)
        if inp["fixing"] == FIXING[1]:
            hreq = inp["hemb"] + inp["cover"] + 2 * float(inp["db"])
            if not quiet:
                calc.heading("Embedded anchor section — thickness")
            calc.check_min("Embedded anchor fits: h ≥ h_emb + c + 2Ø", h, hreq, "m",
                           "Manufacturer drawing", hint="Thicker base (the feet must stay above "
                                                        "the bottom bars).")
        if not quiet:
            calc.crane_marks.append(len(calc.checks))
        if part == "all":
            return cls._str(calc, inp, B, h, W, na, quiet)
        return None

    # ------------------------------------------------------------ manufacturer
    @staticmethod
    def _manufacturer(calc, inp, B, h, W, quiet):
        """Unfactored check in the form of crane data sheets (not EN 1997-1)."""
        rows, worst_e, worst_q = [], None, None
        for cs in inp["cases"]:
            V, M = cs["N"] + W, cs["M"] + cs["H"] * h
            for dname, fx, fy in DIRS:
                e = M / V
                ecc = (e * fx / B) ** 2 + (e * fy / B) ** 2
                qmax = peak_pressure(V, M, fx, fy, B, 30 if quiet else 60)
                lab = f"{cs['name']}, {calc.tr(dname)}"
                rows.append([lab, f"{V / 1e3:.0f}", f"{M / 1e6:.0f}", f"{e / 1e3:.3f}",
                             f"{qmax * 1e3:.0f}"])
                if worst_e is None or ecc > worst_e[0]:
                    worst_e = (ecc, lab)
                if worst_q is None or qmax > worst_q[0]:
                    worst_q = (qmax, lab)
        if not quiet:
            calc.heading("Manufacturer-type check (unfactored loads — not EN 1997-1)")
            calc.text("The loads as given, the weight W, and M + H h at the underside, without "
                      "partial factors — the form in which crane data sheets state their "
                      "foundation requirements. Linear soil pressure without tension; the peak "
                      "is at the edge (M along the axis) or at the corner (M along the "
                      "diagonal).")
            calc.table(["Case", "V = N + W [kN]", "M + H h [kNm]", "e [m]",
                        "q_max [kN/m²]"], rows)
            calc.input("q_all", inp["qall"], "kN/m²", "Allowable soil pressure (manufacturer)")
        calc.check_limit(calc.tr("Manufacturer: (e_x/B)² + (e_y/B)² ≤ 1/9 (e ≤ B/3) — {c}",
                                 c=worst_e[1]), worst_e[0], 1 / 9, "", "Manufacturer data sheet",
                         hint="Enlarge the base or make it heavier.")
        calc.check(calc.tr("Manufacturer: q_max ≤ q_all — {c}", c=worst_q[1]), worst_q[0],
                   inp["qall"], "kN/m²", "Manufacturer data sheet",
                   hint="Enlarge the base.")

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
               "ten": (-math.inf, ""), "ten2": (-math.inf, ""), "pun_all": []}
        emb = inp["fixing"] == FIXING[1]
        hl = inp["hemb"] if emb else 0.0          # level of the leg feet below the top
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
                    # leg forces: legs at (±a/2, ±a/2), Σs² = a² in both directions; the
                    # moment at the level of the leg feet (top of the base, or the foot of an
                    # embedded anchor)
                    lev = (a / 2) * (fx + fy)
                    Ml = gQ * (cs["M"] + cs["H"] * hl)
                    F = g * cs["N"] / 4 + Ml * lev / (a * a)
                    if F > gov["leg"][0]:
                        gov["leg"] = (F, lab)
                    T = Ml * lev / (a * a) - g * cs["N"] / 4
                    key = "ten" if dname == "diagonal" else "ten2"
                    if T > gov[key][0]:
                        gov[key] = (T, lab)
                    gov["pun_all"].append((lab, g * cs["N"], Md * (fx + fy), cls._punch_rows(
                        g * cs["N"], Md * (fx + fy), X, Y, dA, net, c, d, B)))
        Mb, Mh, Vb = gov["mb"][0] * 1000, gov["mt"][0] * 1000, gov["v"][0] * 1000  # per 1 m
        if not quiet:
            cls._leg_table(calc, inp, gG, gGf, gQ, hl)
            # key results for the summary: the case with the largest leg compression, M along
            # the diagonal towards leg 1 (legs 2 and 4 carry N/4, leg 3 the tension)
            best = None
            for cs in inp["cases"]:
                fk = (cs["M"] + cs["H"] * hl) / (math.sqrt(2) * a)
                Fk = [cs["N"] / 4 + fk, cs["N"] / 4, cs["N"] / 4 - fk, cs["N"] / 4]
                Fd = [gG * cs["N"] / 4 + gQ * fk, gG * cs["N"] / 4,
                      gGf * cs["N"] / 4 - gQ * fk, gG * cs["N"] / 4]
                if best is None or Fd[0] > best[2][0]:
                    best = (cs["name"], Fk, Fd)
            calc.crane_key = {"legs": best, "mb": Mb, "mt": Mh, "vb": Vb, "VRc": vrc * d * 1000,
                              "Asb": Asb, "Ast": Ast}
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
            calc.crane_key.update(Asb_req=As_req, Asb_min=As_min)
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
                calc.crane_key["Ast_req"] = Asr
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
        # ---- punching (mast base as a column and the most compressed leg), links if needed
        nu = 0.6 * (1 - fck / 250)
        vmax = na.punch_vmax * nu * fcd
        if not quiet:
            calc.crane_marks.append(len(calc.checks))
        links = cls._punching(calc, quiet, inp, gov, na, B, c, d, vrc, vmax, fck, fyk)
        if emb:
            cls._embedded(calc, quiet, inp, gov, B, h, fcd, fck, na)
        # ---- anchors
        if not quiet:
            calc.heading("Mast anchors", 2)
            T = gov["ten"][0]
            if T > 0 and emb:
                calc.text("The tension is anchored at the feet of the embedded section; the "
                          "pull-out through the concrete is checked above.")
            elif T > 0:
                calc.formula("T_leg", "M_d s_max / Σs² − γ_G,fav N/4", T, "kN",
                             "Design tension in the most stressed mast anchor", dp=1)
                calc.note("Anchor the mast anchors (manufacturer's anchor frame or cast-in "
                          "anchors) below the bottom bars, or tie them with hanger bars for "
                          "T_leg, following the manufacturer's details.")
            else:
                calc.text("No tension in the mast anchors.")
        return links

    @staticmethod
    def _leg_table(calc, inp, gG, gGf, gQ, hl) -> None:
        a = inp["a"]
        calc.heading("Forces on each leg", 2)
        calc.text("Leg force F = N/4 ± M s / Σs² with M at the level of the leg feet{lv}: along "
                  "the axis two legs carry ±M/(2a), along the diagonal one leg +M/(√2 a) and "
                  "the opposite one −M/(√2 a), the other two N/4. Compression +, tension −. "
                  "Design: γ_G N/4 + γ_Q M… (compression), γ_G,fav N/4 − γ_Q M… (tension).",
                  lv=calc.tr(" (M + H h_emb, embedded anchor)") if hl else "")
        rows = []
        for cs in inp["cases"]:
            for dname, lev in (("axis", a / 2), ("diagonal", a / math.sqrt(2))):
                Mk = cs["M"] + cs["H"] * hl
                fk = Mk * lev / (a * a)
                rows.append([cs["name"], calc.tr(dname), f"{(cs['N'] / 4 + fk) / 1e3:.1f}",
                             f"{(cs['N'] / 4 - fk) / 1e3:.1f}",
                             f"{(gG * cs['N'] / 4 + gQ * fk) / 1e3:.1f}",
                             f"{(gGf * cs['N'] / 4 - gQ * fk) / 1e3:.1f}"])
        calc.table(["Case", "M along", "F_max,k [kN]", "F_min,k [kN]", "F_max,d [kN]",
                    "F_min,d [kN]"], rows, "Forces on the mast legs (characteristic and design)")

    @staticmethod
    def _embedded(calc, quiet, inp, gov, B, h, fcd, fck, na) -> None:
        """Embedded anchor section: fits in the base, bearing under the feet (6.7), pull-out of
        the tension legs through the concrete above the feet (6.4.4 on an upward perimeter)."""
        a, cl = inp["a"], inp["cl"]
        hemb, cov = inp["hemb"], inp["cover"]
        dt = float(inp["dt"])
        if not quiet:
            calc.heading("Embedded anchor section", 2)
            calc.text("The manufacturer's anchor section is cast into the base and its feet sit "
                      "just above the bottom bars. The anchor itself and its connection to the "
                      "mast are the manufacturer's responsibility; here the concrete around it "
                      "is checked.")
        # bearing under one foot (6.7): the load spreads through the concrete below the foot,
        # depth h − h_emb ≥ b2 − b1, b2 ≤ 3 b1 (Figure 6.29)
        F = gov["leg"][0]
        b2 = min(cl + max(h - hemb, 0.0), 3 * cl)
        FRdu = min(cl * cl * fcd * b2 / cl, 3 * cl * cl * fcd)
        if not quiet:
            calc.formula("b_2", "min(c_l + (h − h_emb), 3c_l)", b2, "mm",
                         "Spread of the load below the foot", ref="6.7(2), Fig. 6.29", dp=0)
            calc.formula("F_Rdu", "A_c0 f_cd √(A_c1/A_c0) ≤ 3 f_cd A_c0", FRdu, "kN",
                         "Bearing resistance under one foot", ref="EN 1992-1-1 Eq. 6.63", dp=1)
        calc.check("Bearing under the foot: F_leg ≤ F_Rdu", F, FRdu, "kN", "6.7",
                   hint="Larger foot plates or a higher concrete class.")
        # pull-out: the tension is resisted by a cone through the concrete above the feet,
        # with the top bars as the tension reinforcement of that (upside-down) slab
        dup = hemb - cov - dt
        if dup <= 0:
            calc.check("Pull-out: concrete above the feet", 1.0, 0.0, "", "6.4.4",
                       hint="Deeper embedment.")
            return
        Ast = bar_area(dt) * 1000 / inp["st"]
        k = min(1 + math.sqrt(200 / dup), 2.0)
        rho = min(Ast / (1000 * dup), 0.02)
        vrc = max(0.18 / na.gamma_c * k * (100 * rho * fck) ** (1 / 3),
                  0.035 * k ** 1.5 * math.sqrt(fck))
        r = 2 * dup
        u1 = rounded_rect_length(a / 2, a / 2, cl, cl, r, B)
        u2 = rounded_rect_length(a / 2, 0.0, cl, a + cl, r, B)
        T1, T2 = max(gov["ten"][0], 0.0), 2 * max(gov["ten2"][0], 0.0)
        v1, v2 = T1 / (u1 * dup), T2 / (u2 * dup)
        if not quiet:
            calc.text("Pull-out of the tension legs: control perimeter at 2d_up around one foot "
                      "(M along the diagonal) or around the two feet of one side (M along the "
                      "axis), clipped at the edges of the base; v_Rd,c without the 2d/a "
                      "enhancement and without the weight of the concrete (conservative).")
            calc.formula("d_up", "h_emb − c − Ø_top", dup, "mm", dp=0)
            calc.formula("v_Rd,c,up", "max(0.18/γ_c k (100ρ f_ck)^(1/3), v_min)", vrc,
                         "N/mm²", ref="Eq. 6.47", dp=3)
            calc.formula("u_up,1", "4c_l + 4πd_up (inside the base)", u1, "mm", dp=0)
            calc.formula("v_up,1", "T_diag / (u d_up)", v1, "N/mm²", dp=3)
            calc.formula("u_up,2", "2(a + 2c_l) + 4πd_up (inside the base)", u2, "mm", dp=0)
            calc.formula("v_up,2", "2 T_axis / (u d_up)", v2, "N/mm²", dp=3)
        calc.check("Pull-out of one leg: v_up ≤ v_Rd,c", v1, vrc, "N/mm²", "6.4.4",
                   hint="Deeper embedment, more top bars or a larger base.")
        calc.check("Pull-out of two legs: v_up ≤ v_Rd,c", v2, vrc, "N/mm²", "6.4.4",
                   hint="Deeper embedment, more top bars or a larger base.")

    @staticmethod
    def _punch_rows(VN, Mb, X, Y, dA, net, c, d, B):
        """Control perimeters around the mast base (square c) at a = 0.05d, 0.10d, … up to the
        edge of the base: (a, u, V_Ed,red, β, v_Ed).  M_b is the moment that enters β (the
        two components added for the diagonal)."""
        rows = []
        dist = np.hypot(np.clip(np.abs(X) - c / 2, 0, None), np.clip(np.abs(Y) - c / 2, 0, None))
        k = 1
        while c / 2 + 0.05 * d * k <= B / 2:
            ap = 0.05 * d * k
            u = 4 * c + 2 * math.pi * ap
            Vred = max(VN - float((net * (dist <= ap)).sum() * dA), 0.0)
            W1 = c * c / 2 + c * c + 4 * c * ap + 4 * ap * ap + math.pi * ap * c
            beta = 1 + 0.6 * Mb / Vred * u / W1 if Vred > 0 else 1.0
            rows.append((ap, u, Vred, beta, beta * Vred / (u * d)))
            k += 1
        return rows

    @classmethod
    def _punching(cls, calc, quiet, inp, gov, na, B, c, d, vrc, vmax, fck, fyk) -> dict:
        """EN 1992-1-1 6.4.4(2) without links; with links Eq. 6.52, 6.4.5(4), 9.4.3."""
        a, cl = inp["a"], inp["cl"]
        vR = lambda ap: vrc * 2 * d / ap if ap <= 2 * d else vrc  # noqa: E731
        use = inp["links"]
        dsw = float(inp["dsw"])
        A1 = bar_area(dsw)
        fywd = fyk / na.gamma_s
        fywef = min(250 + 0.25 * d, fywd)
        sr = math.floor(0.75 * d / 25) * 25
        s0 = math.floor(0.5 * d / 25) * 25
        rmin = 0.08 * math.sqrt(fck) / fyk
        cs_term = lambda Asw, u: 1.5 * d / sr * Asw * fywef / (u * d)  # noqa: E731
        out = {"frame": None, "leg": None, "c": c, "d": d}
        # ---------------------------------------------------------- mast base
        worst, req, aout = None, 0.0, 0.0
        for lab, VN, Mb, rows in gov["pun_all"]:
            for ap, u, Vred, beta, vEd in rows:
                r = vEd / vR(ap)
                if ap <= 2 * d and (worst is None or r > worst[0]):
                    worst = (r, lab, ap, u, Vred, beta, vEd, vR(ap))
                if r > 1:
                    aout = max(aout, ap)
                    if ap <= 2 * d:
                        req = max(req, (vEd - 0.75 * vR(ap)) * u * sr / (1.5 * fywef))
        edge = B / 2 - c / 2
        if not quiet:
            calc.heading("Punching of the mast base (6.4.4(2))", 2)
            calc.text("The mast base is taken as a square column c = a + c_l. Control perimeters "
                      "0 < a_p ≤ 2d inside the base are searched; the net soil reaction inside "
                      "each one is deducted (Eq. 6.48) and the moment is taken with Eq. 6.51 "
                      "(k = 0.6, both components added — conservative).")
        if worst is None:
            if not quiet:
                calc.text("Every control perimeter within 2d of the mast base lies outside the "
                          "base — punching of the mast base is not critical; beam shear governs.")
        else:
            r, lab, ap, u, Vred, beta, vEd, vRd = worst
            if not quiet:
                calc.text("Governing: {c}.", c=lab)
                calc.formula("a_crit", "critical distance, 0 < a_p ≤ 2d", ap, "mm", dp=0)
                calc.formula("u", "4c + 2πa_p", u, "mm", "Control perimeter", dp=0)
                calc.formula("V_Ed,red", "γ N − Σ (q − w) ΔA inside u", Vred, "kN",
                             ref="Eq. 6.48", dp=1)
                calc.formula("β", "1 + k (M_x + M_y)/V_Ed,red · u/W_1", beta, "",
                             ref="Eq. 6.51", dp=3)
                calc.formula("v_Ed,p", "β V_Ed,red / (u d)", vEd, "N/mm²", dp=3)
                calc.formula("v_Rd,p", "max(C_Rd,c k (100ρ f_ck)^(1/3), v_min) 2d/a_p", vRd,
                             "N/mm²", ref="Eq. 6.50", dp=3)
            if r <= 1 or not use:
                calc.check("Punching of the mast base: v_Ed ≤ v_Rd", vEd, vRd, "N/mm²",
                           "6.4.4(2)", hint=HINT_PUNCH)
                if r <= 1 and not quiet:
                    calc.text("No punching reinforcement is needed around the mast base.")
            else:
                out["frame"] = cls._links(calc, quiet, "frame", req, aout, edge, worst, d, sr,
                                          s0, A1, dsw, fywd, fywef, rmin, na, c, gov, vR,
                                          cs_term, inp)
        # ---------------------------------------------------------- one leg
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
            calc.formula("v_Rd,leg", "max(C_Rd,c k (100ρ f_ck)^(1/3), v_min) 2d/a_p", vRd_l,
                         "N/mm²", ref="Eq. 6.50", dp=3)
        if vEd_l <= vRd_l or not use:
            calc.check("Punching under a leg: v_Ed ≤ v_Rd", vEd_l, vRd_l, "N/mm²", "6.4.4(2)",
                       hint=HINT_PUNCH)
            if vEd_l <= vRd_l and not quiet:
                calc.text("No punching reinforcement is needed around the legs.")
        else:
            req_l = (vEd_l - 0.75 * vRd_l) * u_leg * sr / (1.5 * fywef)
            out["leg"] = cls._links(calc, quiet, "leg", req_l, amax, amax,
                                    (vEd_l / vRd_l, gov["leg"][1], amax, u_leg, F, 1.0, vEd_l,
                                     vRd_l), d, sr, s0, A1, dsw, fywd, fywef, rmin, na, cl, gov,
                                    vR, cs_term, inp)
        v0 = F / (4 * cl * d)
        if not quiet:
            calc.formula("v_Ed,0", "F_leg / (4 c_l d)", v0, "N/mm²",
                         "Shear at the face of the leg base plate", dp=3)
            calc.formula("v_Rd,max", f"{na.punch_vmax:g} ν f_cd, ν = 0.6(1 − f_ck/250)", vmax,
                         "N/mm²", ref="6.4.5(3)", dp=3)
        calc.check("Leg face: v_Ed,0 ≤ v_Rd,max", v0, vmax, "N/mm²", "6.4.5(3)",
                   hint="Larger leg base plates or a higher concrete class — links cannot "
                        "raise this limit.")
        return out

    @staticmethod
    def _links(calc, quiet, where, req, aout, edge, worst, d, sr, s0, A1, dsw, fywd, fywef,
               rmin, na, c, gov, vR, cs_term, inp) -> dict:
        """Perimeters of vertical link legs (α = 90°) for one loaded area (square c)."""
        r, lab, ap, u, Vred, beta, vEd, vRd = worst
        frame = where == "frame"
        kd = na.punch_kout * d
        if frame:
            n_per = max(2, math.ceil((aout - kd - s0) / sr - 1e-9) + 1)
            # the perimeters stay inside the base (cover 75 mm to the edge)
            n_max = max(int((edge - 75 - s0) // sr) + 1, 1)
            capped = n_per > n_max
            n_per = min(n_per, n_max) if capped else n_per
        else:
            n_per, capped = 2, False
        radii = [s0 + i * sr for i in range(n_per)]
        legs, rowsout = [], []
        for ri in radii:
            ui = 4 * c + 2 * math.pi * ri
            st_max = min(1.5 * d if ri <= 2 * d else 2 * d, A1 * 1.5 / (rmin * sr))
            n = max(math.ceil(req / A1 - 1e-9), math.ceil(ui / st_max - 1e-9), 4)
            legs.append(n)
            rowsout.append([f"{ri:.0f}", f"{ui / 1000:.2f}", str(n), f"{ui / n:.0f}"])
        Asw = min(legs) * A1
        vRdcs = 0.75 * vRd + cs_term(Asw, u)
        if not quiet:
            calc.heading("Punching reinforcement around the mast base (6.4.5, 9.4.3)" if frame
                         else "Punching reinforcement around each leg (6.4.5, 9.4.3)", 2)
            calc.text("Vertical links Ø{dsw:.0f} (α = 90°). Eq. 6.52 with the concrete term "
                      "0.75 v_Rd,c taken with the 2d/a_p enhancement of 6.4.4(2), as in the check "
                      "without links (interpretation for column bases); u_out where v_Ed ≤ v_Rd,c "
                      "again (6.4.5(4)).", dsw=dsw)
            calc.formula("f_ywd,ef", "250 + 0.25 d ≤ f_ywd", fywef, "N/mm²", ref="Eq. 6.53",
                         dp=0)
            calc.formula("s_r", "≤ 0.75 d (rounded to 25 mm)", sr, "mm", ref="9.4.3(1)", dp=0)
            calc.formula("s_0", "0.3d ≤ s_0 ≤ 0.5d", s0, "mm",
                         "First perimeter from the face", ref="9.4.3(4)", dp=0)
            calc.formula("A_sw,req" if frame else "A_sw,req,leg",
                         "(v_Ed − 0.75 v_Rd,c) u s_r / (1.5 f_ywd,ef)", req, "mm²",
                         "Links per perimeter (most onerous perimeter)", ref="Eq. 6.52", dp=0)
            if frame:
                calc.formula("a_out", "last perimeter with v_Ed > v_Rd,c, + 0.05d", aout, "mm",
                             "u_out,ef from the face", ref="Eq. 6.54", dp=0)
                calc.formula("r_last,min", f"a_out − {na.punch_kout:g} d", aout - kd, "mm",
                             ref="6.4.5(4)", dp=0)
            calc.table(["Perimeter r [mm]", "u [m]", "Link legs", "s_t [mm]"], rowsout,
                       "Perimeters of link legs, measured from the face of the loaded area")
            calc.formula("v_Rd,cs" if frame else "v_Rd,cs,leg",
                         "0.75 v_Rd,c + 1.5 (d/s_r) A_sw f_ywd,ef / (u d)", vRdcs, "N/mm²",
                         ref="Eq. 6.52", dp=3)
            if not frame:
                calc.text("Two perimeters of link legs around each of the four legs (9.4.3(1)), "
                          "inside a_p; where they overlap the links of the mast base, the denser "
                          "arrangement governs.")
            if capped:
                calc.note("u_out reaches the edge of the base: the link perimeters run up to the "
                          "edge — a thicker base is usually the better solution.")
        calc.check("Punching with links: v_Ed ≤ v_Rd,cs" if frame
                   else "Punching under a leg with links: v_Ed ≤ v_Rd,cs", vEd, vRdcs, "N/mm²",
                   "6.4.5(1)", hint="Larger or more link legs, or a thicker base.")
        if frame and not capped:
            calc.check_min("Last link perimeter ≥ a_out − k d", radii[-1], aout - kd, "mm",
                           "6.4.5(4)", hint="Add a perimeter of links.")
        st = max(float(x[3]) for x in rowsout)
        calc.check_min("Link leg area ≥ A_sw,min", A1,
                       rmin * sr * st / 1.5, "mm²", "Eq. 9.11",
                       hint="Larger link diameter or closer link legs.")
        if not quiet:
            calc.formula("n_sw" if frame else "n_sw,leg",
                         "Σ link legs" if frame else "4 legs × Σ link legs", sum(legs) * (
                             1 if frame else 4), "", "Number of link legs", dp=0)
        return {"radii": radii, "legs": legs, "dsw": dsw}

    # ------------------------------------------------------------------- 3D
    @staticmethod
    def _scene(calc, inp, links=None) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        B, h, a, cl = m(inp["B"]), m(inp["h"]), m(inp["a"]), m(inp["cl"])
        sc = Scene3D("crane_base", calc.tr)
        for key, label in (("base", "Base"), ("bars", "Reinforcement"),
                           ("links", "Punching links"), ("mast", "Mast"), ("soil", "Soil"),
                           ("loads", "Loads")):
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
        y1, y2 = top - h + cov, top - cov
        for key, cx, cy, size in (("frame", 0.0, 0.0, a + cl),
                                  *(("leg", sx * a / 2, sz * a / 2, cl)
                                    for sx in (-1, 1) for sz in (-1, 1))):
            lk = (links or {}).get(key)
            if not lk:
                continue
            for ri, n in zip(lk["radii"], lk["legs"]):
                ring = [(px, top + 0.01, pz) for px, pz in perimeter_points(cx, cy, size, m(ri), 96)
                        if max(abs(px), abs(pz)) <= B / 2 - cov]
                if len(ring) > 2:
                    sc.line("links", ring + ring[:1], PALETTE["punch"], dashed=True)
                for px, pz in perimeter_points(cx, cy, size, m(ri), n):
                    if max(abs(px), abs(pz)) <= B / 2 - cov:
                        sc.cylinder("links", (px, y1, pz), (px, y2, pz), m(lk["dsw"]) / 2,
                                    PALETTE["punch"])
        H = 3.0
        emb = inp["fixing"] == FIXING[1]
        foot = top - m(inp["hemb"]) if emb else top
        for sx in (-1, 1):
            for sz in (-1, 1):
                sc.box("mast", (sx * a / 2, foot + 0.03, sz * a / 2), (cl, 0.06, cl),
                       PALETTE["steel"])
                sc.cylinder("mast", (sx * a / 2, foot, sz * a / 2),
                            (sx * a / 2, top + H, sz * a / 2), 0.07, "#e0a800")
        if emb:   # bracing of the embedded anchor section
            for y0 in (foot + 0.1, (foot + top) / 2):
                ring = [(-a / 2, y0, -a / 2), (a / 2, y0, -a / 2), (a / 2, y0, a / 2),
                        (-a / 2, y0, a / 2), (-a / 2, y0, -a / 2)]
                sc.line("mast", ring, PALETTE["steel"])
        # force on each leg: the case with the largest M, M along the diagonal towards leg 1
        cs = max(inp["cases"], key=lambda r: r["M"])
        if cs.get("legs"):
            Fk = cs["legs"]
        else:
            f = (cs["M"] + cs["H"] * (inp["hemb"] if emb else 0.0)) / (math.sqrt(2) * inp["a"])
            Fk = [cs["N"] / 4 + f, cs["N"] / 4, cs["N"] / 4 - f, cs["N"] / 4]
        for (i, j), F, num in zip(LEGXY, Fk, range(1, 5)):
            sc.label("loads", f"{num}: {F / 1e3:+.0f} kN", (i * a / 2, top + 0.5, -j * a / 2),
                     "force" if F >= 0 else "result")
        for y0 in range(int(H)):
            for (x1, z1), (x2, z2) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)),
                                       ((-1, 1), (-1, -1))):
                sc.line("mast", [(x1 * a / 2, top + y0, z1 * a / 2),
                                 (x2 * a / 2, top + y0 + 1, z2 * a / 2)], "#e0a800")
        sc.arrow("loads", (0, top + H + 1.5, 0), (0, -1, 0), 1.2, PALETTE["load"])
        sc.label("loads", f"{cs['name']}: N = {cs['N'] / 1e3:.0f} kN, M = {cs['M'] / 1e6:.0f} kNm",
                 (0, top + H + 1.8, 0), "force")
        sc.label("base", f"B = {B:.2f} m, h = {h:.2f} m", (B / 2 + 0.3, top - h / 2, B / 2),
                 "result")
        return sc.to_dict()


def perimeter_points(cx, cy, c, r, n):
    """n points equally spaced along the rounded square at distance r around a square c."""
    h = c / 2
    segs = []
    for k in range(4):
        ang0 = k * math.pi / 2
        ux, uy = math.cos(ang0), math.sin(ang0)
        vx, vy = -uy, ux
        segs.append(("line", (cx + ux * (h + r) - vx * h, cy + uy * (h + r) - vy * h),
                     (vx, vy), c))
        segs.append(("arc", (cx + (ux + vx) * h, cy + (uy + vy) * h), ang0, math.pi / 2 * r))
    total = 4 * c + 2 * math.pi * r
    pts = []
    for i in range(n):
        t = (i + 0.5) * total / n
        for kind, p0, dirn, length in segs:
            if t <= length or (kind, p0) == segs[-1][:2]:
                if kind == "line":
                    pts.append((p0[0] + dirn[0] * t, p0[1] + dirn[1] * t))
                else:
                    ang = dirn + (t / r if r > 0 else 0)
                    pts.append((p0[0] + r * math.cos(ang), p0[1] + r * math.sin(ang)))
                break
            t -= length
    return pts


def _as_req(M, d, fcd, fyd):
    """Required area for M on a 1000 mm wide strip (rectangular block λ = 0.8, η = 1, 3.1.7)."""
    mu = M / (1000 * d * d * fcd)
    if mu >= 0.5:
        return math.inf
    xi = 1.25 * (1 - math.sqrt(1 - 2 * mu))
    z = min(d * (1 - 0.4 * xi), 0.95 * d)
    return M / (fyd * z)
