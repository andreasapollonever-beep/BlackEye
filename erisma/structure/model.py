"""3D structural model: nodes, members, supports, diaphragms, load cases.

Units: N and mm throughout (see :mod:`erisma.core.units`).  Global axes: X, Y
horizontal, **Z vertical upwards** (gravity acts in −Z).

Member local axes
-----------------
* local x runs from node *i* to node *j*;
* for a non-vertical member local z lies in the vertical plane through the
  member and points upwards, local y = z × x (horizontal);
* for a vertical member (column) local y = global X and local z = global Y;
* ``beta`` (degrees) rotates local y, z about local x (right-hand rule).

So for a beam ``Iy`` is the inertia for bending in the vertical plane (the
strong axis of an I-section in its usual orientation), exactly as in EN 1993.

The model is a plain description; :func:`erisma.structure.solver.analyse`
does the work.  :meth:`Model.validate` reports problems in plain language,
pointing at the node or member to fix.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from ..i18n import tr

DOF_NAMES = ("ux", "uy", "uz", "rx", "ry", "rz")
G_ACC = 9810.0  # mm/s² — mass [N·s²/mm] = weight [N] / G_ACC


class StructureError(ValueError):
    """A modelling problem the engineer must fix.

    ``ref`` names the offending object (``"node 5"``, ``"member B12"``) so the
    UI can highlight it; :meth:`message` returns the text in ``en`` or ``el``.
    """

    def __init__(self, text: str, ref: str | None = None, **kw) -> None:
        self.text, self.kw, self.ref = text, kw, ref
        super().__init__(text.format(**kw))

    def message(self, lang: str = "en") -> str:
        kw = self.kw
        if lang == "el":  # object labels such as "node 5 ux" / "diaphragm F1 rz"
            kw = {k: (v.replace("diaphragm ", "διάφραγμα ").replace("node ", "κόμβος ")
                      if isinstance(v, str) else v) for k, v in kw.items()}
        return tr(self.text, lang, **kw)


class Msg(str):
    """A warning that can be shown in any language: ``str(msg)`` is English,
    ``msg.text``/``msg.kw`` are the template and values for :func:`erisma.i18n.tr`."""

    def __new__(cls, text: str, **kw):
        obj = super().__new__(cls, text.format(**kw))
        obj.text, obj.kw = text, kw
        return obj

    def message(self, lang: str = "en") -> str:
        return tr(self.text, lang, **self.kw)


# --------------------------------------------------------------------- materials


@dataclass(frozen=True)
class Material:
    """Linear-elastic isotropic material.

    ``weight`` is the unit weight in N/mm³ (25 kN/m³ = 25e-6 N/mm³).
    """

    name: str
    E: float
    nu: float = 0.2
    weight: float = 0.0

    @property
    def G(self) -> float:
        return self.E / (2 * (1 + self.nu))

    @classmethod
    def concrete(cls, fck: float = 25.0, cracked: float = 1.0) -> "Material":
        """EN 1992-1-1 Table 3.1 concrete; ``cracked`` multiplies E (EN 1998-1 4.3.1(7): 0.5)."""
        Ecm = 22000 * ((fck + 8) / 10) ** 0.3
        return cls(f"C{fck:g}", Ecm * cracked, 0.2, 25e-6)

    @classmethod
    def steel(cls, grade: str = "S275") -> "Material":
        """EN 1993-1-1 3.2.6: E = 210 000 MPa, ν = 0.3, 78.5 kN/m³."""
        return cls(grade, 210000.0, 0.3, 78.5e-6)


@dataclass(frozen=True)
class Section:
    """Cross-section properties in mm units.

    ``Iy`` bending about local y (deflection along local z), ``Iz`` about
    local z, ``J`` torsion constant, ``Avy``/``Avz`` shear areas (``None`` =
    neglect shear deformation, i.e. Euler–Bernoulli).
    """

    name: str
    A: float
    Iy: float
    Iz: float
    J: float
    Avy: float | None = None
    Avz: float | None = None

    @classmethod
    def rectangle(cls, b: float, h: float, name: str | None = None) -> "Section":
        """Solid rectangle: ``b`` along local y, ``h`` along local z.

        Torsion constant J = β·h_max·b_min³ with the closed-form approximation
        β = 1/3 − 0.21·(t/w)·(1 − (t/w)⁴/12) (Roark, Table 10.7 case 4);
        shear areas 5/6·A.
        """
        w, t = max(b, h), min(b, h)
        r = t / w
        J = (1 / 3 - 0.21 * r * (1 - r**4 / 12)) * w * t**3
        A = b * h
        return cls(name or f"{b:g}×{h:g}", A, b * h**3 / 12, h * b**3 / 12, J,
                   5 / 6 * A, 5 / 6 * A)

    @classmethod
    def steel(cls, name: str) -> "Section":
        """Hot-rolled I-section from :mod:`erisma.sections.steel` (web along local z)."""
        from ..sections.steel import get_section

        s = get_section(name)
        return cls(s.name, s.A, s.Iy, s.Iz, s.It, 2 * s.b * s.tf, s.Av_z)


# --------------------------------------------------------------------- topology


@dataclass
class Node:
    id: str
    x: float
    y: float
    z: float

    @property
    def xyz(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=float)


@dataclass
class Member:
    id: str
    i: str
    j: str
    section: Section
    material: Material
    beta: float = 0.0
    hinge_i: bool = False  # moment release (My, Mz) at end i
    hinge_j: bool = False
    offset_i: float = 0.0  # rigid end zone at end i, mm along the member (e.g. half a wall)
    offset_j: float = 0.0


@dataclass
class Support:
    """Restraint flags in order (ux, uy, uz, rx, ry, rz) and optional springs.

    ``springs`` are translational N/mm or rotational Nmm/rad stiffnesses on
    unrestrained DOFs (``0`` = none).
    """

    node: str
    restraints: tuple[bool, ...] = (True,) * 6
    springs: tuple[float, ...] = (0.0,) * 6

    @classmethod
    def fixed(cls, node: str) -> "Support":
        return cls(node, (True,) * 6)

    @classmethod
    def pinned(cls, node: str) -> "Support":
        return cls(node, (True, True, True, False, False, False))


@dataclass
class Diaphragm:
    """Rigid in-plane floor (EN 1998-1 4.3.1(4)): the listed nodes share
    ux, uy and rz of a master point at their centroid."""

    name: str
    nodes: list[str]


# --------------------------------------------------------------------- loads


@dataclass
class NodalLoad:
    node: str
    values: tuple[float, ...]  # (Fx, Fy, Fz, Mx, My, Mz) global, N and Nmm


@dataclass
class MemberLoad:
    """Distributed load on a member, N/mm per unit member length.

    ``w`` = (wx, wy, wz) at the start ``a`` and ``w2`` at the end ``b`` of the
    loaded part (``a``, ``b`` as fractions of the length, default the whole
    member; ``w2=None`` → uniform).  ``axes="global"`` → components in global
    axes (gravity: wz < 0); ``axes="local"`` → along the member local axes.
    """

    member: str
    w: tuple[float, float, float]
    axes: str = "global"
    a: float = 0.0
    b: float = 1.0
    w2: tuple[float, float, float] | None = None


@dataclass
class LoadCase:
    name: str
    nodal: list[NodalLoad] = field(default_factory=list)
    member: list[MemberLoad] = field(default_factory=list)
    self_weight: float = 0.0  # multiplier on member self-weight (1.0 = include)


# --------------------------------------------------------------------- model


@dataclass
class Model:
    nodes: dict[str, Node] = field(default_factory=dict)
    members: dict[str, Member] = field(default_factory=dict)
    supports: dict[str, Support] = field(default_factory=dict)
    diaphragms: list[Diaphragm] = field(default_factory=list)
    cases: dict[str, LoadCase] = field(default_factory=dict)
    masses: dict[str, float] = field(default_factory=dict)  # extra nodal mass, N·s²/mm

    # ---- building helpers (ids are converted to str so ints work too)
    def node(self, id, x: float, y: float, z: float) -> Node:
        n = Node(str(id), float(x), float(y), float(z))
        self.nodes[n.id] = n
        return n

    def member(self, id, i, j, section: Section, material: Material, **kw) -> Member:
        m = Member(str(id), str(i), str(j), section, material, **kw)
        self.members[m.id] = m
        return m

    def support(self, node, kind: str = "fixed", springs=None) -> Support:
        node = str(node)
        if kind == "fixed":
            s = Support.fixed(node)
        elif kind == "pinned":
            s = Support.pinned(node)
        elif kind == "free":
            s = Support(node, (False,) * 6)
        else:
            raise StructureError("Unknown support type '{k}' (use fixed, pinned or free)", k=kind)
        if springs is not None:
            s.springs = tuple(float(v) for v in springs)
        self.supports[node] = s
        return s

    def diaphragm(self, name: str, nodes) -> Diaphragm:
        d = Diaphragm(str(name), [str(n) for n in nodes])
        self.diaphragms.append(d)
        return d

    def case(self, name: str, self_weight: float = 0.0) -> LoadCase:
        if name not in self.cases:
            self.cases[name] = LoadCase(name, self_weight=self_weight)
        return self.cases[name]

    def load_node(self, case: str, node, Fx=0.0, Fy=0.0, Fz=0.0, Mx=0.0, My=0.0, Mz=0.0):
        self.case(case).nodal.append(NodalLoad(str(node), (Fx, Fy, Fz, Mx, My, Mz)))

    def load_member(self, case: str, member, wx=0.0, wy=0.0, wz=0.0, axes: str = "global",
                    a: float = 0.0, b: float = 1.0, w2=None):
        """Uniform (``w2=None``) or linearly varying load from ``a`` to ``b`` (fractions of L)."""
        self.case(case).member.append(MemberLoad(str(member), (wx, wy, wz), axes, a, b,
                                                 None if w2 is None else tuple(w2)))

    # ---- geometry
    def length(self, m: Member) -> float:
        return float(np.linalg.norm(self.nodes[m.j].xyz - self.nodes[m.i].xyz))

    def rotation(self, m: Member) -> np.ndarray:
        """3×3 matrix whose rows are local x, y, z in global components."""
        d = self.nodes[m.j].xyz - self.nodes[m.i].xyz
        ex = d / np.linalg.norm(d)
        if math.hypot(ex[0], ex[1]) < 1e-6:  # vertical
            ey = np.array([1.0, 0.0, 0.0])
            ez = np.cross(ex, ey)
            ez /= np.linalg.norm(ez)
            ey = np.cross(ez, ex)
        else:
            ref = np.array([0.0, 0.0, 1.0])
            ez = ref - ref.dot(ex) * ex
            ez /= np.linalg.norm(ez)
            ey = np.cross(ez, ex)
        if m.beta:
            c, s = math.cos(math.radians(m.beta)), math.sin(math.radians(m.beta))
            ey, ez = c * ey + s * ez, -s * ey + c * ez
        return np.vstack([ex, ey, ez])

    # ---- validation
    def validate(self) -> list[str]:
        """Raise :class:`StructureError` for fatal problems; return warnings (English)."""
        warnings: list[str] = []
        if not self.members:
            raise StructureError("The model has no members — add beams or columns")
        for m in self.members.values():
            for end in (m.i, m.j):
                if end not in self.nodes:
                    raise StructureError("Member {m} refers to node {n}, which does not exist",
                                         ref=f"member {m.id}", m=m.id, n=end)
            if m.i == m.j or self.length(m) < 1.0:
                raise StructureError("Member {m} has zero length — its two ends coincide",
                                     ref=f"member {m.id}", m=m.id)
            if m.offset_i < 0 or m.offset_j < 0 or \
                    m.offset_i + m.offset_j > 0.9 * self.length(m):
                raise StructureError("Member {m}: the rigid end zones are longer than the member",
                                     ref=f"member {m.id}", m=m.id)
            s, mat = m.section, m.material
            for name, v in (("A", s.A), ("Iy", s.Iy), ("Iz", s.Iz), ("J", s.J), ("E", mat.E)):
                if not v > 0:
                    raise StructureError("Member {m}: {p} must be greater than zero",
                                         ref=f"member {m.id}", m=m.id, p=name)
        if not self.supports:
            raise StructureError("The model has no supports — fix or pin the base nodes")
        for nid in self.supports:
            if nid not in self.nodes:
                raise StructureError("Support at node {n}, which does not exist",
                                     ref=f"node {nid}", n=nid)
        used = {m.i for m in self.members.values()} | {m.j for m in self.members.values()}
        for nid in self.nodes:
            if nid not in used:
                warnings.append(Msg("Node {n} is not connected to any member and is ignored",
                                    n=nid))
        seen: dict[str, str] = {}
        for d in self.diaphragms:
            if len(d.nodes) < 2:
                raise StructureError("Diaphragm {d} needs at least two nodes", ref=f"diaphragm {d.name}",
                                     d=d.name)
            for nid in d.nodes:
                if nid not in self.nodes:
                    raise StructureError("Diaphragm {d} refers to node {n}, which does not exist",
                                         ref=f"diaphragm {d.name}", d=d.name, n=nid)
                if nid in seen:
                    raise StructureError("Node {n} belongs to two diaphragms ({a}, {b})",
                                         ref=f"node {nid}", n=nid, a=seen[nid], b=d.name)
                seen[nid] = d.name
                sup = self.supports.get(nid)
                if sup and any(sup.restraints[k] for k in (0, 1, 5)):
                    raise StructureError("Node {n} is supported horizontally and also belongs "
                                         "to diaphragm {d} — remove one of the two",
                                         ref=f"node {nid}", n=nid, d=d.name)
        for case in self.cases.values():
            for nl in case.nodal:
                if nl.node not in self.nodes:
                    raise StructureError("Load case {c}: load on node {n}, which does not exist",
                                         ref=f"node {nl.node}", c=case.name, n=nl.node)
            for ml in case.member:
                if ml.member not in self.members:
                    raise StructureError("Load case {c}: load on member {m}, which does not exist",
                                         ref=f"member {ml.member}", c=case.name, m=ml.member)
                if not 0 <= ml.a < ml.b <= 1:
                    raise StructureError("Load case {c}, member {m}: the loaded part must satisfy "
                                         "0 ≤ start < end ≤ 1 (fractions of the length)",
                                         ref=f"member {ml.member}", c=case.name, m=ml.member)
        return warnings
