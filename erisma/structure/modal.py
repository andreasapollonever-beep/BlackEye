"""Modal analysis and EN 1998-1 modal response spectrum analysis.

Masses are lumped at the nodes from the gravity loads of a *mass source*
(EN 1998-1 3.2.4(2): ΣG + Σψ_E,i·Q_i) — member loads half to each end — plus
any explicit nodal masses.  Rotational inertia of the nodes is neglected, so
the massless DOFs are removed by static condensation, which is *exact* for
this mass matrix.  With rigid diaphragms the slave masses are transformed to
the master, which therefore carries the floor's polar mass moment Σm·r².

Spectrum responses are combined with CQC (EN 1998-1 4.3.3.3.2(3),
Der Kiureghian 1981) or SRSS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .loads import totals
from .model import G_ACC, Msg, StructureError
from .solver import Analysis, StaticResult

_DIR = {"X": 0, "Y": 1, "Z": 2}


@dataclass
class ModalResult:
    analysis: Analysis
    omega: np.ndarray          # rad/s
    phi: np.ndarray            # (n_red, n_modes) mass-normalised mode shapes
    gamma: dict[str, np.ndarray]
    meff: dict[str, np.ndarray]  # effective modal mass, N·s²/mm
    total_mass: dict[str, float]  # mass on free DOFs per direction
    mass_source: dict[str, float]
    notes: list[str] = field(default_factory=list)

    @property
    def periods(self) -> np.ndarray:
        return 2 * np.pi / self.omega

    @property
    def n_modes(self) -> int:
        return len(self.omega)

    def ratio(self, d: str) -> np.ndarray:
        """Effective mass ratio of each mode in direction ``d``."""
        tot = self.total_mass[d]
        return self.meff[d] / tot if tot > 0 else np.zeros(self.n_modes)

    def cumulative(self, d: str) -> np.ndarray:
        return np.cumsum(self.ratio(d))

    def mode_shape(self, n: int) -> np.ndarray:
        """(n_nodes, 6) global displacements of mode ``n`` (0-based), max translation = 1."""
        u = self.analysis.dofmap.expand(self.phi[:, n]).reshape(-1, 6)
        s = np.abs(u[:, :3]).max()
        return u / s if s > 0 else u

    def table(self) -> list[dict]:
        rows, cum = [], {d: 0.0 for d in self.meff}
        for n in range(self.n_modes):
            row = {"mode": n + 1, "T": float(self.periods[n]),
                   "f": float(self.omega[n] / (2 * np.pi))}
            for d in self.meff:
                r = float(self.ratio(d)[n])
                cum[d] += r
                row[f"m{d}"], row[f"sum{d}"] = r, cum[d]
            rows.append(row)
        return rows


def nodal_masses(analysis: Analysis, mass_source: dict[str, float]) -> np.ndarray:
    """Translational mass at every node (n_nodes,), N·s²/mm, from gravity loads."""
    model, dm = analysis.model, analysis.dofmap
    W = np.zeros(len(dm.node_ids))  # weight, N (downwards positive)
    for cname, factor in mass_source.items():
        if cname not in model.cases:
            raise StructureError("The mass source refers to load case {c}, which does not exist",
                                 c=cname)
        case = model.cases[cname]
        for nl in case.nodal:
            if nl.node in dm.index:
                W[dm.index[nl.node]] -= factor * nl.values[2]
        segs = analysis.member_segments(case)
        for k, e in enumerate(analysis.elements):
            if segs[k]:
                Rl, Sl = totals(segs[k])
                Rz, Sz = (e.R.T @ Rl)[2], (e.R.T @ Sl)[2]
                W[dm.index[e.member.j]] -= factor * Sz / e.L     # lever rule
                W[dm.index[e.member.i]] -= factor * (Rz - Sz / e.L)
    m = W / G_ACC
    for nid, extra in model.masses.items():
        if nid in dm.index:
            m[dm.index[nid]] += extra
    neg = np.where(m < -1e-9)[0]
    if len(neg):
        raise StructureError("Negative mass at node {n}: the mass-source loads act upwards there",
                             ref=f"node {dm.node_ids[neg[0]]}", n=dm.node_ids[neg[0]])
    return np.maximum(m, 0.0)


def modal(analysis: Analysis, mass_source: dict[str, float] | None = None, n_modes: int = 12,
          directions: str = "XY") -> ModalResult:
    """Natural periods, mode shapes and effective masses.

    ``mass_source`` maps load cases to factors, e.g. ``{"G": 1.0, "Q": 0.3}``
    (ψ_E = φ·ψ_2, EN 1998-1 4.2.4).  ``directions`` = translational DOFs that
    carry mass ("XY" for horizontal seismic analysis, "XYZ" to include vertical).
    """
    if mass_source is None:
        mass_source = {c: 1.0 for c in analysis.model.cases}
    dm = analysis.dofmap
    m_node = nodal_masses(analysis, mass_source)
    if m_node.sum() <= 0:
        raise StructureError("The model has no mass — define the mass source (e.g. G + 0.3·Q)")
    dirs = [_DIR[d] for d in directions]
    M = np.zeros((dm.n, dm.n))
    for k, nid in enumerate(dm.node_ids):
        if m_node[k] <= 0:
            continue
        for d in dirs:
            ids, cs = dm.rows[6 * k + d]
            if len(ids):
                M[np.ix_(ids, ids)] += m_node[k] * np.outer(cs, cs)
    a = analysis.active
    K, Ma = analysis.K[np.ix_(a, a)], M[np.ix_(a, a)]
    scale = np.abs(Ma).max()
    mi = np.where(np.abs(Ma).max(axis=1) > 1e-12 * scale)[0]
    oi = np.setdiff1d(np.arange(len(a)), mi)
    lam, V = np.linalg.eigh(Ma[np.ix_(mi, mi)])
    pos = lam > 1e-10 * lam.max()
    # basis: mass coordinates z+ = V+ᵀu_m (λ > 0); the rest are massless
    Bp = np.zeros((len(a), pos.sum()))
    Bp[mi] = V[:, pos]
    B0 = np.zeros((len(a), (~pos).sum() + len(oi)))
    B0[mi, :(~pos).sum()] = V[:, ~pos]
    B0[oi, (~pos).sum() + np.arange(len(oi))] = 1.0
    Kpp, Kp0, K00 = Bp.T @ K @ Bp, Bp.T @ K @ B0, B0.T @ K @ B0
    if B0.shape[1]:
        X = np.linalg.solve(K00, Kp0.T)  # z0 = −X x
        Kc = Kpp - Kp0 @ X
    else:
        X = np.zeros((0, Bp.shape[1]))
        Kc = Kpp
    s = 1 / np.sqrt(lam[pos])
    A = Kc * s[:, None] * s[None, :]
    w2, Y = np.linalg.eigh((A + A.T) / 2)
    n_modes = min(n_modes, len(w2))
    if w2[0] <= 0:
        raise StructureError("A mode with zero stiffness was found — the structure is a mechanism")
    w2, Y = w2[:n_modes], Y[:, :n_modes]
    x = Y * s[:, None]
    phi_a = Bp @ x - B0 @ (X @ x)
    phi = np.zeros((dm.n, n_modes))
    phi[a] = phi_a
    gamma, meff, total = {}, {}, {}
    for d in directions:
        r = np.array([1.0 if dm.kind[i] == _DIR[d] else 0.0 for i in range(dm.n)])[a]
        p = Ma @ r
        g = phi_a.T @ p
        gamma[d], meff[d], total[d] = g, g**2, float(r @ p)
    return ModalResult(analysis, np.sqrt(w2), phi, gamma, meff, total, dict(mass_source))


# --------------------------------------------------------------------- spectrum


def cqc_rho(omega: np.ndarray, zeta: float = 0.05) -> np.ndarray:
    """Der Kiureghian (1981) correlation coefficients for equal damping."""
    r = omega[None, :] / omega[:, None]
    return (8 * zeta**2 * (1 + r) * r**1.5) / ((1 - r**2) ** 2 + 4 * zeta**2 * r * (1 + r) ** 2)


def _combine(R: np.ndarray, rho: np.ndarray | None) -> np.ndarray:
    """R: (n_modes, ...) modal responses → combined peak (same trailing shape)."""
    flat = R.reshape(R.shape[0], -1)
    if rho is None:
        out = np.sqrt((flat**2).sum(axis=0))
    else:
        out = np.sqrt(np.maximum(np.einsum("iq,ij,jq->q", flat, rho, flat), 0.0))
    return out.reshape(R.shape[1:])


@dataclass
class SpectrumResult:
    direction: str
    combination: str
    periods: np.ndarray
    Sd: np.ndarray             # spectral acceleration per mode [g]
    base_shear_modes: np.ndarray  # N
    base_shear: float          # N, combined
    u: np.ndarray              # (n_nodes, 6) combined peak displacements (absolute)
    end_forces: np.ndarray     # (n_members, 12) combined peak local end forces (absolute)
    reactions: dict[str, np.ndarray]
    mass_ratio: float          # Σ effective mass of the modes used / total
    warnings: list[str] = field(default_factory=list)
    analysis: Analysis | None = None
    modal: list[StaticResult] = field(default_factory=list)  # signed response of each mode
    rho: np.ndarray | None = None                           # correlation (None = SRSS)

    def combine(self, values: np.ndarray) -> np.ndarray:
        """Combine any per-mode quantity (n_modes, ...) with this result's rule."""
        return _combine(np.asarray(values, dtype=float), self.rho)

    def displacement(self, node) -> np.ndarray:
        return self.u[self.analysis.dofmap.index[str(node)]]

    def member_end_forces(self, member) -> np.ndarray:
        return self.end_forces[self.analysis.member_index[str(member)]]


def response_spectrum(modes: ModalResult, Sd: Callable[[np.ndarray], np.ndarray],
                      direction: str = "X", combination: str = "CQC",
                      damping: float = 0.05) -> SpectrumResult:
    """Modal response spectrum analysis (EN 1998-1 4.3.3.3) in one horizontal direction.

    ``Sd(T)`` returns the design spectral acceleration in g (e.g. from
    :func:`ec8_spectrum`).  Displacements are the *elastic-analysis* values
    d_e; multiply by q_d for the design displacement (EN 1998-1 4.3.4).
    """
    if direction not in modes.gamma:
        raise StructureError("Direction {d} has no mass in the modal analysis", d=direction)
    an = modes.analysis
    T = modes.periods
    sd = np.asarray(Sd(T), dtype=float)
    acc = sd * G_ACC
    g = modes.gamma[direction]
    amp = g * acc / modes.omega**2  # modal coordinate peak
    results: list[StaticResult] = [
        an.static_from_displacements(f"mode {n + 1}", modes.phi[:, n] * amp[n])
        for n in range(modes.n_modes)]
    rho = cqc_rho(modes.omega, damping) if combination.upper() == "CQC" else None
    d = _DIR[direction]
    Vn = np.array([-sum(r[d] for r in res.reactions.values()) for res in results])
    u = _combine(np.array([r.u for r in results]), rho)
    ends = _combine(np.array([r.end_forces for r in results]), rho)
    keys = list(results[0].reactions) if results else []
    reac = {k: _combine(np.array([r.reactions[k] for r in results]), rho) for k in keys}
    V = float(_combine(Vn[:, None], rho)[0])
    ratio = float(modes.meff[direction].sum() / modes.total_mass[direction])
    warnings = []
    if ratio < 0.90:
        warnings.append(Msg("The modes used activate {r:.0f} % of the mass in {d} (< 90 %, "
                            "EN 1998-1 4.3.3.3.1(3)) — increase the number of modes",
                            r=100 * ratio, d=direction))
    return SpectrumResult(direction, combination.upper(), T, sd, np.abs(Vn), V, u, ends, reac,
                          ratio, warnings, an, results, rho)


@dataclass
class DesignSpectrum:
    """EN 1998-1 Type 1 horizontal design spectrum S_d(T) [g] (Eq. 3.13–3.16)."""

    ag: float      # design ground acceleration γ_I a_gR [g]
    S: float
    TB: float
    TC: float
    TD: float
    q: float
    beta: float

    def __call__(self, T):
        from ..design.ec8 import design_spectrum

        return design_spectrum(T, self.ag, self.S, self.TB, self.TC, self.TD, self.q, self.beta)


def ec8_spectrum(agR: float, ground: str = "B", q: float = 1.5, importance: str = "II",
                 annex: str | None = "EN") -> DesignSpectrum:
    """EN 1998-1 Type 1 design spectrum with the chosen National Annex values."""
    from ..design.annex import get_annex

    na = get_annex(annex)
    S, TB, TC, TD = na.spectrum[ground]
    return DesignSpectrum(agR * na.gamma_I[importance], S, TB, TC, TD, q, na.spectrum_beta)
