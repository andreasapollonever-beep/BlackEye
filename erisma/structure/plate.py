"""Four-node Mindlin plate element (MITC4, Bathe & Dvorkin 1985) for horizontal,
axis-aligned rectangular plates — rafts and slabs on elastic soil.

Degrees of freedom per node: w (uz), θx (rx), θy (ry), right-hand rotations about the
global axes, so they plug straight into the 6-DOF frame nodes.  Kinematics:
u = z·θy, v = −z·θx; curvatures κx = ∂θy/∂x, κy = −∂θx/∂y, κxy = ∂θy/∂y − ∂θx/∂x;
transverse shear γxz = ∂w/∂x + θy, γyz = ∂w/∂y − θx.  The MITC4 assumed shear strains
(tied at the edge mid-points) remove shear locking, so the element is accurate for thin
and thick plates alike.

Reported stress resultants (per unit width), engineering signs:
Mx, My positive = tension at the **bottom** face (sagging); Mxy twisting moment;
Qx, Qy transverse shear forces.
"""

from __future__ import annotations

import numpy as np

_XI = np.array([-1.0, 1.0, 1.0, -1.0])
_ETA = np.array([-1.0, -1.0, 1.0, 1.0])
_G = 1 / np.sqrt(3)
_GAUSS = [(-_G, -_G), (_G, -_G), (_G, _G), (-_G, _G)]


def _bending_B(xi: float, eta: float, a: float, b: float) -> np.ndarray:
    """3×12 curvature matrix at (ξ, η) for half sizes a (x) and b (y)."""
    dNx = _XI * (1 + eta * _ETA) / (4 * a)
    dNy = _ETA * (1 + xi * _XI) / (4 * b)
    B = np.zeros((3, 12))
    for i in range(4):
        B[0, 3 * i + 2] = dNx[i]          # κx = ∂θy/∂x
        B[1, 3 * i + 1] = -dNy[i]         # κy = −∂θx/∂y
        B[2, 3 * i + 2] = dNy[i]          # κxy = ∂θy/∂y − ∂θx/∂x
        B[2, 3 * i + 1] = -dNx[i]
    return B


def _shear_B(xi: float, eta: float, a: float, b: float) -> np.ndarray:
    """2×12 assumed (MITC) transverse shear strain matrix."""
    # tying points: A (ξ=0, η=−1) edge 1–2, C (η=+1) edge 4–3 for γxz;
    #               D (ξ=−1) edge 1–4, B (ξ=+1) edge 2–3 for γyz
    gA, gC, gB, gD = (np.zeros(12) for _ in range(4))
    # γxz = ∂w/∂x + θy along the x-edges
    gA[0], gA[3] = -1 / (2 * a), 1 / (2 * a)
    gA[2], gA[5] = 0.5, 0.5
    gC[9], gC[6] = -1 / (2 * a), 1 / (2 * a)
    gC[11], gC[8] = 0.5, 0.5
    # γyz = ∂w/∂y − θx along the y-edges
    gD[0], gD[9] = -1 / (2 * b), 1 / (2 * b)
    gD[1], gD[10] = -0.5, -0.5
    gB[3], gB[6] = -1 / (2 * b), 1 / (2 * b)
    gB[4], gB[7] = -0.5, -0.5
    Bs = np.zeros((2, 12))
    Bs[0] = 0.5 * (1 - eta) * gA + 0.5 * (1 + eta) * gC
    Bs[1] = 0.5 * (1 - xi) * gD + 0.5 * (1 + xi) * gB
    return Bs


def _D(E: float, nu: float, t: float) -> tuple[np.ndarray, np.ndarray]:
    Db = E * t**3 / (12 * (1 - nu**2)) * np.array([[1, nu, 0], [nu, 1, 0],
                                                    [0, 0, (1 - nu) / 2]])
    Ds = 5 / 6 * E / (2 * (1 + nu)) * t * np.eye(2)
    return Db, Ds


def mitc4_rect(lx: float, ly: float, t: float, E: float, nu: float) -> np.ndarray:
    """12×12 stiffness of a rectangular MITC4 plate, nodes in the order
    (x−, y−), (x+, y−), (x+, y+), (x−, y+); DOFs per node (w, θx, θy)."""
    a, b = lx / 2, ly / 2
    Db, Ds = _D(E, nu, t)
    K = np.zeros((12, 12))
    for xi, eta in _GAUSS:
        Bb = _bending_B(xi, eta, a, b)
        Bs = _shear_B(xi, eta, a, b)
        K += (Bb.T @ Db @ Bb + Bs.T @ Ds @ Bs) * a * b
    return K


def resultants(u: np.ndarray, lx: float, ly: float, t: float, E: float, nu: float) -> dict:
    """Stress resultants at the element centre from the 12 nodal values (w, θx, θy)."""
    a, b = lx / 2, ly / 2
    Db, Ds = _D(E, nu, t)
    m = Db @ (_bending_B(0.0, 0.0, a, b) @ u)
    q = Ds @ (_shear_B(0.0, 0.0, a, b) @ u)
    # bending stress σx = −z·(E/(1−ν²))(κx + νκy)… positive m = compression at the bottom;
    # engineering sign: sagging (tension at the bottom) positive
    return {"Mx": -m[0], "My": -m[1], "Mxy": -m[2], "Qx": q[0], "Qy": q[1]}
