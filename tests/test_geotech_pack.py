"""Hand-calculation tests: piles, settlement, gabion wall and embedded wall."""

import math

import numpy as np
import pytest

from erisma.core import InputError, get_module
from erisma.design.annex import get_annex
from erisma.modules.ec7_embedded_wall import solve_wall
from erisma.modules.ec7_pile import broms, nq_meyerhof
from erisma.modules.ec7_settlement import corner_influence


# ---------------------------------------------------------------- annex
def test_cyprus_pile_factors():
    cy = get_annex("CY")
    assert cy.pile_R["Bored"]["R2"] == (1.1, 1.1, 1.1, 1.15)
    assert cy.pile_sets["DA2"] == "R2"
    assert cy.xi3[1] == 1.40 and cy.xi4[10] == 1.08
    assert cy.pile_model_min == 1.25


# ---------------------------------------------------------------- piles
def test_pile_static_resistance_hand_calc():
    c = get_module("ec7_pile").calculate({"D": 0.6, "L": 15.0, "G": 1200, "Q": 400})
    perim = math.pi * 0.6
    # clay 3 m (α c_u = 20 kPa), clay 7 m (45 kPa), sand 5 m (β-method, bored K = K0, δ = φ')
    sv10 = 3 * 19 + 7 * (20 - 9.81)
    sv15 = sv10 + 5 * (20 - 9.81)
    beta = (1 - math.sin(math.radians(34))) * math.tan(math.radians(34))
    Rs = perim * (3 * 20 + 7 * 45 + 5 * beta * (sv10 + sv15) / 2)
    assert c.values["R_s,cal"] / 1e3 == pytest.approx(Rs, rel=5e-3)
    Nq = 115.0  # Meyerhof φ' = 34°
    qb = 0.5 * min(Nq * sv15, 0.5 * 100 * Nq * math.tan(math.radians(34)))
    assert c.values["R_b,cal"] / 1e3 == pytest.approx(qb * math.pi * 0.36 / 4, rel=5e-3)


def test_pile_defaults_pass_and_cyprus_model_factor():
    m = get_module("ec7_pile")
    assert m.calculate({}, {"annex": "CY"}).passed
    with pytest.raises(InputError):
        m.calculate({"gRd": 1.1}, {"annex": "CY"})
    m.calculate({"gRd": 1.1}, {"annex": "EN"})  # EN sets no minimum


def test_meyerhof_table():
    assert nq_meyerhof(30) == pytest.approx(56.7, rel=1e-6)
    assert nq_meyerhof(35) == pytest.approx(143.0, rel=1e-6)


def test_broms_cohesionless_short_pile():
    # short pile: H_u = 0.5 γ D L³ K_p / (e + L)
    phi = math.radians(30)
    H, mode, _ = broms("Sand", 500.0, 3000.0, 0.0, 1e12, 0, 18e-6, phi)
    assert mode == "short"
    assert H == pytest.approx(0.5 * 18e-6 * 500 * 3000**3 * 3.0 / 3000, rel=1e-6)


def test_broms_cohesive_short_pile_closed_form():
    D, L, cu = 600.0, 6000.0, 50e-3
    H, mode, _ = broms("Clay", D, L, 0.0, 1e15, cu, 18e-6, 0.0)
    f = H / (9 * cu * D)
    g = L - 1.5 * D - f
    assert mode == "short"
    assert H * (1.5 * D + 0.5 * f) == pytest.approx(2.25 * D * g**2 * cu, rel=1e-6)


# ---------------------------------------------------------------- settlement
def test_newmark_factors():
    assert corner_influence(1, 1, 1) == pytest.approx(0.1752, abs=1e-4)
    assert corner_influence(2, 1, 1) == pytest.approx(0.1999, abs=1e-4)
    assert corner_influence(1e6, 1e6, 1) == pytest.approx(0.25, abs=1e-6)


def test_settlement_elastic_layer_integration():
    lay = [{"h": 20, "soil": "Granular", "gamma": 20, "Eoed": 20, "Cc": 0, "Cr": 0, "e0": 0.6,
            "OCR": 1}]
    c = get_module("ec7_settlement").calculate(
        {"layers": lay, "D": 0, "zw": 50, "q": 100, "rigid": False})
    zi = c.values["z_inf"]  # mm
    z = np.linspace(0, zi, 4001)
    ds = [4 * 0.1 * corner_influence(1250, 1250, zz) for zz in z]
    s = np.trapezoid(ds, z) / 20.0
    assert c.values["s"] == pytest.approx(s, rel=0.02)


def test_settlement_clay_consolidation():
    # very wide load: Δσ = q through a 2 m NC clay layer, 0.25 m sub-layers
    lay = [{"h": 2.0, "soil": "Clay", "gamma": 20, "Eoed": 1, "Cc": 0.3, "Cr": 0.05,
            "e0": 1.0, "OCR": 1}]
    c = get_module("ec7_settlement").calculate(
        {"layers": lay, "D": 0, "zw": 50, "q": 100, "rigid": False, "B": 2000, "L": 2000})
    s = sum(250 * 0.3 / 2.0 * math.log10((20 * zm + 100) / (20 * zm))
            for zm in np.arange(0.125, 2.0, 0.25))
    assert c.values["s"] == pytest.approx(s, rel=1e-3)
    assert c.warnings  # profile too shallow for the influence depth


# ---------------------------------------------------------------- gabions
def test_gabion_defaults_pass_and_unit_weight():
    c = get_module("ec7_gabion_wall").calculate({})
    assert c.passed
    assert c.values["γ_g"] * 1e6 == pytest.approx(26 * 0.65)


def test_gabion_invalid_courses():
    with pytest.raises(InputError):
        get_module("ec7_gabion_wall").calculate(
            {"courses": [{"b": 1, "h": 1, "setback": 0}, {"b": 1, "h": 1, "setback": 1.5}]})


# ---------------------------------------------------------------- embedded wall
def _wall(**kw):
    p = dict(H=6000.0, t=5000.0, a=750.0, EI=0.7 * 32837 * math.pi * 600**4 / 64,
             kh=25e-3, phi=math.radians(32), c=0.0, gam=19e-6, gsat=20e-6, q=10e-3,
             zw=50000.0, anchors=[], d_a=math.radians(21), d_p=math.radians(16))
    p.update(kw)
    return solve_wall(**p)


def test_embedded_wall_equilibrium():
    for anchors in ([], [(1500.0, 20000.0, 100e3)]):
        r = _wall(anchors=anchors)
        assert r["ok"]
        Vmax = np.abs(r["V"]).max()
        Mmax = np.abs(r["M"]).max()
        assert abs(r["V"][-1]) < 1e-6 * Vmax + 1.0
        assert abs(r["M"][-1]) < 1e-3 * Mmax


def test_embedded_wall_pressures_within_limits():
    r = _wall()
    assert (r["pb"] >= r["pa"] - 1e-12).all()
    assert (r["pf"] <= r["pp_f"] + 1e-12).all()


def test_embedded_wall_short_embedment_fails():
    m = get_module("ec7_embedded_wall")
    assert m.calculate({}).passed
    assert not m.calculate({"t": 1.0}, {"annex": "CY"}).passed
    with pytest.raises(InputError):
        m.calculate({"anchors": [], "t": 0.5, "H": 10})
