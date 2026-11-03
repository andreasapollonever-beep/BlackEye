"""EN 1998-1 seismic verification of a building model analysed by modal response spectrum.

* accidental torsion, 4.3.3.3.3 — static moments M_ai = e_ai·F_i with
  e_ai = ±0.05·L_i (4.3.2) and F_i from the lateral force distribution
  (4.3.3.2.3); their effects are added to the spectrum results;
* combination of the horizontal components, 4.3.3.5.1(3):
  E = max(E_X + 0.3·E_Y, 0.3·E_X + E_Y);
* interstorey drift (damage limitation), 4.4.3.2: d_r·ν ≤ α·h with
  d_r = q·d_re (4.3.4) computed column by column (CQC of each mode's drift,
  not the difference of combined values);
* second-order sensitivity θ = P_tot·d_r / (V_tot·h), 4.4.2.2: ≤ 0.10 no
  effect; 0.10–0.20 effects × 1/(1 − θ); > 0.30 not allowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .modal import (G_ACC, DesignSpectrum, ModalResult, SpectrumResult, nodal_masses,
                    response_spectrum)
from .model import LoadCase, NodalLoad, StructureError
from .solver import Analysis, StaticResult


@dataclass
class Storey:
    index: int                 # 1 = ground storey
    level: str                 # diaphragm name at the top
    z: float                   # top level, mm
    h: float                   # storey height, mm
    columns: list[str]
    mass: float                # level mass, N·s²/mm
    P_tot: float = 0.0         # gravity load at and above, N (seismic situation)
    F: dict = field(default_factory=dict)      # lateral force method F_i per direction
    V: dict = field(default_factory=dict)      # storey shear (spectrum, CQC) per direction
    drift: dict = field(default_factory=dict)  # d_r = q·d_re, max over columns, mm
    theta: dict = field(default_factory=dict)


@dataclass
class SeismicResult:
    spectrum: DesignSpectrum
    modes: ModalResult
    rs: dict[str, SpectrumResult]
    torsion: dict[str, StaticResult]
    storeys: list[Storey]
    q: float
    nu: float
    alpha: float
    T1: dict[str, float]
    Fb_lfm: dict[str, float]
    amplification: dict[str, float]
    warnings: list[str] = field(default_factory=list)

    def _directional(self, d: str, arr_rs: np.ndarray, arr_t: np.ndarray) -> np.ndarray:
        return self.amplification[d] * (np.abs(arr_rs) + np.abs(arr_t))

    def member_envelope(self, member) -> np.ndarray:
        """|E| at the 12 local end forces, both components and accidental torsion included."""
        k = self.modes.analysis.member_index[str(member)]
        ex = self._directional("X", self.rs["X"].end_forces[k], self.torsion["X"].end_forces[k])
        ey = self._directional("Y", self.rs["Y"].end_forces[k], self.torsion["Y"].end_forces[k])
        return np.maximum(ex + 0.3 * ey, 0.3 * ex + ey)

    def displacement_envelope(self, node) -> np.ndarray:
        i = self.modes.analysis.dofmap.index[str(node)]
        ex = self._directional("X", self.rs["X"].u[i], self.torsion["X"].u[i])
        ey = self._directional("Y", self.rs["Y"].u[i], self.torsion["Y"].u[i])
        return np.maximum(ex + 0.3 * ey, 0.3 * ex + ey)

    @property
    def base_shear(self) -> dict[str, float]:
        return {d: r.base_shear for d, r in self.rs.items()}

    @property
    def drift_ok(self) -> bool:
        return all(s.drift[d] * self.nu <= self.alpha * s.h for s in self.storeys for d in s.drift)

    @property
    def theta_max(self) -> float:
        return max((t for s in self.storeys for t in s.theta.values()), default=0.0)


def find_storeys(analysis: Analysis) -> list[tuple[str, float, list[str], float]]:
    """(diaphragm, z_top, vertical members ending at that level, z_bottom) bottom-up."""
    model = analysis.model
    levels = sorted(((np.mean([model.nodes[n].z for n in d.nodes]), d) for d in model.diaphragms),
                    key=lambda t: t[0])
    if not levels:
        raise StructureError("Seismic checks need floors: define a rigid diaphragm at each level")
    out = []
    for z, d in levels:
        nodes = set(d.nodes)
        cols = []
        zb = []
        for m in model.members.values():
            ni, nj = model.nodes[m.i], model.nodes[m.j]
            vertical = abs(ni.x - nj.x) < 1 and abs(ni.y - nj.y) < 1
            if not vertical:
                continue
            top, bot = (nj, ni) if nj.z > ni.z else (ni, nj)
            if top.id in nodes:
                cols.append(m.id)
                zb.append(bot.z)
        if not cols:
            raise StructureError("Floor {d} has no columns or walls below it", d=d.name,
                                 ref=f"diaphragm {d.name}")
        out.append((d.name, float(z), cols, float(min(zb))))
    return out


def _col_ends(analysis: Analysis, mid: str) -> tuple[int, str, str, bool]:
    m = analysis.model.members[mid]
    ni, nj = analysis.model.nodes[m.i], analysis.model.nodes[m.j]
    i_is_bottom = ni.z < nj.z
    top, bot = (m.j, m.i) if i_is_bottom else (m.i, m.j)
    return analysis.member_index[mid], top, bot, i_is_bottom


def seismic_check(analysis: Analysis, modes: ModalResult, spectrum: DesignSpectrum,
                  importance: str = "II", annex: str | None = "EN", q_d: float | None = None,
                  alpha: float = 0.005, accidental: bool = True) -> SeismicResult:
    """Run spectrum analysis in X and Y and the EN 1998-1 building checks.

    ``alpha`` = drift limit ratio (0.005 brittle non-structural elements,
    0.0075 ductile ones, 0.010 none interfering); ``q_d`` defaults to q.
    """
    from ..design.annex import get_annex

    na = get_annex(annex)
    nu = na.drift_nu[importance]
    q = spectrum.q
    qd = q if q_d is None else q_d
    rs = {d: response_spectrum(modes, spectrum, d) for d in ("X", "Y")}
    model, dm = analysis.model, analysis.dofmap
    m_node = nodal_masses(analysis, modes.mass_source)
    levels = find_storeys(analysis)
    z_base = min(model.nodes[n].z for n in model.supports)
    storeys: list[Storey] = []
    dia = {d.name: d for d in model.diaphragms}
    for k, (name, z, cols, zb) in enumerate(levels, 1):
        mass = sum(m_node[dm.index[n]] for n in dia[name].nodes if n in dm.index)
        storeys.append(Storey(k, name, z, z - zb, cols, mass))
    # gravity above each storey (seismic situation) from the nodal masses
    zs_nodes = np.array([model.nodes[n].z for n in dm.node_ids])
    for s in storeys:
        s.P_tot = float(m_node[zs_nodes >= s.z - 1.0].sum() * G_ACC)

    # ---- lateral force distribution (for accidental torsion) 4.3.3.2.3
    T1, Fb = {}, {}
    torsion: dict[str, StaticResult] = {}
    n_st = len(storeys)
    for d in ("X", "Y"):
        n1 = int(np.argmax(modes.ratio(d)))
        T1[d] = float(modes.periods[n1])
        lam = 0.85 if (T1[d] <= 2 * spectrum.TC and n_st > 2) else 1.0
        m_tot = sum(s.mass for s in storeys)
        Fb[d] = float(spectrum([T1[d]])[0]) * G_ACC * m_tot * lam
        zm = sum((s.z - z_base) * s.mass for s in storeys) or 1.0
        case = LoadCase(f"T{d}")
        for s in storeys:
            s.F[d] = Fb[d] * (s.z - z_base) * s.mass / zm
            nodes = dia[s.level].nodes
            xy = np.array([[model.nodes[n].x, model.nodes[n].y] for n in nodes])
            Lperp = np.ptp(xy[:, 1]) if d == "X" else np.ptp(xy[:, 0])
            if accidental:
                case.nodal.append(NodalLoad(nodes[0], (0, 0, 0, 0, 0, 0.05 * Lperp * s.F[d])))
        torsion[d] = analysis.static_case(case)

    # ---- storey shears, drifts, θ
    warnings: list[str] = []
    for d, c in (("X", 0), ("Y", 1)):
        r = rs[d]
        for s in storeys:
            V_modes = np.zeros(len(r.modal))
            drift_cols = []
            for mid in s.columns:
                k, top, bot, i_bot = _col_ends(analysis, mid)
                e = analysis.elements[k]
                sl = slice(0, 3) if i_bot else slice(6, 9)
                for n, res in enumerate(r.modal):
                    V_modes[n] += (e.R.T @ res.end_forces[k][sl])[c]
                dmodes = np.array([res.displacement(top)[c] - res.displacement(bot)[c]
                                   for res in r.modal])
                dt = torsion[d].displacement(top)[c] - torsion[d].displacement(bot)[c]
                drift_cols.append(float(r.combine(dmodes[:, None])[0]) + abs(dt))
            s.V[d] = float(r.combine(V_modes[:, None])[0])
            s.drift[d] = qd * max(drift_cols)
            s.theta[d] = s.P_tot * s.drift[d] / (s.V[d] * s.h) if s.V[d] > 0 else 0.0
    amp = {}
    for d in ("X", "Y"):
        th = max(s.theta[d] for s in storeys)
        amp[d] = 1.0 / (1.0 - th) if 0.1 < th <= 0.3 else 1.0
        if th > 0.3:
            warnings.append(f"θ = {th:.2f} > 0.30 in {d}: not allowed (EN 1998-1 4.4.2.2(4)) — "
                            "stiffen the structure")
        elif th > 0.2:
            warnings.append(f"θ = {th:.2f} > 0.20 in {d}: a second-order analysis is required")
    for r in rs.values():
        warnings += r.warnings
    return SeismicResult(spectrum, modes, rs, torsion, storeys, q, nu, alpha, T1, Fb, amp,
                         warnings)
