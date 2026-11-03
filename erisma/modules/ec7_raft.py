"""Raft foundation on elastic springs — strip method (beam on Winkler foundation).

Each column line is analysed in both directions as a beam on elastic springs (k × strip width)
carrying the full column loads (conservative), giving soil pressure, settlement and moments
per metre; reinforcement and punching to EN 1992-1-1; bearing to EN 1997-1 (q_Ed ≤ q_Rd given).
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec2 import bar_area, design_flexure, section_capacity
from ..report.scene3d import PALETTE, Scene3D, heat_color
from .ec7_pad_footing import PadFootingEC7

CONCRETE = ["C25/30", "C30/37", "C35/45"]
BARS = ["12", "14", "16", "20", "25"]
HINT_B = "Increase the raft thickness or the reinforcement."
HINT_Q = "Enlarge the raft (overhang) or improve the ground."


def bef(L: float, EI: float, kb: float, loads: list[tuple[float, float]], n: int = 200):
    """Beam on Winkler springs, free ends. Units N, mm. Returns x, w, M, V."""
    le = L / n
    x = np.linspace(0, L, n + 1)
    K = np.zeros((2 * n + 2, 2 * n + 2))
    k = EI / le**3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le**2, -6 * le, 2 * le**2],
                               [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le**2, -6 * le, 4 * le**2]])
    for e in range(n):
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K[np.ix_(idx, idx)] += k
    trib = np.full(n + 1, le)
    trib[0] = trib[-1] = le / 2
    for i in range(n + 1):
        K[2 * i, 2 * i] += kb * trib[i]
    F = np.zeros(2 * n + 2)
    for xp, P in loads:
        F[2 * int(round(xp / le))] += P
    w = np.linalg.solve(K, F)[0::2]  # settlement, downward +
    q = kb * w  # soil reaction per unit length
    nodal = -np.array([kb * w[i] * trib[i] for i in range(n + 1)])
    for xp, P in loads:
        nodal[int(round(xp / le))] += P
    V = np.cumsum(nodal)
    M = np.zeros(n + 1)
    for i in range(1, n + 1):
        M[i] = M[i - 1] - V[i - 1] * le  # sagging (bottom tension) positive
    return x, w, M, V, q


@register
class RaftEC7(DesignModule):
    id = "ec7_raft"
    title = "Raft foundation on springs"
    category = "Geotechnical"
    has_3d = True
    uses_annex = True
    standard = "EN 1997-1 §6, EN 1992-1-1"
    description = ("Raft under a regular column grid on a Winkler subgrade: strip analysis in "
                   "both directions (settlement, soil pressure, moments), bottom and top "
                   "reinforcement, punching at the columns and bearing pressure. 3D settlement "
                   "map.")

    fields = [
        Field("nx", "Columns in x", "", 4, kind="int", min=2, max=10, group="Geometry"),
        Field("ny", "Columns in y", "", 3, kind="int", min=2, max=10, group="Geometry"),
        Field("ax", "Column spacing in x", "m", 5.0, min=2, max=12, group="Geometry"),
        Field("ay", "Column spacing in y", "m", 5.0, min=2, max=12, group="Geometry"),
        Field("e", "Overhang beyond the outer columns", "m", 0.8, min=0, max=3, group="Geometry"),
        Field("t", "Raft thickness", "mm", 700.0, min=250, max=2500, group="Geometry"),
        Field("c", "Column size (square)", "mm", 450.0, min=200, group="Geometry"),
        Field("N", "Design column load N_Ed (interior)", "kN", 2200.0, min=0, group="Loads",
              help="Edge columns take 60 % and corner columns 35 % of this load."),
        Field("Nk", "Characteristic (SLS) column load", "kN", 1550.0, min=0, group="Loads"),
        Field("k", "Modulus of subgrade reaction k_s", "MN/m³", 15.0, min=1, max=300,
              group="Ground", help="Soft clay 5–15, medium 15–40, dense sand 40–100 MN/m³."),
        Field("qRd", "Design bearing resistance q_Rd", "kN/m²", 300.0, min=20, group="Ground",
              help="From a bearing capacity calculation (e.g. the strip footing module)."),
        Field("s_lim", "Limiting settlement", "mm", 50.0, min=5, group="Ground"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C30/37",
              group="Materials"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Materials"),
        Field("cover", "Cover", "mm", 50.0, min=30, group="Materials"),
        Field("db", "Bottom bars Ø (both ways)", kind="choice", choices=BARS, default="16",
              group="Reinforcement"),
        Field("sb", "Bottom bar spacing", "mm", 150.0, min=75, max=300, group="Reinforcement"),
        Field("dt", "Top bars Ø (both ways)", kind="choice", choices=BARS, default="16",
              group="Reinforcement"),
        Field("st", "Top bar spacing", "mm", 150.0, min=75, max=300, group="Reinforcement"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        nx, ny, ax, ay, e, t = inp["nx"], inp["ny"], inp["ax"], inp["ay"], inp["e"], inp["t"]
        Lx, Ly = (nx - 1) * ax + 2 * e, (ny - 1) * ay + 2 * e
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyk = na.alpha_cc * fck / na.gamma_c, inp["fyk"]
        fyd = fyk / na.gamma_s
        Ecm = 22000 * ((fck + 8) / 10) ** 0.3
        kb = inp["k"]
        calc.heading("Raft and loads")
        calc.formula("L_x × L_y", "(n − 1) a + 2e", Lx, "m", calc.tr("Raft {x:.1f} × {y:.1f} m",
                                                                     x=Lx / 1000, y=Ly / 1000))
        calc.input("t", t, "mm", "Thickness")
        calc.input("k_s", kb, "MN/m³", "Modulus of subgrade reaction")

        def col_load(i, j, N):
            edge = (i in (0, nx - 1)) + (j in (0, ny - 1))
            return N * (1.0, 0.6, 0.35)[edge]

        Ntot = sum(col_load(i, j, inp["Nk"]) for i in range(nx) for j in range(ny))
        q_avg = calc.formula("q_avg", "ΣN_k / (L_x L_y)", Ntot / (Lx * Ly), "kN/m²",
                             "Mean contact pressure (SLS)", dp=1)
        calc.text("Strip method: every column line is a beam on springs of width a (interior) "
                  "or a/2 + e (edge), loaded by the full column loads in both directions "
                  "(conservative); E_c = 0.5 E_cm (cracked, long-term).")
        res = {}
        for direction, n_along, a_along, n_across, a_across, L in (
                ("x", nx, ax, ny, ay, Lx), ("y", ny, ay, nx, ax, Ly)):
            worst = None
            for j in range(n_across):
                width = a_across if 0 < j < n_across - 1 else a_across / 2 + e
                EI = 0.5 * Ecm * width * t**3 / 12
                for Nkey in ("N", "Nk"):
                    loads = [(e + i * a_along, col_load(i if direction == "x" else j,
                                                        j if direction == "x" else i, inp[Nkey]))
                             for i in range(n_along)]
                    x, w, M, V, q = bef(L, EI, kb * width, loads)
                    r = {"width": width, "x": x, "w": w, "M": M / width, "q": q / width,
                         "V": V / width}
                    key = (direction, Nkey)
                    cur = res.get(key)
                    if cur is None:
                        res[key] = {"Mpos": r["M"].max(), "Mneg": r["M"].min(), "wmax": w.max(),
                                    "qmax": r["q"].max(), "strip": r}
                    else:
                        cur["Mpos"] = max(cur["Mpos"], r["M"].max())
                        cur["Mneg"] = min(cur["Mneg"], r["M"].min())
                        if w.max() > cur["wmax"]:
                            cur["wmax"], cur["strip"] = w.max(), r
                        cur["qmax"] = max(cur["qmax"], r["q"].max())
        wmax = calc.formula("s_max", "max w (SLS, strips)", max(res[("x", "Nk")]["wmax"],
                                                               res[("y", "Nk")]["wmax"]), "mm",
                            "Maximum settlement", dp=1)
        calc.check_limit("Settlement s_max ≤ s_lim", wmax, inp["s_lim"], "mm", "EN 1997-1 Annex H",
                         hint=HINT_Q)
        qEd = calc.formula("q_Ed", "max k_s w (ULS)", max(res[("x", "N")]["qmax"],
                                                           res[("y", "N")]["qmax"]), "kN/m²",
                           "Maximum design soil pressure", dp=0)
        calc.check("Bearing: q_Ed ≤ q_Rd", qEd, inp["qRd"], "kN/m²", "EN 1997-1 6.5.2", hint=HINT_Q)

        calc.heading("Reinforcement (per metre, both directions)")
        db, dt = float(inp["db"]), float(inp["dt"])
        d_b = t - inp["cover"] - db * 1.5
        d_t = t - inp["cover"] - dt * 1.5
        Ab = bar_area(db) * 1000 / inp["sb"]
        At = bar_area(dt) * 1000 / inp["st"]
        Mbot = max(res[("x", "N")]["Mpos"], res[("y", "N")]["Mpos"])
        Mtop = -min(res[("x", "N")]["Mneg"], res[("y", "N")]["Mneg"])
        for label, Md, d, As, dia, s in (("Bottom (under the columns)", Mbot, d_b, Ab, db, inp["sb"]),
                                         ("Top (between the columns)", Mtop, d_t, At, dt, inp["st"])):
            calc.heading(label, 2)
            calc.formula("m_Ed", "envelope of the strips", Md, "kNm/m", dp=1)
            r = design_flexure(calc, 1000, d, Md * 1000, fck, fcd, fyk, fyd, t,
                               allow_compression=False, per_metre=True)
            calc.formula("A_s,prov", f"Ø{dia:g} @ {s:g} mm", As * 1e-3, "mm²/m")
            if math.isfinite(r["As"]):
                calc.check_min("Reinforcement: A_s,prov ≥ A_s,req", As * 1e-3, r["As"] * 1e-3,
                               "mm²/m", "6.1", hint=HINT_B)
            calc.check_min("Minimum reinforcement", As * 1e-3, r["As_min"] * 1e-3, "mm²/m",
                           "9.3.1.1", hint=HINT_B)
            MRd, _ = section_capacity(1000, d, As, fcd, fyd)
            calc.check("Bending: m_Ed ≤ m_Rd", Md, MRd / 1000, "kNm/m", "6.1", hint=HINT_B)
        PadFootingEC7._punching(calc, inp["N"], 0.0, 0.0, ax, ay, inp["c"], inp["c"],
                                d_b, Ab, Ab, fck, fcd, na.gamma_c,
                                na.punch_vmax)
        calc.model3d = cls._scene(calc, inp, Lx, Ly, res, wmax)

    @staticmethod
    def _scene(calc, inp, Lx, Ly, res, wmax) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        nx, ny, ax, ay, e, t = inp["nx"], inp["ny"], m(inp["ax"]), m(inp["ay"]), m(inp["e"]), m(inp["t"])
        sx, sy = res[("x", "Nk")]["strip"], res[("y", "Nk")]["strip"]
        sc = Scene3D("raft", calc.tr)
        for key, label in (("raft", "Raft and columns"), ("settle", "Settlement (SLS)"),
                           ("notes", "Results")):
            sc.layer(key, label, toggle=key != "raft")
        X, Y = m(Lx), m(Ly)
        sc.box("raft", (X / 2, -t / 2, Y / 2), (X, t, Y), PALETTE["concrete"], opacity=0.5)
        for i in range(nx):
            for j in range(ny):
                sc.box("raft", (e + i * ax, 0.75, e + j * ay), (m(inp["c"]), 1.5, m(inp["c"])), "#9aa0a8")
        n = 24
        xs, ys = np.linspace(0, Lx, n + 1), np.linspace(0, Ly, n + 1)
        wx = np.interp(xs, sx["x"], sx["w"])
        wy = np.interp(ys, sy["x"], sy["w"])
        W = 0.5 * (wx[None, :] + wy[:, None])
        wm = float(W.max()) or 1.0
        verts, cols, faces = [], [], []
        for j, yy in enumerate(ys):
            for i, xx in enumerate(xs):
                verts.append((m(xx), -t - 0.03 - W[j, i] / wm * 0.6, m(yy)))
                cols.append(heat_color(W[j, i] / wm))
        for j in range(n):
            for i in range(n):
                a0 = j * (n + 1) + i
                faces += [(a0, a0 + 1, a0 + n + 2), (a0, a0 + n + 2, a0 + n + 1)]
        sc.mesh("settle", verts, faces, opacity=0.85, colors=cols)
        sc.label("notes", calc.tr("s_max = {s:.1f} mm", s=wmax), (X / 2, -t - 1.0, Y), "result")
        return sc.to_dict()
