import math

import pytest
from fastapi.testclient import TestClient

from blackeye.core import InputError, get_module
from blackeye.web.app import app

client = TestClient(app)


# ------------------------------------------------------------ slope (Bishop)
@pytest.mark.parametrize("depth,Ns", [(20, 0.181), (0, 0.133)])
def test_bishop_matches_taylor_chart_for_clay(depth, Ns):
    """φ = 0 clay, β = 30°: Taylor stability numbers (deep base failure / firm base at toe)."""
    c = get_module("ec7_slope_stability").calculate(
        {"c": 20, "phi": 0, "gamma": 20, "H": 5, "slope": 30, "q": 0, "seismic": False,
         "depth_firm": depth})
    assert c.values["F_k"] == pytest.approx(20 / (Ns * 20 * 5), rel=0.03)


def test_slope_cohesionless_close_to_infinite_slope():
    c = get_module("ec7_slope_stability").calculate(
        {"c": 0, "phi": 30, "slope": 25, "q": 0, "seismic": False})
    inf = math.tan(math.radians(30)) / math.tan(math.radians(25))
    assert inf <= c.values["F_k"] <= inf * 1.08


def test_slope_design_factor_below_characteristic():
    v = get_module("ec7_slope_stability").calculate({}).values
    assert v["F_d,E"] < v["F_d"] < v["F_k"]


# ------------------------------------------------------------ pad footing
def test_footing_defaults_pass_and_punching_hand_calc():
    c = get_module("ec7_pad_footing").calculate({})
    assert c.passed
    v = c.values
    d = ((600 - 50 - 7) + (600 - 50 - 14 - 7)) / 2
    V = 1.35 * 700e3 + 1.5 * 300e3
    a = v["a_crit"]
    A = 400 * 400 + 2 * a * 800 + math.pi * a**2
    Vred = V - V / 2400**2 * A
    assert v["V_Ed,red"] == pytest.approx(Vred, rel=1e-6)
    u = 1600 + 2 * math.pi * a
    assert v["v_Ed"] == pytest.approx(v["β"] * Vred / (u * d), rel=1e-6)


def test_footing_thin_fails_with_hint():
    c = get_module("ec7_pad_footing").calculate({"h": 0.4})
    failing = [ch for ch in c.checks if not ch.passed]
    assert failing and all(ch.hint for ch in failing)


def test_footing_bearing_shape_factors():
    c = get_module("ec7_pad_footing").calculate({"seismic": False, "approach": "DA2"})
    phi = math.radians(30)
    assert c.values["s_q"] == pytest.approx(1 + c.values["B'"] / c.values["L'"] * math.sin(phi)
                                            if c.values["B'"] <= c.values["L'"] else
                                            1 + c.values["L'"] / c.values["B'"] * math.sin(phi))


def test_footing_invalid_depth_points_to_field():
    with pytest.raises(InputError) as e:
        get_module("ec7_pad_footing").calculate({"D": 0.3})
    assert e.value.field == "D"


# ------------------------------------------------------------ gravity wall
def test_gravity_wall_defaults_pass_and_has_3d():
    c = get_module("ec7_gravity_wall").calculate({})
    assert c.passed
    assert c.model3d["kind"] == "retaining_wall"


def test_gravity_wall_invalid_geometry():
    with pytest.raises(InputError) as e:
        get_module("ec7_gravity_wall").calculate({"b_top": 3})
    assert e.value.field == "B_body"


# ------------------------------------------------------------ language & API
def test_greek_report_and_schema():
    r = client.post("/api/modules/ec7_retaining_wall/run", json={"inputs": {}, "lang": "el"})
    assert r.status_code == 200
    html = r.json()["html"]
    assert "ΕΠΑΡΚΕΙ" in html and "Ενεργητική ώθηση" in html
    s = client.get("/api/modules/ec7_pad_footing?lang=el").json()
    assert s["title"] == "Μεμονωμένο πέδιλο"


def test_api_error_names_field():
    r = client.post("/api/modules/ec3_steel_beam/run", json={"inputs": {"L": -1}, "lang": "el"})
    assert r.status_code == 422
    d = r.json()["detail"]
    assert d["field"] == "L" and "Άνοιγμα" in d["message"]


def test_failing_checks_carry_hints_in_summary():
    r = client.post("/api/modules/ec7_retaining_wall/run",
                    json={"inputs": {"toe": 0.2, "heel": 0.8}})
    fails = [c for c in r.json()["summary"]["checks"] if not c["passed"]]
    assert fails and all(c["hint"] for c in fails)
