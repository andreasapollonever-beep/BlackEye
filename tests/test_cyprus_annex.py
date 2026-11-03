"""Cyprus National Annex — values checked against the CYS documents (see design/annex.py)."""

import math

import pytest
from fastapi.testclient import TestClient

from erisma.core import get_module
from erisma.design.annex import CY, get_annex
from erisma.report import render_html
from erisma.web.app import app

CYP = {"annex": "CY"}


def test_cyprus_values():
    assert CY.combinations("National Annex") == ["DA2"]
    gu, gf, gq, gphi, gc, gRv, gRh = CY.combos["DA2"]
    assert (gu, gf, gq, gphi, gc, gRv, gRh) == (1.35, 1.0, 1.5, 1.0, 1.0, 1.4, 1.1)
    assert CY.gRe("DA2") == 1.4 and CY.slope_gRe == 1.1
    assert CY.equ[:3] == (1.10, 0.90, 1.50)
    assert (CY.gamma_c, CY.gamma_s, CY.alpha_cc, CY.alpha_cc_pl) == (1.5, 1.15, 1.0, 0.8)
    assert CY.punch_vmax == 0.5 and CY.anchor_sls_factor == 1.35
    assert dict(CY.zones) == {"Zone 1": 0.15, "Zone 2": 0.20, "Zone 3": 0.25}


def test_wall_uses_only_DA2_and_reports_annex():
    c = get_module("ec7_retaining_wall").calculate({"seismic": False}, CYP)
    names = [ch.description.split(" ")[0] for ch in c.checks if "sliding" in ch.description]
    assert names == ["DA2"]
    html = render_html(c)
    assert "Cyprus (CYS National Annexes)" in html and "National Annex parameters used" in html


def test_wall_warns_when_approach_overridden():
    c = get_module("ec7_retaining_wall").calculate({"approach": "DA1"}, CYP)
    assert any("requires DA2" in w for w in c.warnings)


def test_footing_punching_vmax_is_half_nu_fcd():
    en = get_module("ec7_pad_footing").calculate({}, {"annex": "EN"}).values["v_Rd,max"]
    cy = get_module("ec7_pad_footing").calculate({}, CYP).values["v_Rd,max"]
    assert cy / en == pytest.approx(0.5 / 0.4)
    fck = 25
    assert cy == pytest.approx(0.5 * 0.6 * (1 - fck / 250) * fck / 1.5)


def test_berlin_anchor_load_at_least_135_Pk():
    c = get_module("ec7_berlin_wall").calculate({"seismic": False}, CYP)
    v = c.values
    assert v["A_d"] == pytest.approx(max(v["P_d"], 1.35 * v["P_k"]))


def test_slope_DA2_effects_with_gRe_11():
    c = get_module("ec7_slope_stability").calculate({"seismic": False}, CYP)
    v = c.values
    assert v["F_d"] == pytest.approx(v["F'"] / (1.35 * 1.1))


def test_api_lists_cyprus_zones():
    r = TestClient(app).get("/api/annexes?lang=el").json()
    cy = next(a for a in r if a["code"] == "CY")
    assert [z["ag"] for z in cy["zones"]] == [0.15, 0.20, 0.25]
    assert cy["zones"][0]["label"] == "Ζώνη 1"
    assert get_annex("XX").code == "EN"  # unknown → EN
