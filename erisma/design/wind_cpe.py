"""Pressure coefficients of EN 1991-1-4 Section 7 for buildings and canopy roofs.

PROVISIONAL: every value below was entered from the final draft prEN 1991-1-4:2004 (January
2004), pages 37–60, and must be checked against the published EN 1991-1-4:2005 + A1:2010
(and AC:2010) before release.  ``SOURCE`` is printed in every report that uses these tables.

Cells are ``(c_pe,10, c_pe,1)``.  Where a table gives a positive and a negative value for the
same zone (NOTE 1 of Tables 7.3a–7.5) a row holds ``{"neg": (...), "pos": (...)}``.
"""

from __future__ import annotations

import math

SOURCE = ("prEN 1991-1-4:2004 (final draft, January 2004) — provisional values, to be verified "
          "against EN 1991-1-4:2005 + A1:2010")
VERIFIED = False

Cell = tuple[float, float]


def _c(a: float, b: float | None = None) -> Cell:
    return (a, a if b is None else b)


def _np(neg: Cell | None, pos: Cell | None) -> dict:
    return {"neg": neg, "pos": pos}


# --------------------------------------------------------------- Table 7.1 walls
# h/d -> zone -> cell (D positive; others negative)
WALLS = {
    5.0: {"A": _c(-1.2, -1.4), "B": _c(-0.8, -1.1), "C": _c(-0.5), "D": _c(0.8, 1.0),
          "E": _c(-0.7)},
    1.0: {"A": _c(-1.2, -1.4), "B": _c(-0.8, -1.1), "C": _c(-0.5), "D": _c(0.8, 1.0),
          "E": _c(-0.5)},
    0.25: {"A": _c(-1.2, -1.4), "B": _c(-0.8, -1.1), "C": _c(-0.5), "D": _c(0.7, 1.0),
           "E": _c(-0.3)},
}

# ------------------------------------------------------------ Table 7.2 flat roofs
FLAT_SHARP = {"F": _c(-1.8, -2.5), "G": _c(-1.2, -2.0), "H": _c(-0.7, -1.2)}
FLAT_PARAPET = {  # h_p/h
    0.025: {"F": _c(-1.6, -2.2), "G": _c(-1.1, -1.8), "H": _c(-0.7, -1.2)},
    0.05: {"F": _c(-1.4, -2.0), "G": _c(-0.9, -1.6), "H": _c(-0.7, -1.2)},
    0.10: {"F": _c(-1.2, -1.8), "G": _c(-0.8, -1.4), "H": _c(-0.7, -1.2)},
}
FLAT_CURVED = {  # r/h
    0.05: {"F": _c(-1.0, -1.5), "G": _c(-1.2, -1.8), "H": _c(-0.4)},
    0.10: {"F": _c(-0.7, -1.2), "G": _c(-0.8, -1.4), "H": _c(-0.3)},
    0.20: {"F": _c(-0.5, -0.8), "G": _c(-0.5, -0.8), "H": _c(-0.3)},
}
FLAT_MANSARD = {  # α
    30.0: {"F": _c(-1.0, -1.5), "G": _c(-1.0, -1.5), "H": _c(-0.3)},
    45.0: {"F": _c(-1.2, -1.8), "G": _c(-1.3, -1.9), "H": _c(-0.4)},
    60.0: {"F": _c(-1.3, -1.9), "G": _c(-1.3, -1.9), "H": _c(-0.5)},
}
FLAT_I = _np(_c(-0.2), _c(0.2))  # zone I: both values shall be considered (NOTE 3)

# ------------------------------------------------------- Table 7.3 monopitch roofs
_Z0 = _c(0.0)
MONO_0 = {
    5.0: {"F": _np(_c(-1.7, -2.5), _Z0), "G": _np(_c(-1.2, -2.0), _Z0),
          "H": _np(_c(-0.6, -1.2), _Z0)},
    15.0: {"F": _np(_c(-0.9, -2.0), _c(0.2)), "G": _np(_c(-0.8, -1.5), _c(0.2)),
           "H": _np(_c(-0.3), _c(0.2))},
    30.0: {"F": _np(_c(-0.5, -1.5), _c(0.7)), "G": _np(_c(-0.5, -1.5), _c(0.7)),
           "H": _np(_c(-0.2), _c(0.4))},
    45.0: {"F": _np(_Z0, _c(0.7)), "G": _np(_Z0, _c(0.7)), "H": _np(_Z0, _c(0.6))},
    60.0: {"F": _np(None, _c(0.7)), "G": _np(None, _c(0.7)), "H": _np(None, _c(0.7))},
    75.0: {"F": _np(None, _c(0.8)), "G": _np(None, _c(0.8)), "H": _np(None, _c(0.8))},
}
MONO_180 = {
    5.0: {"F": _c(-2.3, -2.5), "G": _c(-1.3, -2.0), "H": _c(-0.8, -1.2)},
    15.0: {"F": _c(-2.5, -2.8), "G": _c(-1.3, -2.0), "H": _c(-0.9, -1.2)},
    30.0: {"F": _c(-1.1, -2.3), "G": _c(-0.8, -1.5), "H": _c(-0.8)},
    45.0: {"F": _c(-0.6, -1.3), "G": _c(-0.5), "H": _c(-0.7)},
    60.0: {"F": _c(-0.5, -1.0), "G": _c(-0.5), "H": _c(-0.5)},
    75.0: {"F": _c(-0.5, -1.0), "G": _c(-0.5), "H": _c(-0.5)},
}
MONO_90 = {
    5.0: {"Fup": _c(-2.1, -2.6), "Flow": _c(-2.1, -2.4), "G": _c(-1.8, -2.0),
          "H": _c(-0.6, -1.2), "I": _c(-0.5)},
    15.0: {"Fup": _c(-2.4, -2.9), "Flow": _c(-1.6, -2.4), "G": _c(-1.9, -2.5),
           "H": _c(-0.8, -1.2), "I": _c(-0.7, -1.2)},
    30.0: {"Fup": _c(-2.1, -2.9), "Flow": _c(-1.3, -2.0), "G": _c(-1.5, -2.0),
           "H": _c(-1.0, -1.3), "I": _c(-0.8, -1.2)},
    45.0: {"Fup": _c(-1.5, -2.4), "Flow": _c(-1.3, -2.0), "G": _c(-1.4, -2.0),
           "H": _c(-1.0, -1.3), "I": _c(-0.9, -1.2)},
    60.0: {"Fup": _c(-1.2, -2.0), "Flow": _c(-1.2, -2.0), "G": _c(-1.2, -2.0),
           "H": _c(-1.0, -1.3), "I": _c(-0.7, -1.2)},
    75.0: {"Fup": _c(-1.2, -2.0), "Flow": _c(-1.2, -2.0), "G": _c(-1.2, -2.0),
           "H": _c(-1.0, -1.3), "I": _c(-0.5)},
}

# -------------------------------------------------------- Table 7.4 duopitch roofs
DUO_0 = {
    -45.0: {"F": _np(_c(-0.6), None), "G": _np(_c(-0.6), None), "H": _np(_c(-0.8), None),
            "I": _np(_c(-0.7), None), "J": _np(_c(-1.0, -1.5), None)},
    -30.0: {"F": _np(_c(-1.1, -2.0), None), "G": _np(_c(-0.8, -1.5), None),
            "H": _np(_c(-0.8), None), "I": _np(_c(-0.6), None), "J": _np(_c(-0.8, -1.4), None)},
    -15.0: {"F": _np(_c(-2.5, -2.8), None), "G": _np(_c(-1.3, -2.0), None),
            "H": _np(_c(-0.9, -1.2), None), "I": _np(_c(-0.5), None),
            "J": _np(_c(-0.7, -1.2), None)},
    -5.0: {"F": _np(_c(-2.3, -2.5), None), "G": _np(_c(-1.2, -2.0), None),
           "H": _np(_c(-0.8, -1.2), None), "I": _np(_c(-0.6), _c(0.2)),
           "J": _np(_c(-0.6), _c(0.2))},
    5.0: {"F": _np(_c(-1.7, -2.5), _Z0), "G": _np(_c(-1.2, -2.0), _Z0),
          "H": _np(_c(-0.6, -1.2), _Z0), "I": _np(_c(-0.6), None),
          "J": _np(_c(-0.6), _c(0.2))},
    15.0: {"F": _np(_c(-0.9, -2.0), _c(0.2)), "G": _np(_c(-0.8, -1.5), _c(0.2)),
           "H": _np(_c(-0.3), _c(0.2)), "I": _np(_c(-0.4), _Z0),
           "J": _np(_c(-1.0, -1.5), _Z0)},
    30.0: {"F": _np(_c(-0.5, -1.5), _c(0.7)), "G": _np(_c(-0.5, -1.5), _c(0.7)),
           "H": _np(_c(-0.2), _c(0.4)), "I": _np(_c(-0.4), _Z0), "J": _np(_c(-0.5), _Z0)},
    45.0: {"F": _np(_Z0, _c(0.7)), "G": _np(_Z0, _c(0.7)), "H": _np(_Z0, _c(0.6)),
           "I": _np(_c(-0.2), _Z0), "J": _np(_c(-0.3), _Z0)},
    60.0: {"F": _np(None, _c(0.7)), "G": _np(None, _c(0.7)), "H": _np(None, _c(0.7)),
           "I": _np(_c(-0.2), None), "J": _np(_c(-0.3), None)},
    75.0: {"F": _np(None, _c(0.8)), "G": _np(None, _c(0.8)), "H": _np(None, _c(0.8)),
           "I": _np(_c(-0.2), None), "J": _np(_c(-0.3), None)},
}
DUO_90 = {
    -45.0: {"F": _c(-1.4, -2.0), "G": _c(-1.2, -2.0), "H": _c(-1.0, -1.3), "I": _c(-0.9, -1.2)},
    -30.0: {"F": _c(-1.5, -2.1), "G": _c(-1.2, -2.0), "H": _c(-1.0, -1.3), "I": _c(-0.9, -1.2)},
    -15.0: {"F": _c(-1.9, -2.5), "G": _c(-1.2, -2.0), "H": _c(-0.8, -1.2), "I": _c(-0.8, -1.2)},
    -5.0: {"F": _c(-1.8, -2.5), "G": _c(-1.2, -2.0), "H": _c(-0.7, -1.2), "I": _c(-0.6, -1.2)},
    5.0: {"F": _c(-1.6, -2.2), "G": _c(-1.3, -2.0), "H": _c(-0.7, -1.2), "I": _c(-0.6)},
    15.0: {"F": _c(-1.3, -2.0), "G": _c(-1.3, -2.0), "H": _c(-0.6, -1.2), "I": _c(-0.5)},
    30.0: {"F": _c(-1.1, -1.5), "G": _c(-1.4, -2.0), "H": _c(-0.8, -1.2), "I": _c(-0.5)},
    45.0: {"F": _c(-1.1, -1.5), "G": _c(-1.4, -2.0), "H": _c(-0.9, -1.2), "I": _c(-0.5)},
    60.0: {"F": _c(-1.1, -1.5), "G": _c(-1.2, -2.0), "H": _c(-0.8, -1.0), "I": _c(-0.5)},
    75.0: {"F": _c(-1.1, -1.5), "G": _c(-1.2, -2.0), "H": _c(-0.8, -1.0), "I": _c(-0.5)},
}

# ---------------------------------------------------------- Table 7.5 hipped roofs
HIPPED = {
    5.0: {"F": _np(_c(-1.7, -2.5), _Z0), "G": _np(_c(-1.2, -2.0), _Z0),
          "H": _np(_c(-0.6, -1.2), _Z0), "I": _np(_c(-0.3), None), "J": _np(_c(-0.6), None),
          "K": _np(_c(-0.6), None), "L": _np(_c(-1.2, -2.0), None),
          "M": _np(_c(-0.6, -1.2), None), "N": _np(_c(-0.4), None)},
    15.0: {"F": _np(_c(-0.9, -2.0), _c(0.2)), "G": _np(_c(-0.8, -1.5), _c(0.2)),
           "H": _np(_c(-0.3), _c(0.2)), "I": _np(_c(-0.5), None),
           "J": _np(_c(-1.0, -1.5), None), "K": _np(_c(-1.2, -2.0), None),
           "L": _np(_c(-1.4, -2.0), None), "M": _np(_c(-0.6, -1.2), None),
           "N": _np(_c(-0.3), None)},
    30.0: {"F": _np(_c(-0.5, -1.5), _c(0.5)), "G": _np(_c(-0.5, -1.5), _c(0.7)),
           "H": _np(_c(-0.2), _c(0.4)), "I": _np(_c(-0.4), None),
           "J": _np(_c(-0.7, -1.2), None), "K": _np(_c(-0.5), None),
           "L": _np(_c(-1.4, -2.0), None), "M": _np(_c(-0.8, -1.2), None),
           "N": _np(_c(-0.2), None)},
    45.0: {"F": _np(_Z0, _c(0.7)), "G": _np(_Z0, _c(0.7)), "H": _np(_Z0, _c(0.6)),
           "I": _np(_c(-0.3), None), "J": _np(_c(-0.6), None), "K": _np(_c(-0.3), None),
           "L": _np(_c(-1.3, -2.0), None), "M": _np(_c(-0.8, -1.2), None),
           "N": _np(_c(-0.2), None)},
    60.0: {"F": _np(None, _c(0.7)), "G": _np(None, _c(0.7)), "H": _np(None, _c(0.7)),
           "I": _np(_c(-0.3), None), "J": _np(_c(-0.6), None), "K": _np(_c(-0.3), None),
           "L": _np(_c(-1.2, -2.0), None), "M": _np(_c(-0.4), None),
           "N": _np(_c(-0.2), None)},
    75.0: {"F": _np(None, _c(0.8)), "G": _np(None, _c(0.8)), "H": _np(None, _c(0.8)),
           "I": _np(_c(-0.3), None), "J": _np(_c(-0.6), None), "K": _np(_c(-0.3), None),
           "L": _np(_c(-1.2, -2.0), None), "M": _np(_c(-0.4), None),
           "N": _np(_c(-0.2), None)},
}

# --------------------------------------------------- Tables 7.6, 7.7 canopy roofs
# α -> (max all φ, min φ = 0, min φ = 1); each = (c_f, zone A, zone B, zone C[, zone D])
CANOPY_MONO = {
    0.0: ((0.2, 0.5, 1.8, 1.1), (-0.5, -0.6, -1.3, -1.4), (-1.3, -1.5, -1.8, -2.2)),
    5.0: ((0.4, 0.8, 2.1, 1.3), (-0.7, -1.1, -1.7, -1.8), (-1.4, -1.6, -2.2, -2.5)),
    10.0: ((0.5, 1.2, 2.4, 1.6), (-0.9, -1.5, -2.0, -2.1), (-1.4, -2.1, -2.6, -2.7)),
    15.0: ((0.7, 1.4, 2.7, 1.8), (-1.1, -1.8, -2.4, -2.5), (-1.4, -1.6, -2.9, -3.0)),
    20.0: ((0.8, 1.7, 2.9, 2.1), (-1.3, -2.2, -2.8, -2.9), (-1.4, -1.6, -2.9, -3.0)),
    25.0: ((1.0, 2.0, 3.1, 2.3), (-1.6, -2.6, -3.2, -3.2), (-1.4, -1.5, -2.5, -2.8)),
    30.0: ((1.2, 2.2, 3.2, 2.4), (-1.8, -3.0, -3.8, -3.6), (-1.4, -1.5, -2.2, -2.7)),
}
CANOPY_DUO = {
    -20.0: ((0.7, 0.8, 1.6, 0.6, 1.7), (-0.7, -0.9, -1.3, -1.6, -0.6),
            (-1.3, -1.5, -2.4, -2.4, -0.6)),
    -15.0: ((0.5, 0.6, 1.5, 0.7, 1.4), (-0.6, -0.8, -1.3, -1.6, -0.6),
            (-1.4, -1.6, -2.7, -2.6, -0.6)),
    -10.0: ((0.4, 0.6, 1.4, 0.8, 1.1), (-0.6, -0.8, -1.3, -1.5, -0.6),
            (-1.4, -1.6, -2.7, -2.6, -0.6)),
    -5.0: ((0.3, 0.5, 1.5, 0.8, 0.8), (-0.5, -0.7, -1.3, -1.6, -0.6),
           (-1.3, -1.5, -2.4, -2.4, -0.6)),
    5.0: ((0.3, 0.6, 1.8, 1.3, 0.4), (-0.6, -0.6, -1.4, -1.4, -1.1),
          (-1.3, -1.3, -2.0, -1.8, -1.5)),
    10.0: ((0.4, 0.7, 1.8, 1.4, 0.4), (-0.7, -0.7, -1.5, -1.4, -1.4),
           (-1.3, -1.3, -2.0, -1.8, -1.8)),
    15.0: ((0.4, 0.9, 1.9, 1.4, 0.4), (-0.8, -0.9, -1.7, -1.4, -1.8),
           (-1.3, -1.3, -2.2, -1.6, -2.1)),
    20.0: ((0.6, 1.1, 1.9, 1.5, 0.4), (-0.9, -1.2, -1.8, -1.4, -2.0),
           (-1.3, -1.4, -2.2, -1.6, -2.1)),
    25.0: ((0.7, 1.2, 1.9, 1.6, 0.5), (-1.0, -1.4, -1.9, -1.4, -2.0),
           (-1.3, -1.4, -2.0, -1.5, -2.0)),
    30.0: ((0.9, 1.3, 1.9, 1.6, 0.7), (-1.0, -1.4, -1.9, -1.4, -2.0),
           (-1.3, -1.4, -1.8, -1.4, -2.0)),
}


# ------------------------------------------------------------------ helpers
def lerp(x: float, x1: float, x2: float, y1: float, y2: float) -> float:
    return y1 if x2 == x1 else y1 + (y2 - y1) * (x - x1) / (x2 - x1)


def bracket(keys: list[float], x: float) -> tuple[float, float]:
    """The two table rows around ``x`` (clamped to the table)."""
    ks = sorted(keys)
    if x <= ks[0]:
        return ks[0], ks[0]
    if x >= ks[-1]:
        return ks[-1], ks[-1]
    for a, b in zip(ks, ks[1:]):
        if a <= x <= b:
            return a, b
    return ks[-1], ks[-1]  # pragma: no cover


def interp_cell(c1: Cell, c2: Cell, x: float, x1: float, x2: float) -> Cell:
    return (lerp(x, x1, x2, c1[0], c2[0]), lerp(x, x1, x2, c1[1], c2[1]))


def interp_zones(table: dict, x: float) -> dict[str, Cell]:
    """Linear interpolation of simple cells (no sign cases)."""
    a, b = bracket(list(table), x)
    return {z: interp_cell(table[a][z], table[b][z], x, a, b) for z in table[a]}


def interp_signed(table: dict, x: float) -> dict[str, dict]:
    """Interpolate the negative and positive cases separately (same sign only, NOTE 2).

    A case exists at ``x`` only when both bracketing rows give it.
    """
    a, b = bracket(list(table), x)
    out = {}
    for z in table[a]:
        res = {}
        for s in ("neg", "pos"):
            ca, cb = table[a][z][s], table[b][z][s]
            res[s] = interp_cell(ca, cb, x, a, b) if ca is not None and cb is not None else None
        if res["neg"] is None and res["pos"] is None:  # only one row has a value: take it
            res = dict(table[a][z] if x - a <= b - x else table[b][z])
        out[z] = res
    return out


def cpe_area(cell: Cell, A: float) -> float:
    """c_pe for a loaded area A [m²] — recommended procedure of Figure 7.2."""
    c10, c1 = cell
    if A <= 1.0:
        return c1
    if A >= 10.0:
        return c10
    return c1 - (c1 - c10) * math.log10(A)


def walls(h_d: float) -> dict[str, Cell]:
    return interp_zones(WALLS, h_d)


def lack_of_correlation(h_d: float) -> float:
    """7.2.2(3) NOTE: 1.0 for h/d ≥ 5, 0.85 for h/d ≤ 1, linear between."""
    if h_d >= 5:
        return 1.0
    if h_d <= 1:
        return 0.85
    return 0.85 + 0.15 * (h_d - 1) / 4


def flat_roof(kind: str, ratio: float) -> dict[str, Cell]:
    """Table 7.2 zones F, G, H for the eave type; ``ratio`` = h_p/h, r/h or α."""
    if kind == "sharp":
        return dict(FLAT_SHARP)
    if kind == "parapet":
        if ratio < 0.025:  # between sharp eaves (h_p/h = 0) and 0.025
            t = {0.0: FLAT_SHARP, 0.025: FLAT_PARAPET[0.025]}
            return interp_zones(t, ratio)
        return interp_zones(FLAT_PARAPET, ratio)
    if kind == "curved":
        return interp_zones(FLAT_CURVED, ratio)
    if kind == "mansard":
        if ratio > 60:  # NOTE 2: between α = 60° and sharp eaves (α = 90°)
            return interp_zones({60.0: FLAT_MANSARD[60.0], 90.0: FLAT_SHARP}, ratio)
        return interp_zones(FLAT_MANSARD, ratio)
    raise ValueError(kind)


def internal_mu(mu: float, h_d: float) -> float:
    """c_pi from the opening ratio μ (Figure 7.13), linear in h/d between 0.25 and 1.0."""
    def line(end_mu, end_c):
        if mu <= 0.33:
            return 0.35
        if mu >= end_mu:
            return end_c
        return lerp(mu, 0.33, end_mu, 0.35, end_c)
    lo, hi = line(0.9, -0.3), line(0.95, -0.5)  # h/d ≤ 0.25, h/d ≥ 1.0
    if h_d <= 0.25:
        return lo
    if h_d >= 1.0:
        return hi
    return lerp(h_d, 0.25, 1.0, lo, hi)


def canopy(table: dict, alpha: float, phi: float) -> tuple[tuple, tuple]:
    """(maximum, minimum) rows (c_f, zones…) at pitch α and blockage φ (linear in α and φ)."""
    a, b = bracket(list(table), alpha)

    def row(i):
        return tuple(lerp(alpha, a, b, u, v) for u, v in zip(table[a][i], table[b][i]))

    mx, mn0, mn1 = row(0), row(1), row(2)
    mn = tuple(u + (v - u) * phi for u, v in zip(mn0, mn1))
    return mx, mn


# ------------------------------------------------------- 7.2.7 multispan roofs
def multispan_factor(config: str, k: int, cpe_first: float) -> tuple[str, float]:
    """Figure 7.10: ('factor', f) → c_pe,k = f·c_pe of span 1, or ('value', v) → c_pe,k = v.

    config 'a' — monopitch, wind onto the high eave (θ = 180°): 1, 0.8, 0.6 …
    config 'b' — monopitch, wind onto the low eave (θ = 0°): c_pe > 0 → −0.4 on the following
                 spans; c_pe < 0 → 0.8, 0.6 …
    config 'd' — troughed duopitch spans: 1, 0.8, 0.6 …
    """
    if k == 1:
        return "factor", 1.0
    if config == "b" and cpe_first > 0:
        return "value", -0.4
    return "factor", 0.8 if k == 2 else 0.6


# ------------------------------------------------- 7.2.8 vaulted roofs (Fig. 7.11)
# c_pe,10 read from the lines of Figure 7.11 (f/d from 0.05; constant beyond the ends)
_VAULT_A0 = [(0.05, 0.08), (0.5, 0.8)]                          # A, h/d = 0
_VAULT_A05_NEG = [(0.05, -0.95), (0.1, -1.2), (0.2, -1.2), (0.3, -0.3)]  # A, h/d ≥ 0.5
_VAULT_A05_POS = [(0.2, 0.0), (0.5, 0.8)]                       # A, h/d ≥ 0.5 (f/d ≥ 0.2)
_VAULT_B = [(0.05, -0.75), (0.5, -1.2)]
_VAULT_C = [(0.05, -0.55), (0.1, -0.4), (0.5, -0.4)]


def _poly(pts, x):
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if x1 <= x <= x2:
            return lerp(x, x1, x2, y1, y2)
    return pts[-1][1]  # pragma: no cover


def vaulted(f_d: float, h_d: float) -> dict[str, list[float]]:
    """Zones A, B, C of a cylindrical vault: list of c_pe,10 values to consider (Fig. 7.11).

    For 0.2 ≤ f/d ≤ 0.3 and h/d ≥ 0.5 two values of zone A apply; for 0 < h/d < 0.5 zone A is
    interpolated linearly between h/d = 0 and h/d = 0.5.
    """
    a0 = _poly(_VAULT_A0, f_d)
    if f_d < 0.2:
        a05 = [_poly(_VAULT_A05_NEG, f_d)]
    elif f_d <= 0.3:
        a05 = [_poly(_VAULT_A05_NEG, f_d), _poly(_VAULT_A05_POS, f_d)]
    else:
        a05 = [_poly(_VAULT_A05_POS, f_d)]
    t = min(max(h_d / 0.5, 0.0), 1.0)
    A = [a0 + (v - a0) * t for v in a05]
    return {"A": A, "B": [_poly(_VAULT_B, f_d)], "C": [_poly(_VAULT_C, f_d)]}


# ------------------------------------------------------ 7.2.9 dominant openings
def dominant_factor(ratio: float) -> float:
    """Eq. 7.2 / 7.3: c_pi = f·c_pe with f = 0.75 (ratio 2) … 0.90 (ratio ≥ 3)."""
    if ratio <= 2:
        return 0.75
    if ratio >= 3:
        return 0.90
    return lerp(ratio, 2, 3, 0.75, 0.90)


# ------------------------------------- 7.4.1 free-standing walls (Table 7.9)
FREE_WALL_SOLID = {3.0: (2.3, 1.4, 1.2, 1.2), 5.0: (2.9, 1.8, 1.4, 1.2),
                   10.0: (3.4, 2.1, 1.7, 1.2)}   # φ = 1, without return corners, l/h
FREE_WALL_RETURN = (2.1, 1.8, 1.4, 1.2)          # φ = 1, return corners ≥ h (±)
FREE_WALL_POROUS = (1.2, 1.2, 1.2, 1.2)          # φ = 0.8 (±)


def free_wall(l_h: float, phi: float, ret_h: float) -> tuple[float, ...]:
    """c_p,net of zones A–D for l/h, solidity φ (0.8 … 1) and return corner length / h."""
    a, b = bracket(list(FREE_WALL_SOLID), l_h)
    solid = tuple(lerp(l_h, a, b, u, v) for u, v in zip(FREE_WALL_SOLID[a], FREE_WALL_SOLID[b]))
    r = min(max(ret_h, 0.0), 1.0)
    solid = tuple(u + (v - u) * r for u, v in zip(solid, FREE_WALL_RETURN))
    t = (phi - 0.8) / 0.2
    return tuple(p + (s - p) * t for s, p in zip(solid, FREE_WALL_POROUS))


# Figure 7.20 — shelter factor ψ_s against x/h for φ = 1.0 and φ = 0.8
_SHELTER_1 = [(0.0, 0.3), (5.0, 0.3), (10.0, 0.65), (15.0, 0.85), (20.0, 1.0)]
_SHELTER_08 = [(0.0, 0.3), (5.0, 0.3), (10.0, 0.45), (15.0, 0.65), (20.0, 1.0)]


def shelter(x_h: float, phi: float) -> float:
    s1, s8 = _poly(_SHELTER_1, x_h), _poly(_SHELTER_08, x_h)
    t = min(max((phi - 0.8) / 0.2, 0.0), 1.0)
    return s8 + (s1 - s8) * t


# ------------------------------------------------------- 7.4.3 signboards, 7.5 friction
SIGN_CF = 1.80  # Eq. 7.8
FRICTION = {"smooth": 0.01, "rough": 0.02, "very_rough": 0.04}  # Table 7.10
