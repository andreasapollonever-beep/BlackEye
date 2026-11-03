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
    assert calc.max_utilisation == pytest.approx(d.utilisation)
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
