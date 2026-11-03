"""Generate a complete building model from a grid — the quick way in.

The engineer gives grid spans, storey heights, member sizes and area loads;
the builder creates nodes, columns, beams, fixed bases, a rigid diaphragm
per floor, and the gravity load cases:

* ``G``: self-weight of columns and beams (beam weight below the slab only,
  so the slab overlap is not counted twice), slab self-weight, finishes and
  facade walls on the perimeter beams;
* ``Q``: imposed load (roof value on the top floor).

Slab loads go to the beams by the 45° yield-line rule (triangular /
trapezoidal loads), the standard tributary-area method for two-way slabs.
Grid lines along X are numbered 1, 2, 3…, along Y lettered A, B, C…; node
``A1`` is at the first X and first Y line, column ``C2.A1`` is that column
in storey 2, beam ``B2.A1-A2`` the beam from A1 to A2 at the top of storey 2.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field

from .model import Material, Model, Section, StructureError

CONCRETE_WEIGHT = 25e-6  # N/mm³


def y_label(j: int) -> str:
    s, j = "", j
    while True:
        s = string.ascii_uppercase[j % 26] + s
        j = j // 26 - 1
        if j < 0:
            return s


def grid_label(i: int, j: int) -> str:
    return f"{y_label(j)}{i + 1}"


def node_id(i: int, j: int, k: int) -> str:
    return f"{grid_label(i, j)}@{k}"


@dataclass
class BuildingSpec:
    x_spans: list[float]               # mm
    y_spans: list[float]               # mm
    heights: list[float]               # storey heights, bottom up, mm
    col_b: float = 400.0               # along X, mm
    col_h: float = 400.0               # along Y, mm
    beam_b: float = 250.0
    beam_h: float = 500.0
    slab_t: float = 180.0
    fck: float = 25.0
    cracked: float = 0.5               # EN 1998-1 4.3.1(7): 50 % of the uncracked stiffness
    g_finish: float = 1.5e-3           # N/mm² (1.5 kN/m²)
    q: float = 2.0e-3                  # N/mm² (2.0 kN/m², category A)
    q_roof: float = 2.0e-3
    g_wall: float = 8.0                # N/mm (8 kN/m) on perimeter beams, not on the roof
    walls: list[dict] = field(default_factory=list)  # {"at": "A1", "dir": "X"|"Y", "L", "t"} mm
    labels: dict[str, str] = field(default_factory=dict)

    def check(self) -> None:
        for name, vals in (("X spans", self.x_spans), ("Y spans", self.y_spans),
                           ("storey heights", self.heights)):
            if not vals:
                raise StructureError("Give at least one value for {w}", w=name)
            if any(v <= 0 for v in vals):
                raise StructureError("All {w} must be greater than zero", w=name)
        if self.beam_h <= self.slab_t:
            raise StructureError("The beam depth must be greater than the slab thickness")
        nx, ny = len(self.x_spans) + 1, len(self.y_spans) + 1
        valid = {grid_label(i, j) for i in range(nx) for j in range(ny)}
        seen = set()
        for w in self.walls:
            at = str(w.get("at", "")).strip().upper()
            if at not in valid:
                raise StructureError("Wall at {g}: there is no such grid point (use e.g. A1)",
                                     g=at)
            if at in seen:
                raise StructureError("Two walls at grid point {g}", g=at)
            seen.add(at)
            if w.get("dir") not in ("X", "Y"):
                raise StructureError("Wall at {g}: direction must be X or Y", g=at)
            if not (w.get("L", 0) > 0 and w.get("t", 0) > 0):
                raise StructureError("Wall at {g}: give its length and thickness", g=at)


def tributary(side: float, other: float, p: float) -> list[tuple[float, float, float, float]]:
    """45° rule: load profile on one edge beam of a slab panel.

    Returns segments ``(x1, x2, w1, w2)`` (N/mm) along an edge of length
    ``side`` of a ``side × other`` panel carrying ``p`` N/mm²: triangle when
    the edge is the short side, trapezoid when it is the long side.
    """
    c = min(side, other) / 2
    peak = p * c
    segs = [(0.0, c, 0.0, peak)]
    if side - 2 * c > 1e-9:
        segs.append((c, side - c, peak, peak))
    segs.append((side - c, side, peak, 0.0))
    return segs


def build(spec: BuildingSpec) -> tuple[Model, dict]:
    """Create the model; returns ``(model, info)`` with grid/level data for reports and 3D."""
    spec.check()
    xs = [0.0]
    for s in spec.x_spans:
        xs.append(xs[-1] + s)
    ys = [0.0]
    for s in spec.y_spans:
        ys.append(ys[-1] + s)
    zs = [0.0]
    for h in spec.heights:
        zs.append(zs[-1] + h)
    nx, ny, ns = len(xs), len(ys), len(spec.heights)
    conc = Material.concrete(spec.fck, spec.cracked)
    col = Section.rectangle(spec.col_b, spec.col_h, f"{spec.col_b:g}×{spec.col_h:g}")
    beam = Section.rectangle(spec.beam_b, spec.beam_h, f"{spec.beam_b:g}×{spec.beam_h:g}")
    m = Model()
    m.case("G")
    m.case("Q")
    for k, z in enumerate(zs):
        for i, x in enumerate(xs):
            for j, y in enumerate(ys):
                m.node(node_id(i, j, k), x, y, z)
                if k == 0:
                    m.support(node_id(i, j, k), "fixed")
    wall_at = {str(w["at"]).strip().upper(): w for w in spec.walls}
    wall_sec = {}
    for g, w in wall_at.items():
        b, h = (w["L"], w["t"]) if w["dir"] == "X" else (w["t"], w["L"])
        wall_sec[g] = Section.rectangle(b, h, f"{w['L']:g}×{w['t']:g}")
    xs_idx = {grid_label(i, j): (i, j) for i in range(nx) for j in range(ny)}
    for g, w in wall_at.items():
        i, j = xs_idx[g]
        spans = ([xs[i] - xs[i - 1]] if i else []) + ([xs[i + 1] - xs[i]] if i < nx - 1 else []) \
            if w["dir"] == "X" else \
            ([ys[j] - ys[j - 1]] if j else []) + ([ys[j + 1] - ys[j]] if j < ny - 1 else [])
        if spans and w["L"] / 2 > 0.45 * min(spans):
            raise StructureError("Wall at {g} is too long for the adjacent span — the beam would "
                                 "have no flexible length", g=g)

    def offset(g: str, along: str) -> float:
        """Rigid zone of a beam framing along ``along`` into grid point ``g``."""
        w = wall_at.get(g)
        return w["L"] / 2 if w and w["dir"] == along else 0.0

    w_beam = -CONCRETE_WEIGHT * spec.beam_b * (spec.beam_h - spec.slab_t)
    p_g = CONCRETE_WEIGHT * spec.slab_t + spec.g_finish
    columns, beams_x, beams_y, walls = [], [], [], []
    for k in range(1, ns + 1):
        roof = k == ns
        for i in range(nx):
            for j in range(ny):
                g = grid_label(i, j)
                if g in wall_at:
                    cid, sec = f"W{k}.{g}", wall_sec[g]
                    walls.append(cid)
                else:
                    cid, sec = f"C{k}.{g}", col
                    columns.append(cid)
                m.member(cid, node_id(i, j, k - 1), node_id(i, j, k), sec, conc)
                m.load_member("G", cid, wz=-CONCRETE_WEIGHT * sec.A)
        for j in range(ny):
            for i in range(nx - 1):
                a, b = grid_label(i, j), grid_label(i + 1, j)
                bid = f"B{k}.{a}-{b}"
                m.member(bid, node_id(i, j, k), node_id(i + 1, j, k), beam, conc,
                         offset_i=offset(a, "X"), offset_j=offset(b, "X"))
                m.load_member("G", bid, wz=w_beam)
                if not roof and j in (0, ny - 1) and spec.g_wall:
                    m.load_member("G", bid, wz=-spec.g_wall)
                beams_x.append(bid)
        for i in range(nx):
            for j in range(ny - 1):
                a, b = grid_label(i, j), grid_label(i, j + 1)
                bid = f"B{k}.{a}-{b}"
                m.member(bid, node_id(i, j, k), node_id(i, j + 1, k), beam, conc,
                         offset_i=offset(a, "Y"), offset_j=offset(b, "Y"))
                m.load_member("G", bid, wz=w_beam)
                if not roof and i in (0, nx - 1) and spec.g_wall:
                    m.load_member("G", bid, wz=-spec.g_wall)
                beams_y.append(bid)
        # slab panels → edge beams
        q = spec.q_roof if roof else spec.q
        for i in range(nx - 1):
            for j in range(ny - 1):
                lx, ly = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
                edges = [  # (beam id, edge length, other dimension)
                    (f"B{k}.{grid_label(i, j)}-{grid_label(i + 1, j)}", lx, ly),
                    (f"B{k}.{grid_label(i, j + 1)}-{grid_label(i + 1, j + 1)}", lx, ly),
                    (f"B{k}.{grid_label(i, j)}-{grid_label(i, j + 1)}", ly, lx),
                    (f"B{k}.{grid_label(i + 1, j)}-{grid_label(i + 1, j + 1)}", ly, lx),
                ]
                for bid, a, b in edges:
                    for case, p in (("G", p_g), ("Q", q)):
                        if not p:
                            continue
                        for x1, x2, w1, w2 in tributary(a, b, p):
                            m.load_member(case, bid, wz=-w1, w2=(0.0, 0.0, -w2),
                                          a=x1 / a, b=x2 / a)
        m.diaphragm(f"L{k}", [node_id(i, j, k) for i in range(nx) for j in range(ny)])
    info = {"xs": xs, "ys": ys, "zs": zs, "columns": columns, "walls": walls,
            "wall_spec": wall_at, "beams_x": beams_x,
            "beams_y": beams_y, "concrete": conc, "col": col, "beam": beam,
            "plan_area": xs[-1] * ys[-1]}
    return m, info
