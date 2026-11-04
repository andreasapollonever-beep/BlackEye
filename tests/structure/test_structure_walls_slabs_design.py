"""Design-results data and check mode for walls and slabs; N–M interaction curve."""

import math

import pytest

from erisma.core import get_module
from erisma.structure.design import _nm_points


def test_nm_curve_end_points_by_hand():
    # 400×400, 8Ø16 (3 per face), C25/30: fcd = 16.67, fyd = 434.8 N/mm²
    fcd, fyd = 25 / 1.5, 500 / 1.15
    a = math.pi * 16**2 / 4
    bars = [(54, 3 * a), (200, 2 * a), (346, 3 * a)]
    pts = _nm_points(400, 400, bars, fcd, fyd)
    assert pts[0] == pytest.approx((-fyd * 8 * a / 1e3, 0.0))            # pure tension
    assert pts[-1][0] == pytest.approx((fcd * 400 * 400 + 400 * 8 * a) / 1e3)  # ε = 2 ‰
    # at N = 296 kN the EN 1992-1-1 column module gives M_Rd = 157 kNm for this section
    pts_s = sorted(pts)
    N = 296.46
    i = next(k for k in range(1, len(pts_s)) if pts_s[k][0] >= N)
    (n1, m1), (n2, m2) = pts_s[i - 1], pts_s[i]
    M = m1 + (m2 - m1) * (N - n1) / (n2 - n1)
    assert M == pytest.approx(157.0, rel=0.05)


@pytest.fixture(scope="module")
def base():
    return get_module("building_frame").calculate({}, {"annex": "CY"})


def test_wall_and_slab_results(base):
    ms = base.structure["members"]
    w = ms["W1.B1"]
    assert "web Ø10/200 + Ø12/150, hoops Ø10/85" in w["reinforcement"]
    assert w["outputs"]["h_cr"]["value"] > 0 and w["nm"]["points"]
    # the seismic situation is shown (largest moment), grouped under the module headings
    assert max(p["M"] for p in w["nm"]["points"]) == pytest.approx(
        next(c for c in w["checks"] if c["unit"] == "kNm")["demand"], rel=1e-6)
    assert len({c["section"] for c in w["checks"]}) >= 3
    s = ms["S1.A1"]
    assert s["outputs"]["m_x,span"]["value"] > 0
    assert len({c["section"] for c in s["checks"]}) >= 3


def test_check_mode_wall_and_slab():
    lay = {"reinf": {"W1.B1": {"nbe": 4, "dbe": "20", "sv": 150},
                     "S1.A1": {"dia_b": "8", "s_b": 300, "dia_t": "8", "s_t": 300}}}
    c = get_module("building_frame").calculate({"layout": lay}, {"annex": "CY"})
    ms = c.structure["members"]
    w, s = ms["W1.B1"], ms["S1.A1"]
    assert w["reinforcement"].startswith("2×4Ø20") and "Ø10/150" in w["reinforcement"]
    assert w["ok"] and w["detail"]["override"]
    assert s["reinforcement"] == "bottom Ø8/300, top Ø8/300"
    assert not s["ok"]                       # s ≤ min(2h, 250) fails
