"""Rectangular Kirchhoff plate under uniform load — finite differences.

Each edge is simply supported or fixed. Solves D ∇⁴w = p on an (nx × ny) grid with
ghost nodes (SS: w_ghost = −w_inner, fixed: w_ghost = +w_inner). Verified against
Timoshenko & Woinowsky-Krieger (square SS: w = 0.00406 pa⁴/D, M = 0.0479 pa², ν = 0.3).
"""

from __future__ import annotations

import numpy as np


def solve_plate(lx: float, ly: float, p: float, D: float = 1.0, nu: float = 0.2,
                edges: tuple[str, str, str, str] = ("ss", "ss", "ss", "ss"), n: int = 28):
    """edges = (x = 0, x = lx, y = 0, y = ly); returns dict of grids and extreme values."""
    nx = ny = n
    hx, hy = lx / nx, ly / ny
    N = (nx - 1) * (ny - 1)
    idx = lambda i, j: (i - 1) * (ny - 1) + (j - 1)  # noqa: E731
    sgn = {"ss": -1.0, "fixed": 1.0}

    def ref(i, j):
        """Map a grid point (possibly a ghost) to (coefficient, unknown) or None."""
        c = 1.0
        if i == -1:
            i, c = 1, c * sgn[edges[0]]
        elif i == nx + 1:
            i, c = nx - 1, c * sgn[edges[1]]
        if j == -1:
            j, c = 1, c * sgn[edges[2]]
        elif j == ny + 1:
            j, c = ny - 1, c * sgn[edges[3]]
        if i <= 0 or i >= nx or j <= 0 or j >= ny:
            return None
        return c, idx(i, j)

    A = np.zeros((N, N))
    rhs = np.full(N, p / D)
    st_x = {-2: 1, -1: -4, 0: 6, 1: -4, 2: 1}
    for i in range(1, nx):
        for j in range(1, ny):
            r = idx(i, j)
            for di, w in st_x.items():
                t = ref(i + di, j)
                if t:
                    A[r, t[1]] += w * t[0] / hx**4
            for dj, w in st_x.items():
                t = ref(i, j + dj)
                if t:
                    A[r, t[1]] += w * t[0] / hy**4
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    w = (1 if di else -2) * (1 if dj else -2)
                    t = ref(i + di, j + dj)
                    if t:
                        A[r, t[1]] += 2 * w * t[0] / (hx**2 * hy**2)
    sol = np.linalg.solve(A, rhs)
    W = np.zeros((nx + 1, ny + 1))
    for i in range(1, nx):
        for j in range(1, ny):
            W[i, j] = sol[idx(i, j)]

    def wv(i, j):
        t = ref(i, j)
        return 0.0 if t is None else t[0] * sol[t[1]]

    mx = np.zeros_like(W)
    my = np.zeros_like(W)
    for i in range(nx + 1):
        for j in range(ny + 1):
            wxx = (wv(i + 1, j) - 2 * wv(i, j) + wv(i - 1, j)) / hx**2
            wyy = (wv(i, j + 1) - 2 * wv(i, j) + wv(i, j - 1)) / hy**2
            mx[i, j] = -D * (wxx + nu * wyy)
            my[i, j] = -D * (wyy + nu * wxx)
    return {"w": W, "mx": mx, "my": my, "w_max": float(W.max()),
            "mx_span": float(mx.max()), "my_span": float(my.max()),
            "mx_sup": float(mx.min()), "my_sup": float(my.min()), "nx": nx, "ny": ny}
