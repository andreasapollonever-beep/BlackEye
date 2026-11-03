"""EN 1998-1 4.2.3 regularity: hand checks on simple floors."""

import math

import pytest

from erisma.structure import Material, Model, Section, analyse, modal
from erisma.structure.builder import BuildingSpec, build
from erisma.structure.regularity import _hull_area, regularity

E = 30000.0
MAT = Material("c", E, 0.2)
SQ = Section("sq", A=1e8, Iy=3e9, Iz=3e9, J=4e9)   # Euler–Bernoulli, axially rigid


def _four_columns(a=6000.0, h=3000.0, W=200e3):
    m = Model()
    for k, (x, y) in enumerate([(0, 0), (a, 0), (a, a), (0, a)], 1):
        m.node(f"b{k}", x, y, 0), m.node(f"t{k}", x, y, h)
        m.member(f"C{k}", f"b{k}", f"t{k}", SQ, MAT)
        m.support(f"b{k}")
        m.load_node("G", f"t{k}", Fz=-W)
    m.diaphragm("F", ["t1", "t2", "t3", "t4"])
    info = {"xs": [0.0, a], "ys": [0.0, a], "openings": set()}
    return m, info


def test_torsional_radius_four_cantilever_columns():
    """k = 3EI/h³ per column (tops free to rotate); K_θ = 2 k a² + 4 GJ/h; r = √(K_θ / 4k);
    l_s of a uniform a × a floor = a/√6."""
    a, h = 6000.0, 3000.0
    m, info = _four_columns(a, h)
    an = analyse(m)
    reg = regularity(an, modal(an, {"G": 1.0}, n_modes=3), info)
    f = reg.floors[0]
    k = 3 * E * SQ.Iy / h**3
    Kt = 2 * k * a**2 + 4 * MAT.G * SQ.J / h
    assert f.Kx == pytest.approx(4 * k, rel=1e-6)
    assert f.Kt == pytest.approx(Kt, rel=1e-6)
    assert f.rx == pytest.approx(math.sqrt(Kt / (4 * k)), rel=1e-6)
    assert f.ls == pytest.approx(a / math.sqrt(6))
    assert f.e0x == pytest.approx(0.0, abs=1e-6) and f.e0y == pytest.approx(0.0, abs=1e-6)
    assert reg.plan_regular and not reg.torsionally_flexible


def test_eccentric_walls_make_plan_irregular_and_modes_torsional():
    sp = BuildingSpec([5000, 5000, 5000], [5000, 5000], [3000] * 3,
                      walls=[{"at": "A1", "dir": "X", "L": 2000, "t": 250},
                             {"at": "B1", "dir": "Y", "L": 2000, "t": 250}])
    m, info = build(sp)
    an = analyse(m)
    md = modal(an, {"G": 1.0, "Q": 0.3})
    reg = regularity(an, md, info)
    f = reg.floors[0]
    assert f.cr[0] < f.cm[0] and f.cr[1] < f.cm[1]       # stiffness pulled towards the walls
    assert not reg.plan_regular
    assert "RZ" in md.meff and max(md.ratio("RZ")) > 0.3
    assert md.mode_type(0) in ("X", "Y", "RZ")


def test_q_consequences_and_geometry():
    sp = BuildingSpec([5000, 5000], [5000, 5000], [3000] * 2)
    m, info = build(sp)
    an = analyse(m)
    reg = regularity(an, modal(an, {"G": 1.0, "Q": 0.3}), info)
    assert reg.q_effective(3.9) == pytest.approx(3.9)
    reg.elev_flags.append("stiffness:X:1")
    assert reg.q_effective(3.9) == pytest.approx(3.12)
    # L-shaped floor: one corner panel open → recess = its area / remaining floor
    assert _hull_area([(0, 0), (2, 0), (2, 2), (0, 2), (1, 1)]) == pytest.approx(4.0)
    info2 = {**info, "openings": {"B2"}}
    from erisma.structure.regularity import _floor_geometry
    recess, lam, ls = _floor_geometry(info2)
    # convex envelope of the L cuts the missing corner diagonally: 12.5 m² of 75 m²
    assert recess == pytest.approx(12.5e6 / 75e6, rel=1e-9)
    assert lam == pytest.approx(1.0)
