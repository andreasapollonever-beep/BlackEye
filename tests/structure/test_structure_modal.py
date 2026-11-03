"""Hand-calculation checks of modal and response spectrum analysis."""

import math

import numpy as np
import pytest

from erisma.structure import (G_ACC, Material, Model, Section, StructureError, analyse,
                              ec8_spectrum, modal, response_spectrum)
from erisma.structure.modal import cqc_rho

E = 30000.0
MAT = Material("c", E, 0.2)
COL = Section("col", A=1e8, Iy=4e9, Iz=2e9, J=3e9)  # Euler–Bernoulli, axially rigid


def tip_mass_column(h=3000.0, W=500e3):
    m = Model()
    m.node("b", 0, 0, 0), m.node("t", 0, 0, h)
    m.member("C", "b", "t", COL, MAT)
    m.support("b")
    m.load_node("G", "t", Fz=-W)
    return m


def test_cantilever_with_tip_mass_periods():
    h, W = 3000.0, 500e3
    mass = W / G_ACC
    md = modal(analyse(tip_mass_column(h, W)), {"G": 1.0}, n_modes=4)
    # column local y = global X → sway in X bends about local z (Iz); sway in Y uses Iy
    Tx = 2 * math.pi * math.sqrt(mass * h**3 / (3 * E * COL.Iz))
    Ty = 2 * math.pi * math.sqrt(mass * h**3 / (3 * E * COL.Iy))
    assert md.n_modes == 2  # only two mass DOFs
    assert md.periods[0] == pytest.approx(Tx, rel=1e-9)
    assert md.periods[1] == pytest.approx(Ty, rel=1e-9)
    assert md.ratio("X")[0] == pytest.approx(1.0)
    assert md.ratio("Y")[1] == pytest.approx(1.0)
    assert md.total_mass["X"] == pytest.approx(mass)
    shape = md.mode_shape(0)
    assert abs(shape[1, 0]) == pytest.approx(1.0)


def _two_storey(h=3000.0, W=400e3, n=2):
    """Shear building: rigid beams, axially rigid columns, diaphragm per floor."""
    m = Model()
    beam = Section("rigid", 1e9, 1e15, 1e15, 1e15)
    for lvl in range(n + 1):
        m.node(f"a{lvl}", 0, 0, lvl * h), m.node(f"b{lvl}", 6000, 0, lvl * h)
    m.support("a0"), m.support("b0")
    for lvl in range(1, n + 1):
        m.member(f"Ca{lvl}", f"a{lvl - 1}", f"a{lvl}", COL, MAT)
        m.member(f"Cb{lvl}", f"b{lvl - 1}", f"b{lvl}", COL, MAT)
        m.member(f"B{lvl}", f"a{lvl}", f"b{lvl}", beam, MAT)
        m.diaphragm(f"F{lvl}", [f"a{lvl}", f"b{lvl}"])
        m.load_node("G", f"a{lvl}", Fz=-W / 2), m.load_node("G", f"b{lvl}", Fz=-W / 2)
    return m


def test_two_storey_shear_building():
    h, W = 3000.0, 400e3
    md = modal(analyse(_two_storey(h, W)), {"G": 1.0}, n_modes=6, directions="X")
    k = 2 * 12 * E * COL.Iz / h**3
    mass = W / G_ACC
    w2 = np.array([(3 - math.sqrt(5)) / 2, (3 + math.sqrt(5)) / 2]) * k / mass
    # 1e-4: the (tiny) axial shortening of the columns under overturning is included
    assert md.omega[:2] ** 2 == pytest.approx(w2, rel=1e-4)
    # effective masses of the 2-DOF system, solved independently
    Kc = k * np.array([[2, -1], [-1, 1]])
    Mc = mass * np.eye(2)
    lam, V = np.linalg.eigh(np.linalg.solve(Mc, Kc))
    meff = [(V[:, i] @ Mc @ np.ones(2)) ** 2 / (V[:, i] @ Mc @ V[:, i]) for i in range(2)]
    assert md.meff["X"][:2] == pytest.approx(meff, rel=1e-4)
    assert md.cumulative("X")[1] == pytest.approx(1.0, rel=1e-6)


def test_diaphragm_torsional_mode():
    h, a, W = 3000.0, 6000.0, 200e3
    sq = Section("sq", A=1e8, Iy=3e9, Iz=3e9, J=4e9)
    m = Model()
    for k, (x, y) in enumerate([(0, 0), (a, 0), (a, a), (0, a)], 1):
        m.node(f"b{k}", x, y, 0), m.node(f"t{k}", x, y, h)
        m.member(f"C{k}", f"b{k}", f"t{k}", sq, MAT)
        m.support(f"b{k}")
        m.load_node("G", f"t{k}", Fz=-W)
    m.diaphragm("F", ["t1", "t2", "t3", "t4"])
    md = modal(analyse(m), {"G": 1.0}, n_modes=3)
    mass = W / G_ACC
    k = 3 * E * sq.Iy / h**3  # column tops free to rotate (diaphragm acts in plane only)
    wt2 = k / mass
    wr2 = (2 * k * a**2 + 4 * MAT.G * sq.J / h) / (2 * mass * a**2)
    assert sorted(md.omega**2) == pytest.approx(sorted([wt2, wt2, wr2]), rel=1e-6)


def test_spectrum_sdof_base_shear_and_displacement():
    h, W = 3000.0, 500e3
    mass = W / G_ACC
    md = modal(analyse(tip_mass_column(h, W)), {"G": 1.0})
    Sd = lambda T: 0.25 * np.ones_like(np.asarray(T, dtype=float))  # noqa: E731
    rs = response_spectrum(md, Sd, "X")
    assert rs.base_shear == pytest.approx(mass * 0.25 * G_ACC, rel=1e-9)
    w = md.omega[0]
    assert rs.displacement("t")[0] == pytest.approx(0.25 * G_ACC / w**2, rel=1e-9)
    # base moment = V·h
    Mb = rs.member_end_forces("C")[5]
    assert Mb == pytest.approx(mass * 0.25 * G_ACC * h, rel=1e-9)
    assert rs.mass_ratio == pytest.approx(1.0)
    assert not rs.warnings


def test_spectrum_two_storey_cqc_vs_srss_and_mass_warning():
    md = modal(analyse(_two_storey()), {"G": 1.0}, n_modes=2, directions="X")
    Sd = ec8_spectrum(0.24, "B", q=3.0)
    cqc = response_spectrum(md, Sd, "X", "CQC")
    srss = response_spectrum(md, Sd, "X", "SRSS")
    # well-separated modes (ratio 2.6): CQC ≈ SRSS within 2 %
    assert cqc.base_shear == pytest.approx(srss.base_shear, rel=0.02)
    v = cqc.base_shear_modes
    assert srss.base_shear == pytest.approx(math.sqrt((v**2).sum()))
    assert not cqc.warnings
    md1 = modal(analyse(_two_storey(n=6)), {"G": 1.0}, n_modes=1, directions="X")
    assert response_spectrum(md1, Sd, "X").warnings  # 1 mode of 6 storeys: < 90 % mass


def test_cqc_coefficients():
    rho = cqc_rho(np.array([10.0, 10.0, 30.0]), 0.05)
    assert rho[0, 0] == pytest.approx(1.0) and rho[0, 1] == pytest.approx(1.0)
    assert np.allclose(rho, rho.T)
    assert rho[0, 2] < 0.01


def test_ec8_spectrum_plateau_matches_formula():
    Sd = ec8_spectrum(0.16, "B", q=3.5, importance="II")
    # EN 1998-1 Eq. 3.14: ag·S·2.5/q on the plateau (Type 1, ground B: S = 1.2)
    assert float(Sd(np.array([0.3]))[0]) == pytest.approx(0.16 * 1.2 * 2.5 / 3.5)


def test_no_mass_is_explained():
    m = tip_mass_column()
    m.cases.clear()
    m.case("Q")
    with pytest.raises(StructureError, match="no mass"):
        modal(analyse(m), {"Q": 1.0})
