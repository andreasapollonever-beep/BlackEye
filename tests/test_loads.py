import math

import pytest

from erisma.core import InputError, get_module

LIM = {"annex": "CY", "site": "Limassol", "lat": "34.6841", "lon": "33.0379"}


def test_wind_peak_pressure_hand_calc_limassol():
    c = get_module("ec1_wind_snow").calculate({"terrain": "III", "z": 9.0}, LIM)
    v = c.values
    assert v["v_b,0"] == 24
    z0 = 0.3
    kr = 0.19 * (z0 / 0.05) ** 0.07
    vm = kr * math.log(9 / z0) * 24
    Iv = 1 / math.log(9 / z0)
    qp = (1 + 7 * Iv) * 0.5 * 1.25 * vm**2  # Pa
    assert v["q_p(z)"] * 1e6 == pytest.approx(qp)


def test_cyprus_snow_formula():
    c = get_module("ec1_wind_snow").calculate({"A": 900, "roof": 20}, {"annex": "CY"})
    sk = 0.289 * (1 + (900 / 452) ** 2)
    assert c.values["s_k"] * 1e3 == pytest.approx(sk)
    assert c.values["s"] * 1e3 == pytest.approx(0.8 * sk)


def test_troodos_needs_special_study_and_high_snow():
    with pytest.raises(InputError):
        get_module("ec1_wind_snow").calculate({}, {"annex": "CY", "lat": "34.92", "lon": "32.88"})
    with pytest.raises(InputError):
        get_module("ec1_wind_snow").calculate({"A": 1600, "use_site": False}, {"annex": "CY"})


def test_combinations_hand_calc():
    c = get_module("en1990_combinations").calculate({}, {"annex": "CY"})
    assert c.values["E_d,max"] == pytest.approx(1.35 * 250 + 1.5 * 80 + 1.5 * 0.5 * 10
                                                + 1.5 * 0.6 * 35)
