"""Wind on structural elements — EN 1991-1-4:2005 + A1:2010 (AC:2010).

Force coefficients of 7.6 (rectangular), 7.7 (sharp-edged), 7.8 (polygonal), 7.9 (circular
cylinders), 7.11 (plane lattice of angle members) and cables; effective slenderness of
Table 7.16; structural factor c_s c_d by 6.3.1 with Annex B (procedure 1); dynamic properties of
Annex F; critical velocity of vortex shedding (Annex E, E.1.2, E.1.3).

Figures read as polylines are linear in the axis of the figure (log axis for 7.23); the
intermediate values printed in the figure itself are reproduced exactly (see the tests).
"""

from __future__ import annotations

import math

SOURCE = "EN 1991-1-4:2005 + A1:2010 (incorporating corrigendum January 2010)"
NU_AIR = 15e-6  # kinematic viscosity of air [m²/s], 7.9.1(1)

# Table 7.13 — equivalent surface roughness k [mm]
ROUGHNESS = {
    "Glass": 0.0015, "Polished metal": 0.002, "Fine paint": 0.006, "Spray paint": 0.02,
    "Bright steel": 0.05, "Cast iron": 0.2, "Galvanised steel": 0.2, "Smooth concrete": 0.2,
    "Planed wood": 0.5, "Rough concrete": 1.0, "Rough sawn wood": 2.0, "Rust": 2.0,
    "Brickwork": 3.0,
}

# Table F.2 — logarithmic decrement of structural damping δ_s (selection)
DAMPING = {
    "Reinforced concrete buildings": 0.10, "Steel buildings": 0.05,
    "Mixed structures concrete + steel": 0.08, "Reinforced concrete towers and chimneys": 0.03,
    "Unlined welded steel stack without external insulation": 0.012,
    "Unlined welded steel stack with external insulation": 0.020,
    "Steel stack with internal brick liner": 0.070, "Steel stack with internal gunite": 0.030,
    "Guyed steel stack without liner": 0.04,
    "Lattice steel tower, welded": 0.02, "Lattice steel tower, high resistance bolts": 0.03,
    "Lattice steel tower, ordinary bolts": 0.05, "Spiral cables": 0.020,
}


def _loglerp(x, x1, x2, y1, y2):
    return y1 + (y2 - y1) * (math.log10(x) - math.log10(x1)) / (math.log10(x2) - math.log10(x1))


def cf0_rectangular(d_b: float) -> float:
    """Figure 7.23 — sharp corners, no free-end flow: polyline through the values printed in the
    figure, straight on the log d/b axis: 2.0 (d/b ≤ 0.2), 2.35 (0.6), 2.4 (0.7), 2.1 (1),
    1.65 (2), 1.0 (5), 0.9 (≥ 10)."""
    pts = [(0.2, 2.0), (0.6, 2.35), (0.7, 2.4), (1.0, 2.1), (2.0, 1.65), (5.0, 1.0), (10.0, 0.9)]
    if d_b <= pts[0][0]:
        return 2.0
    if d_b >= pts[-1][0]:
        return 0.9
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if x1 <= d_b <= x2:
            return _loglerp(d_b, x1, x2, y1, y2)
    return 0.9  # pragma: no cover


def psi_r(r_b: float) -> float:
    """Figure 7.24 — square sections with rounded corners: 1.0 (r/b = 0) → 0.5 (r/b ≥ 0.2)."""
    return 1.0 - 2.5 * min(max(r_b, 0.0), 0.2)


CF0_SHARP_EDGED = 2.0  # 7.7(1) NOTE 1, recommended
CF0_CABLE = 1.2        # 7.9.2(3), stranded cables


def cf0_polygon(sides: str, Re: float) -> tuple[float, str]:
    """Table 7.11 (AC2) — c_f,0 of regular polygons; returns (value, case)."""
    if sides == "5":
        return 1.80, "all"
    if sides == "6":
        return 1.60, "all"
    if sides == "8 (smooth, r/b < 0.075)":
        if Re <= 2.4e5:
            return 1.45, "Re ≤ 2.4·10⁵"
        if Re >= 3e5:
            return 1.30, "Re ≥ 3·10⁵"
        return 1.45 + (1.30 - 1.45) * (Re - 2.4e5) / (0.6e5), "interpolated"
    if sides == "8 (smooth, r/b ≥ 0.075)":
        if Re <= 2e5:
            return 1.30, "Re ≤ 2·10⁵"
        if Re >= 7e5:
            return 1.10, "Re ≥ 7·10⁵"
        return 1.30 + (1.10 - 1.30) * (Re - 2e5) / 5e5, "interpolated"
    if sides == "10":
        return 1.30, "all"
    if sides == "12 (smooth, rounded corners)":
        if 2e5 < Re < 1.2e6:
            return 0.90, "2·10⁵ < Re < 1.2·10⁶"
        return 1.30 if Re < 4e5 else 1.10, "outside the range of the smooth case: 'all others'"
    if sides == "12 (all others)":
        return (1.30, "Re < 4·10⁵") if Re < 4e5 else (1.10, "Re > 4·10⁵")
    if sides == "16–18 (smooth, rounded corners)":
        if 2e5 <= Re < 1.2e6:
            return 0.70, "2·10⁵ ≤ Re < 1.2·10⁶"
        if Re < 2e5:
            return math.nan, "circular"  # Table 7.11: treat as a circular cylinder (7.9)
        return math.nan, "outside"       # Re ≥ 1.2·10⁶ not covered: circular cylinder used
    raise ValueError(sides)


POLYGONS = ["5", "6", "8 (smooth, r/b < 0.075)", "8 (smooth, r/b ≥ 0.075)", "10",
            "12 (smooth, rounded corners)", "12 (all others)", "16–18 (smooth, rounded corners)"]


def cf0_circular(Re: float, k_b: float) -> float:
    """Figure 7.28 — c_f,0 = 0.11/(Re/10⁶)^1.4 (≤ 1.2), or
    1.2 + 0.18 log(10 k/b)/(1 + 0.4 log(Re/10⁶)), whichever is larger, with the horizontal part
    0.4 of the k/b ≤ 10⁻⁵ curve; k/b below 10⁻⁵ is taken as 10⁻⁵ (curve '≤ 10⁻⁵')."""
    k_b = max(k_b, 1e-5)
    a = min(1.2, 0.11 / (Re / 1e6) ** 1.4)
    b = 1.2 + 0.18 * math.log10(10 * k_b) / (1 + 0.4 * math.log10(Re / 1e6))
    return max(a, b, 0.4)


def cf0_lattice_angles(phi: float) -> float:
    """Figure 7.33 — plane lattice of angle members: 2.0 (φ = 0) → 1.6 (0.2 ≤ φ ≤ 0.8) →
    2.0 (φ = 1)."""
    phi = min(max(phi, 0.0), 1.0)
    if phi < 0.2:
        return 2.0 - 2.0 * phi
    if phi <= 0.8:
        return 1.6
    return 1.6 + 2.0 * (phi - 0.8)


def slenderness(l: float, b: float, circular: bool, both_ends_closed: bool = False) -> float:
    """Table 7.16 — effective slenderness λ (positions 1–3, or 4 for both ends closed)."""
    if both_ends_closed:
        hi, lo = 0.7 * l / b, l / b
        f = lo if l < 15 else hi if l >= 50 else lo + (hi - lo) * (l - 15) / 35
        return max(f, 70.0)
    k50, k15 = (0.7, 1.0) if circular else (1.4, 2.0)
    l50, l15 = min(k50 * l / b, 70.0), min(k15 * l / b, 70.0)
    if l >= 50:
        return l50
    if l < 15:
        return l15
    return l15 + (l50 - l15) * (l - 15) / 35


# ---------------------------------------------------------------- Annex B / F
def turbulence_length(z: float, z0: float, zmin: float) -> float:
    """Eq. B.1 — L(z) = 300 (z/200)^α, α = 0.67 + 0.05 ln z0, z ≥ z_min."""
    alpha = 0.67 + 0.05 * math.log(z0)
    return 300.0 * (max(z, zmin) / 200.0) ** alpha


def spectral_density(fL: float) -> float:
    """Eq. B.2 — S_L = 6.8 f_L / (1 + 10.2 f_L)^(5/3)."""
    return 6.8 * fL / (1 + 10.2 * fL) ** (5 / 3)


def admittance(eta: float) -> float:
    """Eq. B.7 / B.8."""
    if eta <= 0:
        return 1.0
    return 1 / eta - (1 - math.exp(-2 * eta)) / (2 * eta ** 2)


def peak_factor(nu: float, T: float = 600.0) -> float:
    """Eq. B.4 with ν ≥ 0.08 Hz (B.5): k_p = √(2 ln νT) + 0.6/√(2 ln νT) ≥ 3."""
    nu = max(nu, 0.08)
    s = math.sqrt(2 * math.log(nu * T))
    return max(s + 0.6 / s, 3.0)


def structural_factor(h: float, b: float, zs: float, z0: float, zmin: float, vm: float,
                      Iv: float, n1: float, delta: float) -> dict:
    """6.3.1 with Annex B: B², R², ν, k_p and c_s c_d (Eq. 6.1–6.3)."""
    L = turbulence_length(zs, z0, zmin)
    B2 = 1 / (1 + 0.9 * ((b + h) / L) ** 0.63)
    fL = n1 * L / vm
    SL = spectral_density(fL)
    eh, eb = 4.6 * h / L * fL, 4.6 * b / L * fL
    Rh, Rb = admittance(eh), admittance(eb)
    R2 = math.pi ** 2 / (2 * delta) * SL * Rh * Rb
    nu = max(n1 * math.sqrt(R2 / (B2 + R2)), 0.08)
    kp = peak_factor(nu)
    cscd = (1 + 2 * kp * Iv * math.sqrt(B2 + R2)) / (1 + 7 * Iv)
    cs = (1 + 7 * Iv * math.sqrt(B2)) / (1 + 7 * Iv)
    cd = (1 + 2 * kp * Iv * math.sqrt(B2 + R2)) / (1 + 7 * Iv * math.sqrt(B2))
    return {"L": L, "B2": B2, "fL": fL, "SL": SL, "eta_h": eh, "eta_b": eb, "Rh": Rh, "Rb": Rb,
            "R2": R2, "nu": nu, "kp": kp, "cscd": cscd, "cs": cs, "cd": cd}


def n1_uniform_cantilever(EI: float, m: float, L: float) -> float:
    """Classical beam theory (Euler–Bernoulli): n1 = 1.875²/(2π) √(EI/(m L⁴)) [EI Nm², m kg/m]."""
    return 1.8751 ** 2 / (2 * math.pi) * math.sqrt(EI / (m * L ** 4))


def n1_chimney(eps1: float, b: float, h1: float, h2: float, Ws_Wt: float) -> float:
    """Eq. F.3 / F.4 — n1 = ε1 b / h_eff² √(W_s/W_t), h_eff = h1 + h2/3."""
    heff = h1 + h2 / 3
    return eps1 * b / heff ** 2 * math.sqrt(Ws_Wt)


def aero_damping(cf: float, rho: float, b: float, vm: float, n1: float, me: float) -> float:
    """Eq. F.18 — δ_a = c_f ρ b v_m(z_s) / (2 n1 m_e)."""
    return cf * rho * b * vm / (2 * n1 * me)


ST_CIRCULAR = 0.18  # Table E.1


# ------------------------------------------- Annex E.1.5.2 — approach 1 (cantilevers)
def clat0_circular(Re: float) -> float:
    """Figure E.2 — 0.7 (Re ≤ 3·10⁵) → 0.2 (5·10⁵ … 5·10⁶) → 0.3 (≥ 10⁷); straight lines on the
    log Re axis."""
    if Re <= 3e5:
        return 0.7
    if Re < 5e5:
        return _loglerp(Re, 3e5, 5e5, 0.7, 0.2)
    if Re <= 5e6:
        return 0.2
    if Re < 1e7:
        return _loglerp(Re, 5e6, 1e7, 0.2, 0.3)
    return 0.3


CLAT0_RECTANGULAR = 1.1  # Table E.2, 0.5 ≤ d/b ≤ 10


def clat(clat0: float, ratio: float) -> float:
    """Table E.3 with ratio = v_crit / v_m,Lj."""
    if ratio <= 0.83:
        return clat0
    if ratio < 1.25:
        return (3 - 2.4 * ratio) * clat0
    return 0.0


def kw_cantilever(Lj_b: float, lam: float) -> float:
    """Table E.5, first row (cantilever, ζ = 2, n = m = 1), λ = ℓ/b; K_w ≤ 0.6 (E.8)."""
    x = min(Lj_b / lam, 1.0)
    return min(3 * x * (1 - x + x * x / 3), 0.6)


K_CANTILEVER = 0.13  # Table E.5, first row


def correlation_length(y_b: float) -> float:
    """Table E.4 — L_j/b against y_F/b."""
    if y_b < 0.1:
        return 6.0
    if y_b <= 0.6:
        return 4.8 + 12 * y_b
    return 12.0


def scruton(delta_s: float, me: float, rho: float, b: float) -> float:
    """Eq. E.4 — Sc = 2 δ_s m_e / (ρ b²)."""
    return 2 * delta_s * me / (rho * b * b)


def vortex_cantilever(b: float, l: float, St: float, Sc: float, clat0: float, vcrit: float,
                      vm_at: "callable", iterations: int = 50) -> dict:
    """Approach 1 (E.1.5.2) for a cantilever: iterate L_j (Table E.4) ↔ y_F (Eq. E.7)."""
    lam = l / b
    Lj_b = 6.0
    for _ in range(iterations):
        Lj = min(Lj_b * b, l)
        ratio = vcrit / vm_at(l - Lj / 2)
        cl = clat(clat0, ratio)
        Kw = kw_cantilever(Lj / b, lam)
        y_b = 1 / St ** 2 / Sc * K_CANTILEVER * Kw * cl
        new = correlation_length(y_b)
        if abs(new - Lj_b) < 1e-9:
            break
        Lj_b = new
    return {"Lj": min(Lj_b * b, l), "Lj_b": Lj_b, "ratio": ratio, "clat": cl, "Kw": Kw,
            "y_b": y_b, "y": y_b * b}


def load_cycles(n: float, vcrit: float, v0: float, years: float = 50.0,
                eps0: float = 0.3) -> float:
    """Eq. E.10 — N = 2 T n ε0 (v_crit/v0)² exp(−(v_crit/v0)²), T = 3.2·10⁷ × years."""
    r = (vcrit / v0) ** 2
    return 2 * 3.2e7 * years * n * eps0 * r * math.exp(-r)
