"""Verification problems of Erisma Structure — in the spirit of the verification manuals of
commercial programs (CSI, Dlubal, Tekla): each problem has an independent reference value
from the literature (closed-form solution or tabulated result), the value computed by
Erisma and the difference.  The same problems are in the automatic test-suite.
"""

from __future__ import annotations

import math

import numpy as np

from .model import Material, Model, Section
from .solver import analyse, analyse_pdelta, critical_load_factor

E = 210000.0
STEEL = Material("S", E, 0.3)
SEC = Section("t", A=1e5, Iy=8e7, Iz=8e7, J=1e7)


def _cantilever() -> tuple[float, float]:
    L, P = 3000.0, 10000.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("A", 1, 2, SEC, STEEL)
    m.support(1)
    m.load_node("P", 2, Fz=-P)
    return P * L**3 / (3 * E * SEC.Iy), -analyse(m).static("P").displacement(2)[2]


def _fixed_beam() -> tuple[float, float]:
    L, w = 6000.0, 12.0
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, L, 0, 0)
    m.member("B", 1, 2, SEC, STEEL)
    m.support(1), m.support(2)
    m.load_member("t", "B", wz=0.0, w2=(0, 0, -w))
    f = analyse(m).static("t").forces("B", 5)
    return w * L**2 / 20 / 1e6, -f["My"][-1] / 1e6


def _portal() -> tuple[float, float]:
    h, H = 3000.0, 20000.0
    col = Section("col", 1e10, 5e8, 5e8, 1e9)
    m = Model()
    m.node(1, 0, 0, 0), m.node(2, 5000, 0, 0), m.node(3, 0, 0, h), m.node(4, 5000, 0, h)
    m.member("C1", 1, 3, col, STEEL), m.member("C2", 2, 4, col, STEEL)
    m.member("B", 3, 4, Section("r", 1e9, 1e15, 1e15, 1e15), STEEL)
    m.support(1), m.support(2)
    m.load_node("H", 3, Fx=H)
    return H * h**3 / (24 * E * col.Iz), analyse(m).static("H").displacement(3)[0]


def _shear_building() -> tuple[float, float]:
    from .modal import modal

    h, W = 3000.0, 400e3
    Ec = 30000.0
    mat = Material("c", Ec, 0.2)
    col = Section("col", 1e10, 4e9, 2e9, 3e9)
    m = Model()
    for lvl in range(3):
        m.node(f"a{lvl}", 0, 0, lvl * h), m.node(f"b{lvl}", 6000, 0, lvl * h)
    m.support("a0"), m.support("b0")
    for lvl in (1, 2):
        m.member(f"Ca{lvl}", f"a{lvl - 1}", f"a{lvl}", col, mat)
        m.member(f"Cb{lvl}", f"b{lvl - 1}", f"b{lvl}", col, mat)
        m.member(f"B{lvl}", f"a{lvl}", f"b{lvl}", Section("r", 1e10, 1e16, 1e16, 1e16), mat)
        m.diaphragm(f"F{lvl}", [f"a{lvl}", f"b{lvl}"])
        m.load_node("G", f"a{lvl}", Fz=-W / 2), m.load_node("G", f"b{lvl}", Fz=-W / 2)
    md = modal(analyse(m), {"G": 1.0}, n_modes=2, directions="X")
    k = 2 * 12 * Ec * col.Iz / h**3
    mass = W / 9810.0
    T1 = 2 * math.pi / math.sqrt((3 - math.sqrt(5)) / 2 * k / mass)
    return T1, float(md.periods[0])


def _euler() -> tuple[float, float]:
    L, P, n = 5000.0, 100e3, 8
    m = Model()
    for i in range(n + 1):
        m.node(i, 0, 0, i * L / n)
    for i in range(n):
        m.member(f"C{i}", i, i + 1, SEC, STEEL)
    m.support(0)
    m.load_node("G", n, Fz=-P)
    return math.pi**2 * E * SEC.Iz / (4 * L**2) / P, critical_load_factor(analyse(m), {"G": 1.0})


def _pdelta() -> tuple[float, float]:
    L, P, H, n = 4000.0, 400e3, 5e3, 8
    m = Model()
    for i in range(n + 1):
        m.node(i, 0, 0, i * L / n)
    for i in range(n):
        m.member(f"C{i}", i, i + 1, SEC, STEEL)
    m.support(0)
    m.load_node("G", n, Fz=-P)
    m.load_node("H", n, Fx=H)
    k = math.sqrt(P / (E * SEC.Iz))
    exact = H / (P * k) * (math.tan(k * L) - k * L)
    return exact, analyse_pdelta(m, {"G": 1.0}).static("H").displacement(n)[0]


def _plate(edge: str, t: float, coef: float) -> tuple[float, float]:
    a, n, q, Ec, nu = 6000.0, 16, 1e-5, 30000.0, 0.2
    mat = Material("c", Ec, nu)
    m = Model()
    h = a / n
    for i in range(n + 1):
        for j in range(n + 1):
            nid = f"{i}_{j}"
            m.node(nid, i * h, j * h, 0)
            edge_ = i in (0, n) or j in (0, n)
            r = [True, True, False, False, False, True]
            if edge_:
                r[2] = True
                if edge == "clamped":
                    r[3] = r[4] = True
            m.support(nid, "free").restraints = tuple(r)
    for i in range(n):
        for j in range(n):
            pid = f"P{i}_{j}"
            m.plate(pid, [f"{i}_{j}", f"{i + 1}_{j}", f"{i + 1}_{j + 1}", f"{i}_{j + 1}"], t, mat)
            m.load_plate("q", pid, q)
    D = Ec * t**3 / (12 * (1 - nu**2))
    return coef * q * a**4 / D, -analyse(m).static("q").displacement(f"{n // 2}_{n // 2}")[2]


def _winkler() -> tuple[float, float]:
    q, ks, a, n = 0.05, 0.04, 6000.0, 6
    mat = Material("c", 30000.0, 0.2)
    m = Model()
    h = a / n
    for i in range(n + 1):
        for j in range(n + 1):
            nid = f"{i}_{j}"
            m.node(nid, i * h, j * h, 0)
            trib = (h / (2 if i in (0, n) else 1)) * (h / (2 if j in (0, n) else 1))
            s = m.support(nid, "free", springs=(0, 0, ks * trib, 0, 0, 0))
            s.restraints = (True, True, False, False, False, True)
    for i in range(n):
        for j in range(n):
            pid = f"P{i}_{j}"
            m.plate(pid, [f"{i}_{j}", f"{i + 1}_{j}", f"{i + 1}_{j + 1}", f"{i}_{j + 1}"], 500, mat)
            m.load_plate("q", pid, q)
    w = -analyse(m).static("q").displacement("3_3")[2]
    return q / ks, w


def _spectrum() -> tuple[float, float]:
    from .modal import ec8_spectrum

    return 0.16 * 1.2 * 2.5 / 3.5, float(ec8_spectrum(0.16, "B", 3.5)(np.array([0.3]))[0])


def _bearing() -> tuple[float, float]:
    from .design import strip_bearing

    B, D, c, g = 1000.0, 1200.0, 0.005, 19e-6
    phi = math.radians(30)
    Nq = math.exp(math.pi * math.tan(phi)) * math.tan(math.pi / 4 + phi / 2) ** 2
    Nc = (Nq - 1) / math.tan(phi)
    Ng = 2 * (Nq - 1) * math.tan(phi)
    return (c * Nc + g * D * Nq + 0.5 * g * B * Ng) * 1e3, strip_bearing(B, D, 30, c, g) * 1e3


PROBLEMS = [
    ("1", {"en": "Cantilever, tip load — tip deflection", "el": "Πρόβολος, φορτίο άκρου — βέλος άκρου"},
     "PL³/3EI (Timoshenko & Gere)", "mm", _cantilever),
    ("2", {"en": "Fixed beam, triangular load — end moment", "el": "Αμφίπακτη δοκός, τριγωνικό φορτίο — ροπή άκρου"},
     "wL²/20 (Roark, Table 8.2)", "kNm", _fixed_beam),
    ("3", {"en": "Portal with rigid beam — sway", "el": "Πλαίσιο με άκαμπτο ζύγωμα — οριζόντια μετακίνηση"},
     "Hh³/24EI", "mm", _portal),
    ("4", {"en": "Two-storey shear building — T₁", "el": "Διώροφο διατμητικό κτίριο — T₁"},
     "ω² = (3−√5)/2 · k/m (Chopra §10)", "s", _shear_building),
    ("5", {"en": "Cantilever column — elastic critical load factor", "el": "Πρόβολος υποστύλωμα — συντελεστής κρίσιμου φορτίου"},
     "π²EI/4L² (Euler)", "—", _euler),
    ("6", {"en": "Column with P and H — second-order sway (P-Δ)", "el": "Υποστύλωμα με P και H — μετακίνηση 2ας τάξης (P-Δ)"},
     "H/(Pk)(tan kL − kL)", "mm", _pdelta),
    ("7", {"en": "Simply supported square plate, UDL — centre deflection",
           "el": "Αμφιέρειστη τετραγωνική πλάκα, ομοιόμορφο φορτίο — βέλος κέντρου"},
     "0.00406 qa⁴/D (Timoshenko & Woinowsky-Krieger, Table 8)", "mm",
     lambda: _plate("simple", 20.0, 0.00406)),
    ("8", {"en": "Clamped square plate, UDL — centre deflection",
           "el": "Πακτωμένη τετραγωνική πλάκα, ομοιόμορφο φορτίο — βέλος κέντρου"},
     "0.00126 qa⁴/D (ibid., Table 35)", "mm", lambda: _plate("clamped", 20.0, 0.00126)),
    ("9", {"en": "Plate on Winkler springs, UDL — settlement", "el": "Πλάκα σε ελατήρια Winkler — καθίζηση"},
     "q / k_s", "mm", _winkler),
    ("10", {"en": "EN 1998-1 design spectrum, plateau", "el": "Φάσμα σχεδιασμού EN 1998-1, πλατό"},
     "a_g S 2.5 / q (Eq. 3.14)", "g", _spectrum),
    ("11", {"en": "Strip footing bearing resistance, φ' = 30°", "el": "Φέρουσα ικανότητα λωριδωτού, φ' = 30°"},
     "EN 1997-1 Annex D.4", "kPa", _bearing),
]


def run() -> list[dict]:
    rows = []
    for pid, title, source, unit, fn in PROBLEMS:
        ref, val = fn()
        rows.append({"id": pid, "title": title, "source": source, "unit": unit,
                     "reference": float(ref), "erisma": float(val),
                     "diff": float((val - ref) / ref) if ref else 0.0})
    return rows
