"""EN 1991-1-4 §7.2–7.3 pressures — hand calculations with the tables of prEN 1991-1-4:2004."""

import pytest

from erisma.core import InputError, get_module
from erisma.design import wind_cpe as W

M = get_module("ec1_wind_pressures")
CY = {"annex": "CY"}


def out(c, k):
    return c.outputs[k]["value"]


def qp(c):
    return out(c, "q_p(z)")


def test_tables_and_interpolation():
    # Table 7.1 at h/d = 7/12: D 0.7 → 0.8 between h/d 0.25 and 1
    w = W.walls(7 / 12)
    assert w["D"][0] == pytest.approx(0.7 + 0.1 * (7 / 12 - 0.25) / 0.75)
    assert w["A"] == (-1.2, -1.4)
    # Figure 7.2: c_pe for A = 5 m² between c_pe,1 and c_pe,10
    assert W.cpe_area((-1.2, -1.4), 5) == pytest.approx(-1.4 + 0.2 * 0.69897, abs=1e-4)
    assert W.cpe_area((-1.2, -1.4), 0.5) == -1.4 and W.cpe_area((-1.2, -1.4), 20) == -1.2
    # same-sign interpolation in Table 7.4a: α = 20° between 15° and 30°
    c = W.interp_signed(W.DUO_0, 20)
    assert c["F"]["neg"][0] == pytest.approx(-0.9 + 0.4 / 3)
    assert c["F"]["pos"][0] == pytest.approx(0.2 + 0.5 / 3)
    # parapet h_p/h = 0.05 → Table 7.2 row
    assert W.flat_roof("parapet", 0.05)["F"] == (-1.4, -2.0)
    # Figure 7.13
    assert W.internal_mu(0.2, 0.5) == 0.35 and W.internal_mu(1.0, 0.2) == -0.3
    assert W.internal_mu(1.0, 2.0) == -0.5
    assert W.lack_of_correlation(0.5) == 0.85 and W.lack_of_correlation(5) == 1.0


def test_duopitch_default_hand_calc():
    c = M.calculate({}, CY)  # L 20, W 12, h 7, α 20°, A = 10 m², c_pi +0.2/−0.3
    q = qp(c)
    g90 = -1.3 + (-1.4 + 1.3) / 3          # Table 7.4b, zone G, α = 20°
    assert out(c, "w_roof,min") == pytest.approx(q * (g90 - 0.2))
    f_pos = 0.2 + 0.5 / 3                  # Table 7.4a, zone F (+), α = 20°
    assert out(c, "w_roof,max") == pytest.approx(q * (f_pos + 0.3))
    d = 0.7 + 0.1 * (7 / 12 - 0.25) / 0.75  # Table 7.1, zone D
    e = -0.3 - 0.2 * (7 / 12 - 0.25) / 0.75
    assert out(c, "w_wall,max") == pytest.approx(q * (d + 0.3))
    assert out(c, "w_wall,min") == pytest.approx(q * (-1.2 - 0.2))
    assert out(c, "w_h,0") == pytest.approx(0.85 * q * (d - e))
    assert not c.warnings and W.VERIFIED  # coefficients verified against EN 1991-1-4:2005+A1


def test_monopitch_three_directions_and_flat_roofs():
    c = M.calculate({"roof": "Monopitch", "alpha": 15}, CY)
    assert "w_h,180" in c.outputs
    # worst roof suction: θ = 180°, zone F −2.5 (Table 7.3a, α = 15°; F_up at 90° is −2.4)
    assert out(c, "w_roof,min") == pytest.approx(qp(c) * (-2.5 - 0.2))
    c = M.calculate({"roof": "Flat (α < 5°)"}, CY)
    assert out(c, "w_roof,min") == pytest.approx(qp(c) * (-1.8 - 0.2))  # zone F sharp eaves
    c = M.calculate({"roof": "Flat (α < 5°)", "eave": "Parapets", "hp": 0.35}, CY)
    assert out(c, "w_roof,min") == pytest.approx(qp(c) * (-1.4 - 0.2))  # h_p/h = 0.05


def test_loaded_area_hipped_and_internal_options():
    c1 = M.calculate({"A": 1}, CY)
    assert out(c1, "w_wall,min") == pytest.approx(qp(c1) * (-1.4 - 0.2))  # c_pe,1 of zone A
    c = M.calculate({"roof": "Hipped", "alpha": 25, "alpha90": 40}, CY)
    assert out(c, "w_roof,min") < 0
    c = M.calculate({"internal": "None (no openings)"}, CY)
    assert out(c, "w_wall,min") == pytest.approx(qp(c) * -1.2)


def test_canopies():
    c = M.calculate({"kind": "Canopy roof (no walls)", "alpha": 10, "phi": 0.5}, CY)
    q = qp(c)
    assert out(c, "w_f,max") == pytest.approx(0.5 * q)                 # Table 7.6, α = 10°
    assert out(c, "w_f,min") == pytest.approx((-0.9 - 0.25) * q)       # φ = 0.5: −0.9 ↔ −1.4
    assert out(c, "F_w,max") == pytest.approx(0.5 * q * 20 * 12)
    assert out(c, "w_net,min") == pytest.approx((-2.1 - 0.3) * q)      # zone C
    c = M.calculate({"kind": "Canopy roof (no walls)", "canopy": "Duopitch canopy",
                     "alpha": -10, "phi": 0}, CY)
    assert out(c, "w_f,min") == pytest.approx(-0.6 * qp(c))            # Table 7.7, α = −10°
    with pytest.raises(InputError):
        M.calculate({"kind": "Canopy roof (no walls)", "alpha": 40}, CY)


def test_multispan_vaulted_and_dominant_openings():
    # multispan monopitch θ = 180° (config a): span 2 = 0.8, span 3 = 0.6 × c_pe of span 1
    assert W.multispan_factor("a", 2, -0.9) == ("factor", 0.8)
    assert W.multispan_factor("a", 3, -0.9) == ("factor", 0.6)
    assert W.multispan_factor("b", 2, 0.2) == ("value", -0.4)  # config b, c_pe > 0
    c = M.calculate({"roof": "Monopitch", "alpha": 15, "spans": 3}, CY)
    assert "H 3" in " ".join(r[1] for it in c.items if it.kind == "table"
                             for r in it.data["rows"] if len(r) > 1)
    # vaulted roof f/d = 0.25, h/d = 1/3: zone B −0.75 + (−0.45)(0.2/0.45) = −0.95
    v = W.vaulted(0.25, 4 / 12)
    assert v["B"] == [pytest.approx(-0.95)] and len(v["A"]) == 2
    M.calculate({"roof": "Vaulted (cylindrical)", "f": 3}, CY)
    with pytest.raises(InputError):
        M.calculate({"roof": "Vaulted (cylindrical)", "f": 8}, CY)
    # dominant opening on the long face, ratio 3 → c_pi = 0.9 c_pe,D
    c = M.calculate({"internal": "Dominant opening (7.2.9(5))"}, CY)
    d = 0.7 + 0.1 * (7 / 12 - 0.25) / 0.75
    assert out(c, "f_dom") == 0.9
    assert out(c, "w_wall,min") == pytest.approx(qp(c) * (-1.2 - 0.9 * d))
    assert W.dominant_factor(2.5) == pytest.approx(0.825)


def test_friction_free_walls_and_signboards():
    c = M.calculate({"L": 60, "Wd": 12, "h": 5}, CY)        # θ = 90°: b 12, d 60, x0 = 20 m
    Afr = 40 * (2 * 5 + 12 / __import__("math").cos(__import__("math").radians(20)))
    assert out(c, "F_fr,90") == pytest.approx(0.02 * qp(c) * Afr)
    c = M.calculate({"kind": "Free-standing wall or parapet", "L": 20, "h": 2}, CY)
    assert out(c, "w_A") == pytest.approx(3.4 * qp(c))      # Table 7.9, l/h = 10
    assert out(c, "w_inner") == pytest.approx(1.2 * qp(c))  # zone D
    c = M.calculate({"kind": "Free-standing wall or parapet", "L": 20, "h": 2, "ret": 2,
                     "sheltered": True, "xs": 20}, CY)
    assert out(c, "w_A") == pytest.approx(2.1 * qp(c))      # return corner ≥ h
    assert out(c, "ψ_s") == pytest.approx(0.65)            # Figure 7.20, x/h = 10, φ = 1
    assert out(c, "w_inner") == pytest.approx(0.65 * 1.2 * qp(c))
    assert W.free_wall(4, 0.8, 0) == (1.2, 1.2, 1.2, 1.2)
    c = M.calculate({"kind": "Signboard", "L": 6, "h": 3, "zg": 3}, CY)
    assert out(c, "F_w") == pytest.approx(1.8 * qp(c) * 6 * 3)
    assert out(c, "e") == pytest.approx(1.5)
    c = M.calculate({"kind": "Signboard", "L": 10, "h": 3, "zg": 0.5}, CY)  # boundary wall
    assert "w_A" in c.outputs
    c = M.calculate({"kind": "Canopy roof (no walls)", "canopy": "Duopitch canopy",
                     "alpha": 10, "bays": 4}, CY)
    assert out(c, "F_fr") == pytest.approx(0.02 * qp(c) * 2 * 12 * 20)


def test_values_of_the_final_standard():
    """Corrections of EN 1991-1-4:2005 + A1:2010 (with AC:2010) over the 2004 draft."""
    mx, mn = W.canopy(W.CANOPY_MONO, 10, 1.0)
    assert mn[1] == pytest.approx(-1.6)                     # Table 7.6 AC2: α 10°, φ 1, zone A
    c = M.calculate({"roof": "Monopitch", "alpha": 15, "spans": 3}, CY)
    assert out(c, "F_w,min") == pytest.approx(0.05 * qp(c) * 20 * 12)  # 7.2.7(4) A1
    assert W.dominant_factor(2) == 0.75 and W.dominant_factor(3) == 0.90  # Eq. 7.1, 7.2
    assert "2005" in W.SOURCE and W.VERIFIED
