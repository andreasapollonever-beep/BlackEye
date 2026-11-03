"""Hand checks: welds, stair, pile cap, RC wall, raft, liquefaction, fire, slope nails."""

import math

import pytest

from erisma.core import get_module
from erisma.modules.ec7_raft import bef
from erisma.modules.ec8_5_liquefaction import crr75, fines
from erisma.modules.fire import iso834, theta_cr


def test_weld_group_stresses():
    v = get_module("ec3_weld").calculate({}).values
    Aw, Iw = 5 * (400 + 600), 2 * 5 * 200 * 150**2 + 2 * 5 * 300**3 / 12
    assert v["σ_w"] == pytest.approx(150e3 / Aw + 20e6 * 150 / Iw)
    assert v["τ∥"] == pytest.approx(120e3 / (5 * 600))


def test_stair_geometry_and_moment():
    c = get_module("ec2_rc_stair").calculate({})
    assert c.values["R"] == pytest.approx(2040 / 12) and c.values["G"] == pytest.approx(280)
    a = math.atan(2.04 / 3.08)
    g = 25 * (0.2 / math.cos(a) + 0.17 / 2) + 1.5
    assert c.values["M_Ed"] / 1e3 == pytest.approx((1.35 * g + 1.5 * 3) * 3.08**2 / 8, rel=1e-6)
    assert c.passed


def test_pile_cap_four_piles_hand_calc():
    v = get_module("ec2_pile_cap").calculate({}).values
    P = 3500 / 4 + 150 * 0.9 / (4 * 0.9**2)
    assert v["P_max"] / 1e3 == pytest.approx(P)
    r = 900 * math.sqrt(2)
    a = r - 0.25 * 500 * math.sqrt(2)
    z = 0.9 * (1000 - 75 - 20)
    assert v["T_Ed"] / 1e3 == pytest.approx(P * a / z / math.sqrt(2))


def test_rc_wall_defaults_pass_and_shear_amplified():
    c = get_module("ec8_rc_wall").calculate({}, {"annex": "CY"})
    assert c.passed and c.values["V_Ed"] == pytest.approx(1.5 * 700e3)


def test_bef_rigid_strip():
    x, w, M, V, q = bef(2000, 1e13, 0.01, [(1000, 1000.0)])
    assert M[100] == pytest.approx(1000 * 2000 / 8, rel=1e-3)
    assert w.mean() == pytest.approx(50, rel=1e-3)


def test_raft_settlement_between_mean_and_twice_mean():
    v = get_module("ec7_raft").calculate({}).values
    mean = v["q_avg"] / 15e-3  # q / k for a rigid raft
    assert mean <= v["s_max"] <= 2 * mean


def test_liquefaction_layer_by_hand():
    c = get_module("ec8_5_liquefaction").calculate({"layers": [
        {"h": 2, "soil": "Sand", "gamma": 18, "N60": 12, "FC": 10},
        {"h": 4, "soil": "Sand", "gamma": 19, "N60": 9, "FC": 8}]}, {"annex": "CY"})
    sv, sve = 2 * 18 + 2 * 19, 2 * 18 + 2 * 19 - 2 * 9.81
    n1 = math.sqrt(100 / sve) * 9
    fs = crr75(fines(n1, 8)) * 1.69 * sve / (0.65 * 0.25 * 1.15 * sv)
    chk = c.checks[0]
    assert chk.utilisation == pytest.approx(1.25 / fs, rel=1e-6)
    assert crr75(31) == math.inf


def test_fire_formulas():
    assert iso834(60) == pytest.approx(945.3, abs=0.5)
    assert theta_cr(0.5) == pytest.approx(585, abs=2)  # EN 1993-1-2 Table 4.1
    assert get_module("ec3_fire").calculate({}).passed
    assert not get_module("ec3_fire").calculate({"protection": "None"}).passed


def test_timber_and_concrete_fire():
    c = get_module("ec5_fire").calculate({})
    assert c.values["d_ef"] == pytest.approx(0.7 * 30 + 7)
    c = get_module("ec2_fire").calculate({"R": "R60", "b": 200, "cover": 25, "link": 8,
                                          "dia": 16, "layers": False})
    assert c.values["a_req"] == pytest.approx(30) and c.passed


def test_slope_nails_raise_the_factor():
    m = get_module("ec7_slope_stability")
    f0 = m.calculate({"slope": 40}, {"annex": "CY"}).values["F_d"]
    nails = [{"z": z, "angle": 15, "L": 9, "sh": 1.5, "Td": 150, "bond": 40} for z in (1.5, 3, 4.5)]
    f1 = m.calculate({"slope": 40, "nails": nails}, {"annex": "CY"}).values["F_d"]
    assert f1 > f0 * 1.3
