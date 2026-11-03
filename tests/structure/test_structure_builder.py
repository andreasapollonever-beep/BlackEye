"""Building generator: load take-down and slab distribution by hand."""

import pytest

from erisma.structure import analyse, modal
from erisma.structure.builder import BuildingSpec, build, tributary, y_label


def test_tributary_45_degree_rule():
    p = 0.01
    tri = tributary(4000, 6000, p)          # short edge: triangle, peak p·2000
    assert sum((x2 - x1) * (w1 + w2) / 2 for x1, x2, w1, w2 in tri) == pytest.approx(
        p * 4000 * 2000 / 2)
    trap = tributary(6000, 4000, p)         # long edge: trapezoid
    area = sum((x2 - x1) * (w1 + w2) / 2 for x1, x2, w1, w2 in trap)
    assert area == pytest.approx(p * (6000 + 2000) / 2 * 2000)
    # the four edges carry the whole panel
    assert 2 * area + 2 * p * 4000 * 2000 / 2 == pytest.approx(p * 4000 * 6000)


def test_grid_labels():
    assert [y_label(j) for j in (0, 1, 25, 26, 27)] == ["A", "B", "Z", "AA", "AB"]


def test_load_takedown_matches_hand_sum():
    sp = BuildingSpec([5000, 4000], [6000], [3200, 3000, 3000])
    m, info = build(sp)
    a = analyse(m)
    res = a.run_all()
    area = 9000 * 6000
    n_cols = 3 * 2
    h_tot = 9200
    cols = 25e-6 * 400 * 400 * h_tot * n_cols
    beam_len = (9000 * 2 + 6000 * 3) * 3
    beams = 25e-6 * 250 * (500 - 180) * beam_len
    slab = (25e-6 * 180 + 1.5e-3) * area * 3
    walls = 8.0 * (2 * 9000 + 2 * 6000) * 2
    G = sum(r[2] for r in res["G"].reactions.values())
    assert G == pytest.approx(cols + beams + slab + walls, rel=1e-9)
    Q = sum(r[2] for r in res["Q"].reactions.values())
    assert Q == pytest.approx(2e-3 * area * 3, rel=1e-9)
    assert res["G"].equilibrium_ok() and res["Q"].equilibrium_ok()
    md = modal(a, {"G": 1.0, "Q": 0.3})
    # all mass above the fixed base (the base half of the ground columns goes to the support)
    assert md.total_mass["X"] * 9810 < G + 0.3 * Q
    assert md.cumulative("X")[-1] > 0.9
