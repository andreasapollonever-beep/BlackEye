"""Rigid end zones, P-Δ and elastic critical load factor."""

import math

import numpy as np
import pytest

from erisma.structure import (Material, Model, Section, StructureError, analyse, analyse_pdelta,
                              critical_load_factor)

E = 210000.0
MAT = Material("s", E, 0.3)
SEC = Section("t", A=1e5, Iy=8e7, Iz=8e7, J=1e7)  # Euler–Bernoulli, axially stiff


def test_rigid_zone_at_fixed_end():
    L, oi, P = 3000.0, 500.0, 1000.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("A", 1, 2, SEC, MAT, offset_i=oi)
    m.support(1)
    m.load_node("P", 2, Fz=-P)
    r = analyse(m).static("P")
    Lf = L - oi
    assert -r.displacement(2)[2] == pytest.approx(P * Lf**3 / (3 * E * SEC.Iy), rel=1e-9)
    assert r.forces("A", 3)["My"][0] == pytest.approx(-P * L)   # statics over the full length


def test_rigid_zone_at_free_end():
    L, oj, P = 3000.0, 600.0, 1000.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("A", 1, 2, SEC, MAT, offset_j=oj)
    m.support(1)
    m.load_node("P", 2, Fz=-P)
    r = analyse(m).static("P")
    Lf, EI = L - oj, E * SEC.Iy
    d = P * Lf**3 / (3 * EI) + P * oj * Lf**2 / (2 * EI)
    th = P * Lf**2 / (2 * EI) + P * oj * Lf / EI
    assert -r.displacement(2)[2] == pytest.approx(d + th * oj, rel=1e-9)


def test_udl_over_rigid_zones_equilibrium():
    L, w = 6000.0, 10.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("B", 1, 2, SEC, MAT, offset_i=400, offset_j=400)
    m.support(1), m.support(2)
    m.load_member("w", "B", wz=-w)
    r = analyse(m).static("w")
    assert r.reaction(1)[2] == pytest.approx(w * L / 2)
    assert r.equilibrium_ok()
    # moment at the face of the support equals the fixed-end moment of the flexible span
    # plus the cantilevering rigid zone: M_face = −w Lf²/12, M_node = M_face − (wL/2)·a + w a²/2
    f = r.forces("B", 5)
    a, Lf = 400.0, L - 800.0
    Mface = np.interp(a, f["x"], f["My"])
    assert Mface == pytest.approx(-w * Lf**2 / 12, rel=1e-9)


def test_pdelta_cantilever_matches_exact_second_order():
    """Column with axial compression P and tip shear H:
    δ = H/(P k)·(tan kL − kL), k = √(P/EI)."""
    L, P, H, n = 4000.0, 400e3, 5e3, 8
    m = Model()
    for i in range(n + 1):
        m.node(i, 0, 0, i * L / n)
    for i in range(n):
        m.member(f"C{i}", i, i + 1, SEC, MAT)
    m.support(0)
    m.load_node("G", n, Fz=-P)
    m.load_node("H", n, Fx=H)
    a = analyse_pdelta(m, {"G": 1.0})
    d = a.static("H").displacement(n)[0]
    EI = E * SEC.Iz
    k = math.sqrt(P / EI)
    exact = H / (P * k) * (math.tan(k * L) - k * L)
    assert d == pytest.approx(exact, rel=2e-3)
    assert d > H * L**3 / (3 * EI)  # larger than first order


def test_critical_load_factor_euler_cantilever():
    L, P, n = 5000.0, 100e3, 8
    m = Model()
    for i in range(n + 1):
        m.node(i, 0, 0, i * L / n)
    for i in range(n):
        m.member(f"C{i}", i, i + 1, SEC, MAT)
    m.support(0)
    m.load_node("G", n, Fz=-P)
    a = analyse(m)
    Pcr = math.pi**2 * E * SEC.Iz / (4 * L**2)
    assert critical_load_factor(a, {"G": 1.0}) == pytest.approx(Pcr / P, rel=1e-3)


def test_pdelta_buckling_is_explained():
    L, n = 5000.0, 4
    m = Model()
    for i in range(n + 1):
        m.node(i, 0, 0, i * L / n)
    for i in range(n):
        m.member(f"C{i}", i, i + 1, SEC, MAT)
    m.support(0)
    Pcr = math.pi**2 * E * SEC.Iz / (4 * L**2)
    m.load_node("G", n, Fz=-2 * Pcr)
    with pytest.raises(StructureError, match="buckles"):
        analyse_pdelta(m, {"G": 1.0})


def test_rigid_zones_longer_than_member_rejected():
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, 1000, 0, 0)
    m.member("A", 1, 2, SEC, MAT, offset_i=600, offset_j=600)
    m.support(1)
    with pytest.raises(StructureError, match="rigid end zones"):
        analyse(m)
