"""Hand-calculation tests: plate solver, RC column, RC slab, strip footing and tie beams."""

import math

import pytest

from erisma.analysis.plate import solve_plate
from erisma.core import InputError, get_module
from erisma.design.ec2 import moment_resistance, section_capacity, section_layers


# ---------------------------------------------------------------- plate (Timoshenko)
def test_plate_simply_supported_square():
    r = solve_plate(1.0, 1.0, 1.0, D=1.0, nu=0.3, edges=("ss",) * 4, n=28)
    assert r["w_max"] == pytest.approx(0.00406, rel=0.01)  # Timoshenko Table 8
    assert r["mx_span"] == pytest.approx(0.0479, rel=0.02)


def test_plate_fixed_square():
    r = solve_plate(1.0, 1.0, 1.0, D=1.0, nu=0.3, edges=("fixed",) * 4, n=28)
    assert r["w_max"] == pytest.approx(0.00126, rel=0.03)
    assert abs(r["mx_sup"]) == pytest.approx(0.0513, rel=0.03)


def test_plate_ss_rectangle_1x2():
    r = solve_plate(1.0, 2.0, 1.0, D=1.0, nu=0.3, edges=("ss",) * 4, n=28)
    assert r["w_max"] == pytest.approx(0.01013, rel=0.01)
    assert r["mx_span"] == pytest.approx(0.1017, rel=0.02)
    assert r["my_span"] == pytest.approx(0.0464, rel=0.03)


# ---------------------------------------------------------------- sections
def test_moment_resistance_matches_beam_at_zero_axial():
    b, h, cb, dia = 300.0, 500.0, 50.0, 20.0
    layers = section_layers(b, h, 3, 2, dia, cb)  # 3 bars top, 3 bottom
    M, _ = moment_resistance(b, h, layers, 16.67, 434.8, 0.0)
    As = 3 * math.pi * dia**2 / 4
    M2, _ = section_capacity(b, h - cb, As, 16.67, 434.8, cb, As)
    assert M == pytest.approx(M2, rel=0.02)


def test_moment_resistance_zero_above_squash_load():
    layers = section_layers(400, 400, 3, 3, 16, 46)
    assert moment_resistance(400, 400, layers, 16.67, 434.8, 1e9)[0] == 0.0


# ---------------------------------------------------------------- column
def test_column_defaults_hand_calc():
    c = get_module("ec2_rc_column").calculate({})
    v = c.values
    fcd = 1.0 * 25 / 1.5  # EN recommended α_cc = 1.0
    n = 1200e3 / (400 * 400 * fcd)
    assert v["n"] == pytest.approx(n, rel=1e-3)
    assert v["λ_h"] == pytest.approx(3000 * math.sqrt(12) / 400, rel=1e-3)
    omega = 12 * math.pi * 16**2 / 4 * 500 / 1.15 / (400 * 400 * fcd)
    A, B = 1 / (1 + 0.2 * 0.8), math.sqrt(1 + 2 * omega)
    # M01/M02 = -30/60 = -0.5 -> C = 2.2
    assert v["λ_lim,h"] == pytest.approx(20 * A * B * 2.2 / math.sqrt(n), rel=1e-3)
    # λ < λ_lim: M_Ed = M02 + N e_i  = 60 + 1200 × 7.5 mm = 69 kNm
    assert v["M_Ed,h"] / 1e6 == pytest.approx(69.0, rel=1e-3)
    assert c.passed


def test_column_slender_and_overloaded():
    c = get_module("ec2_rc_column").calculate({"L": 8.0, "braced": False})
    assert "M_2,h" in c.values and c.values["M_2,h"] > 0
    bad = get_module("ec2_rc_column").calculate({"NEd": 5000})
    assert not bad.passed


# ---------------------------------------------------------------- slab
def test_slab_two_way_and_one_way_defaults_pass():
    m = get_module("ec2_rc_slab")
    assert m.calculate({}).passed
    assert m.calculate({"type": "One-way continuous"}).passed


def test_slab_punching_fails_with_hint():
    c = get_module("ec2_rc_slab").calculate({"punch": True})
    failed = [ch for ch in c.checks if not ch.passed]
    assert failed and all(ch.hint for ch in failed)


# ---------------------------------------------------------------- strip footing
def test_strip_footing_bearing_cyprus_hand_calc():
    c = get_module("ec7_strip_footing").calculate({}, {"annex": "CY"})
    # V = 1.35 (180 + 15.75 + 12.02) + 1.5·60 = 370.5 kN/m ; e = 17.625/370.5 m
    V = 1.35 * (180 + 25 * 1.4 * 0.45 + 19 * 1.15 * 0.55) + 90
    M = 1.35 * 5 + 1.5 * (5 + 5 * 0.45)
    Bp = 1.4 - 2 * M / V
    phi = math.radians(30)
    Nq = math.exp(math.pi * math.tan(phi)) * math.tan(math.pi / 4 + phi / 2) ** 2
    Nc, Ng = (Nq - 1) / math.tan(phi), 2 * (Nq - 1) * math.tan(phi)
    r = 1 - 7.5 / (V + Bp * 5 / math.tan(phi))
    iq, ig = r**2, r**3
    ic = iq - (1 - iq) / (Nc * math.tan(phi))
    qRd = (5 * Nc * ic + 19 * 1.0 * Nq * iq + 0.5 * 19 * Bp * Ng * ig) / 1.4
    bear = next(ch for ch in c.checks if "bearing" in ch.description)
    assert bear.utilisation == pytest.approx(V / Bp / qRd, rel=2e-3)
    assert c.passed


def test_tie_beam_force():
    c = get_module("ec7_strip_footing").calculate({"ground": "D", "ag": 0.2,
                                                   "importance": "III"}, {"annex": "EN"})
    # EN: S(D) = 1.35, γI(III) = 1.2  ->  N = 0.6 · 0.24 · 1.35 · 800 kN
    assert c.values["N_tie"] / 1e3 == pytest.approx(0.6 * 0.24 * 1.35 * 800, rel=1e-3)


def test_strip_footing_input_errors():
    m = get_module("ec7_strip_footing")
    with pytest.raises(InputError):
        m.calculate({"D": 0.3})
    with pytest.raises(InputError):
        m.calculate({"bw": 2.0})
