"""Projects: links between calculations, dependency order, cycles, combined report."""

import pytest

from erisma.project import ProjectError, _order, project_report, run_project


def _doc(links=None):
    return {"project": {"project": "Test house", "annex": "CY"}, "calcs": [
        {"uid": "f", "module": "ec7_pad_footing", "name": "Footing F1", "inputs": {},
         "links": links or {}},
        {"uid": "c", "module": "ec2_rc_column", "name": "Column C1",
         "inputs": {"NEd": 1500}, "links": {}},
    ]}


def test_link_transfers_value_with_unit_conversion():
    r = run_project(_doc({"NG": {"from": "c", "symbol": "N_Ed"}}))["results"]
    assert r["f"]["links"]["NG"]["ok"]
    assert r["f"]["inputs"]["NG"] == pytest.approx(1500.0)   # kN → kN
    # the column runs first although it is listed second
    assert "summary" in r["c"] and "summary" in r["f"]


def test_link_factor_and_incompatible_units():
    r = run_project(_doc({"NG": {"from": "c", "symbol": "N_Ed", "factor": 1 / 1.35}}))["results"]
    assert r["f"]["inputs"]["NG"] == pytest.approx(1500 / 1.35)
    r = run_project(_doc({"NG": {"from": "c", "symbol": "λ_h"}}))["results"]
    assert not r["f"]["links"]["NG"]["ok"]


def test_cycle_is_reported():
    calcs = [{"uid": "a", "links": {"x": {"from": "b"}}}, {"uid": "b", "links": {"y": {"from": "a"}}}]
    with pytest.raises(ProjectError):
        _order(calcs)
    assert "error" in run_project({"calcs": calcs})


def test_project_report_has_cover_contents_and_all_sheets():
    html = project_report(_doc(), "el")
    assert "Test house" in html and 'id="c1"' in html and 'id="c2"' in html
    assert "Περιεχόμενα" in html or "Contents" in html
