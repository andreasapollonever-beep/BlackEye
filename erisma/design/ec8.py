"""EN 1998-1 helpers shared by the modules and the 3D structure solver."""

from __future__ import annotations

import numpy as np


def design_spectrum(T, ag, S, TB, TC, TD, q, beta):
    """EN 1998-1 Eq. 3.13–3.16 (Sd in g when ag in g)."""
    T = np.asarray(T, dtype=float)
    s1 = ag * S * (2 / 3 + T / TB * (2.5 / q - 2 / 3))
    s2 = ag * S * 2.5 / q * np.ones_like(T)
    s3 = np.maximum(ag * S * 2.5 / q * TC / np.maximum(T, 1e-9), beta * ag)
    s4 = np.maximum(ag * S * 2.5 / q * TC * TD / np.maximum(T, 1e-9) ** 2, beta * ag)
    return np.where(T <= TB, s1, np.where(T <= TC, s2, np.where(T <= TD, s3, s4)))
