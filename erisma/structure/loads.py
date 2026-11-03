"""Member load segments: exact fixed-end forces and internal-force integrals.

A member load is a list of *segments* in local axes: ``(x1, x2, w1, w2)`` with
``w1``/``w2`` the (wx, wy, wz) intensities in N/mm at ``x1``/``x2`` (mm from
end i), varying linearly in between.  Uniform, partial, triangular and
trapezoidal loads (e.g. from two-way slabs) are all segments.

Fixed-end forces are found by the force method on the cantilever released at
end j, with bending **and shear** flexibility, so they are exact for the
Timoshenko element and any segment (Gauss–Legendre integration of the
piecewise-polynomial integrands is exact).
"""

from __future__ import annotations

import numpy as np

Segment = tuple[float, float, np.ndarray, np.ndarray]

_GX, _GW = np.polynomial.legendre.leggauss(6)


def segment(x1: float, x2: float, w1, w2=None) -> Segment:
    w1 = np.asarray(w1, dtype=float)
    w2 = w1.copy() if w2 is None else np.asarray(w2, dtype=float)
    return (float(x1), float(x2), w1, w2)


def scale_segments(segs: list[Segment], f: float) -> list[Segment]:
    return [(a, b, f * w1, f * w2) for a, b, w1, w2 in segs]


def integrals(segs: list[Segment], x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Q(x) = ∫₀ˣ w dξ and Mx(x) = ∫₀ˣ w(ξ)(x − ξ) dξ, each (3, len(x))."""
    x = np.atleast_1d(np.asarray(x, dtype=float))
    Q = np.zeros((3, len(x)))
    M = np.zeros((3, len(x)))
    for x1, x2, w1, w2 in segs:
        if x2 <= x1:
            continue
        k = (w2 - w1) / (x2 - x1)
        t = np.clip(x, x1, x2)
        s = t - x1
        q = w1[:, None] * s + k[:, None] * s**2 / 2           # ∫ w
        # ∫_{x1}^{t} w(ξ) ξ dξ with w = w1 + k(ξ − x1)
        m1 = (w1[:, None] * (t**2 - x1**2) / 2
              + k[:, None] * ((t**3 - x1**3) / 3 - x1 * (t**2 - x1**2) / 2))
        Q += q
        M += x * q - m1
    return Q, M


def totals(segs: list[Segment]) -> tuple[np.ndarray, np.ndarray]:
    """Resultant (3,) and first moment ∫ w ξ dξ (3,) of the load."""
    R = np.zeros(3)
    S = np.zeros(3)
    for x1, x2, w1, w2 in segs:
        L = x2 - x1
        if L <= 0:
            continue
        R += (w1 + w2) / 2 * L
        # centroid of a trapezoid measured from x1: L (w1 + 2 w2) / (3 (w1 + w2))
        S += (w1 + w2) / 2 * L * x1 + L**2 * (w1 + 2 * w2) / 6
    return R, S


def _plane(segs: list[Segment], comp: int, L: float, EI: float, GA: float | None):
    """Fixed–fixed end forces (Pi, Mi, Pj, Mj) for transverse load component ``comp``
    with rotation θ = dv/dx positive."""
    if not any(np.any(w1[comp]) or np.any(w2[comp]) for _, _, w1, w2 in segs):
        return 0.0, 0.0, 0.0, 0.0
    R, S = totals(segs)
    QL, S1 = R[comp], S[comp]
    cuts = sorted({0.0, L, *[min(max(s[0], 0.0), L) for s in segs],
                   *[min(max(s[1], 0.0), L) for s in segs]})
    vL = thL = 0.0
    for a, b in zip(cuts[:-1], cuts[1:]):
        if b - a <= 0:
            continue
        x = (a + b) / 2 + (b - a) / 2 * _GX
        w = (b - a) / 2 * _GW
        Q, Ml = integrals(segs, x)
        Mc = S1 - x * QL + Ml[comp]      # moment of the loads beyond x, about x
        Vc = QL - Q[comp]
        vL += np.sum(w * (Mc * (L - x) / EI + (Vc / GA if GA else 0.0)))
        thL += np.sum(w * Mc / EI)
    F = np.array([[L**3 / (3 * EI) + (L / GA if GA else 0.0), L**2 / (2 * EI)],
                  [L**2 / (2 * EI), L / EI]])
    Pj, Mj = -np.linalg.solve(F, [vL, thL])
    Pi = -(QL + Pj)
    Mi = -(Mj + Pj * L + S1)
    return Pi, Mi, Pj, Mj


def fixed_end_forces(segs: list[Segment], L: float, EA: float, EIy: float, EIz: float,
                     GAy: float | None, GAz: float | None) -> np.ndarray:
    """12 local end forces on a fixed–fixed member (forces the supports exert on it)."""
    f = np.zeros(12)
    if not segs:
        return f
    R, S = totals(segs)
    # axial: constant EA → load shared by the lever rule
    f[6] = -S[0] / L
    f[0] = -R[0] - f[6]
    Pi, Mi, Pj, Mj = _plane(segs, 1, L, EIz, GAy)       # x–y plane, θz = dv/dx
    f[1], f[5], f[7], f[11] = Pi, Mi, Pj, Mj
    Pi, Mi, Pj, Mj = _plane(segs, 2, L, EIy, GAz)       # x–z plane, θy = −dw/dx
    f[2], f[4], f[8], f[10] = Pi, -Mi, Pj, -Mj
    return f
