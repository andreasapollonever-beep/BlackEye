import math

import pytest
from fastapi.testclient import TestClient

from erisma.core import InputError, get_module
from erisma.design.ec2 import section_capacity
from erisma.design.geotech import (bearing_factors, k_mononobe_okabe, ka_coulomb,
                                     poly_props)
from erisma.web.app import app

WALL = get_module("ec7_retaining_wall")


def test_coulomb_reduces_to_rankine():
    phi = math.radians(30)
    assert ka_coulomb(phi, 0, 0) == pytest.approx(1 / 3, rel=1e-9)


def test_mononobe_okabe_static_limit_and_increase():
    phi, beta = math.radians(30), math.radians(10)
    assert k_mononobe_okabe(phi, beta, beta, 0.0) == pytest.approx(ka_coulomb(phi, beta, beta))
    assert k_mononobe_okabe(phi, 0, 0, math.radians(5)) > ka_coulomb(phi, 0, 0)


def test_bearing_factors_ec7():
    Nq, Nc, Ng = bearing_factors(math.radians(30))
    assert (Nq, Nc, Ng) == (pytest.approx(18.40, abs=0.01), pytest.approx(30.14, abs=0.01),
                            pytest.approx(20.09, abs=0.01))


def test_polygon_centroid():
    a, cx, cz = poly_props([(0, 0), (2, 0), (0, 3)])
    assert (a, cx, cz) == (pytest.approx(3), pytest.approx(2 / 3), pytest.approx(1))


def test_wall_sliding_hand_calc():
    c = WALL.calculate({"seismic": False, "q": 0, "beta": 0, "h_w": 0, "approach": "DA2"})
    hv = 4.5e3
    Ka = 1 / 3
    H = 1.35 * 0.5 * 18e-6 * Ka * hv**2  # N/mm == kN/m
    assert c.values["H_d"] == pytest.approx(H, rel=1e-6)
    # vertical (favourable): stem + base + backfill + front soil + Pa sin δ (δ = 0)
    B, tb = 3.6e3, 500.0
    W = 25e-6 * (0.25e3 * 4e3 + 0.5 * 0.15e3 * 4e3 + B * tb) + 18e-6 * 2.2e3 * 4e3 + \
        18e-6 * 0.15e3 * 4e3 / 2 + 19e-6 * 1.0e3 * 0.5e3
    R = W * math.tan(math.radians(32)) / 1.1
    assert c.values["R_h,d"] == pytest.approx(R, rel=1e-6)


def test_wall_defaults_pass_and_model():
    c = WALL.calculate({})
    assert c.passed, [(x.description, x.utilisation) for x in c.checks if not x.passed]
    m = c.model3d
    assert m["kind"] == "retaining_wall"
    keys = {l["key"] for l in m["layers"]}
    assert keys >= {"concrete", "soil", "earth", "surcharge", "seismic", "bearing", "forces"}
    assert any(o["t"] == "arrow" and o["layer"] == "bearing" for o in m["objects"])


def test_wall_water_and_slope_run():
    c = WALL.calculate({"h_w": 2.0, "beta": 15})
    assert any(o["layer"] == "water" and o["t"] == "arrow" for o in c.model3d["objects"])


def test_wall_invalid_geometry():
    with pytest.raises(InputError):
        WALL.calculate({"t_top": 0.5, "t_bot": 0.3})


def test_api_returns_3d_model():
    r = TestClient(app).post("/api/modules/ec7_retaining_wall/run", json={"inputs": {}})
    assert r.status_code == 200 and r.json()["model3d"]["kind"] == "retaining_wall"
    assert TestClient(app).get("/static/vendor/three/three.module.min.js").status_code == 200


def test_doubly_reinforced_beam():
    c = get_module("ec2_rc_beam").calculate(
        {"MEd": 380, "n_bars": 4, "dia": "25", "n_comp": 3, "dia_comp": "16"})
    v = c.values
    d, d2 = 500 - 30 - 8 - 12.5, 30 + 8 + 8
    fcd, fyd = 25 / 1.5, 500 / 1.15
    Mlim = 0.8 * 0.45 * (1 - 0.18) * 300 * d**2 * fcd
    assert v["M_lim"] == pytest.approx(Mlim)
    As2 = (380e6 - Mlim) / (fyd * (d - d2))
    assert v["A_s2,req"] == pytest.approx(As2)
    MRd, x = section_capacity(300, d, 4 * math.pi * 25**2 / 4, fcd, fyd, d2,
                              3 * math.pi * 16**2 / 4)
    assert v["M_Rd"] == pytest.approx(MRd)


# ------------------------------------------------------------ stem step & shear key
from erisma.modules.ec7_retaining_wall import CantileverGeometry  # noqa: E402


def test_stepped_stem_geometry_and_checks():
    inp = WALL.parse_inputs({"step": True, "h_step": 1.5, "t_low": 0.55})
    g = CantileverGeometry(inp)
    a, _, _ = poly_props(g.stem_poly)
    assert a / 1e6 == pytest.approx(0.55 * 1.5 + (0.40 + 0.25) / 2 * 2.5)
    a, _, _ = poly_props(g.back_soil)  # soil on the ledge of the step is included
    assert a / 1e6 == pytest.approx(2.2 * 4 + 0.15 * 2.5 + 0.15 * 2.5 / 2)
    assert g.B == pytest.approx(1000 + 550 + 2200)
    c = WALL.calculate({"step": True})
    titles = [i.data["text"] for i in c.items if i.kind == "heading"]
    assert any("step" in t for t in titles)


def test_shear_key_adds_rankine_passive_to_sliding():
    c0 = WALL.calculate({"seismic": False, "approach": "DA2"})
    c1 = WALL.calculate({"seismic": False, "approach": "DA2", "key": True, "key_h": 0.5})
    phi = math.radians(32)
    Kp = math.tan(math.pi / 4 + phi / 2) ** 2
    D1, D2 = 500.0, 1000.0
    Pp = 0.5 * Kp * 19e-6 * (D2**2 - D1**2) / 1.4  # γ_R,e = 1.4 in DA2
    assert c1.values["K_p"] == pytest.approx(Kp)
    assert c1.values["P_p,key"] == pytest.approx(Pp)
    assert c1.values["R_h,d"] > c0.values["R_h,d"]
    assert any(o["layer"] == "key" for o in c1.model3d["objects"])


def test_shear_key_outside_base_rejected():
    with pytest.raises(InputError) as e:
        WALL.calculate({"key": True, "key_x": 9})
    assert e.value.field == "key_x"
