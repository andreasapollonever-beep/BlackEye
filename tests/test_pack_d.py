"""Hand-calculation tests: steel column, bolts, base plate, timber, masonry, tank."""

import math

import pytest

from erisma.core import get_module
from erisma.design.annex import get_annex
from erisma.modules.ec2_tank import crack_width, wk1
from erisma.modules.ec3_steel_column import chi_curve
from erisma.modules.ec6_masonry_wall import phi_m
from erisma.sections.steel import get_section


def test_section_minor_axis_properties():
    s = get_section("HEB 200")  # published: Wpl,z 305.8 cm³, Wel,z 200.3 cm³, iz 5.07 cm
    assert s.Wpl_z / 1e3 == pytest.approx(305.8, rel=2e-3)
    assert s.Wel_z / 1e3 == pytest.approx(200.3, rel=2e-3)
    assert s.iz / 10 == pytest.approx(5.07, rel=3e-3)


def test_buckling_curve_values():
    # EN 1993-1-1 Table 6.1 / Fig. 6.4 values
    assert chi_curve(1.0, 0.34) == pytest.approx(0.5970, abs=2e-4)
    assert chi_curve(1.0, 0.49) == pytest.approx(0.5399, abs=2e-4)
    assert chi_curve(0.2, 0.49) == 1.0


def test_steel_column_weak_axis_buckling():
    c = get_module("ec3_steel_column").calculate({})
    s = get_section("HEB 240")
    eps = math.sqrt(235 / 355)
    lam = 4000 / (s.iz * 93.9 * eps)
    assert c.values["λ̄_z"] == pytest.approx(lam, rel=1e-6)
    assert c.values["χ_z"] == pytest.approx(chi_curve(lam, 0.49), rel=1e-6)
    assert c.passed


def test_class4_web_uses_effective_area():
    c = get_module("ec3_steel_column").calculate({"section": "IPE 600"})
    assert c.values["A_eff"] < get_section("IPE 600").A


def test_bolted_connection_hand_calc():
    c = get_module("ec3_bolted_connection").calculate({})
    assert c.values["F_v,Rd"] / 1e3 == pytest.approx(0.6 * 800 * 245 / 1.25 / 1e3, rel=1e-6)
    ab = 50 / (3 * 22)
    assert c.values["F_b,Rd"] / 1e3 == pytest.approx(2.5 * ab * 430 * 20 * 12 / 1.25 / 1e3,
                                                      rel=1e-6)
    assert c.passed


def test_eccentric_bolt_group_increases_bolt_force():
    m = get_module("ec3_bolted_connection")
    assert m.calculate({"ecc": 100}).values["F_v,Ed"] > m.calculate({}).values["F_v,Ed"]


def test_base_plate_bearing_and_tension():
    c = get_module("ec3_base_plate").calculate({})
    kj = math.sqrt(1.44e6 / (400 * 500 / 1e6) / 1e6)
    fjd = 2 / 3 * kj * 25 / 1.5
    assert c.values["f_jd"] == pytest.approx(fjd, rel=1e-6)
    assert c.values["c"] == pytest.approx(25 * math.sqrt(275 / (3 * fjd)), rel=1e-6)
    zC, zT = (240 - 17) / 2, 250 - 50
    assert c.values["F_t,Ed"] == pytest.approx((100e6 - 600e3 * zC) / (zC + zT), rel=1e-6)


def test_timber_beam_bending_hand_calc():
    c = get_module("ec5_timber_beam").calculate({}, {"annex": "CY"})
    sw = 1.1 * 385 * 9.81e-3 * 0.14 * 0.4
    wd = 1.35 * (2 + sw) + 1.5 * 3
    sigma = wd * 6**2 / 8 * 1e6 / (140 * 400**2 / 6)
    fmd = 0.8 * (600 / 400) ** 0.1 * 24 / 1.25
    bend = next(ch for ch in c.checks if ch.description.startswith("Bending"))
    assert bend.utilisation == pytest.approx(sigma / fmd, rel=1e-3)
    assert any("No National Annex for EN 1995-1-1" in w for w in
               [i.data.get("text", "") for i in c.items])


def test_masonry_wall_hand_calc():
    c = get_module("ec6_masonry_wall").calculate({}, {"annex": "CY"})
    fk = 0.45 * 10**0.7 * 10**0.3
    assert c.values["f_k"] == pytest.approx(fk, rel=1e-9)
    assert c.values["γ_M"] == 1.7  # Table 1 (CYS) category I designed mortar, class 2
    top = next(ch for ch in c.checks if "top" in ch.description)
    assert top.capacity == pytest.approx((1 - 2 * 20 / 250) * 250 * fk / 1.7, rel=1e-6)
    assert phi_m(0.05, 0.0) == pytest.approx(0.9 * math.exp(-0.5 * (0.063 / 0.6715) ** 2),
                                             rel=1e-9)


def test_tank_wk1_interpolation_and_moment():
    cy = get_annex("CY")
    assert wk1(cy, 1250, 250) == pytest.approx(0.2)
    assert wk1(cy, 35 * 250, 250) == pytest.approx(0.05)
    assert wk1(cy, 20 * 250, 250) == pytest.approx(0.125)
    c = get_module("ec2_tank").calculate({"hs": 0, "hgw": 0}, {"annex": "CY"})
    assert c.values["M_Ed,base"] / 1e6 == pytest.approx(1.2 * 9.81 * 2.3**3 / 6, rel=2e-3)


def test_crack_width_formula():
    r = crack_width(20e6, 1000, 250, 204, 905, 12, 125, 40, 30)
    fct, Ecm = 0.3 * 30 ** (2 / 3), 22000 * (38 / 10) ** 0.3
    rho = 905 / (1000 * 204)
    xi = -15 * rho + math.sqrt((15 * rho) ** 2 + 2 * 15 * rho)
    x = xi * 204
    ss = 20e6 / (905 * (204 - x / 3))
    hc = min(2.5 * 46, (250 - x) / 3, 125)
    rpe = 905 / (1000 * hc)
    de = max((ss - 0.4 * fct / rpe * (1 + 200000 / Ecm * rpe)) / 2e5, 0.6 * ss / 2e5)
    sr = 3.4 * 40 + 0.425 * 0.8 * 0.5 * 12 / rpe
    assert r["wk"] == pytest.approx(sr * de, rel=1e-9)


def test_tank_flotation_fails_with_high_groundwater():
    c = get_module("ec2_tank").calculate({"hgw": 2.5, "toe": 0}, {"annex": "CY"})
    upl = next(ch for ch in c.checks if ch.description.startswith("UPL"))
    assert not upl.passed and upl.hint
