"""RC beam with a web opening — hand calculations of every step (EN 1992-1-1)."""

import math

import pytest

from erisma.core import InputError, get_module
from erisma.design.ec2 import moment_resistance, section_capacity
from erisma.modules.ec2_beam_opening import chord_util, plastic_centroid

M = get_module("ec2_beam_opening")
CY = {"annex": "CY"}
A12, A20 = math.pi * 36, math.pi * 100


def out(c, k):
    return c.outputs[k]["value"]


def test_default_hand_calculation():
    c = M.calculate({}, CY)
    # actions: simply supported 6 m, p_d = 1.35·25 + 1.5·15, opening Ø150 at x = 1.5 m
    pd = 1.35 * 25 + 1.5 * 15
    assert out(c, "p_d") == pytest.approx(pd)
    x2 = 1.575
    assert out(c, "M_2") == pytest.approx(pd * x2 * (6 - x2) / 2)
    assert out(c, "V_Ed") == pytest.approx(pd * (3 - 1.425))
    # chords: h_t = h_b = 300 − 75 = 225 mm
    assert out(c, "h_t") == 225 and out(c, "h_b") == 225
    fcd, fyd = 25 / 1.5, 500 / 1.15
    # bottom chord in tension: plastic centroid = centroid of its steel
    cb1 = 30 + 8 + 10            # bottom bars Ø20 from the bottom face
    cb2 = 30 + 8 + 6             # bars under the opening Ø12 from the opening face
    Ab, Au = 4 * A20, 2 * A12
    pb = (Au * cb2 + Ab * (225 - cb1)) / (Ab + Au)
    assert out(c, "p_b") == pytest.approx(pb)
    # top chord in compression: symmetric reinforcement → plastic centroid at mid-depth
    assert out(c, "p_t") == pytest.approx(112.5)
    z = 600 - 225 + pb - 112.5
    assert out(c, "z") == pytest.approx(z)
    N = pd * x2 * (6 - x2) / 2 * 1e3 / z           # kN
    assert out(c, "N_t") == pytest.approx(N) and out(c, "N_b") == pytest.approx(-N)
    V = out(c, "V_Ed")
    assert out(c, "V_t") == pytest.approx(V / 2)    # equal chord depths
    assert out(c, "M_t") == pytest.approx(V / 2 * 0.075)
    # edge links: full shear hung by links at each edge
    assert out(c, "A_sw,req") == pytest.approx(V * 1e3 / fyd)
    assert out(c, "A_sw,prov") == pytest.approx(3 * 2 * math.pi * 25)
    # anchorage of the bars over the opening: η1 = 0.7, f_bd = 2.25 η1 f_ctd
    fctd = 0.7 * 0.30 * 25 ** (2 / 3) / 1.5
    lbd = 12 / 4 * fyd / (2.25 * 0.7 * fctd)
    assert out(c, "l_bd,a") == pytest.approx(lbd)
    assert out(c, "L_a") == pytest.approx(150 + 2 * lbd)
    # full section without the opening (strain compatibility)
    MRd, _ = section_capacity(300, 600 - cb1, Ab, fcd, fyd, 30 + 8 + 6, 2 * A12)
    assert out(c, "M_Rd") == pytest.approx(MRd / 1e6)
    assert c.passed


def test_top_chord_shear_with_axial_compression():
    c = M.calculate({}, CY)
    N = out(c, "N_t") * 1e3
    d = 225 - (30 + 8 + 6)
    k = min(1 + math.sqrt(200 / d), 2)
    rho = min(2 * A12 / (300 * d), 0.02)
    scp = min(N / (300 * 225), 0.2 * 25 / 1.5)
    v = max(0.18 / 1.5 * k * (100 * rho * 25) ** (1 / 3), 0.035 * k ** 1.5 * 5) + 0.15 * scp
    assert out(c, "V_Rd,c,t") == pytest.approx(v * 300 * d / 1e3)
    VRs = 2 * math.pi * 16 / 75 * 0.9 * d * 500 / 1.15 / 1e3   # cot θ = 1
    assert out(c, "V_Rd,s,t") == pytest.approx(VRs)


def test_chord_interaction_is_consistent_with_the_plastic_centroid():
    layers = [(400.0, 40.0), (900.0, 180.0)]
    fcd, fyd = 25 / 1.5, 500 / 1.15
    # pure tension acting at the plastic centroid: just inside the capacity
    Nt = -0.999 * 1300 * fyd
    p = plastic_centroid(300, 220, layers, fcd, fyd, compression=False)
    assert p == pytest.approx((400 * 40 + 900 * 180) / 1300)
    u, _, _ = chord_util(300, 220, layers, fcd, fyd, Nt, [Nt * (110 - p)])
    assert u <= 1.0
    u, _, _ = chord_util(300, 220, layers, fcd, fyd, -1.01 * 1300 * fyd, [0.0])
    assert u == math.inf
    # both signs: the mirrored section gives the resistance for the bottom face compressed
    mp, _ = moment_resistance(300, 220, layers, fcd, fyd, 0.0)
    mn, _ = moment_resistance(300, 220, [(a, 220 - d) for a, d in layers], fcd, fyd, 0.0)
    _, a, b = chord_util(300, 220, layers, fcd, fyd, 0.0, [1.0])
    assert (a, b) == (mp, mn) and mp > mn   # more steel at the bottom → larger sagging M_Rd


def test_other_cases():
    c = M.calculate({"mode": "Given M_Ed and V_Ed at the opening"}, CY)
    assert out(c, "M_2") == pytest.approx(150 + 100 * 0.075)
    c = M.calculate({"shape": "Rectangular opening (a × h0)", "a": 400, "h0": 200}, CY)
    assert out(c, "h_t") == 200 and out(c, "M_t") == pytest.approx(out(c, "V_t") * 0.2)
    c = M.calculate({"share": "Each chord takes the full shear (conservative)"}, CY)
    assert out(c, "V_t") == pytest.approx(out(c, "V_Ed"))
    c = M.calculate({"e": 120}, CY)                 # top chord too shallow for two layers
    assert not c.passed
    c = M.calculate({"x": 0.4}, CY)                 # within h of the support
    assert c.warnings
    with pytest.raises(InputError):
        M.calculate({"D": 700}, CY)
    with pytest.raises(InputError):
        M.calculate({"x": 6.0}, CY)


def test_reserve_on_the_opening():
    from erisma import reserve as R
    r = R.reserve("ec2_beam_opening", {}, CY, ["G", "Q"])
    assert r["verify"]["at"]["umax"] <= 1 + 1e-9 < (r["verify"]["beyond"]["umax"] or 2)


def test_seismic_critical_region():
    # EN 1998-1: l_cr = h_w (DCM, 5.4.3.1.2), 1.5 h_w (DCH, 5.5.3.1.3)
    c = M.calculate({"x": 0.7}, CY)                       # left edge at 625 mm ≥ 600
    assert out(c, "l_cr") == 600 and c.passed
    c = M.calculate({"x": 0.7, "duct": "DCH (l_cr = 1.5 h_w)"}, CY)
    assert out(c, "l_cr") == 900 and not c.passed
    c = M.calculate({"x": 0.7, "seismic": False}, CY)
    assert "l_cr" not in c.outputs
    c = M.calculate({"mode": "Given M_Ed and V_Ed at the opening", "x": 5.5, "Lc": 6.0}, CY)
    assert not c.passed                                   # 425 mm from the right column face


def test_envelope_governing_case_is_the_worst_row():
    rows = [{"name": "A", "M": 150.0, "V": 100.0}, {"name": "B", "M": 120.0, "V": 140.0},
            {"name": "C", "M": -30.0, "V": -40.0}]
    c = M.calculate({"mode": "Envelope of actions (several combinations)", "cases": rows,
                     "sls": False}, CY)
    worst = 0.0
    for r in rows:
        ci = M.calculate({"mode": "Given M_Ed and V_Ed at the opening", "MEd": r["M"],
                          "VEd": r["V"], "sls": False}, CY)
        worst = max(worst, max(k.utilisation for k in ci.checks))
    assert max(k.utilisation for k in c.checks) == pytest.approx(worst)
    with pytest.raises(InputError):
        M.calculate({"mode": "Envelope of actions (several combinations)", "cases": []}, CY)


def test_several_openings():
    c = M.calculate({"n_open": 2, "s_open": 900, "x": 2.0, "sls": False}, CY)   # clear 750 ≥ d
    table = next(it for it in c.items if it.kind == "table" and "U_max" in it.data["headers"])
    assert len(table.data["rows"]) == 2 and out(c, "l_0") == 150
    c = M.calculate({"n_open": 2, "s_open": 400, "x": 2.0, "sls": False}, CY)   # clear 250 < d
    assert out(c, "l_0") == 550                           # one opening (n − 1)s + l0


def test_crack_width_hand_calculation():
    c = M.calculate({}, CY)
    fck, b, h = 25, 300, 600
    Ecm = 22000 * ((fck + 8) / 10) ** 0.3
    ae = 200000 * 3 / Ecm                                 # φ = 2
    ht = hb = 225
    lay = [(2 * A12, 44), (2 * A12, 225 - 44), (2 * A12, 375 + 44), (4 * A20, 600 - 48)]

    def fm(x):
        y = min(x, ht)
        return b * y * (x - y / 2) + sum(((ae - 1) if d < x else ae) * a * (x - d)
                                         for a, d in lay)
    lo, hi = 1, 375
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fm(mid) < 0 else (lo, mid)
    x = lo
    assert out(c, "x") == pytest.approx(x, rel=1e-6)
    y = min(x, ht)
    Icr = b * y ** 3 / 12 + b * y * (x - y / 2) ** 2 + sum(
        ((ae - 1) if d < x else ae) * a * (d - x) ** 2 for a, d in lay)
    wq = 25 + 0.3 * 15
    Mq = wq * 1.575 * (6 - 1.575) / 2 * 1e6
    Vq = wq * (3 - 1.425) * 1e3
    Mc = Vq / 2 * 75
    s_bot = ae * Mq * (552 - x) / Icr + Mc / (552 - 419) / (4 * A20)
    s_und = ae * Mq * (419 - x) / Icr + Mc / (552 - 419) / (2 * A12)
    assert out(c, "σ_s") == pytest.approx(max(s_bot, s_und), rel=1e-6)
    sig, sig2 = (s_bot, s_und) if s_bot > s_und else (s_und, s_bot)
    k2 = (sig + sig2) / (2 * sig)
    hef = min(2.5 * 48, 112.5)
    rho = 4 * A20 / (b * hef)
    fctm = 0.30 * fck ** (2 / 3)
    de = max((sig - 0.4 * fctm / rho * (1 + 200000 / Ecm * rho)) / 2e5, 0.6 * sig / 2e5)
    sr = 3.4 * 38 + 0.8 * k2 * 0.425 * 20 / rho
    assert s_bot > s_und and out(c, "w_k") == pytest.approx(sr * de, rel=1e-6)
    assert out(c, "w_max") == 0.3                          # XC2–XC4, Table 7.1(CYS)
