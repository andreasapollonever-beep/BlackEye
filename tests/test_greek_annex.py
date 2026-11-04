"""Greek National Annex — EN 1992-1-1 values per the ELOT NA (recommended values adopted)."""

from erisma.core import get_module
from erisma.design.annex import EN, GR, get_annex
from erisma.report import render_html


def test_greek_ec2_values_are_recommended():
    assert get_annex("GR") is GR
    assert (GR.gamma_c, GR.gamma_s, GR.alpha_cc, GR.alpha_cc_pl) == (1.5, 1.15, 1.0, 0.8)
    assert GR.punch_vmax == EN.punch_vmax == 0.4
    assert GR.zones == ()          # no zones until the Greek EN 1998-1 annex is verified


def test_en1990_psi_and_factors_match_table_a1():
    # EN 1990 Table A1.1 and A1.2(B) (BS EN 1990:2002 text)
    assert GR.psi["A"] == (0.7, 0.5, 0.3) and GR.psi["B"] == (0.7, 0.5, 0.3)
    assert GR.psi["C"] == GR.psi["D"] == GR.psi["F"] == (0.7, 0.7, 0.6)
    assert GR.psi["E"] == (1.0, 0.9, 0.8) and GR.psi["H"] == (0.0, 0.0, 0.0)
    assert GR.psi["wind"] == (0.6, 0.2, 0.0) and GR.psi["snow_low"] == (0.5, 0.2, 0.0)
    gu, gf, gq = GR.combos["DA1-C1"][:3]
    assert (gu, gf, gq) == (1.35, 1.0, 1.5)


def test_report_states_greek_annex_and_its_limits():
    c = get_module("ec7_pad_footing").calculate({}, {"annex": "GR"})
    html = render_html(c)
    assert "Greece (ELOT National Annexes)" in html
    assert "not yet verified" in html
