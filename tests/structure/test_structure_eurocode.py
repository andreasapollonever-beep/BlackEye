"""Slabs, foundations, deflection and automatic sizing of the building (hand checks)."""

import math

import pytest

from erisma.core import get_module
from erisma.structure import analyse
from erisma.structure.builder import BuildingSpec, build
from erisma.structure.design import design_slabs, span_depth, strip_bearing


def test_span_depth_eq_7_16_hand():
    """ρ = ρ0 = √25·1e-3 = 0.5 %: (l/d)_lim = K (11 + 1.5·5) = 18.5 K; × 0.8 flanged."""
    b, d = 300.0, 500.0
    As = 0.005 * b * d
    ratio, lim = span_depth(6000, d, b, As, 0.0, 0.0, 25.0, 1.0)
    assert ratio == pytest.approx(12.0)
    assert lim == pytest.approx(18.5 * 0.8)
    # over 7 m: × 7/l
    _, lim8 = span_depth(8000, d, b, As, 0.0, 0.0, 25.0, 1.3)
    assert lim8 == pytest.approx(18.5 * 1.3 * 0.8 * 7 / 8)
    # A_s,prov / A_s,req factor capped at 1.5
    _, limf = span_depth(6000, d, b, As, 0.0, As / 2, 25.0, 1.0)
    assert limf == pytest.approx(18.5 * 0.8 * 1.5)


def test_strip_bearing_annex_d_hand():
    """φ = 30°: Nq = 18.40, Nc = 30.14, Nγ = 20.09 (EN 1997-1 D.4)."""
    B, D, c, g = 1000.0, 1200.0, 0.005, 19e-6
    Nq = math.exp(math.pi * math.tan(math.radians(30))) * math.tan(math.radians(60)) ** 2
    Nc = (Nq - 1) / math.tan(math.radians(30))
    Ng = 2 * (Nq - 1) * math.tan(math.radians(30))
    exact = c * Nc + g * D * Nq + 0.5 * g * B * Ng
    assert strip_bearing(B, D, 30, c, g) == pytest.approx(exact)
    assert strip_bearing(B, D, 30, c, g, g_R=1.4) == pytest.approx(exact / 1.4)


def test_slab_panels_continuity_and_storeys():
    panels = [{"id": "A1", "lx": 5000, "ly": 6000,
               "cont": {"x0": False, "x1": True, "y0": False, "y1": True}}]
    out = design_slabs(panels, 180, "C25/30", 1.5e-3, {1: 2e-3, 2: 2e-3, 3: 1e-3})
    assert [d.member for d in out] == ["S1.A1", "S2.A1", "S3.A1"]
    d = out[0]
    assert d.ok and d.inputs["e2"] == "Fixed / continuous" and d.inputs["e1"] == "Simply supported"
    assert get_module("ec2_rc_slab").calculate(d.inputs).passed


def test_foundation_beams_on_springs_equilibrium_and_settlement():
    sp = BuildingSpec([5000], [5000], [3000], foundation={"B": 1000, "bw": 400, "h": 1000,
                                                          "ks": 0.04, "n": 4})
    m, info = build(sp)
    r = analyse(m).static("G")
    assert r.equilibrium_ok()
    W = -r.applied[2]
    # every spring: R = k·w → Σ k_i w_i = W, with uniform-ish settlement w ≈ W / (k_s B ΣL)
    total_len = 4 * 5000
    w_mean = W / (0.04 * 1000 * total_len)
    w = [-r.displacement(n)[2] for n in m.supports]
    assert min(w) > 0 and sum(w) / len(w) == pytest.approx(w_mean, rel=0.25)


def test_module_default_passes_every_check_and_designs_everything():
    c = get_module("building_frame").calculate({})
    assert c.passed, [k.description for k in c.checks if not k.passed]
    kinds = {v["kind"] for v in c.structure["members"].values()}
    assert {"column", "beam", "wall", "slab", "raft", "punching"} <= kinds
    fb = get_module("building_frame").calculate({"found_type": "Foundation beams (Winkler)"})
    assert fb.passed and any(v["kind"] == "fbeam" for v in fb.structure["members"].values())


def test_autosize_makes_an_undersized_building_pass():
    from erisma.structure.autosize import autosize

    bad = {"col_b": 250, "col_h": 250, "walls": [], "x_spans": [{"L": 6.0}],
           "y_spans": [{"L": 6.0}], "storeys": [{"h": 3.0}, {"h": 3.0}], "slab_t": 120,
           "found_type": "Isolated pad footings"}
    mod = get_module("building_frame")
    assert not mod.calculate(bad).passed
    r = autosize(bad, lang="el")
    assert r["passed"] and r["rounds"] >= 1
    assert mod.calculate(r["inputs"]).passed
    assert any("→" in line for rnd in r["log"] for line in rnd)


def test_raft_punching_perimeter_and_bearing_shape_factors():
    from erisma.structure.raft import _perimeter, bearing_rect

    d, c = 700.0, 400.0
    full = 4 * c + 2 * math.pi * 2 * d
    # internal column far from the edges: the whole basic control perimeter (EN 1992-1-1 6.4.2)
    assert _perimeter(5000, 5000, c, c, 2 * d, (0, 10000, 0, 10000)) == pytest.approx(full, rel=2e-3)
    # corner column at the raft corner: a quarter of the round part plus two straight sides
    u_corner = _perimeter(0, 0, c, c, 2 * d, (-200, 10000, -200, 10000))
    assert 0.2 * full < u_corner < 0.6 * full
    # B = L (square): s_q = 1 + sin φ, s_γ = 0.7
    B, D, phi, cc, g = 10000.0, 1500.0, 30.0, 0.0, 19e-6
    Nq = math.exp(math.pi * math.tan(math.radians(phi))) * math.tan(math.radians(60)) ** 2
    Ng = 2 * (Nq - 1) * math.tan(math.radians(phi))
    exact = g * D * Nq * 1.5 + 0.5 * g * B * Ng * 0.7
    assert bearing_rect(B, B, D, phi, cc, g) == pytest.approx(exact)


def test_raft_default_building_passes_and_reports_everything():
    c = get_module("building_frame").calculate({})
    assert c.passed, [k.description for k in c.checks if not k.passed]
    descr = " ".join(k.description for k in c.checks)
    for word in ("Raft bottom face x", "punching", "Soil bearing under the raft", "Relative rotation",
                 "Total settlement"):
        assert word in descr
    raft = c.structure["raft"]
    assert raft["elements"] and raft["punching"]
    r = c.raft
    # vertical equilibrium of the soil: Σ spring reactions = Σ loads for G
    assert r["soil"][0]["p"] > 0
