"""Settlement of a rectangular foundation — EN 1997-1 §6.6.2 and Annex F/H.

Vertical stress increase below the centre by Boussinesq (Newmark corner solution × 4),
compression of each sub-layer from the oedometer modulus (granular / stiff soils) or the
one-dimensional consolidation parameters C_c, C_r, e_0 and OCR (clays), down to the depth
where the stress increase falls to 20 % of the effective overburden (6.6.2(6)).
"""

from __future__ import annotations

import math

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..report.scene3d import PALETTE, Scene3D, heat_color
from ..report.svg import vertical_diagrams

GW = 9.81e-6
HINT_S = ("Increase the foundation size (lower pressure), found deeper on stiffer soil, "
          "pre-load the clay or use piles.")


def corner_influence(a: float, b: float, z: float) -> float:
    """Newmark (1935) influence factor below the corner of a uniformly loaded a×b rectangle."""
    if z <= 0:
        return 0.25
    m, n = a / z, b / z
    m2, n2 = m * m, n * n
    r = math.sqrt(m2 + n2 + 1)
    t1 = 2 * m * n * r / (m2 + n2 + m2 * n2 + 1) * (m2 + n2 + 2) / (m2 + n2 + 1)
    den = m2 + n2 + 1 - m2 * n2
    t2 = math.atan2(2 * m * n * r, den)  # correct branch when den < 0
    return (t1 + t2) / (4 * math.pi)


def stress_centre(B: float, L: float, q: float, z: float) -> float:
    return 4 * q * corner_influence(B / 2, L / 2, z)


@register
class SettlementEC7(DesignModule):
    id = "ec7_settlement"
    title = "Foundation settlement"
    category = "Geotechnical"
    has_3d = True
    standard = "EN 1997-1 §6.6, Annex F, Annex H"
    description = ("Immediate and consolidation settlement of a rectangular footing or raft "
                   "on layered soil: Boussinesq stress distribution, oedometer modulus or "
                   "C_c/C_r/OCR per layer, influence depth and limits of EN 1997-1 Annex H. "
                   "3D stress bulb.")

    fields = [
        Field("B", "Foundation width B", "m", 2.5, min=0.3, group="Foundation"),
        Field("L", "Foundation length L", "m", 2.5, min=0.3, group="Foundation"),
        Field("D", "Founding depth D", "m", 1.0, min=0, group="Foundation"),
        Field("q", "Contact pressure (SLS, quasi-permanent)", "kN/m²", 180.0, min=0,
              group="Foundation",
              help="Total pressure under the foundation for G + ψ2Q. The net pressure "
                   "q − γD causes settlement."),
        Field("rigid", "Rigid foundation (s = 0.8 s_centre)", kind="bool", default=True,
              group="Foundation",
              help="A rigid footing settles uniformly ≈ 0.8 × the flexible centre value."),
        Field("zw", "Groundwater depth below ground", "m", 4.0, min=0, group="Ground"),
        Field("layers", "Soil layers (from the ground surface down)", kind="table",
              group="Ground", default=[
                  {"h": 3.0, "soil": "Granular", "gamma": 19.0, "Eoed": 25.0, "Cc": 0.0,
                   "Cr": 0.0, "e0": 0.6, "OCR": 1.0},
                  {"h": 5.0, "soil": "Clay", "gamma": 19.5, "Eoed": 8.0, "Cc": 0.25,
                   "Cr": 0.04, "e0": 0.8, "OCR": 3.0},
                  {"h": 10.0, "soil": "Granular", "gamma": 20.0, "Eoed": 60.0, "Cc": 0.0,
                   "Cr": 0.0, "e0": 0.5, "OCR": 1.0}],
              columns=[Field("h", "Thickness", "m", 2.0, min=0.1),
                       Field("soil", "Model", kind="choice", choices=["Granular", "Clay"],
                             default="Granular"),
                       Field("gamma", "γ", "kN/m³", 19.0, min=10),
                       Field("Eoed", "E_oed (granular)", "MPa", 20.0, min=0.5),
                       Field("Cc", "C_c (clay)", "", 0.2, min=0),
                       Field("Cr", "C_r (clay)", "", 0.03, min=0),
                       Field("e0", "e_0", "", 0.7, min=0.2, max=3),
                       Field("OCR", "OCR", "", 1.0, min=1, max=20)]),
        Field("s_lim", "Limiting settlement", "mm", 50.0, min=5, group="Limits",
              help="EN 1997-1 Annex H: up to 50 mm is often acceptable for normal structures "
                   "on separate foundations; less for sensitive structures."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        B, L, D, zw = inp["B"], inp["L"], inp["D"], inp["zw"]
        if L < B:
            B, L = L, B
        layers = inp["layers"]
        if not layers:
            raise InputError("Add at least one soil layer", "layers")
        bottom = sum(r["h"] for r in layers)
        if bottom <= D:
            raise InputError("The soil layers must extend below the founding depth", "layers")
        for r in layers:
            if r["soil"] == "Clay" and r["Cc"] <= 0:
                raise InputError("Clay layers need C_c > 0", "layers")
        bounds = np.cumsum([0.0] + [r["h"] for r in layers])

        def layer_at(z):
            i = int(np.searchsorted(bounds, z, side="right") - 1)
            return layers[min(max(i, 0), len(layers) - 1)]

        def sv0(z):
            s, top = 0.0, 0.0
            for r in layers:
                bot = min(top + r["h"], z)
                if bot > top:
                    dry = max(min(bot, zw) - top, 0.0)
                    s += r["gamma"] * dry + (r["gamma"] - GW) * (bot - top - dry)
                top += r["h"]
                if top >= z:
                    break
            return s

        calc.heading("Foundation and loading")
        calc.input("B", B, "m", "Width (shorter side)")
        calc.input("L", L, "m", "Length")
        calc.input("D", D, "m", "Founding depth")
        q = calc.input("q", inp["q"], "kN/m²", "Contact pressure (SLS)")
        s0D = calc.formula("σ'_v0(D)", "Σ γ' h", sv0(D), "kN/m²",
                           "Effective overburden at founding level")
        qn = calc.formula("q_net", "q − σ_v0(D)", max(q - (s0D + GW * max(D - zw, 0.0)), 0.0),
                          "kN/m²", "Net pressure causing settlement")
        calc.table(["Layer", "From – to [m]", "Model", "γ [kN/m³]", "E_oed [MPa]",
                    "C_c", "C_r", "e_0", "OCR"],
                   [[str(i + 1), f"{bounds[i] / 1000:.1f} – {bounds[i + 1] / 1000:.1f}",
                     calc.tr(r["soil"]), f"{r['gamma'] * 1e6:g}",
                     f"{r['Eoed']:g}" if r["soil"] == "Granular" else "—",
                     *([f"{r['Cc']:g}", f"{r['Cr']:g}", f"{r['e0']:g}", f"{r['OCR']:g}"]
                       if r["soil"] == "Clay" else ["—"] * 4)]
                    for i, r in enumerate(layers)], caption="Soil profile")

        calc.heading("Stress increase and compression of the sub-layers")
        calc.text("Δσ_z below the centre = 4 q_net I(B/2, L/2, z) (Newmark corner factor). "
                  "Sub-layers of 0.25 m; granular: Δs = Δσ h / E_oed; clay: "
                  "Δs = h/(1 + e_0) [C_r log(σ'_p/σ'_0) + C_c log(σ'_f/σ'_p)] with "
                  "σ'_p = OCR σ'_0.")
        dz = 250.0
        zs, s_cum, dsig, s0s, total = [D], [0.0], [qn], [s0D], 0.0
        z_inf = None
        rows = []
        per_layer = [0.0] * len(layers)
        z = D
        while z < bottom - 1e-6:
            z2 = min(z + dz, bottom)
            for b in bounds:
                if z < b < z2:
                    z2 = b
            zm = 0.5 * (z + z2)
            r = layer_at(zm)
            li = layers.index(r)
            ds = stress_centre(B, L, qn, zm - D)
            s0 = sv0(zm)
            h = z2 - z
            if r["soil"] == "Granular":
                dset = ds * h / r["Eoed"]
            else:
                sp = r["OCR"] * s0
                sf = s0 + ds
                if sf <= sp:
                    dset = h / (1 + r["e0"]) * r["Cr"] * math.log10(sf / s0)
                else:
                    dset = h / (1 + r["e0"]) * (r["Cr"] * math.log10(sp / s0)
                                               + r["Cc"] * math.log10(sf / sp))
            total += dset
            per_layer[li] += dset
            zs.append(z2)
            s_cum.append(total)
            dsig.append(stress_centre(B, L, qn, z2 - D))
            s0s.append(sv0(z2))
            if ds <= 0.2 * s0:
                z_inf = zm
                break
            z = z2
        for i, r in enumerate(layers):
            if per_layer[i] > 0:
                rows.append([str(i + 1), calc.tr(r["soil"]), f"{per_layer[i]:.1f}"])
        calc.table(["Layer", "Model", "Settlement [mm]"], rows,
                   caption="Contribution of each layer (centre, flexible)")
        if z_inf is not None:
            calc.formula("z_inf", "Δσ_z = 0.2 σ'_v0", z_inf - D, "m",
                         "Influence depth below founding level", ref="EN 1997-1 6.6.2(6)")
        else:
            calc.warn("The stress increase is still above 20 % of the overburden at the "
                      "bottom of the soil profile — extend the profile (deeper boreholes).")
        sc = calc.formula("s_c", "Σ Δs", total, "mm", "Settlement below the centre (flexible)",
                          dp=1)
        s = sc
        if inp["rigid"]:
            s = calc.formula("s", "0.8 s_c", 0.8 * sc, "mm", "Settlement of the rigid foundation",
                             dp=1)
        calc.check_limit("Settlement: s ≤ s_lim", s, inp["s_lim"], "mm", "EN 1997-1 Annex H",
                         hint=HINT_S)
        calc.note("Consolidation settlement develops with time; secondary compression (creep) "
                  "and differential settlement between foundations are not included.")
        zz = np.array(zs)
        calc.figure(vertical_diagrams(zz / 1000, D / 1000, 0.0, [
            (calc.tr("σ'_v0 [kN/m²]"), np.array(s0s) * 1000, "#8a6d3b"),
            (calc.tr("Δσ_z [kN/m²]"), np.array(dsig) * 1000, "#e03b3b"),
            (calc.tr("s(z) [mm]"), np.array(s_cum), "#2a6f97")]),
            "Overburden, stress increase and cumulative settlement below the centre")
        calc.values["s"] = s
        calc.model3d = cls._scene(calc, inp, B, L, D, qn, layers, bounds, z_inf, s)

    @staticmethod
    def _scene(calc, inp, B, L, D, qn, layers, bounds, z_inf, s) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        Bm, Lm, Dm = m(B), m(L), m(D)
        sc = Scene3D("settlement", calc.tr)
        for key, label in (("found", "Foundation"), ("soil", "Soil layers"),
                           ("bulb", "Stress increase Δσ_z"), ("notes", "Results")):
            sc.layer(key, label, toggle=key != "found")
        depth = min(m(bounds[-1]), Dm + 3 * Bm + 2)
        W = max(4 * Bm, 6.0)
        cols = {"Clay": "#a88b6a", "Granular": PALETTE["soil"]}
        for i, r in enumerate(layers):
            a, b = m(bounds[i]), min(m(bounds[i + 1]), depth)
            if a >= depth:
                break
            sc.box("soil", (0, -(a + b) / 2, W / 4), (W, b - a, W / 2), cols[r["soil"]],
                   opacity=0.10 + 0.05 * (i % 2))
        sc.box("found", (0, -Dm + 0.25, 0), (Bm, 0.5, Lm), PALETTE["concrete"])
        nx, nz = 24, 30
        xs = np.linspace(-W / 2, W / 2, nx + 1)
        zz = np.linspace(Dm, depth, nz + 1)
        verts, colsv, faces = [], [], []
        for zv in zz:
            for xv in xs:
                ds = 0.0
                if zv > Dm:
                    # superposition of corner rectangles for an off-centre point
                    x1, x2 = xv * 1000 + B / 2, B / 2 - xv * 1000
                    def part(a, b_):
                        sgn = 1 if a >= 0 else -1
                        return sgn * corner_influence(abs(a), L / 2, (zv - Dm) * 1000)
                    ds = 2 * qn * (part(x1, 0) + part(x2, 0))
                else:
                    ds = qn if abs(xv) <= Bm / 2 else 0.0
                verts.append((xv, -zv, 0.0))
                colsv.append(heat_color(min(ds / qn, 1.0) ** 0.5 if qn > 0 else 0))
        for j in range(nz):
            for i in range(nx):
                a0 = j * (nx + 1) + i
                faces += [(a0, a0 + 1, a0 + nx + 2), (a0, a0 + nx + 2, a0 + nx + 1)]
        sc.mesh("bulb", verts, faces, opacity=0.8, colors=colsv)
        if z_inf is not None:
            zi = m(z_inf)
            sc.line("bulb", [(-W / 2, -zi, 0.01), (W / 2, -zi, 0.01)], "#ffffff", dashed=True)
            sc.label("notes", calc.tr("z_inf (Δσ = 0.2 σ'_v0)"), (W / 2, -zi, 0), "")
        sc.label("notes", calc.tr("s = {s:.1f} mm", s=s), (Bm / 2 + 0.4, -Dm + 0.6, 0),
                 "result")
        sc.label("notes", calc.tr("q_net = {q:.0f} kN/m²", q=qn * 1000), (0, -Dm + 1.0, 0),
                 "force")
        sc.views["default"] = {"pos": [W * 0.7, 1.5, W * 1.2], "target": [0, -depth / 2, 0]}
        return sc.to_dict()
