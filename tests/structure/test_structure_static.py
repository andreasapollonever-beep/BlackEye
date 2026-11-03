"""Hand-calculation checks of the 3D frame solver (erisma.structure)."""

import math

import numpy as np
import pytest

from erisma.structure import Material, Model, Section, StructureError, analyse

E, NU = 210000.0, 0.3
MAT = Material("steel", E, NU)
G = MAT.G
# Euler–Bernoulli section (no shear areas)
SEC = Section("test", A=5000.0, Iy=8e7, Iz=3e7, J=2e6)


def approx(v, rel=1e-6):
    return pytest.approx(v, rel=rel, abs=1e-9)


def cantilever(L=3000.0, axis="x", sec=SEC):
    m = Model()
    m.node(1, 0, 0, 0)
    end = {"x": (L, 0, 0), "y": (0, L, 0), "z": (0, 0, L)}[axis]
    m.node(2, *end)
    m.member("A", 1, 2, sec, MAT)
    m.support(1, "fixed")
    return m


def test_cantilever_tip_loads_both_planes_axial_and_torsion():
    L, P = 3000.0, 10000.0
    m = cantilever(L)
    m.load_node("P", 2, Fx=P, Fy=P, Fz=-P, Mx=1e6)
    a = analyse(m)
    r = a.static("P")
    u = r.displacement(2)
    assert u[0] == approx(P * L / (E * SEC.A))
    assert u[1] == approx(P * L**3 / (3 * E * SEC.Iz))   # beam along X: y bending uses Iz
    assert u[2] == approx(-P * L**3 / (3 * E * SEC.Iy))  # vertical bending uses Iy
    assert u[3] == approx(1e6 * L / (G * SEC.J))
    R = r.reaction(1)
    assert R[:3] == pytest.approx([-P, -P, P])
    assert R[4] == approx(-P * L)   # My reaction balances the overturning about Y
    assert r.equilibrium_ok()
    f = r.forces("A")
    assert f["My"][0] == approx(-P * L)  # hogging at the root (tension on top)
    assert f["My"][-1] == approx(0.0)
    assert f["N"][0] == approx(P)       # tension
    assert f["Vz"][0] == approx(P)      # dM/dx = V: My goes from −PL to 0
    assert f["T"][0] == approx(1e6)


def test_timoshenko_shear_deflection():
    L, P = 1000.0, 50000.0
    sec = Section.rectangle(300, 600)
    m = cantilever(L, sec=sec)
    m.load_node("P", 2, Fz=-P)
    u = analyse(m).static("P").displacement(2)
    exact = P * L**3 / (3 * E * sec.Iy) + P * L / (G * sec.Avz)
    assert -u[2] == approx(exact)


def test_simply_supported_beam_udl_diagrams():
    L, w = 6000.0, 20.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L / 2, 0, 0), m.node(3, L, 0, 0)
    m.member("B1", 1, 2, SEC, MAT), m.member("B2", 2, 3, SEC, MAT)
    m.support(1, "pinned")
    m.support(3, "free").restraints = (False, True, True, True, False, False)
    m.load_member("w", "B1", wz=-w), m.load_member("w", "B2", wz=-w)
    r = analyse(m).static("w")
    assert -r.displacement(2)[2] == approx(5 * w * L**4 / (384 * E * SEC.Iy))
    assert r.reaction(1)[2] == approx(w * L / 2)
    assert r.reaction(3)[2] == approx(w * L / 2)
    f = r.forces("B1", 3)
    assert f["My"][-1] == approx(w * L**2 / 8)  # sagging positive
    assert f["Vz"][0] == approx(w * L / 2)
    assert f["My"][1] == approx(w * L / 2 * L / 4 - w * (L / 4) ** 2 / 2)
    assert r.equilibrium_ok()


def test_fixed_beam_single_element_udl():
    L, w = 5000.0, 10.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("B", 1, 2, SEC, MAT)
    m.support(1), m.support(2)
    m.load_member("w", "B", wz=-w)
    f = analyse(m).static("w").forces("B", 3)
    assert f["My"][0] == approx(-w * L**2 / 12)
    assert f["My"][1] == approx(w * L**2 / 24)


def test_space_frame_l_cantilever_bending_plus_torsion():
    """Two members at right angles in plan, vertical tip load:
    δ = Pa³/3EI + Pb³/3EI + P·b²·a/GJ."""
    a, b, P = 2000.0, 1500.0, 5000.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, a, 0, 0), m.node(3, a, b, 0)
    m.member("M1", 1, 2, SEC, MAT), m.member("M2", 2, 3, SEC, MAT)
    m.support(1)
    m.load_node("P", 3, Fz=-P)
    r = analyse(m).static("P")
    exact = P * a**3 / (3 * E * SEC.Iy) + P * b**3 / (3 * E * SEC.Iy) + P * b**2 * a / (G * SEC.J)
    assert -r.displacement(3)[2] == approx(exact)
    assert abs(r.forces("M1")["T"][0]) == approx(P * b)
    assert r.equilibrium_ok()


def test_inclined_member_and_beta_rotation_are_frame_invariant():
    """A cantilever along a skew direction must give the same tip deflection."""
    L, P = 2500.0, 3000.0
    d = np.array([1.0, 2.0, 2.0]) / 3.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, *(L * d))
    m.member("A", 1, 2, SEC, MAT, beta=30.0)
    m.support(1)
    # load perpendicular to the member
    n = np.cross(d, [0.0, 0.0, 1.0])
    n /= np.linalg.norm(n)
    m.load_node("P", 2, *(P * n))
    a = analyse(m)
    r = a.static("P")
    R = a.elements[0].R
    ul = R @ r.displacement(2)[:3]
    fl = R @ (P * n)
    # local y uses Iz, local z uses Iy
    assert ul[1] == approx(fl[1] * L**3 / (3 * E * SEC.Iz))
    assert ul[2] == approx(fl[2] * L**3 / (3 * E * SEC.Iy))
    assert np.allclose(R @ R.T, np.eye(3))
    assert r.equilibrium_ok()


def test_column_local_axes():
    m = cantilever(3000.0, axis="z")
    R = analyse(m).elements[0].R
    assert np.allclose(R, [[0, 0, 1], [1, 0, 0], [0, 1, 0]])


def test_portal_rigid_beam_sway_and_diaphragm():
    """Two fixed-base columns tied by a rigid diaphragm: k = 2·12EI/h³ (beam stiffness irrelevant)."""
    h, H, span = 3000.0, 20000.0, 5000.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, span, 0, 0), m.node(3, 0, 0, h), m.node(4, span, 0, h)
    col = Section("col", 1e10, 5e8, 5e8, 1e9)  # axially rigid: no overturning shortening
    m.member("C1", 1, 3, col, MAT), m.member("C2", 2, 4, col, MAT)
    m.member("B", 3, 4, Section("rigid", 1e9, 1e15, 1e15, 1e15), MAT)
    m.support(1), m.support(2)
    m.diaphragm("F1", [3, 4])
    m.load_node("H", 3, Fx=H)
    r = analyse(m).static("H")
    # columns bend about local axis: column local y = X → bending in X uses Iz
    k = 2 * 12 * E * col.Iz / h**3
    assert r.displacement(3)[0] == approx(H / k, rel=1e-6)
    assert r.displacement(4)[0] == approx(r.displacement(3)[0])
    assert r.equilibrium_ok()


def test_diaphragm_torsion_centre_of_stiffness():
    """Four equal columns at the corners, load at centroid in X: pure translation;
    with an eccentric load the floor rotates and the nearer columns take more."""
    h, a = 3000.0, 6000.0
    m = Model()
    col = Section.rectangle(400, 400)
    conc = Material.concrete(30)
    pts = [(0, 0), (a, 0), (a, a), (0, a)]
    for k, (x, y) in enumerate(pts, 1):
        m.node(f"b{k}", x, y, 0), m.node(f"t{k}", x, y, h)
        m.member(f"C{k}", f"b{k}", f"t{k}", col, conc)
        m.support(f"b{k}")
    m.diaphragm("F", ["t1", "t2", "t3", "t4"])
    m.load_node("E", "t1", Fy=100e3)
    r = analyse(m).static("E")
    u = [r.displacement(f"t{k}")[1] for k in range(1, 5)]
    assert u[0] == approx(u[3]) and u[1] == approx(u[2])
    assert u[0] > u[1]  # floor twists: the loaded side (x = 0) moves more
    assert sum(r.reaction(f"b{k}")[1] for k in range(1, 5)) == approx(-100e3)
    assert r.equilibrium_ok()


def test_springs_support():
    L, P, ks = 2000.0, 1000.0, 50.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("A", 1, 2, SEC, MAT)
    m.support(1, "fixed")
    m.support(2, "free", springs=(0, 0, ks, 0, 0, 0))
    m.load_node("P", 2, Fz=-P)
    r = analyse(m).static("P")
    kb = 3 * E * SEC.Iy / L**3
    assert -r.displacement(2)[2] == approx(P / (kb + ks))
    assert r.reaction(2)[2] == approx(P * ks / (kb + ks))
    assert r.equilibrium_ok()


def test_self_weight_and_combination():
    L = 4000.0
    conc = Material.concrete(25)
    sec = Section.rectangle(300, 500)
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("B", 1, 2, sec, conc)
    m.support(1), m.support(2)
    m.case("G", self_weight=1.0)
    m.load_member("Q", "B", wz=-5.0)
    a = analyse(m)
    res = a.run_all()
    wg = 25e-6 * sec.A
    assert res["G"].reaction(1)[2] == approx(wg * L / 2)
    c = a.combine(res, {"G": 1.35, "Q": 1.5})
    assert c.reaction(1)[2] == approx((1.35 * wg + 1.5 * 5.0) * L / 2)
    assert c.forces("B", 3)["My"][0] == approx(-(1.35 * wg + 1.5 * 5.0) * L**2 / 12)
    assert c.equilibrium_ok()


def test_propped_cantilever_with_hinge():
    L, w = 6000.0, 10.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("B", 1, 2, SEC, MAT, hinge_j=True)
    m.support(1), m.support(2)
    m.load_member("w", "B", wz=-w)
    r = analyse(m).static("w")
    assert r.forces("B", 3)["My"][0] == approx(-w * L**2 / 8)
    assert r.forces("B", 3)["My"][-1] == approx(0.0)
    assert r.reaction(2)[2] == approx(3 * w * L / 8)


# ----------------------------------------------------------------- user-friendly errors


def test_mechanism_points_at_the_node():
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, 3000, 0, 0)
    m.member("A", 1, 2, SEC, MAT)
    m.support(1, "pinned")
    with pytest.raises(StructureError) as e:
        analyse(m)
    assert "unstable" in str(e.value)
    assert "Η κατασκευή" in e.value.message("el")


def test_missing_supports_and_bad_ids():
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, 3000, 0, 0)
    m.member("A", 1, 2, SEC, MAT)
    with pytest.raises(StructureError, match="no supports"):
        analyse(m)
    m.member("B", 1, 9, SEC, MAT)
    m.support(1)
    with pytest.raises(StructureError) as e:
        analyse(m)
    assert e.value.ref == "member B"


def test_hinged_node_rotation_is_dropped_not_an_error():
    """A column with a beam hinged at both ends on top: beam torsion/rotation fine."""
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, 4000, 0, 0), m.node(3, 2000, 0, 0)
    m.member("A", 1, 3, SEC, MAT, hinge_j=True)
    m.member("B", 3, 2, SEC, MAT, hinge_i=True)
    m.support(1), m.support(2)
    m.load_node("P", 3, Fz=-1000)
    r = analyse(m).static("P")
    assert -r.displacement(3)[2] == approx(1000 * 2000**3 / (6 * E * SEC.Iy))
    assert any("no rotational stiffness" in n for n in r.notes)


def test_rectangle_torsion_constant():
    s = Section.rectangle(300, 600)
    # Roark: β(2.0) ≈ 0.229
    assert s.J / (600 * 300**3) == pytest.approx(0.229, abs=0.002)
    assert math.isclose(s.Iy, 300 * 600**3 / 12)
