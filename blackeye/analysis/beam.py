"""Continuous beam analysis by the direct stiffness method.

Euler-Bernoulli beam elements, 2 DOF per node (vertical displacement v,
rotation θ).  Units: N, mm.  Sign conventions:

* Loads: positive **downwards** (gravity).
* Displacements: reported positive **downwards** (deflection).
* Bending moment: **sagging positive**.
* Shear: positive when the left-hand part tends to move up (standard).
* Reactions: positive **upwards**; reaction moments positive anticlockwise.
* Applied point moments: positive **clockwise**.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

SUPPORT_TYPES = ("pinned", "fixed", "free")


@dataclass
class Support:
    x: float
    kind: str = "pinned"  # pinned | fixed


@dataclass
class PointLoad:
    x: float
    P: float  # N, downward positive


@dataclass
class UDL:
    x1: float
    x2: float
    w: float  # N/mm, downward positive


@dataclass
class PointMoment:
    x: float
    M: float  # Nmm, clockwise positive


@dataclass
class BeamResult:
    x: np.ndarray          # stations (mm); duplicated at discontinuities
    shear: np.ndarray      # N
    moment: np.ndarray     # Nmm
    xd: np.ndarray         # node positions for deflection (mm)
    deflection: np.ndarray # mm, downward positive
    reactions: list[tuple[float, float, float]]  # (x, R [N, up +], M [Nmm, acw +])

    @property
    def max_sagging(self) -> tuple[float, float]:
        i = int(np.argmax(self.moment))
        return float(self.moment[i]), float(self.x[i])

    @property
    def max_hogging(self) -> tuple[float, float]:
        i = int(np.argmin(self.moment))
        return float(self.moment[i]), float(self.x[i])

    @property
    def max_shear(self) -> tuple[float, float]:
        i = int(np.argmax(np.abs(self.shear)))
        return float(self.shear[i]), float(self.x[i])

    @property
    def max_deflection(self) -> tuple[float, float]:
        i = int(np.argmax(np.abs(self.deflection)))
        return float(self.deflection[i]), float(self.xd[i])


@dataclass
class Beam:
    length: float
    E: float
    I: float
    supports: list[Support] = field(default_factory=list)
    point_loads: list[PointLoad] = field(default_factory=list)
    udls: list[UDL] = field(default_factory=list)
    moments: list[PointMoment] = field(default_factory=list)
    divisions: int = 200

    # -------------------------------------------------------------- helpers
    def _validate(self) -> None:
        if self.length <= 0:
            raise ValueError("Beam length must be positive")
        if self.E <= 0 or self.I <= 0:
            raise ValueError("EI must be positive")
        for s in self.supports:
            if not 0 <= s.x <= self.length:
                raise ValueError(f"Support at x={s.x} is outside the beam")
            if s.kind not in SUPPORT_TYPES:
                raise ValueError(f"Unknown support type '{s.kind}'")
        restraints = sum(2 if s.kind == "fixed" else 1 for s in self.supports
                         if s.kind != "free")
        has_fixed = any(s.kind == "fixed" for s in self.supports)
        distinct = len({round(s.x, 6) for s in self.supports if s.kind != "free"})
        if restraints < 2 or (not has_fixed and distinct < 2):
            raise ValueError("The beam is unstable - add supports")
        for p in self.point_loads:
            if not 0 <= p.x <= self.length:
                raise ValueError(f"Point load at x={p.x} is outside the beam")
        for m in self.moments:
            if not 0 <= m.x <= self.length:
                raise ValueError(f"Moment at x={m.x} is outside the beam")
        for u in self.udls:
            if not (0 <= u.x1 < u.x2 <= self.length):
                raise ValueError(f"UDL extent {u.x1}-{u.x2} is invalid")

    def _nodes(self) -> np.ndarray:
        key = {0.0, self.length}
        key.update(s.x for s in self.supports)
        key.update(p.x for p in self.point_loads)
        key.update(m.x for m in self.moments)
        for u in self.udls:
            key.update((u.x1, u.x2))
        key_sorted = sorted(key)
        target = self.length / self.divisions
        nodes: list[float] = []
        for a, b in zip(key_sorted[:-1], key_sorted[1:]):
            n = max(1, int(np.ceil((b - a) / target)))
            nodes.extend(np.linspace(a, b, n + 1)[:-1])
        nodes.append(key_sorted[-1])
        return np.array(nodes)

    # --------------------------------------------------------------- solver
    def solve(self) -> BeamResult:
        self._validate()
        xn = self._nodes()
        nn = len(xn)
        ndof = 2 * nn
        EI = self.E * self.I
        K = np.zeros((ndof, ndof))
        F = np.zeros(ndof)          # applied nodal loads (upward +, ccw +)
        fef_all = []                # fixed-end forces per element
        q_el = np.zeros(nn - 1)

        def node_of(x: float) -> int:
            return int(np.argmin(np.abs(xn - x)))

        for u in self.udls:
            for e in range(nn - 1):
                xm = 0.5 * (xn[e] + xn[e + 1])
                if u.x1 <= xm <= u.x2:
                    q_el[e] += u.w

        for e in range(nn - 1):
            L = xn[e + 1] - xn[e]
            k = EI / L**3 * np.array([
                [12, 6 * L, -12, 6 * L],
                [6 * L, 4 * L**2, -6 * L, 2 * L**2],
                [-12, -6 * L, 12, -6 * L],
                [6 * L, 2 * L**2, -6 * L, 4 * L**2],
            ])
            idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
            K[np.ix_(idx, idx)] += k
            q = q_el[e]
            # fixed-end reactions for a downward UDL (up +, ccw +)
            fef = np.array([q * L / 2, q * L**2 / 12, q * L / 2, -q * L**2 / 12])
            fef_all.append((k, idx, fef))
            F[idx] -= fef

        for p in self.point_loads:
            F[2 * node_of(p.x)] -= p.P
        for m in self.moments:
            F[2 * node_of(m.x) + 1] -= m.M  # clockwise positive -> ccw negative

        fixed_dofs: list[int] = []
        for s in self.supports:
            n = node_of(s.x)
            if s.kind in ("pinned", "fixed"):
                fixed_dofs.append(2 * n)
            if s.kind == "fixed":
                fixed_dofs.append(2 * n + 1)
        fixed_dofs = sorted(set(fixed_dofs))
        free = np.setdiff1d(np.arange(ndof), fixed_dofs)

        U = np.zeros(ndof)
        U[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])

        # reactions = K U - F (load vector including equivalent nodal loads)
        R = K @ U - F
        reactions = []
        for s in self.supports:
            if s.kind == "free":
                continue
            n = node_of(s.x)
            Mr = R[2 * n + 1] if s.kind == "fixed" else 0.0  # anticlockwise +
            reactions.append((float(xn[n]), float(R[2 * n]), float(Mr)))

        xs, Vs, Ms = [], [], []
        for e, (k, idx, fef) in enumerate(fef_all):
            f = k @ U[idx] + fef
            L = xn[e + 1] - xn[e]
            q = q_el[e]
            V_left = f[0]
            M_left = -f[1]
            for t in (0.0, 0.5, 1.0):
                x = t * L
                xs.append(xn[e] + x)
                Vs.append(V_left - q * x)
                Ms.append(M_left + V_left * x - q * x * x / 2)

        return BeamResult(
            x=np.array(xs), shear=np.array(Vs), moment=np.array(Ms),
            xd=xn, deflection=-U[0::2], reactions=reactions,
        )
