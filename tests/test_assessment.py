"""EN 1998-3 Annex A — hand checks of the assessment & strengthening module."""

import math

import pytest

from erisma.core import get_module
from erisma.design.annex import get_annex
from erisma.design.ec8_3 import RCSection, confinement_alpha, theta_um

M = "ec8_3_assessment"


def _sec():
    a = math.pi * 16**2 / 4
    return RCSection(b=300, h=400, d1=35, As=3 * a, As2=3 * a, Asv=2 * a, db=16,
                     Asw=2 * math.pi * 8**2 / 4, sh=200, nb=3, nh=3, dh=8)


def test_theta_um_eq_A1_by_hand():
    s = _sec()
    fc, fy = 16 / 1.2, 450 / 1.2
    N, Lv = 600e3, 1500.0
    nu = N / (300 * 400 * fc)
    d = 365
    w = (s.As + s.Asv) * fy / (300 * d * fc)
    w2 = s.As2 * fy / (300 * d * fc)
    rsx = s.Asw / (300 * 200)
    al = confinement_alpha(s)
    hand = (1 / 1.5) * 0.016 * 0.3**nu * (w2 / w * fc) ** 0.225 * (Lv / 400) ** 0.35 \
        * 25 ** (al * rsx * fy / fc) / 1.2
    val, _ = theta_um(s, fc, fy, fy, N, Lv, 1.5, False)
    assert val == pytest.approx(hand, rel=1e-12)


def test_confinement_alpha_by_hand():
    s = _sec()
    b0 = 300 - 2 * (35 - 8) + 8
    h0 = 400 - 2 * (35 - 8) + 8
    sb = 2 * 2 * (b0 / 2) ** 2 + 2 * 2 * (h0 / 2) ** 2
    hand = (1 - 200 / (2 * b0)) * (1 - 200 / (2 * h0)) * (1 - sb / (6 * h0 * b0))
    assert confinement_alpha(s) == pytest.approx(hand, rel=1e-12)


def test_confidence_factor_from_annex():
    assert get_annex("CY").CF == {"KL1": 1.35, "KL2": 1.20, "KL3": 1.00}
    c = get_module(M).calculate({"kl": "KL1 — limited knowledge"}, {"annex": "CY"})
    assert c.values["CF"] == 1.35
    assert c.values["f_c"] == pytest.approx(16 / 1.35)


def test_existing_fails_and_jacket_passes():
    m = get_module(M)
    ex = m.calculate({"strengthen": "None (assessment only)"}, {"annex": "CY"})
    assert not ex.passed and all(ch.hint for ch in ex.checks if not ch.passed)
    j = m.calculate({}, {"annex": "CY"})
    assert j.passed
    assert len(j.checks) == 4  # only the strengthened member decides the verdict


def test_frp_confinement_never_decreases():
    m = get_module(M)
    th = [m.calculate({"strengthen": "FRP wrapping", "nf": n}).values["θ_um"]
          for n in (1, 2, 3, 6)]
    assert all(b >= a - 1e-12 for a, b in zip(th, th[1:]))
    V = [m.calculate({"strengthen": "FRP wrapping", "nf": n}).values["V_R"] for n in (1, 2)]
    assert V[1] > V[0]
