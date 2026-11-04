"""Design-results window data and check mode (engineer's reinforcement), Tekla-style."""

import pytest

from erisma.core import get_module


@pytest.fixture(scope="module")
def auto():
    return get_module("building_frame").calculate({}, {"annex": "CY"})


def test_every_designed_member_lists_its_checks(auto):
    ms = auto.structure["members"]
    b = ms["B1.A1-A2"]
    secs = {c["section"] for c in b["checks"]}
    assert {"span", "support", "ec8"} <= secs
    assert any(c["ref"] == "EN 1992-1-1 7.4.2" for c in b["checks"])
    assert b["detail"]["top"]["n_bars"] >= 2 and b["detail"]["l_cr"] == 500
    # demand / capacity in display units (kNm, not N·mm)
    m = next(c for c in b["checks"] if c["section"] == "span" and c["unit"] == "kNm")
    assert m["demand"] == pytest.approx(b["detail"]["M_sag"], rel=1e-6)
    col = ms["C1.A1"]
    assert col["checks"] and all(c["ok"] for c in col["checks"]) == col["ok"]
    assert "combos" not in col["detail"]           # not sent to the page


def test_check_mode_beam_too_weak_fails_and_is_reported():
    lay = {"reinf": {"B1.A1-A2": {"bottom_n": 2, "bottom_dia": "10", "top_n": 2,
                                  "top_dia": "10"}}}
    c = get_module("building_frame").calculate({"layout": lay}, {"annex": "CY"})
    b = c.structure["members"]["B1.A1-A2"]
    assert b["reinforcement"].startswith("bottom 2Ø10, top 2Ø10")
    assert b["detail"]["override"] and not b["ok"] and b["util"] > 1
    assert any("check mode" in n for n in b["notes"])
    assert any(not ch["ok"] and ch["section"] == "support" for ch in b["checks"])


def test_check_mode_column_rechecks_all_combinations():
    lay = {"reinf": {"C1.A1": {"dia": "20", "nb": 3}}}
    c = get_module("building_frame").calculate({"layout": lay}, {"annex": "CY"})
    col = c.structure["members"]["C1.A1"]
    assert col["reinforcement"].startswith("8Ø20")
    assert col["ok"] and col["detail"]["override"]
