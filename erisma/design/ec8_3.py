"""EN 1998-3 Annex A — deformation and shear capacity of existing RC members (N, mm).

Chord rotation at yield θ_y (A.10a), ultimate chord rotation θ_um (A.1) and cyclic shear
resistance V_R (A.12), with the yield curvature/moment of Annex A (A.3.2.4, after
Panagiotakos & Fardis).  Strengths are passed in already divided by CF (and by the
partial factors for brittle mechanisms where required).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

ES = 200000.0


@dataclass
class RCSection:
    b: float           # width (perpendicular to bending)
    h: float           # depth (in the direction of bending)
    d1: float          # cover to the centre of the longitudinal bars (d')
    As: float          # tension reinforcement
    As2: float         # compression reinforcement
    Asv: float         # web (intermediate) longitudinal reinforcement
    db: float          # longitudinal bar diameter
    Asw: float         # area of one hoop set parallel to the shear (all legs)
    sh: float          # hoop spacing
    nb: int            # bars along b (each face)
    nh: int            # bars along h (each face)
    dh: float          # hoop diameter

    @property
    def d(self) -> float:
        return self.h - self.d1


def ec_mean(fc: float) -> float:
    """E_c [N/mm²] from the mean strength (EN 1992-1-1 Table 3.1, E_cm = 22 (f_cm/10)^0.3)."""
    return 22000.0 * (fc / 10) ** 0.3


def yield_props(s: RCSection, fc: float, fy: float, N: float) -> dict:
    """Yield curvature, neutral-axis depth and moment (tension steel yielding)."""
    b, d = s.b, s.d
    dp = s.d1 / d
    Ec = ec_mean(fc)
    a = ES / Ec
    r, r2, rv = s.As / (b * d), s.As2 / (b * d), s.Asv / (b * d)
    n = N / (b * d * fy)
    A = r + r2 + rv + n
    B = r + r2 * dp + 0.5 * rv * (1 + dp) + n
    xi = math.sqrt(a**2 * A**2 + 2 * a * B) - a * A
    phi = fy / (ES * (1 - xi) * d)
    My = phi * b * d**3 * (Ec * xi**2 / 2 * (0.5 * (1 + dp) - xi / 3)
                           + ES / 2 * ((1 - xi) * r + (xi - dp) * r2 + rv / 6 * (1 - dp))
                           * (1 - dp))
    return {"xi": xi, "x": xi * d, "phi_y": phi, "My": My}


def confinement_alpha(s: RCSection) -> float:
    b0 = s.b - 2 * (s.d1 - s.db / 2) + s.dh
    h0 = s.h - 2 * (s.d1 - s.db / 2) + s.dh
    sb = 2 * (s.nb - 1) * (b0 / max(s.nb - 1, 1)) ** 2 + 2 * (s.nh - 1) * (h0 / max(s.nh - 1, 1)) ** 2
    return max((1 - s.sh / (2 * b0)) * (1 - s.sh / (2 * h0)) * (1 - sb / (6 * h0 * b0)), 0.0)


def theta_y(s: RCSection, fc: float, fy: float, N: float, Lv: float, av: float) -> tuple:
    """EN 1998-3 Eq. A.10a (beams and columns)."""
    yp = yield_props(s, fc, fy, N)
    z = s.d - s.d1
    ey = fy / ES
    t1 = yp["phi_y"] * (Lv + av * z) / 3
    t2 = 0.0014 * (1 + 1.5 * s.h / Lv)
    t3 = ey * s.db * fy / ((s.d - s.d1) * 6 * math.sqrt(fc))
    return t1 + t2 + t3, (t1, t2, t3), yp


def theta_um(s: RCSection, fc: float, fy: float, fyw: float, N: float, Lv: float,
             gamma_el: float, seismic_detailing: bool, frp: float = 0.0) -> tuple:
    """EN 1998-3 Eq. A.1; ``frp`` = α_f ρ_f f_f,e / f_c (A.4.4.3), 0 without FRP."""
    b, h, d = s.b, s.h, s.d
    nu = N / (b * h * fc)
    w = (s.As + s.Asv) * fy / (b * d * fc)
    w2 = s.As2 * fy / (b * d * fc)
    alpha = confinement_alpha(s)
    rsx = s.Asw / (b * s.sh)
    conf = alpha * rsx * fyw / fc + frp
    val = (1 / gamma_el) * 0.016 * 0.3**nu * (max(0.01, w2) / max(0.01, w) * fc) ** 0.225 \
        * (Lv / h) ** 0.35 * 25 ** conf
    if not seismic_detailing:
        val /= 1.2
    return val, {"nu": nu, "w": w, "w2": w2, "alpha": alpha, "rsx": rsx, "conf": conf}


def shear_VR(s: RCSection, fc: float, fyw: float, N: float, Lv: float, x: float,
             mu_pl: float, gamma_el: float, Vwf: float = 0.0) -> tuple:
    """EN 1998-3 Eq. A.12 (cyclic shear resistance after flexural yielding)."""
    b, h, d = s.b, s.h, s.d
    Ac = b * d
    rtot = (s.As + s.As2 + s.Asv) / (b * d)
    z = d - s.d1
    Vw = s.Asw / s.sh * z * fyw + Vwf
    VN = (h - x) / (2 * Lv) * min(max(N, 0.0), 0.55 * Ac * fc)
    Vc = 0.16 * max(0.5, 100 * rtot) * (1 - 0.16 * min(5.0, Lv / h)) * math.sqrt(fc) * Ac
    k = 1 - 0.05 * min(5.0, max(mu_pl, 0.0))
    return (VN + k * (Vc + Vw)) / gamma_el, {"VN": VN, "Vc": Vc, "Vw": Vw, "k": k}
