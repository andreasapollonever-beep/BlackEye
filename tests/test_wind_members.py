"""EN 1991-1-4 wind on members — values of the standard and hand calculations."""

import math

import pytest

from erisma.core import get_module
from erisma.design import wind_members as W

M = get_module("ec1_wind_members")
CY = {"annex": "CY"}


def out(c, k):
    return c.outputs[k]["value"]


def test_force_coefficients_of_the_figures_and_tables():
    # Figure 7.23 — values printed in the figure
    for db, v in [(0.1, 2.0), (0.2, 2.0), (0.6, 2.35), (0.7, 2.4), (1.0, 2.1), (2.0, 1.65),
                  (5.0, 1.0), (10.0, 0.9), (50.0, 0.9)]:
        assert W.cf0_rectangular(db) == pytest.approx(v)
    assert W.psi_r(0.0) == 1.0 and W.psi_r(0.1) == pytest.approx(0.75) and W.psi_r(0.3) == 0.5
    # Figure 7.28 formulae
    assert W.cf0_circular(1e5, 1e-3) == 1.2
    assert W.cf0_circular(1e6, 1e-5) == pytest.approx(1.2 - 0.18 * 4)       # 0.48
    assert W.cf0_circular(4.5e5, 1e-6) == 0.4                                # horizontal part
    assert W.cf0_circular(1e7, 1e-2) == pytest.approx(1.2 - 0.18 / 1.4)
    # Table 7.11 and 7.7, 7.9.2(3), Figure 7.33
    assert W.cf0_polygon("6", 1e6)[0] == 1.60 and W.cf0_polygon("10", 1e6)[0] == 1.30
    assert W.cf0_polygon("8 (smooth, r/b < 0.075)", 2e5)[0] == 1.45
    assert W.cf0_polygon("12 (smooth, rounded corners)", 5e5)[0] == 0.90
    assert math.isnan(W.cf0_polygon("16–18 (smooth, rounded corners)", 1e5)[0])
    assert W.CF0_SHARP_EDGED == 2.0 and W.CF0_CABLE == 1.2
    assert [W.cf0_lattice_angles(p) for p in (0, 0.1, 0.5, 0.9, 1.0)] == pytest.approx(
        [2.0, 1.8, 1.6, 1.8, 2.0])
    # Table 7.16
    assert W.slenderness(12, 0.3, True) == pytest.approx(40)
    assert W.slenderness(60, 1.0, True) == pytest.approx(42)
    assert W.slenderness(30, 1.0, False) == pytest.approx(60 + (42 - 60) * 15 / 35)
    assert W.slenderness(10, 1.0, False, both_ends_closed=True) == 70


def test_structural_factor_limits_and_dynamics():
    # no resonance (huge damping) and full correlation: c_s c_d = (1 + 2·3·I_v)/(1 + 7 I_v)
    Iv = 0.25
    sf = W.structural_factor(1e-6, 1e-6, 5.0, 0.3, 5.0, 20.0, Iv, 1.0, 1e9)
    assert sf["B2"] == pytest.approx(1.0, abs=1e-4) and sf["kp"] == 3.0 and sf["R2"] < 1e-9
    assert sf["cscd"] == pytest.approx((1 + 6 * Iv * math.sqrt(sf["B2"] + sf["R2"])) / (1 + 7 * Iv))
    assert sf["cscd"] == pytest.approx((1 + 6 * Iv) / (1 + 7 * Iv), rel=1e-4)
    assert sf["cscd"] == pytest.approx(sf["cs"] * sf["cd"])
    assert W.turbulence_length(200, 0.05, 2) == pytest.approx(300)
    assert W.spectral_density(0.1) == pytest.approx(0.68 / 2.02 ** (5 / 3))
    assert W.admittance(0) == 1.0 and W.peak_factor(0.01) == 3.0
    assert W.n1_uniform_cantilever(3.5e6, 45, 12) == pytest.approx(
        1.8751 ** 2 / (2 * math.pi) * math.sqrt(3.5e6 / (45 * 12 ** 4)))
    assert W.n1_chimney(1000, 1.0, 30, 0, 1.0) == pytest.approx(1000 / 900)
    assert W.aero_damping(0.8, 1.25, 0.3, 20, 1.0, 45) == pytest.approx(0.8 * 1.25 * 0.3 * 20 / 90)


def test_default_pole_hand_calculation():
    c = M.calculate({}, CY)   # Ø 0.30 m galvanised pole, 12 m, EI 12 600 kNm², 45 kg/m
    q = out(c, "q_p(z)")
    I = math.pi / 64 * (0.3 ** 4 - 0.288 ** 4)
    assert I == pytest.approx(6.0e-5, rel=0.01) and 210e9 * I == pytest.approx(12.6e6, rel=0.01)
    assert out(c, "n_1") == pytest.approx(1.8751 ** 2 / (2 * math.pi)
                                          * math.sqrt(12.6e6 / (45 * 12 ** 4)))
    Re = 0.3 * math.sqrt(2 * q * 1e3 / 1.25) / 15e-6
    assert out(c, "Re") == pytest.approx(Re)
    assert out(c, "c_f") == pytest.approx(W.cf0_circular(Re, 0.2e-3 / 0.3))
    F = out(c, "c_s c_d") * out(c, "c_f") * q * 12 * 0.3
    assert out(c, "F_w") == pytest.approx(F)
    assert out(c, "M_base") == pytest.approx(F * 6)
    # vortex shedding (approach 1): Sc, converged correlation length, amplitude, moment
    assert out(c, "Sc") == pytest.approx(2 * 0.012 * 45 / (1.25 * 0.09))
    Lj_b = out(c, "L_j") / 0.3
    y_b = out(c, "y_F/b")
    assert Lj_b == pytest.approx(4.8 + 12 * y_b, rel=1e-6)      # Table E.4 satisfied
    Kw = W.kw_cantilever(Lj_b, 40)
    assert y_b == pytest.approx(1 / 0.18 ** 2 / 9.6 * 0.13 * Kw * out(c, "c_lat"))
    y = y_b * 0.3
    assert out(c, "M_vortex") == pytest.approx(45 * (2 * math.pi * out(c, "n_1")) ** 2 * y * 144 / 4
                                               / 1000)


def test_other_sections_and_options():
    c = M.calculate({"section": "Rectangular or square", "b": 0.4, "d": 0.4, "r": 0.04}, CY)
    assert out(c, "c_f,0") == pytest.approx(2.1) and out(c, "ψ_r") == pytest.approx(0.75)
    assert out(c, "c_f") == pytest.approx(2.1 * 0.75)
    c = M.calculate({"section": "Plane lattice of angle members", "b": 1.2, "h": 20, "phi": 0.25,
                     "damping": "Lattice steel tower, ordinary bolts"}, CY)
    assert out(c, "c_f") == 1.6 and out(c, "A_ref") == pytest.approx(0.25 * 20 * 1.2)
    c = M.calculate({"cscd_mode": "c_s c_d = 1 (only where 6.2(1) allows)"}, CY)
    assert out(c, "c_s c_d") == 1.0 and c.warnings     # pole is not a squat chimney
    c = M.calculate({"psi_mode": "Given ψ_λ (Figure 7.36)", "psi_l": 0.8}, CY)
    assert out(c, "c_f") == pytest.approx(0.8 * out(c, "c_f,0"))
    c = M.calculate({"n1_mode": "Chimney (Eq. F.3)", "h": 30, "b": 1.0, "m": 400}, CY)
    assert out(c, "n_1") == pytest.approx(1000 / 900)
    c = M.calculate({"b": 2.5, "h": 12, "n1_mode": "Given n1", "n1": 5.0}, CY)  # stiff, wide
    assert "Sc" not in c.outputs                       # ℓ/b ≤ 6 → no vortex calculation


def test_vortex_helpers():
    assert W.clat0_circular(1e5) == 0.7 and W.clat0_circular(1e6) == 0.2
    assert W.clat0_circular(2e7) == 0.3
    assert W.clat(0.7, 1.0) == pytest.approx(0.6 * 0.7) and W.clat(0.7, 1.3) == 0
    assert W.kw_cantilever(6, 40) == pytest.approx(3 * 0.15 * (1 - 0.15 + 0.15 ** 2 / 3))
    assert W.correlation_length(0.05) == 6 and W.correlation_length(0.7) == 12
    r = (3.0 / 4.0) ** 2
    assert W.load_cycles(1.0, 3.0, 4.0) == pytest.approx(2 * 3.2e7 * 50 * 0.3 * r * math.exp(-r))
