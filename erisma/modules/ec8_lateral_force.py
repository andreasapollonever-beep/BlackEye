"""Seismic design spectrum and lateral force method — EN 1998-1 §3.2.2.5 and §4.3.3.2."""

from __future__ import annotations

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..report.scene3d import PALETTE, Scene3D
from ..report.svg import spectrum_plot

CT = {"Steel moment frames": 0.085, "RC moment frames / eccentric braced steel": 0.075,
      "All other structures (walls, masonry…)": 0.050}


def design_spectrum(T, ag, S, TB, TC, TD, q, beta):
    """EN 1998-1 Eq. 3.13–3.16 (Sd in g when ag in g)."""
    T = np.asarray(T, dtype=float)
    s1 = ag * S * (2 / 3 + T / TB * (2.5 / q - 2 / 3))
    s2 = ag * S * 2.5 / q * np.ones_like(T)
    s3 = np.maximum(ag * S * 2.5 / q * TC / np.maximum(T, 1e-9), beta * ag)
    s4 = np.maximum(ag * S * 2.5 / q * TC * TD / np.maximum(T, 1e-9) ** 2, beta * ag)
    return np.where(T <= TB, s1, np.where(T <= TC, s2, np.where(T <= TD, s3, s4)))


@register
class LateralForceEC8(DesignModule):
    id = "ec8_lateral_force"
    title = "Seismic spectrum and lateral forces"
    category = "Loads"
    standard = "EN 1998-1"
    uses_annex = True
    has_3d = True
    description = ("Design response spectrum (Type 1) and the lateral force method: fundamental "
                   "period, base shear and storey forces for regular buildings.")

    fields = [
        Field("ag", "Reference ground acceleration a_gR", "", 0.25, min=0, max=0.6, group="Site",
              help="In g (a_gR × γI). Pick a zone with the buttons of the selected National "
                   "Annex."),
        Field("ground", "Ground type", kind="choice", choices=list("ABCDE"), default="B",
              group="Site", help="A rock, B very dense sand/gravel or stiff clay, C dense to "
                                 "medium-dense, D loose, E soft surface layer on rock."),
        Field("importance", "Importance class", kind="choice", choices=["I", "II", "III", "IV"],
              default="II", group="Site",
              help="II ordinary buildings, III schools/assembly, IV hospitals/civil protection."),
        Field("q", "Behaviour factor q", "", 3.9, min=1.0, max=8.0, group="Structure",
              help="e.g. RC frame DCM multi-storey: 3.0·αu/α1 = 3.9."),
        Field("system", "Structural system (for T1 = C_t H^¾)", kind="choice", choices=list(CT),
              default="RC moment frames / eccentric braced steel", group="Structure"),
        Field("T1", "Fundamental period T1 (0 = estimate)", "", 0.0, min=0, max=4,
              group="Structure", help="s"),
        Field("storeys", "Storeys (height and weight)", kind="table", group="Structure",
              default=[{"h": 3.2, "W": 2200.0}, {"h": 3.0, "W": 2100.0},
                       {"h": 3.0, "W": 2100.0}, {"h": 3.0, "W": 1700.0}],
              columns=[Field("h", "Storey height", "m", 3.0, min=0.5),
                       Field("W", "Seismic weight G + ψE Q", "kN", 1000.0, min=0)]),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        st = inp["storeys"]
        if not st:
            raise InputError("Add at least one storey", "storeys")
        S, TB, TC, TD = na.spectrum[inp["ground"]]
        gI = na.gamma_I[inp["importance"]]
        calc.heading("Seismic action")
        agR = calc.input("a_gR", inp["ag"], "", "Reference peak ground acceleration [g]", dp=3)
        calc.input("γ_I", gI, "", calc.tr("Importance factor (class {c})", c=inp["importance"]),
                   dp=2)
        ag = calc.formula("a_g", "γ_I a_gR", gI * agR, "", "Design ground acceleration [g]",
                          ref="3.2.1(3)", dp=3)
        calc.table(["Ground type", "S", "T_B [s]", "T_C [s]", "T_D [s]"],
                   [[inp["ground"], f"{S:g}", f"{TB:g}", f"{TC:g}", f"{TD:g}"]],
                   caption="EN 1998-1 Table 3.2 (National Annex), Type 1 spectrum")
        q = calc.input("q", inp["q"], "", "Behaviour factor", dp=2)
        beta = na.spectrum_beta
        if ag <= 0.04:
            calc.note("Very low seismicity (a_g ≤ 0.04 g): EN 1998 need not be applied (3.2.1(5)).")
        elif ag <= 0.08:
            calc.note("Low seismicity (a_g ≤ 0.08 g): simplified procedures may be used.")

        calc.heading("Fundamental period")
        H = sum(r["h"] for r in st) / 1000
        calc.input("H", H * 1000, "m", "Building height from the foundation")
        if inp["T1"] > 0:
            T1 = calc.input("T_1", inp["T1"], "", "Fundamental period [s] (given)", dp=3)
        else:
            Ct = CT[inp["system"]]
            T1 = calc.formula("T_1", f"C_t H^(3/4), C_t = {Ct:g}", Ct * H ** 0.75, "",
                              "Fundamental period [s]", ref="Eq. 4.6", dp=3)
        lim = min(4 * TC, 2.0)
        calc.check_limit("Lateral force method: T_1 ≤ min(4T_C, 2.0 s)", T1, lim, "", "4.3.3.2.1(2)",
                         hint="Use modal response spectrum analysis for this building.")
        Sd = calc.formula("S_d(T_1)", "Eq. 3.13–3.16", float(design_spectrum(
            [T1], ag, S, TB, TC, TD, q, beta)[0]), "", "Design spectral acceleration [g]",
            ref="3.2.2.5", dp=4)
        n = len(st)
        lam = 0.85 if (T1 <= 2 * TC and n > 2) else 1.0
        lam = calc.formula("λ", "0.85 if T_1 ≤ 2T_C and > 2 storeys, else 1.0", lam, "",
                           ref="4.3.3.2.2(1)", dp=2)
        Wt = sum(r["W"] for r in st)
        calc.formula("W", "Σ W_i", Wt, "kN", "Total seismic weight")
        Fb = calc.formula("F_b", "S_d(T_1) W λ", Sd * Wt * lam, "kN", "Base shear",
                          ref="Eq. 4.5")
        calc.formula("F_b / W", "F_b / W", Fb / Wt if Wt else 0, "", "Base shear coefficient",
                     dp=4)

        calc.heading("Storey forces (Eq. 4.11, linear mode shape)")
        z, zs = 0.0, []
        for r in st:
            z += r["h"] / 1000
            zs.append(z)
        sw = sum(zi * r["W"] for zi, r in zip(zs, st))
        rows, Vs = [], 0.0
        forces = [Fb * zi * r["W"] / sw for zi, r in zip(zs, st)]
        for i in range(n - 1, -1, -1):
            Vs += forces[i]
            rows.append([str(i + 1), f"{zs[i]:.2f}", f"{st[i]['W'] / 1000:.0f}",
                         f"{forces[i] / 1000:.1f}", f"{Vs / 1000:.1f}"])
        calc.table(["Storey", "z [m]", "W_i [kN]", "F_i [kN]", "V_i [kN]"], rows[::-1],
                   caption="F_i = F_b z_i W_i / Σ z_j W_j")
        T = np.linspace(0, 4, 161)
        calc.figure(spectrum_plot(T, design_spectrum(T, ag, S, TB, TC, TD, q, beta), T1, Sd,
                                  calc.tr("Design spectrum S_d(T) [g]")),
                    "Design spectrum (Type 1) and fundamental period")
        calc.model3d = cls._scene(calc, zs, forces, Fb, T1)

    @staticmethod
    def _scene(calc, zs, forces, Fb, T1) -> dict:
        sc = Scene3D("lateral_force", calc.tr)
        for key, label in (("frame", "Building"), ("forces", "Storey forces"),
                           ("shear", "Base shear")):
            sc.layer(key, label, toggle=key != "frame")
        B = 8.0
        Fmax = max(forces) or 1.0
        prev = 0.0
        for z, F in zip(zs, forces):
            for x in (-B / 2, B / 2):
                for y in (-B / 2, B / 2):
                    sc.box("frame", (x, (prev + z) / 2, y), (0.35, z - prev, 0.35), "#9aa0a8")
            sc.box("frame", (0, z, 0), (B + 0.5, 0.25, B + 0.5), PALETTE["concrete"], opacity=0.8)
            ln = 0.6 + 3.0 * F / Fmax
            sc.arrow("forces", (-B / 2 - ln - 0.4, z, 0), (1, 0, 0), ln, PALETTE["seismic"], 0.35)
            sc.label("forces", f"F = {F / 1000:.0f} kN", (-B / 2 - ln - 0.6, z + 0.35, 0), "force")
            prev = z
        sc.box("frame", (0, -0.25, 0), (B + 2, 0.5, B + 2), PALETTE["rock"], opacity=0.5)
        sc.arrow("shear", (B / 2 + 4.0, 0.3, 0), (-1, 0, 0), 3.0, PALETTE["seismic"], 0.5)
        sc.label("shear", calc.tr("F_b = {f:.0f} kN, T_1 = {t:.2f} s", f=Fb / 1000, t=T1),
                 (B / 2 + 3.0, 1.0, 0), "result")
        return sc.to_dict()

