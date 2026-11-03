"""Unit handling.

All engineering calculations inside Erisma are carried out in a single
consistent base system: **N, mm** (so stresses are N/mm² = MPa, moments are
Nmm, line loads are N/mm).  Values are converted to/from friendly display
units only at the boundaries (user input and report output).
"""

from __future__ import annotations

# factor: 1 display unit = factor * base unit
UNIT_FACTORS: dict[str, float] = {
    "": 1.0,
    "-": 1.0,
    "%": 0.01,
    "°": 1.0,
    # length
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    # force
    "N": 1.0,
    "kN": 1e3,
    # moment
    "Nmm": 1.0,
    "kNm": 1e6,
    "kNm/m": 1e3,  # moment per metre run -> Nmm/mm
    # line load / stiffness per length
    "N/mm": 1.0,
    "kN/m": 1.0,
    # pressure / stress
    "N/mm²": 1.0,
    "MPa": 1.0,
    "GPa": 1e3,
    "kN/m²": 1e-3,
    "kPa": 1e-3,
    # density (weight)
    "kN/m³": 1e-6,
    # area
    "mm²": 1.0,
    "cm²": 1e2,
    "m²": 1e6,
    "mm²/m": 1e-3,  # area per metre length -> mm²/mm
    # section moduli / inertias
    "mm³": 1.0,
    "cm³": 1e3,
    "mm⁴": 1.0,
    "cm⁴": 1e4,
    "cm⁶": 1e6,
    "mm⁶": 1.0,
    # mass per length (kg/m -> kN/m using g = 9.81)
    "kg/m": 9.81e-3,
}


def to_base(value: float, unit: str) -> float:
    """Convert a value given in ``unit`` to the internal base system."""
    try:
        return value * UNIT_FACTORS[unit]
    except KeyError as exc:  # pragma: no cover - programming error
        raise ValueError(f"Unknown unit '{unit}'") from exc


def from_base(value: float, unit: str) -> float:
    """Convert a base-system value to ``unit`` for display."""
    try:
        return value / UNIT_FACTORS[unit]
    except KeyError as exc:  # pragma: no cover - programming error
        raise ValueError(f"Unknown unit '{unit}'") from exc
