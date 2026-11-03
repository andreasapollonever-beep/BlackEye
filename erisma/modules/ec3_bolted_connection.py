"""Bolted shear connection (lap / splice plate with a bolt group) — EN 1993-1-8 §3."""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec3_bolts import (BOLT_AS, BOLT_CLASSES, PLATE, hole, shear_resistance,
                                tension_resistance)
from ..report.scene3d import PALETTE, Scene3D

HINT_BOLT = "Use more bolts, a larger diameter or a higher bolt class."
HINT_BEAR = "Increase the plate thickness or the end/edge distances and pitch."
HINT_POS = "Increase the end/edge distance or pitch to the minimum of Table 3.3."
HINT_NET = "Use a thicker or wider plate."


@register
class BoltedConnectionEC3(DesignModule):
    id = "ec3_bolted_connection"
    title = "Bolted connection"
    category = "Steel"
    has_3d = True
    uses_annex = True
    standard = "EN 1993-1-8 §3"
    description = ("Bolt group in single or double shear with eccentric shear and tension: "
                   "spacing rules, bolt shear, bearing, tension, punching, combined shear and "
                   "tension, long joints, block tearing and the net section of the plate. "
                   "Interactive 3D model with bolt forces.")

    fields = [
        Field("cls", "Bolt class", kind="choice", choices=list(BOLT_CLASSES), default="8.8",
              group="Bolts"),
        Field("d", "Bolt diameter", kind="choice", choices=[f"M{k}" for k in BOLT_AS],
              default="M20", group="Bolts"),
        Field("thread", "Threads in the shear plane", kind="bool", default=True, group="Bolts"),
        Field("planes", "Shear planes", kind="choice", choices=["1", "2"], default="1",
              group="Bolts", help="2 = double cover plates (splice)."),
        Field("n1", "Bolt rows in the force direction n1", "", 3, kind="int", min=1, max=12,
              group="Layout"),
        Field("n2", "Bolt columns across n2", "", 2, kind="int", min=1, max=8, group="Layout"),
        Field("p1", "Pitch p1 (in force direction)", "mm", 70.0, min=20, group="Layout"),
        Field("p2", "Pitch p2 (across)", "mm", 70.0, min=20, group="Layout"),
        Field("e1", "End distance e1", "mm", 50.0, min=10, group="Layout"),
        Field("e2", "Edge distance e2", "mm", 40.0, min=10, group="Layout"),
        Field("t", "Thinnest plate thickness t", "mm", 12.0, min=4, max=60, group="Plates"),
        Field("grade", "Plate steel grade", kind="choice", choices=list(PLATE), default="S275",
              group="Plates"),
        Field("V", "Shear force V_Ed (along the force direction)", "kN", 300.0, min=0,
              group="Design actions"),
        Field("ecc", "Eccentricity of V from the bolt-group centroid", "mm", 0.0, min=0,
              group="Design actions", help="Causes a torsional moment on the group "
                                           "(elastic method)."),
        Field("Ft", "Tension per bolt F_t,Ed", "kN", 0.0, min=0, group="Design actions"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        gM2, gM0 = na.gamma_M2, na.gamma_M0
        d = float(inp["d"][1:])
        d0 = hole(d)
        n1, n2 = inp["n1"], inp["n2"]
        p1, p2, e1, e2, t = inp["p1"], inp["p2"], inp["e1"], inp["e2"], inp["t"]
        fy, fu = PLATE[inp["grade"]]
        fyb, fub = BOLT_CLASSES[inp["cls"]]
        ns = int(inp["planes"])
        n = n1 * n2
        calc.heading("Bolts and plates")
        calc.label("Bolts", f"{n} × M{d:g} {inp['cls']}")
        calc.input("d_0", d0, "mm", "Hole diameter (normal clearance)")
        calc.input("f_ub", fub, "N/mm²", "Bolt ultimate strength")
        calc.input("f_u", fu, "N/mm²", calc.tr("Plate ultimate strength ({g})", g=inp["grade"]))
        calc.text("γ_M2 = {g:g} (National Annex).", g=gM2)

        calc.heading("Positioning of holes (Table 3.3)")
        for sym, val, lim in (("e_1", e1, 1.2 * d0), ("e_2", e2, 1.2 * d0)):
            calc.check_min(calc.tr("{s} ≥ 1.2 d_0", s=sym), val, lim, "mm", "Table 3.3",
                           hint=HINT_POS)
        if n1 > 1:
            calc.check_min("p_1 ≥ 2.2 d_0", p1, 2.2 * d0, "mm", "Table 3.3", hint=HINT_POS)
        if n2 > 1:
            calc.check_min("p_2 ≥ 2.4 d_0", p2, 2.4 * d0, "mm", "Table 3.3", hint=HINT_POS)
        calc.check_limit("p_1, p_2 ≤ min(14t, 200)", max(p1 if n1 > 1 else 0, p2 if n2 > 1 else 0),
                         min(14 * t, 200.0), "mm", "Table 3.3", hint="Reduce the pitch.")

        # bolt coordinates: x along the force, y across
        xs = np.array([i * p1 for i in range(n1)], dtype=float)
        ys = np.array([j * p2 for j in range(n2)], dtype=float)
        X, Y = np.meshgrid(xs - xs.mean(), ys - ys.mean())
        X, Y = X.ravel(), Y.ravel()
        V = inp["V"]
        T = V * inp["ecc"]
        Ip = float(np.sum(X**2 + Y**2))
        fx = V / n + (-T * Y / Ip if Ip > 0 else 0)
        fy_ = T * X / Ip if Ip > 0 else 0 * X
        F = np.hypot(fx, fy_)
        k = int(np.argmax(F))
        calc.heading("Bolt forces (elastic distribution)")
        calc.formula("V_Ed / n", "direct shear per bolt", V / n, "kN")
        if T > 0:
            calc.formula("M_t", "V_Ed e", T, "kNm", "Torsional moment on the group")
            calc.formula("Σr²", "Σ(x² + y²)", Ip, "cm²", dp=1)
        Fv = calc.formula("F_v,Ed", "max √(F_x² + F_y²)", float(F[k]), "kN",
                          "Governing bolt shear force")

        calc.heading("Bolt resistances")
        Lj = (n1 - 1) * p1
        beta = 1.0
        if Lj > 15 * d:
            beta = max(min(1 - (Lj - 15 * d) / (200 * d), 1.0), 0.75)
            calc.formula("β_Lf", "1 − (L_j − 15d)/(200d), 0.75 … 1.0", beta, "",
                         "Long joint reduction", ref="3.8", dp=3)
        Fv1, av = shear_resistance(inp["cls"], d, gM2, inp["thread"])
        FvRd = calc.formula("F_v,Rd", f"β_Lf n_s α_v f_ub A / γ_M2, α_v = {av:g}",
                            beta * ns * Fv1, "kN", "Shear resistance per bolt", ref="Table 3.4")
        calc.check("Bolt shear: F_v,Ed ≤ F_v,Rd", Fv, FvRd, "kN", "Table 3.4", hint=HINT_BOLT)
        # bearing — end bolts in the force direction (conservative for all bolts)
        ab = min(e1 / (3 * d0), (p1 / (3 * d0) - 0.25) if n1 > 1 else 9, fub / fu, 1.0)
        k1 = min(2.8 * e2 / d0 - 1.7, (1.4 * p2 / d0 - 1.7) if n2 > 1 else 9, 2.5)
        FbRd = calc.formula("F_b,Rd", "k_1 α_b f_u d t / γ_M2", k1 * ab * fu * d * t / gM2, "kN",
                            calc.tr("Bearing (α_b = {a:.3f}, k_1 = {k:.3f})", a=ab, k=k1),
                            ref="Table 3.4")
        calc.check("Bearing: F_v,Ed ≤ F_b,Rd", Fv, FbRd, "kN", "Table 3.4", hint=HINT_BEAR)
        if inp["Ft"] > 0:
            FtRd = calc.formula("F_t,Rd", "0.9 f_ub A_s / γ_M2",
                                tension_resistance(inp["cls"], d, gM2), "kN", ref="Table 3.4")
            calc.check("Tension: F_t,Ed ≤ F_t,Rd", inp["Ft"], FtRd, "kN", "Table 3.4",
                       hint=HINT_BOLT)
            dm = 1.7 * d  # mean of across-flats and across-corners of nut/head (approx.)
            BpRd = calc.formula("B_p,Rd", "0.6 π d_m t f_u / γ_M2", 0.6 * math.pi * dm * t * fu
                                / gM2, "kN", "Punching shear (d_m ≈ 1.7d)")
            calc.check("Punching: F_t,Ed ≤ B_p,Rd", inp["Ft"], BpRd, "kN", "Table 3.4",
                       hint=HINT_BEAR)
            calc.check("Shear + tension: F_v/F_v,Rd + F_t/(1.4 F_t,Rd) ≤ 1",
                       Fv / FvRd + inp["Ft"] / (1.4 * FtRd), 1.0, "", "Table 3.4",
                       hint=HINT_BOLT)
        calc.check("Group: V_Ed ≤ n min(F_v,Rd, F_b,Rd)", V, n * min(FvRd, FbRd), "kN",
                   "3.7", hint=HINT_BOLT)

        calc.heading("Plate: net section and block tearing")
        b = 2 * e2 + (n2 - 1) * p2
        calc.formula("b", "2e_2 + (n_2 − 1)p_2", b, "mm", "Plate width")
        Npl = calc.formula("N_pl,Rd", "b t f_y / γ_M0", b * t * fy / gM0, "kN", ref="6.2.3")
        Nu = calc.formula("N_u,Rd", "0.9 (b − n_2 d_0) t f_u / γ_M2",
                          0.9 * (b - n2 * d0) * t * fu / gM2, "kN", ref="EN 1993-1-1 6.2.3")
        calc.check("Plate tension: V_Ed ≤ min(N_pl,Rd, N_u,Rd)", V, min(Npl, Nu), "kN",
                   "EN 1993-1-1 6.2.3", hint=HINT_NET)
        Ant = ((n2 - 1) * p2 - (n2 - 1) * d0) * t
        Anv = 2 * (e1 + (n1 - 1) * p1 - (n1 - 0.5) * d0) * t
        Veff = calc.formula("V_eff,1,Rd", "f_u A_nt / γ_M2 + f_y A_nv / (√3 γ_M0)",
                            fu * Ant / gM2 + fy * Anv / (math.sqrt(3) * gM0), "kN",
                            "Block tearing (concentric)", ref="Eq. 3.9")
        calc.check("Block tearing: V_Ed ≤ V_eff,1,Rd", V, Veff, "kN", "3.10.2", hint=HINT_NET)
        calc.model3d = cls._scene(calc, inp, X, Y, fx, fy_, F, b, d)

    @staticmethod
    def _scene(calc, inp, X, Y, fx, fy_, F, b, d) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        t = m(inp["t"])
        Lp = m(2 * inp["e1"] + (inp["n1"] - 1) * inp["p1"])
        sc = Scene3D("bolted_connection", calc.tr)
        for key, label in (("plates", "Plates"), ("bolts", "Bolts"), ("forces", "Bolt forces")):
            sc.layer(key, label, toggle=key != "plates")
        bm = m(b)
        sc.box("plates", (0, 0, 0), (Lp, t, bm), PALETTE["steel"])
        sc.box("plates", (Lp * 0.6, -t, 0), (Lp * 1.4, t, bm), "#7d8794")
        if inp["planes"] == "2":
            sc.box("plates", (Lp * 0.6, t, 0), (Lp * 1.4, t, bm), "#7d8794")
        Fmax = float(F.max()) or 1.0
        for x, y, f1, f2, f in zip(X, Y, fx, fy_, F):
            p = (m(x), 0, m(y))
            sc.cylinder("bolts", (p[0], -2.2 * t, p[2]), (p[0], 2.2 * t, p[2]), m(d) / 2,
                        "#333a44")
            ln = 0.05 + 0.08 * f / Fmax
            sc.arrow("forces", (p[0], 2.5 * t, p[2]), (f1 / f, 0, f2 / f) if f else (1, 0, 0),
                     ln, "#e03b3b" if f >= 0.999 * Fmax else PALETTE["load"], 0.02)
        sc.label("forces", calc.tr("F_v,Ed = {f:.1f} kN", f=Fmax / 1000),
                 (m(X.max()) + 0.05, 3 * t, m(Y.max())), "result")
        sc.views["default"] = {"pos": [Lp * 1.2, Lp * 1.5, Lp * 1.5], "target": [0, 0, 0]}
        return sc.to_dict()
