"""Tower crane foundation — hand calculations (EN 1997-1, EN 1992-1-1, CY National Annex)."""

import math

import pytest

from erisma.core import InputError, get_module
from erisma.design.annex import get_annex
from erisma.design.geotech import bearing_factors
from erisma.modules.ec7_crane_base import (contact_pressure, mean_radius, peak_pressure,
                                           perimeter_points, rounded_rect_length,
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
    # most compressed leg: 1.35 N/4 + M_d/(√2 a); anchor tension: M_d/(√2 a) − N/4, with M at
    # the level of the leg feet (top of the base for a bolted mast)
    Md = 1.5 * 2800
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


EMB = "Embedded anchor section (cast in, built-in mast)"
T = 9.80665   # kN per tonne


def test_peak_pressure_closed_forms():
    B, V = 5000.0, 900e3
    # axis, full contact (e = 0.6 m ≤ B/6): q = V/B² (1 + 6e/B)
    assert peak_pressure(V, V * 600, 1, 0, B) == pytest.approx(V / B**2 * (1 + 6 * 600 / B),
                                                              rel=2e-3)
    # axis, lift-off (e = 1.2 m): q = 2V / (3B(B/2 − e))
    assert peak_pressure(V, V * 1200, 1, 0, B) == pytest.approx(2 * V / (3 * B * 1300), rel=5e-3)
    # diagonal, full contact (e = 0.4 m ≤ B/(6√2)): q = V/B² (1 + 6√2 e/B)
    f = 1 / math.sqrt(2)
    assert peak_pressure(V, V * 400, f, f, B) == pytest.approx(
        V / B**2 * (1 + 6 * math.sqrt(2) * 400 / B), rel=5e-3)


def test_rounded_rectangle_perimeter():
    assert rounded_rect_length(0, 0, 400, 1600, 300, 9000) == pytest.approx(
        2 * (400 + 1600) + 2 * math.pi * 300, rel=1e-4)
    assert rounded_rect_length(0, 0, 500, 500, 200, 9000) == pytest.approx(
        rounded_square_length(0, 0, 500, 200, 9000), rel=1e-6)


def test_loads_in_tonnes_and_leg_forces_give_the_same_result():
    base = {"size": False, "B": 5, "h": 1.2, "a": 1.2, "cl": 0.3}
    kn = M.calculate({**base, "cases": [{"name": "c", "N": 19 * T, "M": 106.4 * T,
                                         "H": 4.9 * T, "Mt": 0}]}, CY)
    t = M.calculate({**base, "lunit": "t, t·m",
                     "cases_t": [{"name": "c", "N": 19, "M": 106.4, "H": 4.9, "Mt": 0}]}, CY)
    # the same crane given as leg forces along the diagonal: F1 = C, F3 = −T, F2 = F4 = N/4
    f = 106.4 / (math.sqrt(2) * 1.2)
    legs = M.calculate({**base, "lunit": "t, t·m", "input": "Forces on each leg",
                        "legs_t": [{"name": "c", "F1": 19 / 4 + f, "F2": 19 / 4, "F3": 19 / 4 - f,
                                    "F4": 19 / 4, "H": 4.9, "Mt": 0}]}, CY)
    for x, y, z in zip(kn.checks, t.checks, legs.checks):
        assert x.utilisation == pytest.approx(y.utilisation, rel=1e-6)
        assert x.utilisation == pytest.approx(z.utilisation, rel=1e-6)


def test_manufacturer_check_saez_s46():
    """Saez S46 4T, H = 23.9 m (P = 19 t, M = 106.4 t·m, T = 4.9 t), base 5 × 5 × 1.2 m as on the
    Saez built-in foundation drawing, allowable 1.6 kg/cm²: unfactored check by hand."""
    c = M.calculate({"size": False, "lunit": "t, t·m", "mfr": True, "qall": 1.6 * T * 10,
                     "cases_t": [{"name": "S46", "N": 19, "M": 106.4, "H": 4.9, "Mt": 0}],
                     "B": 5, "h": 1.2, "a": 1.2, "cl": 0.3, "fixing": EMB}, CY)
    V = 19 * T + 25 * 5 * 5 * 1.2
    Mk = 106.4 * T + 4.9 * T * 1.2
    e = Mk / V
    ecc = chk(c, "Manufacturer: (e_x/B)²")[0]
    assert ecc.demand == pytest.approx((e / 5) ** 2) and ecc.passed       # e ≤ B/3
    # peak pressure: the corner with M along the diagonal governs; along the axis
    # q = 2V / (3B(B/2 − e)) = 94 kN/m²
    q_axis = 2 * V / (3 * 5 * (2.5 - e))
    assert q_axis == pytest.approx(94.3, abs=0.5)
    q = chk(c, "Manufacturer: q_max")[0]
    assert q.demand * 1e3 > q_axis and q.passed
    assert q.capacity * 1e3 == pytest.approx(156.9, abs=0.1)
    # the Eurocode check with γ_Q = 1.5 on the whole M is stricter than the data sheet
    assert not chk(c, "DA2 eccentricity")[0].passed


def test_embedded_anchor_hand_calculation():
    c = M.calculate({"size": False, "lunit": "t, t·m", "fixing": EMB, "hemb": 1.1,
                     "cases_t": [{"name": "S46", "N": 19, "M": 106.4, "H": 4.9, "Mt": 0}],
                     "B": 5, "h": 1.2, "a": 1.2, "cl": 0.3, "cover": 40, "db": "16",
                     "dt": "12", "st": 200, "concrete": "C25/30"}, CY)
    # feet above the bottom bars: h ≥ 1100 + 40 + 2·16
    fits = chk(c, "Embedded anchor fits")[0]
    assert (fits.demand, fits.capacity) == (pytest.approx(1172), pytest.approx(1200))
    # leg force with M + H h_emb at the level of the feet
    f = (106.4 + 4.9 * 1.1) * T / (math.sqrt(2) * 1.2)
    assert out(c, "F_leg") == pytest.approx(1.35 * 19 * T / 4 + 1.5 * f, rel=1e-6)
    # bearing (6.7): b2 = min(c + (h − h_emb), 3c) = 400 mm → F_Rdu = A_c0 f_cd b2/b1
    assert out(c, "b_2") == pytest.approx(400)
    assert out(c, "F_Rdu") == pytest.approx(0.3**2 * 25 / 1.5 * 1e3 * 400 / 300, rel=1e-6)
    # pull-out: d_up = 1100 − 40 − 12; perimeters at 2 d_up
    dup = 1100 - 40 - 12
    assert out(c, "d_up") == pytest.approx(dup)
    tdiag = 1.5 * f - 19 * T / 4
    u1 = out(c, "u_up,1")
    assert u1 <= 4 * 300 + 4 * math.pi * dup + 1
    assert out(c, "v_up,1") == pytest.approx(tdiag * 1e3 / (u1 * dup), rel=1e-6)
    taxis = 1.5 * (106.4 + 4.9 * 1.1) * T / (2 * 1.2) - 19 * T / 4
    assert out(c, "v_up,2") == pytest.approx(2 * taxis * 1e3 / (out(c, "u_up,2") * dup),
                                             rel=1e-6)


def test_summary_answers_dimensions_reinforcement_punching():
    c = M.calculate(NOSIZE, CY)
    i = next(k for k, it in enumerate(c.items) if it.kind == "heading"
             and it.data["text"] == "Summary")
    table = next(it for it in c.items[i:] if it.kind == "table")
    assert [r[1] for r in table.data["rows"]] == ["OK", "OK", "OK"]
    assert any(it.kind == "text" and "not required" in it.data["text"] for it in c.items[i:i + 6])
    c = M.calculate(HEAVY, CY)
    texts = [it.data["text"] for it in c.items[:20] if it.kind == "text"]
    assert any("REQUIRED around the mast base" in t for t in texts)


def test_sizing_with_an_embedded_anchor():
    c = M.calculate({"lunit": "t, t·m", "fixing": EMB, "hemb": 1.1, "a": 1.2, "cl": 0.3,
                     "cases_t": [{"name": "S46", "N": 19, "M": 106.4, "H": 4.9, "Mt": 0}],
                     "B": 5, "h": 1.2}, CY)
    B, h = out(c, "B_min") * 1000, out(c, "h_min") * 1000
    assert h >= 1100 + 50 + 2 * 25          # the feet stay above the bottom bars
    inp = M.parse_inputs({"lunit": "t, t·m", "fixing": EMB, "hemb": 1.1, "a": 1.2, "cl": 0.3,
                          "cases_t": [{"name": "S46", "N": 19, "M": 106.4, "H": 4.9,
                                       "Mt": 0}]}, "en")
    assert M.passes(inp, B, h, get_annex("CY")) and not M.passes(inp, B - 100, h,
                                                                  get_annex("CY"))
