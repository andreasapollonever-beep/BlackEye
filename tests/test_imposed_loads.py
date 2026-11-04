"""EN 1991-1-1 floor loads — hand calculations with the values of the 2002 standard."""

import pytest

from erisma.core import InputError, get_module

M = get_module("ec1_imposed_loads")
CY = {"annex": "CY"}


def out(c, k):
    return c.outputs[k]["value"]


def test_default_residential_floor_hand_calc():
    c = M.calculate({}, CY)
    g = 0.020 * 21 + 0.050 * 23 + 0.180 * 25 + 0.015 * 18  # Annex A, upper values
    assert out(c, "g_k") == pytest.approx(g)
    assert out(c, "q_k") == 2.0 and out(c, "Q_k") == 2.0      # Table 6.2, category A
    assert out(c, "α_A") == pytest.approx(1.0)                  # 5/7·0.7 + 10/20 = 1.0
    assert out(c, "q_k,part") == 0.8                            # partitions ≤ 2.0 kN/m
    assert out(c, "p_Ed") == pytest.approx(1.35 * g + 1.5 * 2.8)
    assert out(c, "p_qp") == pytest.approx(g + 0.3 * 2.8)
    assert out(c, "q_k,par") == 0.5                             # Table 6.12


@pytest.mark.parametrize("cat,qk,Qk", [
    ("A — residential: balconies", 2.5, 2.0), ("B — offices", 3.0, 4.5),
    ("C2 — fixed seats (churches, theatres, cinemas)", 4.0, 4.0),
    ("C5 — large crowds (concert halls, stands, terraces)", 5.0, 4.5),
    ("D2 — department stores", 5.0, 7.0), ("E1 — storage (incl. books and documents)", 7.5, 7.0),
    ("F — garages, vehicles ≤ 30 kN", 2.5, 20.0), ("G — traffic areas, vehicles 30–160 kN", 5.0, 90.0),
    ("H — roofs not accessible except for maintenance", 0.4, 1.0)])
def test_recommended_values(cat, qk, Qk):
    c = M.calculate({"cat": cat}, CY)
    assert (out(c, "q_k"), out(c, "Q_k")) == (qk, Qk)


def test_alpha_A_lower_limit_for_C_and_D():
    c = M.calculate({"cat": "C3 — no obstacles to moving people (museums, halls, lobbies)",
                     "A": 200}, CY)
    assert out(c, "α_A") == pytest.approx(0.6)          # 0.5 + 0.05 = 0.55 → 0.6
    c = M.calculate({"A": 200}, CY)                      # category A: no lower limit
    assert out(c, "α_A") == pytest.approx(0.55)


def test_alpha_n_columns():
    c = M.calculate({"cat": "B — offices", "element": "Column or wall (several storeys)",
                     "n": 5}, CY)
    assert out(c, "α_n") == pytest.approx((2 + 3 * 0.7) / 5)
    assert out(c, "q_k,tot") == pytest.approx(0.82 * 3.0 + 0.8)
    c = M.calculate({"element": "Column or wall (several storeys)", "n": 2}, CY)
    assert "α_n" not in c.outputs


def test_partitions_and_user_values():
    c = M.calculate({"partitions": "Movable partitions ≤ 3.0 kN/m"}, CY)
    assert out(c, "q_k,part") == 1.2
    c = M.calculate({"partitions": "Heavier partitions (> 3.0 kN/m)"}, CY)
    assert c.warnings and "q_k,part" not in c.outputs
    c = M.calculate({"mode": "My own values", "qk_user": 3.5, "Qk_user": 3.0,
                     "partitions": "None", "reduce": False}, CY)
    assert out(c, "q_k,tot") == 3.5


def test_other_material_and_vehicle_barrier():
    c = M.calculate({"layers": [{"name": "Bricks", "material": "Other material (enter γ)",
                                 "t": 100, "gamma": 15}], "g_extra": 0.5}, CY)
    assert out(c, "g_k") == pytest.approx(0.1 * 15 + 0.5)
    c = M.calculate({"cat": "F — garages, vehicles ≤ 30 kN"}, CY)
    assert out(c, "F_B") == pytest.approx(0.5 * 1500 * 4.5**2 / 0.1 / 1000)  # ≈ 150 kN (B(3))
    with pytest.raises(InputError):
        M.calculate({"layers": []}, CY)
