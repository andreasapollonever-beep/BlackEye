"""Geotechnical helpers: earth pressure coefficients, bearing capacity, polygons."""

from __future__ import annotations

import math

Point = tuple[float, float]


# ------------------------------------------------------------------ polygons
def poly_props(pts: list[Point]) -> tuple[float, float, float]:
    """Area and centroid ``(A, cx, cz)`` of a simple polygon (any orientation)."""
    if len(pts) < 3:
        return 0.0, 0.0, 0.0
    a = cx = cz = 0.0
    for (x1, z1), (x2, z2) in zip(pts, pts[1:] + pts[:1]):
        cr = x1 * z2 - x2 * z1
        a += cr
        cx += (x1 + x2) * cr
        cz += (z1 + z2) * cr
    if abs(a) < 1e-12:
        return 0.0, 0.0, 0.0
    a *= 0.5
    return abs(a), cx / (6 * a), cz / (6 * a)


def clip_z(pts: list[Point], zc: float, keep_below: bool) -> list[Point]:
    """Clip a polygon by the horizontal line z = zc (Sutherland–Hodgman)."""
    inside = (lambda p: p[1] <= zc) if keep_below else (lambda p: p[1] >= zc)
    out: list[Point] = []
    for i, cur in enumerate(pts):
        prev = pts[i - 1]
        if inside(cur):
            if not inside(prev):
                out.append(_cross(prev, cur, zc))
            out.append(cur)
        elif inside(prev):
            out.append(_cross(prev, cur, zc))
    return out


def _cross(p: Point, q: Point, zc: float) -> Point:
    t = (zc - p[1]) / (q[1] - p[1])
    return (p[0] + t * (q[0] - p[0]), zc)


# ----------------------------------------------------------- earth pressure
def ka_coulomb(phi: float, beta: float, delta: float, alpha: float = 0.0) -> float:
    """Coulomb active coefficient (angles in radians; α = back inclination from vertical)."""
    if beta > phi:
        raise ValueError("Backfill slope β exceeds the angle of shearing resistance φ'")
    num = math.cos(phi - alpha) ** 2
    root = math.sqrt(max(math.sin(phi + delta) * math.sin(phi - beta), 0.0)
                     / (math.cos(alpha + delta) * math.cos(alpha - beta)))
    return num / (math.cos(alpha) ** 2 * math.cos(alpha + delta) * (1 + root) ** 2)


def k_mononobe_okabe(phi: float, beta: float, delta: float, theta: float) -> float:
    """EN 1998-5 Eq. E.2 (vertical back, ψ = 90°, β ≤ φ − θ)."""
    if phi - beta - theta < 0:
        raise ValueError("β > φ'd − θ: Mononobe-Okabe has no solution (use Eq. E.3)")
    root = math.sqrt(math.sin(phi + delta) * math.sin(phi - beta - theta)
                     / (math.cos(theta + delta) * math.cos(beta)))
    return math.cos(phi - theta) ** 2 / (math.cos(theta) * math.cos(theta + delta)
                                         * (1 + root) ** 2)


def kp_rankine(phi: float) -> float:
    return math.tan(math.pi / 4 + phi / 2) ** 2


def linear_resultant(z1: float, p1: float, z2: float, p2: float) -> tuple[float, float]:
    """Force and point of application of a linear pressure from z1 to z2."""
    dz = z2 - z1
    F = 0.5 * (p1 + p2) * dz
    if abs(p1 + p2) < 1e-15:
        return 0.0, 0.5 * (z1 + z2)
    return F, z1 + dz * (p1 + 2 * p2) / (3 * (p1 + p2))


# ---------------------------------------------------------------- bearing
def bearing_factors(phi: float) -> tuple[float, float, float]:
    """EN 1997-1 Annex D.4: (Nq, Nc, Nγ) for φ in radians (φ > 0)."""
    Nq = math.exp(math.pi * math.tan(phi)) * math.tan(math.pi / 4 + phi / 2) ** 2
    Nc = (Nq - 1) / math.tan(phi)
    Ng = 2 * (Nq - 1) * math.tan(phi)
    return Nq, Nc, Ng


def kp_coulomb(phi: float, delta: float) -> float:
    """Coulomb passive coefficient for a vertical wall and horizontal ground.

    ``delta`` is the magnitude of the (negative) wall friction angle; keep
    δ ≤ φ/2 because Coulomb overestimates passive resistance for larger δ.
    """
    root = math.sqrt(math.sin(phi + delta) * math.sin(phi) / math.cos(delta))
    return math.cos(phi) ** 2 / (math.cos(delta) * (1 - root) ** 2)


def kp_seismic(phi: float, theta: float) -> float:
    """EN 1998-5 Eq. E.4 passive coefficient (vertical wall, horizontal ground, δ = 0)."""
    val = math.sin(phi) * math.sin(phi - theta) / math.cos(theta)
    return math.cos(phi - theta) ** 2 / (math.cos(theta) ** 2 * (1 - math.sqrt(max(val, 0))) ** 2)
