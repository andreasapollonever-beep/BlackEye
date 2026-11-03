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
    "MN/m³": 1e-3,  # modulus of subgrade reaction
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


# units that measure the same quantity (a link may convert between them)
DIMENSIONS: dict[str, str] = {
    "mm": "L", "cm": "L", "m": "L",
    "N": "F", "kN": "F",
    "Nmm": "M", "kNm": "M",
    "kNm/m": "M/L",
    "N/mm": "F/L", "kN/m": "F/L",
    "N/mm²": "P", "MPa": "P", "GPa": "P", "kN/m²": "P", "kPa": "P",
    "kN/m³": "W", "MN/m³": "K",
    "mm²": "A", "cm²": "A", "m²": "A", "mm²/m": "A/L",
    "°": "deg", "": "1", "-": "1", "%": "1",
}


def compatible(u1: str, u2: str) -> bool:
    d1, d2 = DIMENSIONS.get(u1), DIMENSIONS.get(u2)
    return u1 == u2 or (d1 is not None and d1 == d2)


def convert(value: float, from_unit: str, to_unit: str) -> float:
    return from_base(to_base(value, from_unit), to_unit)
