"""Tower crane foundation — hand calculations (EN 1997-1, EN 1992-1-1, CY National Annex)."""

import math

import pytest

from erisma.core import InputError, get_module
from erisma.design.annex import get_annex
from erisma.design.geotech import bearing_factors
from erisma.modules.ec7_crane_base import (contact_pressure, mean_radius, perimeter_points,
                                           rounded_square_length)

M = get_module("ec7_crane_base")
CY = {"annex": "CY"}
NOSIZE = {"size": False}


def out(c, k):
    return c.outputs[k]["value"]


def chk(c, start):
    return [x for x in c.checks if x.description.startswith(start)]


def strip_moment(V, Md, B, w, x0, n=20000):
    """1-D hand integration of (q − w)(x − x0) per metre, linear pressure with lift-off [kN, m]."""
    e = Md / V
    if e <= B / 6:
        q = lambda x: V / B ** 2 * (1 + 12 * e * x / B ** 2)  # noqa: E731
    else:
        Lc = 3 * (B / 2 - e)
        q1 = 2 * V / (3 * B * (B / 2 - e))
        q = lambda x: max(q1 * (1 - (B / 2 - x) / Lc), 0.0)  # noqa: E731
    dx = (B / 2 - x0) / n
    return sum((q(x0 + (i + 0.5) * dx) - w) * (i + 0.5) * dx * dx for i in range(n))


def test_contact_pressure_closed_forms():
    B = 6000.0
    # full contact: q = V/B² (1 ± 6e/B); e = 0.8 m
    X, Y, dA, q = contact_pressure(2000e3, 2000e3 * 800, 1, 0, B, 60)
    assert (q * dA).sum() == pytest.approx(2000e3)
    assert q.max() == pytest.approx(2000e3 / B ** 2 * (1 + 6 * 800 / B * (59 / 60)), rel=1e-3)
    # lift-off: q_max = 2V / (3B(B/2 − e)), contact length 3(B/2 − e); e = 2 m
    X, Y, dA, q = contact_pressure(2000e3, 2000e3 * 2000, 1, 0, B, 200)
    assert (q * dA).sum() == pytest.approx(2000e3)
    assert (q * X * dA).sum() == pytest.approx(2000e3 * 2000, rel=1e-4)
    assert q.max() == pytest.approx(2 * 2000e3 / (3 * B * (B / 2 - 2000)), rel=0.01)
    assert (q[:, 0] > 0).sum() / 200 == pytest.approx(3 * (B / 2 - 2000) / B, abs=0.01)
    # outside the base
    assert contact_pressure(1e3, 1e3 * 5000, 1, 0, B) is None


def test_geometry_helpers():
    # mean distance of a square from its centre = s (√2 + ln(1 + √2)) / 6
    assert mean_radius(3000, 3000, 60) == pytest.approx(
        3000 * (math.sqrt(2) + math.log(1 + math.sqrt(2))) / 6, rel=1e-3)
    # unclipped control perimeter 4c + 2πr; clipped by a base edge
    assert rounded_square_length(0, 0, 400, 500, 6000) == pytest.approx(
        4 * 400 + 2 * math.pi * 500, rel=1e-4)
    assert rounded_square_length(2800, 0, 400, 500, 6000) < 4 * 400 + 2 * math.pi * 500


def test_default_equ_and_eccentricity():
    c = M.calculate(NOSIZE, CY)
    W = 25 * 6 * 6 * 1.4
    assert out(c, "W") == pytest.approx(W)
    # EQU out of service: 1.5 (2800 + 95·1.4) ≤ 0.9 (950 + W) · 3
    e = chk(c, "EQU Out of service")[0]
    assert e.demand / 1e6 == pytest.approx(1.5 * (2800 + 95 * 1.4))
    assert e.capacity / 1e6 == pytest.approx(0.9 * (950 + W) * 3)
    # DA2 (CY): min V = 1.0 (950 + W), M_d = 1.5 (2800 + 95·1.4) along the axis
    ecc = chk(c, "DA2 eccentricity")[0]
    ed = 1.5 * (2800 + 95 * 1.4) / (950 + W)
    assert ecc.demand == pytest.approx((ed / 6) ** 2)
    assert ecc.passed and ecc.utilisation > 0.98


def test_default_bearing_annex_d():
    c = M.calculate(NOSIZE, CY)
    W = 25 * 6 * 6 * 1.4
    V, Md, Hd = 950 + W, 1.5 * (2800 + 95 * 1.4), 1.5 * 95
    Bp = 6 - 2 * Md / V
    A = Bp * 6
    phi = math.radians(30)
    Nq, Nc, Ng = bearing_factors(phi)
    assert Nq == pytest.approx(math.exp(math.pi * math.tan(phi)) * math.tan(math.radians(60)) ** 2)
    r = Bp / 6
    sq, sg = 1 + r * math.sin(phi), 1 - 0.3 * r
    m = (2 + r) / (1 + r)
    iq, ig = (1 - Hd / V) ** m, (1 - Hd / V) ** (m + 1)
    qRd = (19 * 1.4 * Nq * sq * iq + 0.5 * 19 * Bp * Ng * sg * ig) / 1.4
    b = chk(c, "DA2 bearing")[0]
    assert "Out of service, min V, axis" in b.description
    assert b.demand * 1e3 == pytest.approx(V / A)
    assert b.capacity * 1e3 == pytest.approx(qRd)


def test_default_sliding_with_torque():
    c = M.calculate(NOSIZE, CY)
    W = 25 * 6 * 6 * 1.4
    V = 1100 + W
    e = 1.5 * (2400 + 35 * 1.4) / V / math.sqrt(2)          # diagonal: e_x = e_y
    side = 6 - 2 * e
    rm = side * (math.sqrt(2) + math.log(1 + math.sqrt(2))) / 6
    Rh = V * math.tan(math.radians(30)) / 1.1
    s = chk(c, "DA2 sliding")[0]
    assert "In service, min V, diagonal" in s.description
    assert s.demand == pytest.approx(1.5 * 35 / Rh + 1.5 * 300 / (Rh * rm), rel=2e-3)


def test_default_structural():
    c = M.calculate(NOSIZE, CY)
    W = 25 * 6 * 6 * 1.4
    # sagging at x = a/2 = 1 m, worst along the axis (γ_G 1.35 / 1.0, both cases)
    m = max(strip_moment(g * (N + W), 1.5 * (Mk + H * 1.4), 6, g * W / 36, 1.0)
            for N, Mk, H in ((1100, 2400, 35), (950, 2800, 95)) for g in (1.35, 1.0))
    assert out(c, "m_Ed") == pytest.approx(m, rel=0.01)
    # most compressed leg: 1.35 N/4 + M_d/(√2 a); anchor tension: M_d/(√2 a) − N/4
    Md = 1.5 * (2800 + 95 * 1.4)
    assert out(c, "F_leg") == pytest.approx(1.35 * 950 / 4 + Md / (math.sqrt(2) * 2))
    assert out(c, "T_leg") == pytest.approx(Md / (math.sqrt(2) * 2) - 950 / 4)
    # leg punching: d = 1400 − 50 − 25, a_p = min(2d, (a − c_l)/2) = 800 mm
    d = 1325.0
    assert out(c, "a_p") == pytest.approx(800)
    u = 4 * 400 + 2 * math.pi * 800
    assert out(c, "u_leg") == pytest.approx(u, rel=1e-3)
    assert out(c, "v_Ed,leg") == pytest.approx(out(c, "F_leg") * 1e3 / (u * d), rel=1e-3)
    k = 1 + math.sqrt(200 / d)
    rho = math.pi * 25 ** 2 / 4 / 150 / d
    vrc = max(0.12 * k * (100 * rho * 30) ** (1 / 3), 0.035 * k ** 1.5 * math.sqrt(30))
    assert out(c, "v_Rd,leg") == pytest.approx(vrc * 2 * d / 800, rel=1e-6)
    # v_Rd,max = 0.5 ν f_cd (NA to CYS EN 1992-1-1 NA 2.34(3))
    assert out(c, "v_Rd,max") == pytest.approx(0.5 * 0.6 * (1 - 30 / 250) * 20, rel=1e-6)
    assert c.passed


def test_design_values_and_given_qrd():
    c = M.calculate({"size": False, "loadtype": "Design values (factors already included)",
                     "soil": "Given design bearing resistance q_Rd", "qRd": 250}, CY)
    W = 25 * 6 * 6 * 1.4
    e = chk(c, "EQU Out of service")[0]
    assert e.demand / 1e6 == pytest.approx(2800 + 95 * 1.4)
    assert e.capacity / 1e6 == pytest.approx((950 + W) * 3)
    b = chk(c, "DA2 bearing")[0]
    assert b.capacity * 1e3 == pytest.approx(250)


def test_failing_base_gives_hints():
    c = M.calculate({"size": False, "B": 4.5}, CY)
    bad = [x for x in c.checks if not x.passed]
    assert bad and all(x.hint for x in bad)
    assert any("eccentricity" in x.description for x in bad)


def test_sizing_finds_the_smallest_passing_base():
    c = M.calculate({}, CY)
    B, h = out(c, "B_min") * 1000, out(c, "h_min") * 1000
    na = get_annex("CY")
    inp = M.parse_inputs({}, "en")
    assert M.passes(inp, B, h, na)
    assert not M.passes(inp, B - 100, h, na)
    assert h >= 1000                      # minimum thickness of the search
    # the base entered (h = 1.4 m) needs B ≥ 6.0 m
    assert out(c, "B_min(h)") == pytest.approx(6.0)


def test_input_errors():
    with pytest.raises(InputError):
        M.calculate({"B": 2.2, "a": 2.0, "cl": 0.4}, CY)
    with pytest.raises(InputError):
        M.calculate({"cases": []}, CY)


HEAVY = {"size": False, "B": 9, "h": 0.8, "a": 2.4, "cl": 0.35, "concrete": "C25/30",
         "db": "20", "sb": 200,
         "cases": [{"name": "In service", "N": 2500, "M": 6000, "H": 60, "Mt": 500},
                   {"name": "Out of service", "N": 2200, "M": 7500, "H": 150, "Mt": 0}]}


def test_perimeter_points_are_on_the_control_perimeter():
    pts = perimeter_points(0, 0, 2000, 500, 40)
    assert len(pts) == 40
    for x, y in pts:   # distance from the square = r
        assert math.hypot(max(abs(x) - 1000, 0), max(abs(y) - 1000, 0)) == pytest.approx(500)
    gaps = [math.dist(p, q) for p, q in zip(pts, pts[1:])]
    assert max(gaps) == pytest.approx((4 * 2000 + 2 * math.pi * 500) / 40, rel=0.02)


def test_no_links_when_concrete_alone_resists():
    c = M.calculate(NOSIZE, CY)
    assert not chk(c, "Punching with links") and "A_sw,req" not in c.outputs
    assert chk(c, "Punching of the mast base")[0].passed


def test_punching_links_hand_calculation():
    c = M.calculate(HEAVY, CY)
    # without links the same base fails punching
    c0 = M.calculate({**HEAVY, "links": False}, CY)
    assert not chk(c0, "Punching of the mast base")[0].passed
    assert not chk(c0, "Punching under a leg")[0].passed
    d = 800 - 50 - 20
    fywd = 500 / 1.15
    assert out(c, "f_ywd,ef") == pytest.approx(min(250 + 0.25 * d, fywd))       # Eq. 6.53
    sr, s0 = math.floor(0.75 * d / 25) * 25, math.floor(0.5 * d / 25) * 25     # 9.4.3
    assert out(c, "s_r") == sr and out(c, "s_0") == s0 and 0.3 * d <= s0 <= 0.5 * d
    # leg: A_sw = (v_Ed − 0.75 v_Rd,c 2d/a_p) u s_r / (1.5 f_ywd,ef)   (Eq. 6.52, sin α = 1)
    vEd, vRd, u = out(c, "v_Ed,leg"), out(c, "v_Rd,leg"), out(c, "u_leg")
    req = (vEd - 0.75 * vRd) * u * sr / (1.5 * out(c, "f_ywd,ef"))
    assert out(c, "A_sw,req,leg") == pytest.approx(req, rel=1e-6)
    A1 = math.pi * 12 ** 2 / 4
    n = out(c, "n_sw,leg") / 4 / 2          # legs per perimeter (4 legs, 2 perimeters)
    assert n * A1 >= req
    vRdcs = 0.75 * vRd + 1.5 * d / sr * (n * A1) * out(c, "f_ywd,ef") / (u * d)
    assert out(c, "v_Rd,cs,leg") == pytest.approx(vRdcs, rel=0.02)
    assert vEd <= out(c, "v_Rd,cs,leg")
    # mast base: outermost perimeter within k d = 1.5 d of u_out (6.4.5(4), CY NA 2.34(4))
    assert out(c, "r_last,min") == pytest.approx(out(c, "a_out") - 1.5 * d)
    for name in ("Punching with links", "Punching under a leg with links", "Link leg area",
                 "Last link perimeter"):
        assert all(x.passed for x in chk(c, name)) and chk(c, name)
    # link legs drawn in the 3D view
    assert any(o.get("layer") == "links" for o in c.model3d["objects"])


def test_links_allow_a_thinner_base():
    heavy = {**HEAVY, "size": True, "hmin": 0.8, "db": "25", "sb": 125}
    with_links = M.calculate(heavy, CY)
    without = M.calculate({**heavy, "links": False}, CY)
    assert out(with_links, "h_min") <= out(without, "h_min")
