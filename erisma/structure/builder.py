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

import numpy as np

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
    # free layout (typical floor, all storeys):
    #   omit_columns: ["B2", …] grid points without a column;
    #   omit_beams: ["A1-A2", …] grid segments without a beam;
    #   openings: ["A1", …] slab panels (named by their corner with the lowest indices) left open;
    #   col_sizes: {"A1": [b, h]} and beam_sizes: {"A1-A2": [b, h]} in mm override the defaults.
    layout: dict = field(default_factory=dict)
    # foundation: None = fixed base; {"B", "bw", "h" (mm), "ks" (N/mm³), "n"} = foundation beams
    # (inverted T: flange width B, web bw, depth h) on Winkler springs along the grid lines
    foundation: dict | None = None
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
        segs = set(grid_segments(nx, ny))
        panels = {grid_label(i, j) for i in range(nx - 1) for j in range(ny - 1)}
        lay = self.layout or {}
        for g in list(lay.get("omit_columns", [])) + list(lay.get("col_sizes", {})):
            if g not in valid:
                raise StructureError("Layout: there is no grid point {g}", g=g)
        for key in list(lay.get("omit_beams", [])) + list(lay.get("beam_sizes", {})):
            if key not in segs:
                raise StructureError("Layout: there is no grid segment {g} (e.g. A1-A2)", g=key)
        for g in lay.get("openings", []):
            if g not in panels:
                raise StructureError("Layout: there is no slab panel {g}", g=g)
        for key, bh in list(lay.get("col_sizes", {}).items()) + \
                list(lay.get("beam_sizes", {}).items()):
            if len(bh) != 2 or min(bh) < 150:
                raise StructureError("Layout: the section of {g} must be two sizes ≥ 150 mm",
                                     g=key)
        for key, bh in lay.get("beam_sizes", {}).items():
            if bh[1] <= self.slab_t:
                raise StructureError("Beam {g}: the depth must be greater than the slab "
                                     "thickness", g=key)


def grid_segments(nx: int, ny: int) -> list[str]:
    """All grid segments ``"A1-A2"`` (along X) and ``"A1-B1"`` (along Y)."""
    out = [f"{grid_label(i, j)}-{grid_label(i + 1, j)}" for j in range(ny) for i in range(nx - 1)]
    out += [f"{grid_label(i, j)}-{grid_label(i, j + 1)}" for i in range(nx) for j in range(ny - 1)]
    return out


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

    lay = spec.layout or {}
    omit_cols = set(lay.get("omit_columns", []))
    omit_beams = set(lay.get("omit_beams", []))
    openings = set(lay.get("openings", []))
    col_size = {g: tuple(map(float, v)) for g, v in lay.get("col_sizes", {}).items()}
    beam_size = {g: tuple(map(float, v)) for g, v in lay.get("beam_sizes", {}).items()}
    sec_cache: dict[tuple, Section] = {}

    def rect(b: float, h: float) -> Section:
        if (b, h) not in sec_cache:
            sec_cache[(b, h)] = Section.rectangle(b, h, f"{b:g}×{h:g}")
        return sec_cache[(b, h)]

    p_g = CONCRETE_WEIGHT * spec.slab_t + spec.g_finish
    columns, beams_x, beams_y, walls = [], [], [], []
    sizes: dict[str, tuple[float, float]] = {}  # member → (b, h) of its rectangle
    for k in range(1, ns + 1):
        roof = k == ns
        for i in range(nx):
            for j in range(ny):
                g = grid_label(i, j)
                if g in wall_at:
                    cid, sec = f"W{k}.{g}", wall_sec[g]
                    walls.append(cid)
                elif g in omit_cols:
                    continue
                else:
                    bh = col_size.get(g, (spec.col_b, spec.col_h))
                    cid, sec = f"C{k}.{g}", rect(*bh)
                    sizes[cid] = bh
                    columns.append(cid)
                m.member(cid, node_id(i, j, k - 1), node_id(i, j, k), sec, conc)
                m.load_member("G", cid, wz=-CONCRETE_WEIGHT * sec.A)
                if k == 1 and not spec.foundation:
                    m.support(node_id(i, j, 0), "fixed")

        def add_beam(i1, j1, i2, j2, along, perimeter, store):
            a, b = grid_label(i1, j1), grid_label(i2, j2)
            key = f"{a}-{b}"
            if key in omit_beams:
                return
            bh = beam_size.get(key, (spec.beam_b, spec.beam_h))
            bid = f"B{k}.{key}"
            m.member(bid, node_id(i1, j1, k), node_id(i2, j2, k), rect(*bh), conc,
                     offset_i=offset(a, along), offset_j=offset(b, along))
            sizes[bid] = bh
            m.load_member("G", bid, wz=-CONCRETE_WEIGHT * bh[0] * (bh[1] - spec.slab_t))
            if not roof and perimeter and spec.g_wall:
                m.load_member("G", bid, wz=-spec.g_wall)
            store.append(bid)

        for j in range(ny):
            for i in range(nx - 1):
                add_beam(i, j, i + 1, j, "X", j in (0, ny - 1), beams_x)
        for i in range(nx):
            for j in range(ny - 1):
                add_beam(i, j, i, j + 1, "Y", i in (0, nx - 1), beams_y)
        # slab panels → edge beams (45° rule); a missing edge beam's share goes to the others
        q = spec.q_roof if roof else spec.q
        for i in range(nx - 1):
            for j in range(ny - 1):
                if grid_label(i, j) in openings:
                    continue
                lx, ly = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
                edges = [  # (beam id, edge length, other dimension)
                    (f"B{k}.{grid_label(i, j)}-{grid_label(i + 1, j)}", lx, ly),
                    (f"B{k}.{grid_label(i, j + 1)}-{grid_label(i + 1, j + 1)}", lx, ly),
                    (f"B{k}.{grid_label(i, j)}-{grid_label(i, j + 1)}", ly, lx),
                    (f"B{k}.{grid_label(i + 1, j)}-{grid_label(i + 1, j + 1)}", ly, lx),
                ]
                present = [e for e in edges if e[0] in m.members]
                if not present:
                    raise StructureError("Slab panel {p} has no supporting beam — add a beam "
                                         "or make it an opening", p=grid_label(i, j))
                share = lambda a, b: min(a, b) / 2 * (a - min(a, b) / 2)  # noqa: E731
                scale = sum(share(a, b) for _, a, b in edges) / \
                    sum(share(a, b) for _, a, b in present)
                for bid, a, b in present:
                    for case, p in (("G", p_g), ("Q", q)):
                        if not p:
                            continue
                        for x1, x2, w1, w2 in tributary(a, b, p * scale):
                            m.load_member(case, bid, wz=-w1, w2=(0.0, 0.0, -w2),
                                          a=x1 / a, b=x2 / a)
        used = {mm.i for mm in m.members.values()} | {mm.j for mm in m.members.values()}
        level = [node_id(i, j, k) for i in range(nx) for j in range(ny)
                 if node_id(i, j, k) in used]
        m.diaphragm(f"L{k}", level)
    fbeams, raft = {}, None
    if spec.foundation and spec.foundation.get("type") == "raft":
        raft = _raft(m, spec, xs, ys, wall_at, conc)
    elif spec.foundation:
        fbeams = _foundation(m, spec, xs, ys, wall_at, conc)
    used = {mm.i for mm in m.members.values()} | {mm.j for mm in m.members.values()} | \
        {n for p in m.plates.values() for n in p.nodes}
    for nid in [n for n in m.nodes if n not in used]:
        del m.nodes[nid]
    area = sum((xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j]) for i in range(nx - 1)
               for j in range(ny - 1) if grid_label(i, j) not in openings)
    info = {"xs": xs, "ys": ys, "zs": zs, "columns": columns, "walls": walls,
            "wall_spec": wall_at, "beams_x": beams_x,
            "beams_y": beams_y, "concrete": conc, "col": col, "beam": beam,
            "plan_area": area, "sizes": sizes, "openings": openings, "fbeams": fbeams,
            "raft": raft}
    return m, info


def _foundation(m: Model, spec: BuildingSpec, xs, ys, wall_at, conc) -> dict[str, list[str]]:
    """Foundation beams on Winkler springs along every grid segment joining two supported
    grid points; returns grid segment → its sub-elements (FB.<segment>.<n>).

    Each segment is divided into ``n`` elements; a node carries the vertical spring
    k = k_s·B·(tributary length), horizontal translations are restrained (friction and
    passive resistance), rotations are free.  Walls bear on the beam over their length
    (rigid zone of half the wall length, which also takes its share of the springs).
    """
    f = spec.foundation
    B, bw, h, ks, n = f["B"], f["bw"], f["h"], f["ks"], int(f.get("n", 6))
    sec = Section.rectangle(bw, h, f"FB {bw:g}×{h:g}")
    hf = min(250.0, h / 3)                       # flange thickness of the inverted T
    w_self = -CONCRETE_WEIGHT * (bw * h + (B - bw) * hf)
    nx, ny = len(xs), len(ys)
    base = {nid for mm in m.members.values() for nid in (mm.i, mm.j) if nid.endswith("@0")}
    trib: dict[str, float] = {}
    out: dict[str, list[str]] = {}

    def seg(i1, j1, i2, j2, along):
        a, b = grid_label(i1, j1), grid_label(i2, j2)
        na, nb = node_id(i1, j1, 0), node_id(i2, j2, 0)
        if na not in base or nb not in base:
            return
        pa, pb = m.nodes[na].xyz, m.nodes[nb].xyz
        L = float(np.linalg.norm(pb - pa))
        oa = wall_at[a]["L"] / 2 if a in wall_at and wall_at[a]["dir"] == along else 0.0
        ob = wall_at[b]["L"] / 2 if b in wall_at and wall_at[b]["dir"] == along else 0.0
        Lf = L - oa - ob
        key = f"{a}-{b}"
        ids, prev = [], na
        for k in range(1, n + 1):
            if k < n:
                nid = f"{key}@f{k}"
                p = pa + (pb - pa) * (oa + Lf * k / n) / L
                m.node(nid, *p)
            else:
                nid = nb
            mid = f"FB.{key}.{k}"
            spec.labels[mid] = key
            m.member(mid, prev, nid, sec, conc, offset_i=oa if k == 1 else 0.0,
                     offset_j=ob if k == n else 0.0)
            m.load_member("G", mid, wz=w_self)
            ids.append(mid)
            for node, length in ((prev, Lf / n / 2 + (oa if k == 1 else 0.0)),
                                 (nid, Lf / n / 2 + (ob if k == n else 0.0))):
                trib[node] = trib.get(node, 0.0) + length
            prev = nid
        out[key] = ids

    for j in range(ny):
        for i in range(nx - 1):
            seg(i, j, i + 1, j, "X")
    for i in range(nx):
        for j in range(ny - 1):
            seg(i, j, i, j + 1, "Y")
    for nid in base:
        if nid not in trib:
            raise StructureError("The column at {g} has no foundation beam — connect it to a "
                                 "neighbouring column or use pad footings",
                                 g=nid.split("@")[0])
    for nid, length in trib.items():
        s = m.support(nid, "free", springs=(0.0, 0.0, ks * B * length, 0.0, 0.0, 0.0))
        s.restraints = (True, True, False, False, False, False)
    return out


def _raft(m: Model, spec: BuildingSpec, xs, ys, wall_at, conc) -> dict:
    """Raft foundation: MITC4 plate mesh under the whole plan (plus an overhang) on Winkler
    springs k = k_s·(tributary area); horizontal translations restrained, rotations free.
    Walls are tied to the raft over their length by rigid links (they bear on a strip, not a
    point)."""
    import math

    f = spec.foundation
    t, over, ks, target = f["t"], f.get("over", 500.0), f["ks"], f.get("mesh", 1000.0)

    def lines(grid, extra):
        pts = sorted(set([grid[0] - over, grid[-1] + over] + list(grid) + extra))
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            if b - a < 1.0:
                continue
            n = max(1, math.ceil((b - a) / target))
            out += [a + (b - a) * k / n for k in range(1, n + 1)]
        return out

    extra_x, extra_y = [], []
    gpos = {grid_label(i, j): (xs[i], ys[j]) for i in range(len(xs)) for j in range(len(ys))}
    for g, w in wall_at.items():
        x0, y0 = gpos[g]
        if w["dir"] == "X":
            extra_x += [x0 - w["L"] / 2, x0 + w["L"] / 2]
        else:
            extra_y += [y0 - w["L"] / 2, y0 + w["L"] / 2]
    X, Y = lines(xs, extra_x), lines(ys, extra_y)
    gid = {}
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            gid[(round(x, 3), round(y, 3))] = node_id(i, j, 0)
    ids = {}
    for a, x in enumerate(X):
        for b, y in enumerate(Y):
            nid = gid.get((round(x, 3), round(y, 3))) or f"R{a}_{b}"
            if nid not in m.nodes:
                m.node(nid, x, y, 0.0)
            ids[(a, b)] = nid
    plates, trib = [], {}
    w_self = CONCRETE_WEIGHT * t
    for a in range(len(X) - 1):
        for b in range(len(Y) - 1):
            pid = f"RF{a}_{b}"
            corners = [ids[(a, b)], ids[(a + 1, b)], ids[(a + 1, b + 1)], ids[(a, b + 1)]]
            m.plate(pid, corners, t, conc)
            m.load_plate("G", pid, w_self)
            A = (X[a + 1] - X[a]) * (Y[b + 1] - Y[b])
            for n in corners:
                trib[n] = trib.get(n, 0.0) + A / 4
            plates.append({"id": pid, "x0": X[a], "x1": X[a + 1], "y0": Y[b], "y1": Y[b + 1]})
    for nid, A in trib.items():
        s = m.support(nid, "free", springs=(0.0, 0.0, ks * A, 0.0, 0.0, 0.0))
        s.restraints = (True, True, False, False, False, False)
    rigid = Section("rigid link", 1e8, 1e14, 1e14, 1e14)
    for g, w in wall_at.items():
        base = node_id(*next((i, j) for i in range(len(xs)) for j in range(len(ys))
                             if grid_label(i, j) == g), 0)
        x0, y0 = gpos[g]
        k = 0
        for (a, b), nid in ids.items():
            x, y = X[a], Y[b]
            along = (w["dir"] == "X" and abs(y - y0) < 1 and 0 < abs(x - x0) <= w["L"] / 2 + 1) or \
                (w["dir"] == "Y" and abs(x - x0) < 1 and 0 < abs(y - y0) <= w["L"] / 2 + 1)
            if along:
                k += 1
                m.member(f"RL.{g}.{k}", base, nid, rigid, conc)
    return {"X": X, "Y": Y, "plates": plates, "trib": trib, "t": t, "ks": ks,
            "bounds": (X[0], X[-1], Y[0], Y[-1])}
