"""EN 1990 combinations and user load cases."""

import pytest

from erisma.core import get_module
from erisma.structure.combinations import Case, generate


def test_generated_combinations_en1990():
    cases = [Case("G", "G"), Case("Q", "Q", (0.7, 0.5, 0.3)), Case("S", "S", (0.5, 0.2, 0.0))]
    cb = {c.name: c for c in generate(cases, 1.35, 1.5)}
    assert cb["ULS 1"].factors == {"G": 1.35, "Q": 1.5, "S": pytest.approx(0.75)}
    assert cb["ULS 2"].factors == {"G": 1.35, "Q": pytest.approx(1.05), "S": 1.5}
    assert cb["SLS-qp"].factors == {"G": 1.0, "Q": 0.3, "S": 0.0}
    assert cb["SLS-freq 1"].factors == {"G": 1.0, "Q": 0.5, "S": 0.0}
    assert cb["Seismic G+ψ2Q"].factors == cb["SLS-qp"].factors
    only_g = generate([Case("G", "G")], 1.35, 1.5, [{"name": "U", "factors": {"G": 1.0, "X": 2}}])
    assert [c.name for c in only_g if c.kind in ("ULS", "user")] == ["ULS 1", "U"]
    assert only_g[-1].factors == {"G": 1.0}          # unknown cases are ignored


def test_user_loads_change_the_design_and_the_take_down():
    mod = get_module("building_frame")
    base = mod.calculate({"walls": [], "found_type": "Isolated pad footings", "seismic": False})
    loads = {"cases": [{"name": "G2", "type": "G", "loads": [
        {"kind": "area", "panels": "all", "storeys": "all", "q": 2.0},
        {"kind": "point", "points": ["B2"], "storeys": [1], "F": 100.0}]}],
        "combos": [{"name": "Heavy", "factors": {"G": 1.5, "G2": 1.5, "Q": 1.5}}]}
    c = mod.calculate({"walls": [], "found_type": "Isolated pad footings", "seismic": False,
                       "loads": loads})
    names = [x.name for x in c.combos]
    assert "Heavy" in names and "ULS 1" in names
    # Σ G2 = 2 kN/m² × plan area × storeys + 100 kN
    area = 14.5 * 10.0
    tot = sum(r[2] for r in c._res_agg["G"].reactions.values()) - \
        sum(r[2] for r in base._res_agg["G"].reactions.values())
    assert tot == pytest.approx((2.0 * area * 3 + 100) * 1e3, rel=1e-6)
    m = c.structure["members"]["C1.B2"]
    assert m["util"] > 0 and c.structure["combos"]
    with pytest.raises(Exception):
        mod.calculate({"loads": {"cases": [{"name": "G", "type": "G", "loads": []}]}})
