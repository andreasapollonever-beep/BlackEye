import math

import pytest
from fastapi.testclient import TestClient

from blackeye.cli import main
from blackeye.core import InputError, all_modules, get_module
from blackeye.report import render_html
from blackeye.sections.steel import get_section
from blackeye.web.app import app


@pytest.mark.parametrize("name,A,Iy,Wpl,It", [
    ("IPE 300", 53.81, 8356, 628.4, 20.12),
    ("HEA 200", 53.83, 3692, 429.5, 20.98),
    ("HEB 300", 149.1, 25170, 1869, 185.0),
])
def test_section_properties_match_tables(name, A, Iy, Wpl, It):
    s = get_section(name)
    assert s.A / 1e2 == pytest.approx(A, rel=2e-3)
    assert s.Iy / 1e4 == pytest.approx(Iy, rel=2e-3)
    assert s.Wpl_y / 1e3 == pytest.approx(Wpl, rel=2e-3)
    assert s.It / 1e4 == pytest.approx(It, rel=5e-3)


@pytest.mark.parametrize("mod", [m.id for m in all_modules()])
def test_every_module_runs_with_defaults_and_renders(mod):
    calc = get_module(mod).calculate({})
    html = render_html(calc)
    assert "<html" in html and calc.title in html


def test_ec3_hand_calc():
    c = get_module("ec3_steel_beam").calculate({"Lcr": 0, "gk": 0, "qk": 10,
                                                "gamma_G": 1.0, "gamma_Q": 1.0})
    v = c.values
    s = get_section("IPE 300")
    w = 10 + s.mass * 9.81e-3
    assert v["M_Ed"] == pytest.approx(w * 6000**2 / 8, rel=1e-4)
    assert v["M_c,Rd"] == pytest.approx(s.Wpl_y * 275, rel=1e-9)
    # SN003 / published value: Mcr ≈ 90.5 kNm for IPE300, L = 6 m, C1 = 1.0
    assert v["M_cr"] / v["C_1"] / 1e6 == pytest.approx(90.5, rel=0.01)


def test_ec2_hand_calc():
    c = get_module("ec2_rc_beam").calculate({"MEd": 140, "b": 300, "h": 500})
    v = c.values
    d = 500 - 30 - 8 - 8
    assert v["d"] == pytest.approx(d)
    mu = 140e6 / (300 * d**2 * 25 / 1.5)
    assert v["μ"] == pytest.approx(mu)
    z = d * (1 - 0.4 * 1.25 * (1 - math.sqrt(1 - 2 * mu)))
    assert v["A_s,req"] == pytest.approx(140e6 / (500 / 1.15 * z))


def test_ec2_high_moment_needs_compression_steel():
    c = get_module("ec2_rc_beam").calculate({"MEd": 900})
    assert not c.passed and c.values["A_s2,req"] > 0


def test_invalid_input_rejected():
    with pytest.raises(InputError):
        get_module("ec3_steel_beam").calculate({"L": -1})
    with pytest.raises(InputError):
        get_module("ec3_steel_beam").calculate({"section": "XYZ"})


def test_api_roundtrip():
    client = TestClient(app)
    mods = client.get("/api/modules").json()
    assert {m["id"] for m in mods} >= {"ec3_steel_beam", "ec2_rc_beam", "beam_analysis"}
    r = client.post("/api/modules/ec3_steel_beam/run",
                    json={"inputs": {"section": "IPE 360"}, "project": {"job_no": "J1"}})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["passed"] is True and "J1" in body["html"]
    assert client.post("/api/modules/beam_analysis/run",
                       json={"inputs": {"supports": [{"x": 0, "kind": "pinned"}]}}
                       ).status_code == 422
    assert client.get("/api/modules/nope").status_code == 404
    assert client.get("/").status_code == 200


def test_cli(tmp_path, capsys):
    out = tmp_path / "r.html"
    assert main(["run", "ec2_rc_beam", "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")
