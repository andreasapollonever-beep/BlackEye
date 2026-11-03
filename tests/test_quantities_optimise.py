"""Quantities, cost estimate and the automatic design search."""

import json
import math

import pytest

from erisma.core import all_modules, get_module
from erisma.optimize import SPECS, optimise, spec


def test_pad_footing_quantities_by_hand():
    q = get_module("ec7_pad_footing").calculate({}).quantities
    rows = {r["item"]: r["qty"] for r in q["rows"]}
    assert rows["concrete"] == pytest.approx(2.4 * 2.4 * 0.6)
    As = math.pi * 14**2 / 4 * 2400 / 150          # bars Ø14/150 across 2.4 m
    assert rows["rebar"] == pytest.approx(2 * As * 2400 * 1e-9 * 7850)


def test_custom_prices_change_the_cost():
    m = get_module("ec3_steel_beam")
    base = m.calculate({}).quantities
    dear = m.calculate({}, {"prices": json.dumps({"steel": 6.4})}).quantities
    assert dear["total"] == pytest.approx(2 * base["total"])


def test_every_spec_refers_to_existing_fields():
    for mid, vs in SPECS.items():
        names = {f.name for f in get_module(mid).fields}
        assert all(v["name"] in names for v in vs), mid


def test_optimiser_finds_cheaper_passing_steel_beam():
    r = optimise("ec3_steel_beam", {}, {}, spec("ec3_steel_beam"))
    assert r["passed"] and r["cost"] <= r["start_cost"]
    c = get_module("ec3_steel_beam").calculate(r["best"])
    assert c.passed


def test_optimiser_reports_no_solution():
    r = optimise("ec2_rc_beam", {"MEd": 5000}, {}, [{"name": "h", "lo": 250, "hi": 300, "step": 25}])
    assert not r["passed"]


def test_quantities_never_break_a_module():
    for m in all_modules():
        c = m.calculate({})
        assert c.quantities is None or c.quantities["total"] >= 0
