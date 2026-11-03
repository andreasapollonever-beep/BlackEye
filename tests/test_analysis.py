import pytest

from erisma.analysis import UDL, Beam, PointLoad, PointMoment, Support

E, I = 210000.0, 1e8


def approx(v, rel=1e-4):
    return pytest.approx(v, rel=rel)


def test_simply_supported_udl():
    L, w = 6000.0, 10.0
    r = Beam(L, E, I, [Support(0), Support(L)], udls=[UDL(0, L, w)]).solve()
    assert r.max_sagging[0] == approx(w * L**2 / 8)
    assert r.max_deflection[0] == approx(5 * w * L**4 / (384 * E * I))
    assert [R for _, R, _ in r.reactions] == [approx(w * L / 2)] * 2


def test_cantilever_point_load():
    L, P = 4000.0, 1000.0
    r = Beam(L, E, I, [Support(0, "fixed")], point_loads=[PointLoad(L, P)]).solve()
    assert r.max_hogging[0] == approx(-P * L)
    assert r.max_deflection[0] == approx(P * L**3 / (3 * E * I))
    x, R, M = r.reactions[0]
    assert R == approx(P) and M == approx(P * L)


def test_two_span_continuous():
    L, w = 5000.0, 1.0
    r = Beam(2 * L, E, I, [Support(0), Support(L), Support(2 * L)],
             udls=[UDL(0, 2 * L, w)]).solve()
    assert r.max_hogging[0] == approx(-w * L**2 / 8)
    assert [R for _, R, _ in r.reactions] == [approx(0.375 * w * L), approx(1.25 * w * L),
                                              approx(0.375 * w * L)]


def test_point_moment_equilibrium():
    L, M0 = 6000.0, 1e6
    r = Beam(L, E, I, [Support(0), Support(L)], moments=[PointMoment(L / 2, M0)]).solve()
    assert sum(R for _, R, _ in r.reactions) == pytest.approx(0, abs=1e-6)
    assert abs(r.reactions[0][1]) == approx(M0 / L)


def test_unstable_beam_rejected():
    with pytest.raises(ValueError):
        Beam(5000, E, I, [Support(0)]).solve()
