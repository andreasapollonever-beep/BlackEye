"""Wind on the whole building (EN 1991-1-4) — hand calculations."""

import math

import pytest

from erisma.structure import analyse
from erisma.structure.builder import BuildingSpec, build
from erisma.structure.combinations import Case, generate
from erisma.structure.wind import qp, reference_height, storey_forces


def test_peak_velocity_pressure_by_hand():
    # v_b = 24 m/s, terrain III (z0 = 0.3 m), z = 9.2 m, c_o = 1
    kr = 0.19 * (0.3 / 0.05) ** 0.07
    cr = kr * math.log(9.2 / 0.3)
    Iv = 1 / math.log(9.2 / 0.3)
    hand = (1 + 7 * Iv) * 0.5 * 1.25 * (cr * 24) ** 2 / 1000
    assert qp(9.2, 24, "III") == pytest.approx(hand, rel=1e-12)
    assert hand == pytest.approx(0.596, abs=1e-3)
    assert qp(2.0, 24, "III") == qp(5.0, 24, "III")          # below z_min


def test_reference_height_figure_7_4():
    assert reference_height(3, h=9, b=10) == 9                 # h ≤ b
    assert reference_height(3, h=15, b=10) == 10               # b < h ≤ 2b, lower part
    assert reference_height(12, h=15, b=10) == 15
    assert reference_height(5, h=40, b=10) == 10               # h > 2b: strips
    assert reference_height(20, h=40, b=10) == 20
    assert reference_height(35, h=40, b=10) == 40


def test_storey_forces_low_building():
    # 14.5 × 10 m plan, 3 storeys of 3 m; wind along X: b = 10, d = 14.5, h/d = 0.62
    zs = [0, 3000, 6000, 9000]
    wx, wy = storey_forces(14500, 10000, zs, 24, "III")
    q = qp(9.0, 24, "III")                                    # h ≤ b → z_e = h everywhere
    hd = 9 / 14.5
    cD = 0.7 + (0.8 - 0.7) * (hd - 0.25) / 0.75               # Table 7.1, linear
    cE = -0.3 + (-0.5 + 0.3) * (hd - 0.25) / 0.75
    net = 0.85 * (cD - cE)                                    # h/d ≤ 1
    assert wx.cf_net == pytest.approx(net, rel=1e-9)
    # facade bands 1.5–4.5, 4.5–7.5, 7.5–9.0 m
    hand = [net * q * 3.0 * 10.0 * 1e3, net * q * 3.0 * 10.0 * 1e3, net * q * 1.5 * 10.0 * 1e3]
    assert wx.forces == pytest.approx(hand, rel=1e-9)
    assert sum(wy.forces) == pytest.approx(wy.cf_net * q * 7.5 * 14.5 * 1e3, rel=1e-9)


def test_wind_combinations_both_senses_and_exclusive():
    psi_w = (0.6, 0.2, 0.0)
    cs = [Case("G", "G"), Case("Q", "Q", (0.7, 0.5, 0.3)), Case("WX", "W", psi_w),
          Case("WY", "W", psi_w)]
    uls = [c.factors for c in generate(cs, 1.35, 1.5) if c.kind == "ULS"]
    assert len(uls) == 1 + 4 * 2                              # no wind, ±WX, ±WY × 2 leads
    assert not any(f.get("WX") and f.get("WY") for f in uls)   # never both directions
    assert {"G": 1.35, "Q": 1.05, "WX": -1.5} in uls
    assert {"G": 1.35, "Q": 1.5, "WY": 0.9} in uls
    seis = next(c for c in generate(cs, 1.35, 1.5) if c.kind == "seismic").factors
    assert not seis.get("WX") and not seis.get("WY")          # ψ2 = 0


def test_building_wind_case_in_equilibrium():
    spec = BuildingSpec([5000, 5000], [4000], [3000, 3000])
    zs = [0, 3000, 6000]
    wx, _ = storey_forces(10000, 4000, zs, 24, "II")
    spec.lateral = {"WX": {k + 1: (F, 0.0) for k, F in enumerate(wx.forces)}}
    m, _ = build(spec)
    r = analyse(m).static("WX")
    assert r.applied[0] == pytest.approx(sum(wx.forces), rel=1e-9)
    assert r.equilibrium_ok()
    # resultant at mid-depth of the plan (y = 2 m): Mz about the origin = −F y
    assert r.applied[5] == pytest.approx(-sum(wx.forces) * 2000, rel=1e-6)
