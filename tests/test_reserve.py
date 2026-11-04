"""Reserve factor λ and inverse solution — hand calculations and self-verification."""

import math

import pytest

from erisma import reserve as R
from erisma.core import get_module

CY = {"annex": "CY"}


def umax_of(mid, inputs, checks=None):
    c = get_module(mid).calculate(inputs, CY)
    return {k.description: k.utilisation for k in c.checks}


def test_search_finds_the_first_failure_of_a_non_monotonic_response():
    # passes below 2 and again between 3 and 5: the reserve is the FIRST failure (2), not 5
    br = R._search(lambda x: x < 2 or 3 < x < 5, 0.0, 8.0)
    assert br[0] < 2 <= br[1] and br[1] - br[0] <= 2 * R.TOL * 2
    assert R._search(lambda x: True, 0.0, 8.0) is None


@pytest.mark.parametrize("mid,check", [("ec3_steel_beam", "LTB: M_Ed ≤ M_b,Rd"),
                                       ("ec5_timber_beam", "w_net,fin ≤ L/250")])
def test_linear_checks_hand_calculation(mid, check):
    """For a check linear in the loads U(λ) = U0 + λ (U1 − U0), so λ = (1 − U0)/(U1 − U0).

    U0 (loads set to zero) keeps the self-weight that the program adds itself."""
    loads = [f for f, _ in R.LOADS[mid]]
    d = get_module(mid).defaults()
    U1 = umax_of(mid, d)[check]
    U0 = umax_of(mid, {**d, **{f: 0.0 for f in loads}})[check]
    lam = (1 - U0) / (U1 - U0)
    # linearity of the check itself, verified at λ = 2
    U2 = umax_of(mid, R.scaled(d, loads, 2.0))[check]
    assert U2 == pytest.approx(U0 + 2 * (U1 - U0), rel=1e-9)
    r = R.reserve(mid, {}, CY, ["G", "Q"])
    assert r["governing"] == check
    assert r["lam"] == pytest.approx(lam, rel=2 * R.TOL)


def test_steel_beam_self_weight_is_not_scaled():
    r = R.reserve("ec3_steel_beam", {}, CY, ["G", "Q"])
    u = max(umax_of("ec3_steel_beam", {}).values())
    assert r["lam"] > 1 / u  # the section self-weight stays constant


def test_load_independent_checks_are_excluded():
    r = R.reserve("ec7_pad_footing", {}, CY, ["G", "Q"])
    assert any("Minimum reinforcement" in d for d, _ in r["fixed"])
    assert r["governing"] == "Shear: V_Ed ≤ V_Rd,c"
    assert r["lam"] == pytest.approx(1.558, abs=2e-3)  # also found by hand bisection earlier


@pytest.mark.parametrize("mid", [m for m in R.LOADS if m != "ec7_slope_stability"])
def test_every_module_verifies_its_own_reserve(mid):
    r = R.reserve(mid, {}, CY, ["G", "Q", "E", "A"])
    if r.get("lam") is None:
        assert r["beyond"] >= 1000
        return
    v = r["verify"]
    assert v["at"]["umax"] <= 1 + 1e-9                          # passes at λ
    assert v["beyond"]["error"] or v["beyond"]["umax"] > 1      # fails just above
    assert (r["lam_fail"] - r["lam"]) <= R.TOL * r["lam_fail"] * 1.01
    # independent re-run of the calculation at λ: every load-dependent check passes
    loads = r["fields"]
    d = {**get_module(mid).defaults()}
    c = get_module(mid).calculate(R.scaled(d, loads, r["lam"]), CY)
    fixed = {f for f, _ in r["fixed"]}
    assert all(k.utilisation <= 1 + 1e-9 for k in c.checks if k.description not in fixed)


def test_inverse_numeric_choice_and_int():
    r = R.inverse("ec3_steel_beam", {}, CY, "L")
    hi = r["high"]
    assert hi and not hi["range_end"] and hi["value"] > 6.0
    ok = umax_of("ec3_steel_beam", {"L": hi["value"]})
    bad = umax_of("ec3_steel_beam", {"L": hi["fail_at"]})
    assert max(ok.values()) <= 1 + 1e-9 < max(bad.values())
    assert r["low"]["range_end"]               # no lower limit except the input range
    r = R.inverse("ec7_pad_footing", {}, CY, "phi")
    lo = r["low"]
    assert max(umax_of("ec7_pad_footing", {"phi": lo["value"]}).values()) <= 1 + 1e-9
    assert max(umax_of("ec7_pad_footing", {"phi": lo["fail_at"]}).values()) > 1
    assert r["high"] is None                   # passes up to the top of the range
    r = R.inverse("ec3_steel_beam", {}, CY, "section")
    assert "IPE 300" in r["passing"] and all(
        x["ok"] == (x["umax"] <= 1 + 1e-9) for x in r["rows"] if x["umax"] is not None)
    r = R.inverse("ec2_rc_beam", {}, CY, "n_bars")
    assert r["kind"] == "int" and r["min_pass"] is not None
    with pytest.raises(ValueError):
        R.reserve("ec1_imposed_loads", {}, CY, ["G"])


def test_reserve_api_and_licence(monkeypatch):
    from fastapi.testclient import TestClient

    from erisma import license as lic
    from erisma.web.app import app
    c = TestClient(app)
    sp = c.get("/api/modules/ec7_pad_footing/reserve?lang=el").json()
    assert sp["groups"] == ["G", "Q", "E"] and sp["group_labels"]["G"] == "Μόνιμα φορτία G"
    r = c.post("/api/modules/ec7_pad_footing/reserve", json={"mode": "loads", "groups": ["Q"]})
    assert r.status_code == 200 and math.isclose(r.json()["lam"], 2.66, abs_tol=0.01)
    r = c.post("/api/modules/ec7_pad_footing/reserve", json={"mode": "field", "field": "phi"})
    assert r.status_code == 200 and r.json()["low"]["value"] < 30
    monkeypatch.setattr(lic, "allowed", lambda: False)
    assert c.post("/api/modules/ec7_pad_footing/reserve", json={}).status_code == 402
