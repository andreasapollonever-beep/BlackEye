"""Hot-rolled steel section library.

Only the nominal dimensions (h, b, tw, tf, r) are stored; all section
properties are derived with the standard formulas used by European section
tables (root fillets included), so the library is easy to extend and audit.
Results agree with published tables (e.g. IPE 300: Iy = 8356 cm⁴,
Wpl,y = 628.4 cm³, It = 20.12 cm⁴).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property

# name: (h, b, tw, tf, r) in mm
_DIMS: dict[str, tuple[float, float, float, float, float]] = {
    "IPE 80": (80, 46, 3.8, 5.2, 5), "IPE 100": (100, 55, 4.1, 5.7, 7),
    "IPE 120": (120, 64, 4.4, 6.3, 7), "IPE 140": (140, 73, 4.7, 6.9, 7),
    "IPE 160": (160, 82, 5.0, 7.4, 9), "IPE 180": (180, 91, 5.3, 8.0, 9),
    "IPE 200": (200, 100, 5.6, 8.5, 12), "IPE 220": (220, 110, 5.9, 9.2, 12),
    "IPE 240": (240, 120, 6.2, 9.8, 15), "IPE 270": (270, 135, 6.6, 10.2, 15),
    "IPE 300": (300, 150, 7.1, 10.7, 15), "IPE 330": (330, 160, 7.5, 11.5, 18),
    "IPE 360": (360, 170, 8.0, 12.7, 18), "IPE 400": (400, 180, 8.6, 13.5, 21),
    "IPE 450": (450, 190, 9.4, 14.6, 21), "IPE 500": (500, 200, 10.2, 16.0, 21),
    "IPE 550": (550, 210, 11.1, 17.2, 24), "IPE 600": (600, 220, 12.0, 19.0, 24),
    "HEA 100": (96, 100, 5.0, 8.0, 12), "HEA 120": (114, 120, 5.0, 8.0, 12),
    "HEA 140": (133, 140, 5.5, 8.5, 12), "HEA 160": (152, 160, 6.0, 9.0, 15),
    "HEA 180": (171, 180, 6.0, 9.5, 15), "HEA 200": (190, 200, 6.5, 10.0, 18),
    "HEA 220": (210, 220, 7.0, 11.0, 18), "HEA 240": (230, 240, 7.5, 12.0, 21),
    "HEA 260": (250, 260, 7.5, 12.5, 24), "HEA 280": (270, 280, 8.0, 13.0, 24),
    "HEA 300": (290, 300, 8.5, 14.0, 27),
    "HEB 100": (100, 100, 6.0, 10.0, 12), "HEB 120": (120, 120, 6.5, 11.0, 12),
    "HEB 140": (140, 140, 7.0, 12.0, 12), "HEB 160": (160, 160, 8.0, 13.0, 15),
    "HEB 180": (180, 180, 8.5, 14.0, 15), "HEB 200": (200, 200, 9.0, 15.0, 18),
    "HEB 220": (220, 220, 9.5, 16.0, 18), "HEB 240": (240, 240, 10.0, 17.0, 21),
    "HEB 260": (260, 260, 10.0, 17.5, 24), "HEB 280": (280, 280, 10.5, 18.0, 24),
    "HEB 300": (300, 300, 11.0, 19.0, 27),
}

STEEL_DENSITY = 7850.0  # kg/m³


@dataclass(frozen=True)
class ISection:
    name: str
    h: float
    b: float
    tw: float
    tf: float
    r: float

    @cached_property
    def hw(self) -> float:
        return self.h - 2 * self.tf

    @cached_property
    def d(self) -> float:
        """Depth of straight portion of web."""
        return self.h - 2 * self.tf - 2 * self.r

    @cached_property
    def A(self) -> float:
        return 2 * self.b * self.tf + (self.h - 2 * self.tf) * self.tw + (4 - math.pi) * self.r**2

    @cached_property
    def mass(self) -> float:
        """Mass per metre (kg/m)."""
        return self.A * 1e-6 * STEEL_DENSITY

    @cached_property
    def Iy(self) -> float:
        h, b, tw, tf, r = self.h, self.b, self.tw, self.tf, self.r
        return ((b * h**3 - (b - tw) * (h - 2 * tf) ** 3) / 12
                + 0.03 * r**4 + 0.2146 * r**2 * (h - 2 * tf - 0.4468 * r) ** 2)

    @cached_property
    def Iz(self) -> float:
        h, b, tw, tf, r = self.h, self.b, self.tw, self.tf, self.r
        return ((2 * tf * b**3 + (h - 2 * tf) * tw**3) / 12
                + 0.03 * r**4 + 0.2146 * r**2 * (tw + 0.4468 * r) ** 2)

    @cached_property
    def Wel_y(self) -> float:
        return 2 * self.Iy / self.h

    @cached_property
    def Wpl_y(self) -> float:
        h, b, tw, tf, r = self.h, self.b, self.tw, self.tf, self.r
        return (tw * h**2 / 4 + (b - tw) * (h - tf) * tf
                + (4 - math.pi) / 2 * r**2 * (h - 2 * tf) + (3 * math.pi - 10) / 3 * r**3)

    @cached_property
    def It(self) -> float:
        h, b, tw, tf, r = self.h, self.b, self.tw, self.tf, self.r
        a1 = (tw / tf) * (0.145 + 0.1 * r / tf)
        D1 = ((r + tw / 2) ** 2 + (r + tf) ** 2 - r**2) / (2 * r + tf)
        return (2 / 3 * (b - 0.63 * tf) * tf**3 + 1 / 3 * (h - 2 * tf) * tw**3
                + 2 * a1 * D1**4)

    @cached_property
    def Iw(self) -> float:
        return self.Iz * (self.h - self.tf) ** 2 / 4

    @cached_property
    def Av_z(self) -> float:
        """Shear area for load parallel to web (EN 1993-1-1 6.2.6(3)a), η = 1."""
        return max(self.A - 2 * self.b * self.tf + (self.tw + 2 * self.r) * self.tf,
                   self.hw * self.tw)


def get_section(name: str) -> ISection:
    try:
        return ISection(name, *_DIMS[name])
    except KeyError as exc:
        raise KeyError(f"Unknown section '{name}'") from exc


def section_names() -> list[str]:
    return list(_DIMS)
