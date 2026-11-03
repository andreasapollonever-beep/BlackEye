"""Linear static analysis of 3D frames by the direct stiffness method.

Element: two-node 3D beam with 6 DOF per node (ux, uy, uz, rx, ry, rz),
Timoshenko shear deformation when the section has shear areas (exact
stiffness for prismatic members — Przemieniecki, *Theory of Matrix Structural
Analysis*, §5.6), optional moment hinges at either end (static condensation).

Rigid diaphragms are imposed exactly by a master–slave transformation:
``ux = Ux − (y − yc)·Rz``, ``uy = Uy + (x − xc)·Rz``, ``rz = Rz``.

Reported internal forces (engineering convention, along local x):

* ``N``  axial force, tension positive;
* ``Vy``, ``Vz`` shear forces with dM/dx = V (left support of a simply
  supported beam has V > 0);
* ``T``  torsion;
* ``My`` bending in the local x–z plane, positive = tension on the −z face
  (sagging of a beam is positive);
* ``Mz`` bending in the local x–y plane, positive = tension on the −y face.

Every result carries an equilibrium check (Σ loads + Σ reactions = 0).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .loads import Segment, fixed_end_forces, integrals, scale_segments, segment, totals
from .model import DOF_NAMES, Member, Model, StructureError
from .plate import mitc4_rect, resultants

_HINGE_I = (4, 5)
_HINGE_J = (10, 11)


# --------------------------------------------------------------------- element


def local_stiffness(m: Member, L: float) -> np.ndarray:
    """12×12 local stiffness of a prismatic 3D Timoshenko beam."""
    s, mat = m.section, m.material
    E, G = mat.E, mat.G
    phy = 12 * E * s.Iz / (G * s.Avy * L**2) if s.Avy else 0.0  # bending in x–y (uses Iz)
    phz = 12 * E * s.Iy / (G * s.Avz * L**2) if s.Avz else 0.0  # bending in x–z (uses Iy)
    k = np.zeros((12, 12))
    ea, gj = E * s.A / L, G * s.J / L
    k[0, 0] = k[6, 6] = ea
    k[0, 6] = k[6, 0] = -ea
    k[3, 3] = k[9, 9] = gj
    k[3, 9] = k[9, 3] = -gj
    # x–y plane: dofs v1=1, θz1=5, v2=7, θz2=11 (θz = dv/dx)
    c = E * s.Iz / ((1 + phy) * L**3)
    kb = c * np.array([[12, 6 * L, -12, 6 * L],
                       [6 * L, (4 + phy) * L**2, -6 * L, (2 - phy) * L**2],
                       [-12, -6 * L, 12, -6 * L],
                       [6 * L, (2 - phy) * L**2, -6 * L, (4 + phy) * L**2]])
    idx = [1, 5, 7, 11]
    k[np.ix_(idx, idx)] = kb
    # x–z plane: dofs w1=2, θy1=4, w2=8, θy2=10 (θy = −dw/dx)
    c = E * s.Iy / ((1 + phz) * L**3)
    kb = c * np.array([[12, -6 * L, -12, -6 * L],
                       [-6 * L, (4 + phz) * L**2, 6 * L, (2 - phz) * L**2],
                       [-12, 6 * L, 12, 6 * L],
                       [-6 * L, (2 - phz) * L**2, 6 * L, (4 + phz) * L**2]])
    idx = [2, 4, 8, 10]
    k[np.ix_(idx, idx)] = kb
    return k


def geometric_stiffness(N: float, L: float) -> np.ndarray:
    """12×12 local geometric stiffness for axial force ``N`` (tension +), cubic shapes."""
    kg = np.zeros((12, 12))
    c = N / L
    kb = c * np.array([[6 / 5, L / 10, -6 / 5, L / 10],
                       [L / 10, 2 * L**2 / 15, -L / 10, -L**2 / 30],
                       [-6 / 5, -L / 10, 6 / 5, -L / 10],
                       [L / 10, -L**2 / 30, -L / 10, 2 * L**2 / 15]])
    kg[np.ix_([1, 5, 7, 11], [1, 5, 7, 11])] = kb
    kb = c * np.array([[6 / 5, -L / 10, -6 / 5, -L / 10],
                       [-L / 10, 2 * L**2 / 15, L / 10, -L**2 / 30],
                       [-6 / 5, L / 10, 6 / 5, L / 10],
                       [-L / 10, -L**2 / 30, L / 10, 2 * L**2 / 15]])
    kg[np.ix_([2, 4, 8, 10], [2, 4, 8, 10])] = kb
    return kg


@dataclass
class _Element:
    member: Member
    L: float             # node-to-node length
    R: np.ndarray        # 3×3 rows = local axes
    T: np.ndarray        # 12×12
    oi: float = 0.0      # rigid end zones
    oj: float = 0.0
    N: float = 0.0       # axial force used for the geometric stiffness (P-Δ)
    k: np.ndarray = field(default=None)       # node-level local stiffness
    H: np.ndarray = field(default=None)       # flexible-end DOFs = H @ node DOFs
    released: list[int] = field(default_factory=list)
    kept: list[int] = field(default_factory=list)
    kr: np.ndarray | None = None              # k_cr k_rr⁻¹ for load condensation

    def __post_init__(self) -> None:
        m = self.member
        self.oi, self.oj = m.offset_i, m.offset_j
        H = np.eye(12)
        H[1, 5], H[2, 4] = self.oi, -self.oi
        H[7, 11], H[8, 10] = -self.oj, self.oj
        self.H = H
        self.released = ([*_HINGE_I] if m.hinge_i else []) + ([*_HINGE_J] if m.hinge_j else [])
        self.kept = [d for d in range(12) if d not in self.released]
        self.set_axial(self.N)

    @property
    def Lf(self) -> float:
        """Flexible length between the rigid end zones."""
        return self.L - self.oi - self.oj

    def set_axial(self, N: float) -> None:
        """(Re)build the stiffness, including the geometric stiffness of ``N``."""
        self.N = N
        k = local_stiffness(self.member, self.Lf)
        if N:
            k = k + geometric_stiffness(N, self.Lf)
        rel, kept = self.released, self.kept
        self.kr = None
        if rel:
            krr = k[np.ix_(rel, rel)]
            self.kr = k[np.ix_(kept, rel)] @ np.linalg.inv(krr)
            kc = k[np.ix_(kept, kept)] - self.kr @ k[np.ix_(rel, kept)]
            k = np.zeros((12, 12))
            k[np.ix_(kept, kept)] = kc
        self.k = self.H.T @ k @ self.H

    @property
    def rigidities(self) -> tuple[float, float, float, float | None, float | None]:
        s, mat = self.member.section, self.member.material
        return (mat.E * s.A, mat.E * s.Iy, mat.E * s.Iz, mat.G * s.Avy if s.Avy else None,
                mat.G * s.Avz if s.Avz else None)

    def condense_f(self, f: np.ndarray) -> np.ndarray:
        if not self.released:
            return f
        out = f.copy()
        out[self.kept] -= self.kr @ f[self.released]
        out[self.released] = 0.0
        return out

    def fixed_end(self, segs: list[Segment]) -> np.ndarray:
        """Node-level fixed-end forces: flexible part exactly, rigid zones by statics."""
        L, oi, oj = self.L, self.oi, self.oj
        if not oi and not oj:
            return self.condense_f(fixed_end_forces(segs, L, *self.rigidities))
        flex, zone_i, zone_j = [], [], []
        for x1, x2, w1, w2 in segs:
            for lo, hi, bucket in ((0.0, oi, zone_i), (oi, L - oj, flex), (L - oj, L, zone_j)):
                a, b = max(x1, lo), min(x2, hi)
                if b - a <= 1e-9:
                    continue
                wa = w1 + (w2 - w1) * (a - x1) / (x2 - x1)
                wb = w1 + (w2 - w1) * (b - x1) / (x2 - x1)
                bucket.append(segment(a, b, wa, wb))
        flex = [(a - oi, b - oi, wa, wb) for a, b, wa, wb in flex]
        f = self.H.T @ self.condense_f(fixed_end_forces(flex, self.Lf, *self.rigidities))
        for zone, base, sl in ((zone_i, 0.0, slice(0, 6)), (zone_j, L, slice(6, 12))):
            if zone:
                Rz, Sz = totals(zone)
                S = Sz - base * Rz  # first moment about the node
                f[sl] -= np.concatenate([Rz, [0.0, -S[2], S[1]]])
        return f

    @property
    def kg(self) -> np.ndarray:
        return self.T.T @ self.k @ self.T


def _make_element(model: Model, m: Member) -> _Element:
    L = model.length(m)
    R = model.rotation(m)
    return _Element(m, L, R, np.kron(np.eye(4), R))


# --------------------------------------------------------------------- DOF map


class DofMap:
    """Maps the 6 DOF of every node onto the reduced (independent) unknowns."""

    def __init__(self, model: Model) -> None:
        used = {m.i for m in model.members.values()} | {m.j for m in model.members.values()} | \
            {n for p in model.plates.values() for n in p.nodes}
        self.node_ids = [n for n in model.nodes if n in used]
        self.index = {n: k for k, n in enumerate(self.node_ids)}
        self.labels: list[str] = []
        self.kind: list[int] = []  # 0..5 = ux..rz, for influence vectors
        self.masters: dict[str, tuple[np.ndarray, list[int]]] = {}
        member_of: dict[str, str] = {}
        for d in model.diaphragms:
            xyz = np.array([model.nodes[n].xyz for n in d.nodes])
            centre = xyz.mean(axis=0)
            ids = [self._new(f"diaphragm {d.name} {name}", k)
                   for name, k in (("ux", 0), ("uy", 1), ("rz", 5))]
            self.masters[d.name] = (centre, ids)
            for n in d.nodes:
                member_of[n] = d.name
        self.rows: list[tuple[np.ndarray, np.ndarray]] = []
        empty = (np.zeros(0, dtype=int), np.zeros(0))
        for nid in self.node_ids:
            node = model.nodes[nid]
            sup = model.supports.get(nid)
            dia = member_of.get(nid)
            for k in range(6):
                if dia is not None and k in (0, 1, 5):
                    (c, (iu, iv, ir)) = self.masters[dia]
                    dx, dy = node.x - c[0], node.y - c[1]
                    if k == 0:
                        self.rows.append((np.array([iu, ir]), np.array([1.0, -dy])))
                    elif k == 1:
                        self.rows.append((np.array([iv, ir]), np.array([1.0, dx])))
                    else:
                        self.rows.append((np.array([ir]), np.array([1.0])))
                elif sup is not None and sup.restraints[k]:
                    self.rows.append(empty)
                else:
                    i = self._new(f"node {nid} {DOF_NAMES[k]}", k)
                    self.rows.append((np.array([i]), np.array([1.0])))
        self.n = len(self.labels)

    def _new(self, label: str, kind: int) -> int:
        self.labels.append(label)
        self.kind.append(kind)
        return len(self.labels) - 1

    def full_dofs(self, nid: str) -> range:
        b = 6 * self.index[nid]
        return range(b, b + 6)

    def gather(self, full: list[int]) -> tuple[np.ndarray, np.ndarray]:
        """(reduced ids, T) with u_full[full] = T @ u_red[ids]."""
        ids = sorted({int(i) for f in full for i in self.rows[f][0]})
        pos = {i: c for c, i in enumerate(ids)}
        T = np.zeros((len(full), len(ids)))
        for r, f in enumerate(full):
            for i, c in zip(*self.rows[f]):
                T[r, pos[int(i)]] += c
        return np.array(ids, dtype=int), T

    def expand(self, u_red: np.ndarray) -> np.ndarray:
        out = np.zeros(6 * len(self.node_ids))
        for f, (ids, cs) in enumerate(self.rows):
            if len(ids):
                out[f] = cs @ u_red[ids]
        return out


# --------------------------------------------------------------------- results


@dataclass
class StaticResult:
    """Displacements, member end forces and reactions for one load case/combination."""

    name: str
    analysis: "Analysis"
    u: np.ndarray            # (n_nodes, 6) global displacements, mm and rad
    end_forces: np.ndarray   # (n_members, 12) local end forces on the member
    loads: list[list[Segment]]  # member load segments in local axes (for the diagrams)
    reactions: dict[str, np.ndarray]
    applied: np.ndarray      # resultant of applied loads (Fx, Fy, Fz, Mx, My, Mz) about origin
    notes: list[str] = field(default_factory=list)

    # ---- queries
    def displacement(self, node) -> np.ndarray:
        return self.u[self.analysis.dofmap.index[str(node)]]

    def reaction(self, node) -> np.ndarray:
        return self.reactions[str(node)]

    def forces(self, member, n: int = 11) -> dict[str, np.ndarray]:
        """Internal force diagrams at ``n`` equally spaced stations along the member."""
        k = self.analysis.member_index[str(member)]
        L = self.analysis.elements[k].L
        f1 = self.end_forces[k]
        e = self.analysis.elements[k]
        x = np.linspace(0.0, L, n)
        segs = self.loads[k]
        extra = [s[i] for s in segs for i in (0, 1)] + [e.oi, L - e.oj]
        # load break points and faces of the rigid zones, so peaks/face values are exact
        x = np.unique(np.concatenate([x, np.clip(extra, 0.0, L)]))
        Q, Ml = integrals(segs, x)
        return {
            "x": x,
            "N": -f1[0] - Q[0],
            "Vy": f1[1] + Q[1],
            "Vz": f1[2] + Q[2],
            "T": -f1[3] * np.ones_like(x),
            "My": f1[4] + x * f1[2] + Ml[2],
            "Mz": -f1[5] + x * f1[1] + Ml[1],
        }

    def plate_forces(self, plate) -> dict:
        """Mx, My (sagging +), Mxy [Nmm/mm] and Qx, Qy [N/mm] at the plate centre."""
        an = self.analysis
        d = an.plates[an.plate_index[str(plate)]]
        p = d["plate"]
        u = self.u.reshape(-1)[d["full"]]
        return resultants(u, d["lx"], d["ly"], p.t, p.material.E, p.material.nu)

    def max_abs(self, member, key: str, n: int = 41) -> float:
        return float(np.max(np.abs(self.forces(member, n)[key])))

    def equilibrium(self) -> np.ndarray:
        """Σ applied + Σ reactions (forces and moments about the origin) — should be ≈ 0."""
        tot = self.applied.copy()
        model = self.analysis.model
        for nid, r in self.reactions.items():
            p = model.nodes[nid].xyz
            tot[:3] += r[:3]
            tot[3:] += r[3:] + np.cross(p, r[:3])
        return tot

    def equilibrium_ok(self, rel: float = 1e-6) -> bool:
        scale_f = max(np.abs(self.applied[:3]).max(), 1.0)
        scale_m = max(np.abs(self.applied[3:]).max(), scale_f * 1000.0)
        e = self.equilibrium()
        return bool(np.abs(e[:3]).max() <= rel * scale_f and np.abs(e[3:]).max() <= rel * scale_m)

    # ---- superposition
    def scaled(self, factor: float, name: str | None = None) -> "StaticResult":
        return StaticResult(name or f"{factor:g}·{self.name}", self.analysis, factor * self.u,
                            factor * self.end_forces,
                            [scale_segments(sg, factor) for sg in self.loads],
                            {k: factor * v for k, v in self.reactions.items()},
                            factor * self.applied, list(self.notes))

    def __add__(self, other: "StaticResult") -> "StaticResult":
        return StaticResult(f"{self.name} + {other.name}", self.analysis, self.u + other.u,
                            self.end_forces + other.end_forces,
                            [a + b for a, b in zip(self.loads, other.loads)],
                            {k: self.reactions[k] + other.reactions[k] for k in self.reactions},
                            self.applied + other.applied, list(self.notes))


# --------------------------------------------------------------------- analysis


class Analysis:
    """Assembled model: call :meth:`static` per load case, :meth:`combine` for combinations."""

    def __init__(self, model: Model, axial: dict[str, float] | None = None) -> None:
        """``axial`` = member axial forces (N, tension +) for the geometric stiffness (P-Δ)."""
        self.model = model
        self.warnings = model.validate()
        self.dofmap = dm = DofMap(model)
        self.elements = [_make_element(model, m) for m in model.members.values()]
        self.pdelta = bool(axial)
        if axial:
            for e in self.elements:
                if e.member.id in axial:
                    e.set_axial(float(axial[e.member.id]))
        self.member_index = {m: k for k, m in enumerate(model.members)}
        self._gath = [dm.gather([*dm.full_dofs(e.member.i), *dm.full_dofs(e.member.j)])
                      for e in self.elements]
        # plates: nodes ordered (x−,y−), (x+,y−), (x+,y+), (x−,y+); DOFs uz, rx, ry
        self.plates = []
        for p in model.plates.values():
            xyz = {n: model.nodes[n].xyz for n in p.nodes}
            x0, x1 = min(v[0] for v in xyz.values()), max(v[0] for v in xyz.values())
            y0, y1 = min(v[1] for v in xyz.values()), max(v[1] for v in xyz.values())
            order = []
            for tx, ty in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                order.append(next(n for n, v in xyz.items()
                                  if abs(v[0] - tx) < 1 and abs(v[1] - ty) < 1))
            full = [6 * dm.index[n] + k for n in order for k in (2, 3, 4)]
            k12 = mitc4_rect(x1 - x0, y1 - y0, p.t, p.material.E, p.material.nu)
            self.plates.append({"plate": p, "order": order, "lx": x1 - x0, "ly": y1 - y0,
                                "k": k12, "full": full, "gath": dm.gather(full),
                                "centre": ((x0 + x1) / 2, (y0 + y1) / 2)})
        self.plate_index = {d["plate"].id: n for n, d in enumerate(self.plates)}
        K = np.zeros((dm.n, dm.n))
        for e, (ids, T) in zip(self.elements, self._gath):
            K[np.ix_(ids, ids)] += T.T @ e.kg @ T
        for d in self.plates:
            ids, T = d["gath"]
            K[np.ix_(ids, ids)] += T.T @ d["k"] @ T
        for nid, sup in model.supports.items():
            if nid not in dm.index:
                continue
            for k, ks in enumerate(sup.springs):
                if ks and not sup.restraints[k]:
                    ids, T = dm.gather([6 * dm.index[nid] + k])
                    K[np.ix_(ids, ids)] += ks * np.outer(T[0], T[0])
        self.K = K
        diag = np.diag(K)
        scale = max(np.abs(diag).max(), 1.0) if dm.n else 1.0
        # DOFs with no stiffness at all (e.g. rotation of a node where every member is
        # hinged) carry nothing: drop them, but never a translation.
        dead = np.where(np.abs(diag) <= 1e-20 * scale)[0]  # released DOFs are exactly 0
        for i in dead:
            if dm.kind[i] < 3:
                raise StructureError("The structure is unstable: {d} is not restrained by any "
                                     "member or support — add a support or a member there",
                                     ref=dm.labels[i].rsplit(" ", 1)[0], d=dm.labels[i])
        self.notes = [f"{dm.labels[i]} has no rotational stiffness (all members hinged) — "
                      "taken as free and unloaded" for i in dead]
        self.active = np.array([i for i in range(dm.n) if i not in set(dead.tolist())], dtype=int)
        Ka = K[np.ix_(self.active, self.active)]
        d = 1 / np.sqrt(np.diag(Ka))
        if not len(d):  # every DOF restrained: nothing to solve
            self._Ks, self._d, self._Kinv = Ka, d, Ka
            return
        Ks = Ka * d[:, None] * d[None, :]
        try:
            Lc = np.linalg.cholesky(Ks)
            ok = np.min(np.diag(Lc)) ** 2 > 1e-11
        except np.linalg.LinAlgError:
            ok = False
        if not ok:
            w, v = np.linalg.eigh(Ks)
            i = int(np.argmax(np.abs(v[:, 0])))
            lab = dm.labels[self.active[i]]
            if self.pdelta:
                raise StructureError("With P-Δ the structure buckles under the gravity loads "
                                     "(first at {d}) — increase the column sizes",
                                     ref=lab.rsplit(" ", 1)[0], d=lab)
            raise StructureError("The structure is unstable (a mechanism): it can move freely at "
                                 "{d} — check supports, hinges and missing members around it",
                                 ref=lab.rsplit(" ", 1)[0], d=lab)
        self._Ks, self._d = Ks, d
        self._Kinv: np.ndarray | None = None

    # ---- solve K u = F on the active DOFs
    def solve(self, F: np.ndarray) -> np.ndarray:
        """Solve on the reduced DOFs; ``F`` may be (n,) or (n, k)."""
        a, d = self.active, self._d
        if self._Kinv is None:  # factorised once, reused for every load case
            self._Kinv = np.linalg.inv(self._Ks)
        rhs = F[a] * (d if F.ndim == 1 else d[:, None])
        z = self._Kinv @ rhs
        u = np.zeros_like(F, dtype=float)
        u[a] = z * (d if F.ndim == 1 else d[:, None])
        return u

    def member_segments(self, case) -> list[list[Segment]]:
        """Load segments (local axes) of every member for a load case."""
        segs: list[list[Segment]] = [[] for _ in self.elements]
        for ml in case.member:
            k = self.member_index[ml.member]
            e = self.elements[k]
            w1 = np.asarray(ml.w, dtype=float)
            w2 = w1 if ml.w2 is None else np.asarray(ml.w2, dtype=float)
            if ml.axes != "local":
                w1, w2 = e.R @ w1, e.R @ w2
            segs[k].append(segment(ml.a * e.L, ml.b * e.L, w1, w2))
        if case.self_weight:
            for k, e in enumerate(self.elements):
                g = -case.self_weight * e.member.material.weight * e.member.section.A
                if g:
                    segs[k].append(segment(0.0, e.L, e.R @ np.array([0.0, 0.0, g])))
        return segs

    def static(self, case_name: str) -> StaticResult:
        if case_name not in self.model.cases:
            raise StructureError("There is no load case called {c}", c=case_name)
        return self.static_case(self.model.cases[case_name])

    def static_case(self, case) -> StaticResult:
        """Solve a :class:`LoadCase` that need not be stored in the model."""
        case_name = case.name
        dm, model = self.dofmap, self.model
        nn = len(dm.node_ids)
        P = np.zeros(6 * nn)
        applied = np.zeros(6)
        for nl in case.nodal:
            if nl.node not in dm.index:
                continue
            v = np.asarray(nl.values, dtype=float)
            P[list(dm.full_dofs(nl.node))] += v
            applied[:3] += v[:3]
            applied[3:] += v[3:] + np.cross(model.nodes[nl.node].xyz, v[:3])
        for pl in case.plate:                       # lumped: q·A/4 at every corner
            d = self.plates[self.plate_index[pl.plate]]
            F = -pl.q * d["lx"] * d["ly"] / 4
            for nid in d["order"]:
                P[6 * dm.index[nid] + 2] += F
                applied[2] += F
                applied[3:] += np.cross(model.nodes[nid].xyz, [0.0, 0.0, F])
        w = self.member_segments(case)
        fe = np.zeros((len(self.elements), 12))
        Feq = P.copy()
        for k, e in enumerate(self.elements):
            if not w[k]:
                continue
            fe[k] = e.fixed_end(w[k])
            full = [*dm.full_dofs(e.member.i), *dm.full_dofs(e.member.j)]
            Feq[full] -= e.T.T @ fe[k]
            Rl, Sl = totals(w[k])
            pi = model.nodes[e.member.i].xyz
            wg = e.R.T @ Rl
            applied[:3] += wg
            # moment about the origin: ∫ (p_i + ξ e_x) × w_g dξ
            applied[3:] += np.cross(pi, wg) + np.cross(e.R[0], e.R.T @ Sl)
        F = np.zeros(dm.n)
        for f, (ids, cs) in enumerate(dm.rows):
            if len(ids) and Feq[f]:
                F[ids] += cs * Feq[f]
        u = self.solve(F)
        return self._result(case_name, u, fe, w, P, applied)

    def _result(self, name, u_red, fe, w, P, applied) -> StaticResult:
        dm, model = self.dofmap, self.model
        u_full = dm.expand(u_red)
        ends = np.zeros((len(self.elements), 12))
        node_force = np.zeros_like(u_full)
        for k, e in enumerate(self.elements):
            full = [*dm.full_dofs(e.member.i), *dm.full_dofs(e.member.j)]
            ends[k] = e.k @ (e.T @ u_full[full]) + fe[k]
            node_force[full] += e.T.T @ ends[k]
        for d in self.plates:
            node_force[d["full"]] += d["k"] @ u_full[d["full"]]
        reactions = {}
        for nid, sup in model.supports.items():
            if nid not in dm.index:
                continue
            idx = list(dm.full_dofs(nid))
            r = node_force[idx] - P[idx]
            keep = np.array([sup.restraints[k] or bool(sup.springs[k]) for k in range(6)])
            reactions[nid] = np.where(keep, r, 0.0)
        return StaticResult(name, self, u_full.reshape(-1, 6), ends, w, reactions, applied,
                            list(self.notes))

    def static_from_displacements(self, name: str, u_red: np.ndarray) -> StaticResult:
        """Forces caused by a reduced displacement vector alone (no member loads)."""
        z = np.zeros((len(self.elements), 12))
        return self._result(name, u_red, z, [[] for _ in self.elements],
                            np.zeros(6 * len(self.dofmap.node_ids)), np.zeros(6))

    def run_all(self) -> dict[str, StaticResult]:
        return {c: self.static(c) for c in self.model.cases}

    @staticmethod
    def combine(results: dict[str, StaticResult], factors: dict[str, float],
                name: str = "") -> StaticResult:
        """Linear combination Σ γ_i·E_i (e.g. ``{"G": 1.35, "Q": 1.5}``)."""
        out = None
        for case, g in factors.items():
            if case not in results:
                raise StructureError("Combination refers to load case {c}, which was not analysed",
                                     c=case)
            part = results[case].scaled(g)
            out = part if out is None else out + part
        if out is None:
            raise StructureError("The combination is empty")
        out.name = name or " + ".join(f"{g:g}·{c}" for c, g in factors.items())
        return out


def analyse(model: Model) -> Analysis:
    """Validate and assemble the model (raises :class:`StructureError` with a clear message)."""
    return Analysis(model)


def axial_forces(result: StaticResult) -> dict[str, float]:
    """Mean axial force of every member (tension +) — input for P-Δ."""
    return {m: float(-(result.end_forces[k][0] - result.end_forces[k][6]) / 2)
            for m, k in result.analysis.member_index.items()}


def analyse_pdelta(model: Model, gravity: dict[str, float]) -> Analysis:
    """P-Δ analysis: geometric stiffness from the axial forces of the ``gravity``
    combination (e.g. ``{"G": 1.0, "Q": 0.3}``), as used for seismic analysis.

    Every load case solved with the returned analysis includes the P-Δ effect.
    """
    lin = Analysis(model)
    res = {c: lin.static(c) for c in gravity}
    N = axial_forces(lin.combine(res, gravity))
    return Analysis(model, N)


def critical_load_factor(analysis: Analysis, gravity: dict[str, float]) -> float:
    """Elastic critical load factor α_cr of the ``gravity`` combination (EN 1993-1-1 5.2.1):
    smallest λ with (K + λ K_G) φ = 0."""
    res = {c: analysis.static(c) for c in gravity}
    N = axial_forces(analysis.combine(res, gravity))
    dm, a = analysis.dofmap, analysis.active
    KG = np.zeros((dm.n, dm.n))
    for e, (ids, T) in zip(analysis.elements, analysis._gath):
        n = N[e.member.id]
        if not n:
            continue
        g = geometric_stiffness(n, e.Lf)
        if e.released:  # hinged ends: consistent with the condensed element
            g = np.where(np.isin(np.arange(12), e.released)[:, None]
                         | np.isin(np.arange(12), e.released)[None, :], 0.0, g)
        g = e.T.T @ e.H.T @ g @ e.H @ e.T
        KG[np.ix_(ids, ids)] += T.T @ g @ T
    K = analysis.K[np.ix_(a, a)]
    G = KG[np.ix_(a, a)]
    lam = np.linalg.eigvals(np.linalg.solve(K, -G))
    lam = np.real(lam[np.abs(np.imag(lam)) < 1e-9 * np.abs(lam).max()])
    pos = lam[lam > 1e-12]
    if not len(pos):
        return float("inf")
    return float(1.0 / pos.max())
