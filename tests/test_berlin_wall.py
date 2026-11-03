import math

import numpy as np
import pytest

from erisma.core import InputError, get_module
from erisma.design.geotech import ka_coulomb, kp_coulomb
from erisma.modules.ec7_berlin_wall import BerlinWallEC7 as BW

CB = {"name": "char", "gG": 1.0, "gQ": 1.0, "gphi": 1.0, "gc": 1.0, "gRe": 1.0, "seis": None}


def _inp(**kw):
    d = {"H": 5000.0, "a": 2000.0, "gamma": 19e-6, "q": 0.0, "c": 0.0, "delta_a": 0.0,
         "delta_p": 0.0, "z_a": 1500.0}
    d.update(kw)
    return d


def _coeffs(phi=32):
    p = math.radians(phi)
    return ka_coulomb(p, 0, 0), kp_coulomb(p, 0)


def test_blum_cantilever_matches_closed_form_for_continuous_wall():
    """b = b_p = a → continuous wall: Ka (H + t)³ = Kp t³ about the toe."""
    inp = _inp()
    Ka, Kp = _coeffs()
    r = BW._combination(None, inp, CB, False, inp["a"], inp["a"], math.radians(32))
    t0 = inp["H"] / ((Kp / Ka) ** (1 / 3) - 1)
    assert r["t0"] == pytest.approx(t0, rel=2e-3)
    assert r["t_req"] == pytest.approx(1.2 * r["t0"])


def test_free_earth_support_matches_closed_form():
    inp = _inp()
    Ka, Kp = _coeffs()
    H, zA = inp["H"], inp["z_a"]
    r = BW._combination(None, inp, CB, True, inp["a"], inp["a"], math.radians(32))
    # Ka[D³/3 − zA D²/2] = Kp[t³/3 + (H − zA) t²/2], D = H + t
    def f(t):
        D = H + t
        return Ka * (D**3 / 3 - zA * D**2 / 2) - Kp * (t**3 / 3 + (H - zA) * t**2 / 2)
    lo, hi = 1.0, 3 * H
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    assert r["t0"] == pytest.approx(lo, rel=2e-3)
    # horizontal equilibrium: anchor = active − passive
    g, a, t = inp["gamma"], inp["a"], r["t0"]
    A = a * g * (Ka * (H + t) ** 2 / 2 - Kp * t**2 / 2)
    assert r["A"] == pytest.approx(A, rel=5e-3)
    # the pinned toe reaction of the beam model is ~0 at limit equilibrium
    assert abs(r["Vz"][-1]) < 0.02 * r["A"]


def test_defaults_pass_and_3d():
    c = get_module("ec7_berlin_wall").calculate({})
    assert c.passed, [(x.description, x.utilisation) for x in c.checks if not x.passed]
    layers = {l["key"] for l in c.model3d["layers"]}
    assert {"steel", "lagging", "anchors", "active", "passive", "moment"} <= layers


def test_cantilever_needs_more_and_hints():
    c = get_module("ec7_berlin_wall").calculate({"support": "Cantilever"})
    fails = [x for x in c.checks if not x.passed]
    assert fails and all(x.hint for x in fails)


def test_anchor_below_excavation_rejected():
    with pytest.raises(InputError) as e:
        get_module("ec7_berlin_wall").calculate({"z_a": 6})
    assert e.value.field == "z_a"


def test_passive_width_limited_by_spacing():
    c = get_module("ec7_berlin_wall").calculate({"a": 0.6, "section": "HEB 240"})
    assert c.values["b_p"] == pytest.approx(600.0)
