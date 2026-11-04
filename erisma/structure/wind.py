"""Wind on the whole building (EN 1991-1-4) — storey forces for the 3D analysis.

For each direction the net pressure on the building is taken from the external pressure
coefficients of the windward (D) and leeward (E) walls, Table 7.1 (c_pe,10), with the
lack-of-correlation factor of 7.2.2(3), and the peak velocity pressure q_p(z_e) at the
reference height z_e of Figure 7.4 (h ≤ b: z_e = h; b < h ≤ 2b: two parts; h > 2b: strips).
The pressure on the facade band of each floor (half the storey below and half the storey
above) gives the storey force F_k, applied at the centre of the facade (rigid diaphragm).

Units: N and mm (pressures in N/mm²).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..design import wind_cpe

# EN 1991-1-4 Table 4.1: terrain category → (z_0, z_min) [m]
TERRAIN = {"0": (0.003, 1.0), "I": (0.01, 1.0), "II": (0.05, 2.0), "III": (0.3, 5.0),
           "IV": (1.0, 10.0)}


def qp(z_m: float, vb: float, terrain: str, co: float = 1.0, rho: float = 1.25) -> float:
    """Peak velocity pressure q_p(z) [kN/m²] (EN 1991-1-4 Eqs. 4.3–4.8, k_I = 1)."""
    z0, zmin = TERRAIN[terrain]
    kr = 0.19 * (z0 / 0.05) ** 0.07
    ze = max(z_m, zmin)
    cr = kr * math.log(ze / z0)
    vm = cr * co * vb
    Iv = 1.0 / (co * math.log(ze / z0))
    return (1 + 7 * Iv) * 0.5 * rho * vm**2 / 1000.0


def reference_height(z: float, h: float, b: float) -> float:
    """z_e for a point at height z on a windward wall of height h and width b (Fig. 7.4)."""
    if h <= b:
        return h
    if h <= 2 * b:
        return b if z <= b else h
    if z <= b:
        return b
    if z >= h - b:
        return h
    return z


@dataclass
class WindDirection:
    name: str              # "WX" | "WY"
    axis: int              # 0 = X, 1 = Y
    b: float               # crosswind width [mm]
    d: float               # depth in the wind direction [mm]
    cpe_D: float
    cpe_E: float
    corr: float            # lack-of-correlation factor
    forces: list[float] = field(default_factory=list)       # storey forces [N], floors 1..n
    qp_ref: list[float] = field(default_factory=list)       # q_p(z_e) at each floor [kN/m²]

    @property
    def cf_net(self) -> float:
        return self.corr * (self.cpe_D - self.cpe_E)


def storey_forces(width_x: float, width_y: float, zs: list[float], vb: float, terrain: str,
                  co: float = 1.0, rho: float = 1.25) -> list[WindDirection]:
    """Storey wind forces for wind along X and along Y.

    ``zs`` are the floor levels [mm], zs[0] = 0 (base); ``width_x`` / ``width_y`` the plan
    dimensions [mm]."""
    h = zs[-1]
    out = []
    for name, axis, b, d in (("WX", 0, width_y, width_x), ("WY", 1, width_x, width_y)):
        hd = h / d
        cells = wind_cpe.walls(hd)
        wd = WindDirection(name, axis, b, d, cells["D"][0], cells["E"][0],
                           wind_cpe.lack_of_correlation(hd))
        n = len(zs) - 1
        for k in range(1, n + 1):
            lo = (zs[k - 1] + zs[k]) / 2
            hi = (zs[k] + zs[k + 1]) / 2 if k < n else zs[k]
            steps = 40
            dz = (hi - lo) / steps
            integral = sum(qp(reference_height(lo + (s + 0.5) * dz, h, b) / 1000, vb, terrain,
                              co, rho) for s in range(steps)) * dz          # kN/m² × mm
            wd.forces.append(wd.cf_net * integral * 1e-3 * b)                # N/mm² × mm × mm
            wd.qp_ref.append(qp(reference_height(zs[k], h, b) / 1000, vb, terrain, co, rho))
        out.append(wd)
    return out


VERIFIED = wind_cpe.VERIFIED
SOURCE = wind_cpe.SOURCE
