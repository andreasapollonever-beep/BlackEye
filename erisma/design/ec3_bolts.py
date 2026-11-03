"""EN 1993-1-8 bolt data and resistances (N, mm)."""

from __future__ import annotations

import math

# property class -> (f_yb, f_ub) N/mm² (Table 3.1)
BOLT_CLASSES = {"4.6": (240.0, 400.0), "5.6": (300.0, 500.0), "8.8": (640.0, 800.0),
                "10.9": (900.0, 1000.0)}
# nominal diameter -> tensile stress area A_s [mm²] (ISO 898-1)
BOLT_AS = {12: 84.3, 16: 157.0, 20: 245.0, 22: 303.0, 24: 353.0, 27: 459.0, 30: 561.0,
           36: 817.0}
# plate grades -> (f_y, f_u) for t ≤ 40 mm (EN 1993-1-1 Table 3.1)
PLATE = {"S235": (235.0, 360.0), "S275": (275.0, 430.0), "S355": (355.0, 490.0)}


def hole(d: float) -> float:
    """Normal round clearance hole d0 (EN 1090-2: +1 M12–M14, +2 M16–M24, +3 ≥ M27)."""
    return d + (1 if d <= 14 else 2 if d <= 24 else 3)


def shear_resistance(cls: str, d: float, gM2: float, thread: bool = True) -> tuple[float, float]:
    """F_v,Rd per shear plane and α_v (Table 3.4)."""
    fub = BOLT_CLASSES[cls][1]
    if thread:
        av = 0.5 if cls == "10.9" else 0.6
        A = BOLT_AS[int(d)]
    else:
        av, A = 0.6, math.pi * d**2 / 4
    return av * fub * A / gM2, av


def tension_resistance(cls: str, d: float, gM2: float, k2: float = 0.9) -> float:
    return k2 * BOLT_CLASSES[cls][1] * BOLT_AS[int(d)] / gM2
