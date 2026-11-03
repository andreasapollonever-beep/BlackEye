"""MITC4 plate element against classical plate solutions (Timoshenko & Woinowsky-Krieger)."""

import numpy as np
import pytest

from erisma.structure import Material, Model, analyse

E, NU, T = 30000.0, 0.2, 200.0
MAT = Material("c", E, NU)
D = E * T**3 / (12 * (1 - NU**2))


def square_plate(a=6000.0, n=12, edge="simple", q=0.01, springs=None):
    m = Model()
    h = a / n
    for i in range(n + 1):
        for j in range(n + 1):
            nid = f"{i}_{j}"
            m.node(nid, i * h, j * h, 0)
            on_edge = i in (0, n) or j in (0, n)
            s = m.support(nid, "free")
            r = [True, True, False, False, False, True]  # in-plane and drilling restrained
            if on_edge and edge == "simple":
                r[2] = True
            if on_edge and edge == "clamped":
                r[2] = r[3] = r[4] = True
            s.restraints = tuple(r)
            if springs:
                trib = (h / (2 if i in (0, n) else 1)) * (h / (2 if j in (0, n) else 1))
                s.springs = (0, 0, springs * trib, 0, 0, 0)
    for i in range(n):
        for j in range(n):
            pid = f"P{i}_{j}"
            m.plate(pid, [f"{i}_{j}", f"{i + 1}_{j}", f"{i + 1}_{j + 1}", f"{i}_{j + 1}"], T, MAT)
            m.load_plate("q", pid, q)
    return m


def test_simply_supported_square_plate_deflection_and_moment():
    a, n, q = 6000.0, 16, 0.01
    m = square_plate(a, n, "simple", q)
    r = analyse(m).static("q")
    w = -r.displacement(f"{n // 2}_{n // 2}")[2]
    # t/a = 1/30: Mindlin theory adds the shear deformation, ≈ +2 % over Kirchhoff's 0.00406
    wk = 0.00406 * q * a**4 / D
    assert wk < w < 1.04 * wk
    # centre moment Mx = My = 0.0479 q a² (ν = 0.3 in the tables; ν = 0.2 gives 0.0442)
    f = r.plate_forces(f"P{n // 2}_{n // 2}")
    assert f["Mx"] > 0 and f["Mx"] == pytest.approx(f["My"], rel=1e-6)
    assert f["Mx"] == pytest.approx(0.0442 * q * a**2, rel=0.05)
    assert r.equilibrium_ok()


def test_clamped_square_plate_deflection():
    a, n, q = 6000.0, 16, 0.01
    r = analyse(square_plate(a, n, "clamped", q)).static("q")
    w = -r.displacement(f"{n // 2}_{n // 2}")[2]
    assert w == pytest.approx(0.00126 * q * a**4 / D, rel=0.03)


def test_free_plate_on_winkler_springs_settles_uniformly():
    """Rigid-body response: w = q / k_s everywhere, no bending."""
    q, ks = 0.05, 0.04
    m = square_plate(6000.0, 6, "free", q, springs=ks)
    r = analyse(m).static("q")
    w = np.array([-r.displacement(n)[2] for n in m.nodes])
    assert w == pytest.approx(np.full_like(w, q / ks), rel=1e-6)
    assert abs(r.plate_forces("P2_2")["Mx"]) < 1e-6 * q * 6000**2
    assert sum(R[2] for R in r.reactions.values()) == pytest.approx(q * 6000**2)


def test_thin_plate_no_shear_locking():
    """t/a = 1/300: MITC4 must not lock (deflection still within 3 %)."""
    a, n, q = 6000.0, 12, 1e-5
    m = square_plate(a, n, "simple", q)
    for p in m.plates.values():
        p.t = 20.0
    r = analyse(m).static("q")
    Dthin = E * 20.0**3 / (12 * (1 - NU**2))
    assert -r.displacement(f"{n // 2}_{n // 2}")[2] == pytest.approx(0.00406 * q * a**4 / Dthin,
                                                                     rel=0.03)
