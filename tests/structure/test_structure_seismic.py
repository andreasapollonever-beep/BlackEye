"""EN 1998-1 building checks on hand-checkable models."""

import numpy as np
import pytest

from erisma.structure import G_ACC, analyse, modal
from erisma.structure.builder import BuildingSpec, build
from erisma.structure.modal import DesignSpectrum
from erisma.structure.seismic import seismic_check

FLAT = DesignSpectrum(ag=0.2, S=1.0, TB=0.1, TC=10.0, TD=12.0, q=2.0, beta=0.2)  # plateau


def _one_storey():
    m, info = build(BuildingSpec([6000], [6000], [3000], g_wall=0, q=0, q_roof=0))
    return m, info


def test_single_storey_hand_values():
    m, _ = _one_storey()
    a = analyse(m)
    md = modal(a, {"G": 1.0}, n_modes=3)
    res = seismic_check(a, md, FLAT, accidental=False)
    s = res.storeys[0]
    Sd = 0.2 * 2.5 / 2.0
    mass = md.total_mass["X"]
    # one level, plateau: V = m·Sd·g, F_1 = F_b (λ = 1, single storey)
    assert s.V["X"] == pytest.approx(mass * Sd * G_ACC, rel=1e-6)
    assert res.Fb_lfm["X"] == pytest.approx(mass * Sd * G_ACC, rel=1e-6)
    assert s.F["X"] == pytest.approx(res.Fb_lfm["X"])
    # drift = q·d_e with d_e = Sd·g/ω²
    w = md.omega[int(np.argmax(md.ratio("X")))]
    assert s.drift["X"] == pytest.approx(2.0 * Sd * G_ACC / w**2, rel=1e-6)
    assert s.theta["X"] == pytest.approx(s.P_tot * s.drift["X"] / (s.V["X"] * 3000))
    assert s.P_tot == pytest.approx(mass * G_ACC)
    assert res.amplification["X"] == 1.0
    assert res.drift_ok == (s.drift["X"] * 0.5 <= 0.005 * 3000)


def test_accidental_torsion_moment_and_combination():
    m, _ = _one_storey()
    a = analyse(m)
    md = modal(a, {"G": 1.0}, n_modes=3)
    res = seismic_check(a, md, FLAT)
    t = res.torsion["X"]
    Mz = sum(r[5] + (m.nodes[n].x * r[1] - m.nodes[n].y * r[0])
             for n, r in t.reactions.items())
    assert abs(Mz) == pytest.approx(0.05 * 6000 * res.storeys[0].F["X"], rel=1e-6)
    # symmetric building: torsion adds drift at the corners
    res0 = seismic_check(a, md, FLAT, accidental=False)
    assert res.storeys[0].drift["X"] > res0.storeys[0].drift["X"]
    env = res.member_envelope("C1.A1")
    ex = np.abs(res.rs["X"].end_forces[a.member_index["C1.A1"]]) + np.abs(
        res.torsion["X"].end_forces[a.member_index["C1.A1"]])
    assert np.all(env >= ex - 1e-6)


def test_multi_storey_lateral_force_distribution():
    m, _ = build(BuildingSpec([5000, 5000], [5000], [3000] * 4))
    a = analyse(m)
    md = modal(a, {"G": 1.0, "Q": 0.3}, n_modes=12)
    res = seismic_check(a, md, FLAT)
    assert sum(s.F["X"] for s in res.storeys) == pytest.approx(res.Fb_lfm["X"])
    # storey shear decreases upwards; P_tot too
    V = [s.V["X"] for s in res.storeys]
    assert all(V[i] > V[i + 1] for i in range(len(V) - 1))
    assert res.storeys[0].V["X"] == pytest.approx(res.rs["X"].base_shear, rel=1e-6)
    assert res.storeys[0].P_tot > res.storeys[-1].P_tot
