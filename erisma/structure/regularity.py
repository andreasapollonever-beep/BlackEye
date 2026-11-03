"""EN 1998-1 4.2.3 — structural regularity of a building model with rigid diaphragms.

Plan (4.2.3.2), per floor:
* (4) compactness: area between the floor outline and its convex envelope ≤ 5 % of the floor;
* (5) slenderness λ = L_max / L_min ≤ 4;
* (6) e_0x ≤ 0.30 r_x, e_0y ≤ 0.30 r_y and r_x ≥ l_s, r_y ≥ l_s, with
  e_0 the distance between the centres of stiffness and mass, r the torsional radius
  √(K_θ / K_lateral) and l_s the radius of gyration of the floor mass in plan.

The centre of stiffness, torsional and lateral stiffness of a floor are taken from the
3 × 3 flexibility of its diaphragm (u_x, u_y, θ_z) under unit loads applied to that floor
(the usual floor-by-floor approximation, 4.2.3.2(8)).  A building with r < l_s is
**torsionally flexible** (5.1.2): q₀ = 2.0 for DCM frames/walls (Table 5.1).

Elevation (4.2.3.3): lateral systems continuous to the top (2) and lateral stiffness and
mass without abrupt changes (3).  EN 1998-1 gives no numbers for (3); the program flags a
storey whose stiffness is below 70 % of the storey above or whose mass exceeds 150 % of the
storey above — indicative limits stated in the report.

Consequences (4.2.3.1, Table 4.1): not regular in elevation → q × 0.8 (4.2.3.1(7));
torsionally flexible → q ≤ 2.0 (5.2.2.2, Table 5.1, DCM).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .modal import ModalResult, nodal_masses
from .seismic import find_storeys
from .solver import Analysis


@dataclass
class FloorRegularity:
    level: str
    index: int
    mass: float                    # N·s²/mm
    cm: tuple[float, float]        # mm
    cr: tuple[float, float]
    rx: float
    ry: float
    ls: float
    e0x: float
    e0y: float
    Kx: float                      # N/mm
    Ky: float
    Kt: float                      # Nmm/rad

    @property
    def ok_ecc(self) -> bool:
        return self.e0x <= 0.30 * self.rx and self.e0y <= 0.30 * self.ry

    @property
    def ok_radius(self) -> bool:
        return self.rx >= self.ls and self.ry >= self.ls


@dataclass
class Regularity:
    floors: list[FloorRegularity]
    compact_ratio: float           # recess area / floor area
    slenderness: float
    storey_k: dict[str, list[float]]   # lateral storey stiffness (N/mm) per direction
    storey_m: list[float]
    elev_flags: list[str] = field(default_factory=list)

    @property
    def plan_regular(self) -> bool:
        return (self.compact_ratio <= 0.05 and self.slenderness <= 4.0
                and all(f.ok_ecc and f.ok_radius for f in self.floors))

    @property
    def torsionally_flexible(self) -> bool:
        return any(not f.ok_radius for f in self.floors)

    @property
    def elevation_regular(self) -> bool:
        return not self.elev_flags

    def q_effective(self, q: float) -> float:
        """q after the EN 1998-1 consequences of irregularity."""
        if not self.elevation_regular:
            q *= 0.8                       # 4.2.3.1(7)
        if self.torsionally_flexible:
            q = min(q, 2.0)                # Table 5.1, DCM, torsionally flexible system
        return max(q, 1.5)                 # 2.2.2(2): q = 1.5 at least for RC (Note)


def _floor_geometry(info: dict) -> tuple[float, float, float]:
    """(recess ratio, slenderness, l_s about the slab centroid) of the typical floor."""
    xs, ys, op = info["xs"], info["ys"], info["openings"]
    cells = [(i, j) for i in range(len(xs) - 1) for j in range(len(ys) - 1)]
    slab = [(i, j) for i, j in cells if _gl(i, j) not in op]
    if not slab:
        return 0.0, 1.0, 0.0
    # interior openings (surrounded by slab on four sides) are holes, not recesses
    holes = [(i, j) for i, j in cells if _gl(i, j) in op and all(
        (a, b) in slab for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)))]
    A = sum((xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j]) for i, j in slab + holes)
    pts = [(xs[a], ys[b]) for i, j in slab for a in (i, i + 1) for b in (j, j + 1)]
    hull = _hull_area(pts)
    recess = max(hull - A, 0.0) / A
    xmin, xmax = min(p[0] for p in pts), max(p[0] for p in pts)
    ymin, ymax = min(p[1] for p in pts), max(p[1] for p in pts)
    lam = max(xmax - xmin, ymax - ymin) / max(min(xmax - xmin, ymax - ymin), 1.0)
    # radius of gyration of a uniformly distributed floor mass
    Ai = [(xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j]) for i, j in slab]
    cx = sum(a * (xs[i] + xs[i + 1]) / 2 for a, (i, j) in zip(Ai, slab)) / sum(Ai)
    cy = sum(a * (ys[j] + ys[j + 1]) / 2 for a, (i, j) in zip(Ai, slab)) / sum(Ai)
    Ip = sum(a * (((xs[i + 1] - xs[i]) ** 2 + (ys[j + 1] - ys[j]) ** 2) / 12 +
                  ((xs[i] + xs[i + 1]) / 2 - cx) ** 2 + ((ys[j] + ys[j + 1]) / 2 - cy) ** 2)
             for a, (i, j) in zip(Ai, slab))
    return recess, lam, math.sqrt(Ip / sum(Ai))


def _gl(i: int, j: int) -> str:
    from .builder import grid_label
    return grid_label(i, j)


def _hull_area(pts) -> float:
    pts = sorted(set(pts))
    if len(pts) < 3:
        return 0.0

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    h = lower[:-1] + upper[:-1]
    return 0.5 * abs(sum(h[k][0] * h[(k + 1) % len(h)][1] - h[(k + 1) % len(h)][0] * h[k][1]
                         for k in range(len(h))))


def regularity(an: Analysis, modes: ModalResult, info: dict) -> Regularity:
    model, dm = an.model, an.dofmap
    m_node = nodal_masses(an, modes.mass_source)
    dia = {d.name: d for d in model.diaphragms}
    recess, lam, ls = _floor_geometry(info)
    floors: list[FloorRegularity] = []
    levels = find_storeys(an)
    for k, (name, z, cols, zb) in enumerate(levels, 1):
        centre, ids = dm.masters[name]
        F = np.zeros((3, 3))
        for c, i in enumerate(ids):
            e = np.zeros(dm.n)
            e[i] = 1.0
            u = an.solve(e)
            F[:, c] = u[ids]
        # point where a force causes no twist (centre of stiffness), relative to the master
        xs_ = -F[2, 1] / F[2, 2]
        ys_ = F[2, 0] / F[2, 2]
        Kt = 1 / F[2, 2]
        Kx = 1 / (F[0, 0] - ys_ * F[0, 2])
        Ky = 1 / (F[1, 1] + xs_ * F[1, 2])
        nodes = [n for n in dia[name].nodes if n in dm.index]
        ms = np.array([m_node[dm.index[n]] for n in nodes])
        xy = np.array([[model.nodes[n].x, model.nodes[n].y] for n in nodes])
        M = float(ms.sum())
        cm = tuple(ms @ xy / M) if M > 0 else (centre[0], centre[1])
        cr = (centre[0] + xs_, centre[1] + ys_)
        floors.append(FloorRegularity(name, k, M, cm, cr, math.sqrt(Kt / Ky), math.sqrt(Kt / Kx),
                                      ls, abs(cr[0] - cm[0]), abs(cr[1] - cm[1]), Kx, Ky, Kt))
    # storey stiffness under the lateral-force pattern F_i ∝ z_i m_i (4.3.3.2.3)
    z0 = min(model.nodes[n].z for n in model.supports)
    storey_k: dict[str, list[float]] = {}
    for d, c in (("X", 0), ("Y", 1)):
        P = np.zeros(dm.n)
        forces = []
        for f, (name, z, cols, zb) in zip(floors, levels):
            Fi = (z - z0) * f.mass
            forces.append(Fi)
            P[dm.masters[name][1][c]] += Fi
        u = an.solve(P)
        ks, prev = [], 0.0
        for n, (name, z, cols, zb) in enumerate(levels):
            ui = u[dm.masters[name][1][c]]
            V = sum(forces[n:])
            ks.append(V / max(ui - prev, 1e-12))
            prev = ui
        storey_k[d] = ks
    masses = [f.mass for f in floors]
    flags = []
    for d, ks in storey_k.items():
        for n in range(len(ks) - 1):
            if ks[n] < 0.70 * ks[n + 1]:
                flags.append(f"stiffness:{d}:{n + 1}")
    for n in range(len(masses) - 2):          # the roof is normally lighter: not a flag
        if masses[n + 1] > 1.5 * masses[n]:
            flags.append(f"mass:{n + 2}")
    return Regularity(floors, recess, lam, storey_k, masses, flags)
