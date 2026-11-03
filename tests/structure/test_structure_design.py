"""Automatic member design from the 3D analysis."""

import pytest

from erisma.core import get_module
from erisma.structure import analyse, modal
from erisma.structure.builder import BuildingSpec, build
from erisma.structure.design import design_beams, design_columns
from erisma.structure.modal import ec8_spectrum
from erisma.structure.seismic import seismic_check


@pytest.fixture(scope="module")
def frame():
    sp = BuildingSpec([5000, 4500], [5000], [3200, 3000])
    m, info = build(sp)
    a = analyse(m)
    res = a.run_all()
    md = modal(a, {"G": 1, "Q": 0.3})
    seis = seismic_check(a, md, ec8_spectrum(0.16, "B", 3.9))
    uls = a.combine(res, {"G": 1.35, "Q": 1.5})
    quasi = a.combine(res, {"G": 1.0, "Q": 0.3})
    return sp, info, res, seis, uls, quasi


def test_columns_are_designed_and_reproducible(frame):
    sp, info, res, seis, uls, quasi = frame
    cols = {c: (int(c[1]), sp.heights[int(c[1]) - 1]) for c in info["columns"]}
    out = design_columns(res, seis, uls, quasi, 400, 400, 500, "C25/30", cols)
    assert len(out) == len(cols) and all(d.ok for d in out)
    # the governing combination re-run in the column module passes, as reported
    d = max(out, key=lambda d: d.utilisation)
    calc = get_module("ec2_rc_column").calculate(d.inputs)
    assert calc.passed
    strength = max(k.utilisation for k in calc.checks if not k.is_min)
    assert strength == pytest.approx(d.utilisation)
    assert 0.01 <= d.rho <= 0.04  # EN 1998-1 5.4.3.2.2(1)
    # ULS axial force of a ground column = its share of the load take-down
    f = uls.forces("C1.A1", 2)
    assert -f["N"][0] > 0


def test_beams_are_designed_with_seismic_rules(frame):
    sp, info, res, seis, uls, quasi = frame
    beams = {b: int(b[1]) for b in info["beams_x"] + info["beams_y"]}
    out = design_beams(beams, seis, uls, quasi, 250, 500, "C25/30")
    assert all(d.ok for d in out)
    assert all("ends Ø8/" in d.reinforcement for d in out)


def test_undersized_column_gets_a_clear_hint(frame):
    sp, info, res, seis, uls, quasi = frame
    out = design_columns(res, seis, uls, quasi, 200, 200, 500, "C20/25",
                         {"C1.B1": (1, 3200)})
    assert not out[0].ok
    assert "increase the column size" in out[0].notes[-1]


def test_walls_capacity_design_and_pdelta_in_the_module():
    from erisma.structure.builder import BuildingSpec, build
    from erisma.structure.design import capacity_design, design_walls

    sp = BuildingSpec([5000, 5000], [5000], [3000, 3000, 3000],
                      walls=[{"at": "A2", "dir": "X", "L": 2000, "t": 250}])
    m, info = build(sp)
    assert "W1.A2" in m.members and "C1.A2" not in m.members
    assert m.members["B1.A1-A2"].offset_j == 1000 and m.members["B1.A2-A3"].offset_i == 1000
    a = analyse(m)
    res = a.run_all()
    assert res["G"].equilibrium_ok()
    md = modal(a, {"G": 1, "Q": 0.3})
    seis = seismic_check(a, md, ec8_spectrum(0.24, "B", 3.6))
    uls = a.combine(res, {"G": 1.35, "Q": 1.5})
    quasi = a.combine(res, {"G": 1.0, "Q": 0.3})
    dw = design_walls({"W1.A2": info["wall_spec"]["A2"]}, seis, uls, quasi, "C25/30",
                      sp.heights, 500)
    assert dw[0].ok and get_module("ec8_rc_wall").calculate(dw[0].inputs).passed
    cols = {c: (int(c[1]), 3000) for c in info["columns"]}
    dc = design_columns(res, seis, uls, quasi, 400, 400, 500, "C25/30", cols)
    beams = {b: int(b[1]) for b in info["beams_x"] + info["beams_y"]}
    db = design_beams(beams, seis, uls, quasi, 250, 500, "C25/30")
    joints = [{"node": "B2@1", "dir": "X", "cols": ["C1.B2", "C2.B2"],
               "beams": ["B1.B1-B2", "B1.B2-B3"]}]
    out = capacity_design(dc, db, joints, quasi, seis, (400, 400), (250, 500), "C25/30")
    assert out[0].ok and out[0].ratio >= 1.3


def test_module_variants_run():
    mod = get_module("building_frame")
    assert mod.calculate({"walls": [], "pdelta": True}).checks
    with pytest.raises(Exception):
        mod.calculate({"walls": [{"at": "Z9", "dir": "X", "L": 2, "t": 250}]})
