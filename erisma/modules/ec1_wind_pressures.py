"""Wind pressures on buildings and canopy roofs — EN 1991-1-4 Section 7.2, 7.3.

For every orthogonal wind direction θ (0°, 90° and, for monopitch roofs, 180°) the zones of
the walls (A–E) and of the roof (F … N) are laid out with e = min(b, 2h), the external
pressure coefficients c_pe are read from Tables 7.1–7.5 (c_pe,1 → c_pe,10 by the loaded area,
Figure 7.2), and the net pressures w = q_p (c_pe − c_pi) are formed with the most onerous
internal pressure.  Canopies use c_f and c_p,net of Tables 7.6 / 7.7 with the blockage φ.

The coefficients come from :mod:`erisma.design.wind_cpe` (provisional, see its ``SOURCE``).
"""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..design import wind_cpe as W
from ..report.scene3d import Scene3D, heat_color
from .ec1_wind_snow import TERRAIN, site_qp

KINDS = ["Building (walls and roof)", "Canopy roof (no walls)", "Free-standing wall or parapet",
         "Signboard"]
ROOFS = ["Flat (α < 5°)", "Monopitch", "Duopitch", "Hipped", "Vaulted (cylindrical)"]
EAVES = ["Sharp eaves", "Parapets", "Curved eaves", "Mansard eaves"]
CANOPIES = ["Monopitch canopy", "Duopitch canopy"]
INTERNAL = ["Most onerous of +0.2 and −0.3", "From the opening ratio μ (Figure 7.13)",
            "None (no openings)", "Dominant opening (7.2.9(5))"]
DOM_FACES = ["Long face (length L)", "End face (width W)"]
SURFACES = {"Smooth (steel, smooth concrete)": "smooth",
            "Rough (rough concrete, tar-boards)": "rough",
            "Very rough (ripples, ribs, folds)": "very_rough"}
PSI_MC = {1: (1.0, 0.8), 2: (0.9, 0.7), 3: (0.7, 0.7)}  # Table 7.8 (max, min)
VIEWS = ["θ = 0°", "θ = 90°", "θ = 180°"]


def kpa(v: float) -> float:
    return from_base(v, "kN/m²")


@register
class WindPressuresEC1(DesignModule):
    id = "ec1_wind_pressures"
    title = "Wind pressures on buildings and canopies"
    category = "Loads"
    standard = "EN 1991-1-4 §7.2, §7.3"
    uses_annex = True
    has_3d = True
    description = ("External pressure coefficients for the walls (zones A–E) and the roof — "
                   "flat, monopitch, duopitch, hipped, multispan, vaulted — for every wind "
                   "direction, internal pressure (incl. dominant openings), net pressures and "
                   "friction; canopy roofs, free-standing walls, parapets and signboards. 3D view "
                   "of the zones.")

    fields = [
        Field("use_site", "Use the project site (maps of the National Annex)", kind="bool",
              default=True, group="Site",
              help="Pick the site in the project details (📍 Map). Otherwise give v_b,0."),
        Field("vb0", "Fundamental basic wind velocity v_b,0", "", 24.0, min=10, max=60,
              group="Site", help="m/s — used when no site is selected or for EN values."),
        Field("terrain", "Terrain category", kind="choice", choices=list(TERRAIN), default="III",
              group="Site", help="0 sea, I lakes/flat, II open country, III suburbs/villages, "
                                 "IV cities (≥15 % covered by buildings > 15 m)."),
        Field("co", "Orography factor c_o", "", 1.0, min=1.0, max=2.0, group="Site",
              help="1.0 unless the site is on a hill or cliff (Annex A.3)."),
        Field("kind", "Structure", kind="choice", choices=KINDS, default=KINDS[0],
              group="Geometry"),
        Field("L", "Length L (along the ridge / eaves)", "m", 20.0, min=1, max=500,
              group="Geometry", help="θ = 0°: wind perpendicular to L (crosswind b = L)."),
        Field("Wd", "Width W (across the ridge)", "m", 12.0, min=1, max=500, group="Geometry",
              help="θ = 0°: depth in the wind direction d = W."),
        Field("h", "Height to the top of the roof h", "m", 7.0, min=1, max=200,
              group="Geometry", help="Reference height z_e = h for the roof and the walls "
                                     "(conservative for tall walls, Figure 7.4)."),
        Field("roof", "Roof type", kind="choice", choices=ROOFS, default="Duopitch",
              group="Roof", show_if="kind=Building (walls and roof)"),
        Field("alpha", "Roof pitch α", "°", 20.0, min=-45, max=75, group="Roof",
              help="Monopitch, duopitch (negative = troughed), hipped (long faces), canopies. "
                   "Not used for flat roofs."),
        Field("alpha90", "Pitch of the hipped ends α90", "°", 30.0, min=5, max=75,
              group="Roof", show_if="roof=Hipped"),
        Field("eave", "Eaves of the flat roof", kind="choice", choices=EAVES, default=EAVES[0],
              group="Roof", show_if="roof=Flat (α < 5°)"),
        Field("hp", "Parapet height h_p", "m", 0.5, min=0, group="Roof",
              show_if="eave=Parapets", help="Reference height becomes h + h_p (7.2.3(3)); "
                                            "here h is the height of the roof slab."),
        Field("r", "Radius of the curved eave r", "m", 0.5, min=0, group="Roof",
              show_if="eave=Curved eaves"),
        Field("am", "Mansard eave angle α", "°", 45.0, min=30, max=89, group="Roof",
              show_if="eave=Mansard eaves"),
        Field("f", "Rise of the vault f", "m", 3.0, min=0.1, group="Roof",
              show_if="roof=Vaulted (cylindrical)",
              help="h is the height to the crown; the walls are h − f high (Figure 7.11)."),
        Field("spans", "Number of spans (multispan roofs)", "", 1, kind="int", min=1, max=20,
              group="Roof", help="Monopitch (saw-tooth) or duopitch spans side by side across "
                                 "W, each W/n wide (7.2.7, Figure 7.10)."),
        Field("canopy", "Canopy type", kind="choice", choices=CANOPIES, default=CANOPIES[0],
              group="Canopy", show_if="kind=Canopy roof (no walls)"),
        Field("phi", "Blockage under the canopy φ", "", 0.0, min=0, max=1, group="Canopy",
              show_if="kind=Canopy roof (no walls)",
              help="0 = empty, 1 = fully blocked to the downwind eaves by stored goods "
                   "(Figure 7.15)."),
        Field("bays", "Number of bays (multibay duopitch canopy)", "", 1, kind="int", min=1,
              max=20, group="Canopy", show_if="canopy=Duopitch canopy",
              help="Reduction factors ψ_mc of Table 7.8 for the end, second and inner bays."),
        Field("wphi", "Solidity φ of the wall / fence", "", 1.0, min=0.8, max=1.0,
              group="Wall / signboard", show_if="kind=Free-standing wall or parapet",
              help="1 = solid; 0.8 = 20 % openings. Below 0.8 treat as a plane lattice (7.11)."),
        Field("ret", "Length of return corner", "m", 0.0, min=0, group="Wall / signboard",
              show_if="kind=Free-standing wall or parapet",
              help="Wall returning at the end, 0 … h (Table 7.9 note a)."),
        Field("on_building", "Parapet on a building", kind="bool", default=False,
              group="Wall / signboard", show_if="kind=Free-standing wall or parapet",
              help="Then h is the parapet height and z_e = h_b + h (7.4.1(2))."),
        Field("hb", "Building height below the parapet h_b", "m", 9.0, min=0,
              group="Wall / signboard", show_if="on_building"),
        Field("sheltered", "Sheltered by an upwind wall", kind="bool", default=False,
              group="Wall / signboard", show_if="kind=Free-standing wall or parapet",
              help="Upwind wall at least as high (7.4.2, Figure 7.20)."),
        Field("xs", "Distance to the upwind wall x", "m", 10.0, min=0, group="Wall / signboard",
              show_if="sheltered"),
        Field("phi_up", "Solidity of the upwind wall", "", 1.0, min=0.8, max=1.0,
              group="Wall / signboard", show_if="sheltered"),
        Field("zg", "Clearance of the signboard above ground z_g", "m", 2.5, min=0,
              group="Wall / signboard", show_if="kind=Signboard",
              help="For a signboard L is its width b and h its height (Figure 7.21)."),
        Field("A", "Loaded area A (element or fixing)", "m²", 10.0, min=0.1, group="Pressures",
              help="≥ 10 m²: c_pe,10 (overall structure); ≤ 1 m²: c_pe,1 (cladding, fixings); "
                   "between: Figure 7.2."),
        Field("internal", "Internal pressure", kind="choice", choices=INTERNAL,
              default=INTERNAL[0], group="Pressures", show_if="kind=Building (walls and roof)",
              help="7.2.9(6) NOTE 2. A dominant opening must be treated separately (7.2.9(3)–(5))."),
        Field("mu", "Opening ratio μ", "", 0.5, min=0, max=1, group="Pressures",
              show_if="internal=From the opening ratio μ (Figure 7.13)",
              help="Area of openings where c_pe ≤ 0 / area of all openings (Eq. 7.4)."),
        Field("dom_face", "Face with the dominant opening", kind="choice", choices=DOM_FACES,
              default=DOM_FACES[0], group="Pressures",
              show_if="internal=Dominant opening (7.2.9(5))",
              help="The opening may be windward, leeward or on a side wall depending on the wind "
                   "direction; all cases are checked."),
        Field("dom_ratio", "Openings of the dominant face / openings of the other faces", "",
              3.0, min=2.0, max=100, group="Pressures",
              show_if="internal=Dominant opening (7.2.9(5))",
              help="≥ 2 makes the face dominant (7.2.9(4)); 2 → c_pi = 0.75 c_pe, ≥ 3 → 0.90 c_pe."),
        Field("surface", "Surface roughness (friction)", kind="choice", choices=list(SURFACES),
              default="Rough (rough concrete, tar-boards)", group="Pressures",
              help="Table 7.10 — friction on the surfaces parallel to the wind (7.5)."),
        Field("view", "Direction shown in 3D", kind="choice", choices=VIEWS, default=VIEWS[0],
              group="Pressures"),
    ]

    # ---------------------------------------------------------------------------- run
    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        if not W.VERIFIED:
            calc.warn("Provisional pressure coefficients: {s}.", s=W.SOURCE)
        L, Wd, h = inp["L"] / 1000, inp["Wd"] / 1000, inp["h"] / 1000
        A = inp["A"] / 1e6
        kind = inp["kind"]
        ze = h
        if kind == KINDS[0] and inp["roof"] == ROOFS[0] and inp["eave"] == "Parapets":
            ze = h + inp["hp"] / 1000
        if kind == KINDS[2] and inp["on_building"]:
            ze = inp["hb"] / 1000 + h
        sign_wall = kind == KINDS[3] and inp["zg"] < inp["h"] / 4 and inp["L"] > inp["h"]
        if kind == KINDS[3]:
            ze = (inp["zg"] / 1000 + h) if sign_wall else inp["zg"] / 1000 + h / 2
        qp = site_qp(calc, inp, ze * 1000)
        calc.heading("Geometry")
        if kind in (KINDS[0], KINDS[1]):
            calc.input("L", inp["L"], "m", "Length (along the ridge)")
            calc.input("W", inp["Wd"], "m", "Width (across the ridge)")
            calc.input("h", inp["h"], "m", "Height")
            calc.input("A", inp["A"], "m²", "Loaded area for c_pe")
        fr = W.FRICTION[SURFACES[inp["surface"]]]
        if kind == KINDS[1]:
            cls._canopy(calc, inp, qp, L, Wd, h, fr)
        elif kind == KINDS[2]:
            cls._free_wall(calc, inp, qp, L, h, fr, ze)
        elif kind == KINDS[3]:
            cls._signboard(calc, inp, qp, L, h, ze, sign_wall, fr)
        else:
            cls._building(calc, inp, qp, L, Wd, h, A, fr)

    # ------------------------------------------------------------------- building
    @classmethod
    def _building(cls, calc, inp, qp, L, Wd, h, A, fr) -> None:
        roof = inp["roof"]
        alpha = inp["alpha"]
        n = inp["spans"] if roof in (ROOFS[1], ROOFS[2]) else 1
        if roof == ROOFS[4] and inp["f"] >= inp["h"]:
            raise InputError("The rise f must be smaller than the height h", "f")
        if roof == ROOFS[2] and abs(alpha) < 5:
            calc.note("Duopitch with |α| < 5° is treated as a flat roof (Table 7.4a NOTE 2).")
            roof = ROOFS[0]
        if roof in (ROOFS[1], ROOFS[3]):
            if alpha < 5:
                calc.note("Pitch below 5°: treated as a flat roof (7.2.3(1)).")
                roof = ROOFS[0]
            elif alpha > 75:
                raise InputError("Roof pitch above 75° is outside Tables 7.3–7.5", "alpha")
        dirs = ["0", "90", "180"] if roof == ROOFS[1] else ["0", "90"]
        if n > 1:
            calc.text("Multispan roof: {n} spans of {s:.2f} m (7.2.7, Figure 7.10).", n=n,
                      s=Wd / n)

        # internal pressure
        calc.heading("Internal pressure")
        mode = inp["internal"]
        dom = None
        if mode == INTERNAL[3]:
            fdom = calc.formula("f_dom", f"Eq. 7.2/7.3, ratio {inp['dom_ratio']:g}",
                                W.dominant_factor(inp["dom_ratio"]), "",
                                "c_pi / c_pe at the dominant opening", ref="7.2.9(5)", dp=3)
            dom = (fdom, inp["dom_face"])
            cpis = []
            calc.text("Dominant opening on the {f}: c_pi = {k:.2f} × c_pe of that face, for "
                      "the opening windward, leeward or on a side wall (area-weighted c_pe of "
                      "zones A–C) as the wind direction makes it.",
                      f=calc.tr(inp["dom_face"]).lower(), k=fdom)
            calc.note("If the dominant opening (door, window) is assumed closed at ULS, the open "
                      "condition is an accidental design situation (7.2.9(3), EN 1990).")
        elif mode == INTERNAL[2]:
            cpis = [0.0]
            calc.text("No internal pressure considered (c_pi = 0).")
        elif mode == INTERNAL[1]:
            h_d = h / Wd
            cpi = calc.formula("c_pi", f"Figure 7.13 (μ = {inp['mu']:g}, h/d = {h_d:.2f})",
                               W.internal_mu(inp["mu"], h_d), "", "Internal pressure coefficient",
                               ref="7.2.9(6)", dp=2)
            cpis = [cpi]
        else:
            cpis = [0.2, -0.3]
            calc.text("c_pi = +0.2 and −0.3, the more onerous is used for each zone "
                      "(7.2.9(6) NOTE 2).")

        def net(cpe: float, cands: list[float]) -> tuple[float, float]:
            """(most onerous c_pi, net coefficient c_pe − c_pi)."""
            best = max(cands, key=lambda c: abs(cpe - c))
            return best, cpe - best

        results = {}  # direction -> list of zone dicts
        hdr = ["Surface", "Zone", "Size [m]", "c_pe,10", "c_pe,1", "c_pe", "w_e [kN/m²]",
               "c_pi", "w_net [kN/m²]"]
        for th in dirs:
            b, d = (L, Wd) if th in ("0", "180") else (Wd, L)
            e = min(b, 2 * h)
            calc.heading(f"Wind direction θ = {th}°")
            calc.text("Crosswind dimension b = {b:.2f} m, depth d = {d:.2f} m, e = min(b, 2h) "
                      "= {e:.2f} m", b=b, d=d, e=e)
            hw = h - inp["f"] / 1000 if roof == ROOFS[4] else h
            walls = cls._walls(calc, b, d, h, e, hw)
            if n > 1 and th == "90":
                calc.text("θ = 90°: each span is treated individually, b = W/n = {b:.2f} m "
                          "(7.2.7(1)).", b=Wd / n)
                roofz = cls._roof(calc, roof, th, inp, Wd / n, d, h, min(Wd / n, 2 * h))
            elif n > 1:
                roofz = cls._multispan(calc, roof, th, inp, b, d / n, h, e, n)
            else:
                roofz = cls._roof(calc, roof, th, inp, b, d, h, e)
            zones = walls + roofz
            cands = cpis
            if dom:
                cpe_w = {z["zone"]: W.cpe_area(z["cell"], A) for z in walls}
                side = sum(cpe_w[z["zone"]] * (z["u"][1] - z["u"][0]) for z in walls
                           if "u" in z) / d
                along = (th in ("0", "180")) == (dom[1] == DOM_FACES[0])
                face = [cpe_w["D"], cpe_w["E"]] if along else [side]
                cands = [dom[0] * c for c in face]
                calc.text("Dominant opening: c_pe at the opening {c} → c_pi = {p}",
                          c=" / ".join(f"{c:+.2f}" for c in face),
                          p=" / ".join(f"{c:+.2f}" for c in cands))
            rows = []
            for z in zones:
                cpe = W.cpe_area(z["cell"], A)
                cpi, cn = net(cpe, cands)
                z.update(cpe=cpe, we=qp * cpe, cpi=cpi, wn=qp * cn, theta=th)
                rows.append([calc.tr(z["surface"]), z["zone"], z["size"],
                             f"{z['cell'][0]:+.2f}", f"{z['cell'][1]:+.2f}", f"{cpe:+.2f}",
                             f"{kpa(qp * cpe):+.3f}", f"{cpi:+.2f}", f"{kpa(qp * cn):+.3f}"])
            calc.table(hdr, rows, caption=calc.tr("θ = {t}°: zones, coefficients and pressures "
                                                  "(q_p = {q:.3f} kN/m²)", t=th, q=kpa(qp)))
            wD = next(z for z in zones if z["zone"] == "D")
            wE = next(z for z in zones if z["zone"] == "E")
            f = W.lack_of_correlation(h / d)
            calc.formula(f"w_h,{th}", f"f·q_p·(c_pe,D − c_pe,E), f = {f:.2f}",
                         f * qp * (wD["cpe"] - wE["cpe"]), "kN/m²",
                         "Net horizontal pressure on the building (windward + leeward)",
                         ref="7.2.2(3)", dp=3)
            results[th] = zones
            # friction on the surfaces parallel to the wind (7.5)
            x0 = min(2 * b, 4 * h)
            roof_par = roof == ROOFS[0] or th == "90"
            wroof = b if roof == ROOFS[0] else (
                b / math.cos(math.radians(alpha)) if roof in (ROOFS[1], ROOFS[2], ROOFS[3])
                else b)
            par_total = d * (2 * hw + (wroof if roof_par else 0))
            perp = 2 * b * h
            if par_total <= 4 * perp:
                calc.text("Friction: surfaces parallel to the wind {a:.0f} m² ≤ 4 × surfaces "
                          "perpendicular {p:.0f} m² — may be disregarded (5.3(4)).",
                          a=par_total, p=4 * perp)
            elif d > x0:
                Afr = (d - x0) * (2 * hw + (wroof if roof_par else 0))
                calc.formula(f"F_fr,{th}", f"c_fr·q_p·A_fr = {fr:g}·q_p·{Afr:.1f} m²",
                             fr * qp * Afr * 1e6, "kN",
                             "Friction force (beyond min(2b, 4h) from the upwind edge)",
                             ref="7.5, Table 7.10", dp=2)
        if any(z.get("signed") for zs in results.values() for z in zs):
            calc.note("Where a zone has a negative and a positive value (marked −/+), consider "
                      "separately the case with all negative and the case with all positive "
                      "values on the windward face; for duopitch roofs combine each with the "
                      "largest and the smallest values of zones I and J. Do not mix signs on "
                      "the same face (Tables 7.3a–7.5, NOTE 1).")

        # governing values
        calc.heading("Governing net pressures (all directions)")
        allz = [z for zs in results.values() for z in zs]
        roofz = [z for z in allz if z["surface"] == "Roof"]
        wallz = [z for z in allz if z["surface"] != "Roof"]

        def gov(sym, items, fn, desc):
            z = fn(items, key=lambda z: z["wn"])
            calc.formula(sym, f"θ = {z['theta']}°, {calc.tr('zone')} {z['zone']}", z["wn"],
                         "kN/m²", desc, dp=3)
        gov("w_roof,min", roofz, min, "Roof — maximum suction (uplift, fixings, holding down)")
        gov("w_roof,max", roofz, max, "Roof — maximum downward pressure")
        gov("w_wall,max", wallz, max, "Walls — maximum pressure")
        gov("w_wall,min", wallz, min, "Walls — maximum suction")
        calc.note("Domes (Figure 7.12) and walls or roofs with more than one skin (7.2.10) are "
                  "not included.")
        th = {"θ = 0°": "0", "θ = 90°": "90", "θ = 180°": "180"}[inp["view"]]
        if th not in results:
            th = "0"
        calc.model3d = cls._scene(calc, roof, inp, L, Wd, h, results[th], th, n)

    @staticmethod
    def _walls(calc, b, d, h, e, hw=None) -> list[dict]:
        cells = W.walls(h / d)
        h = hw or h
        out = []
        if e < d:
            parts = [("A", 0, e / 5), ("B", e / 5, e), ("C", e, d)]
        elif e < 5 * d:
            parts = [("A", 0, e / 5), ("B", e / 5, d)]
        else:
            parts = [("A", 0, d)]
        for zn, u0, u1 in parts:
            out.append({"surface": "Side walls", "zone": zn, "cell": cells[zn],
                        "size": f"{u1 - u0:.2f} × {h:.2f}", "u": (u0, u1)})
        out.append({"surface": "Windward wall", "zone": "D", "cell": cells["D"],
                    "size": f"{b:.2f} × {h:.2f}"})
        out.append({"surface": "Leeward wall", "zone": "E", "cell": cells["E"],
                    "size": f"{b:.2f} × {h:.2f}"})
        return out

    @staticmethod
    def _expand(zone: str, cell, rects, size) -> list[dict]:
        """One row per sign case of a signed cell."""
        base = {"surface": "Roof", "rects": rects, "size": size}
        if isinstance(cell, dict):
            rows = []
            for s, mark in (("neg", " (−)"), ("pos", " (+)")):
                if cell.get(s) is not None:
                    rows.append({**base, "zone": zone + (mark if all(cell.values()) else ""),
                                 "cell": cell[s], "signed": all(cell.values())})
            return rows
        return [{**base, "zone": zone, "cell": cell}]

    @classmethod
    def _roof(cls, calc, roof, th, inp, b, d, h, e) -> list[dict]:
        alpha = inp["alpha"]
        e10, e4, e2 = e / 10, e / 4, min(e / 2, d)

        def sz(r):
            return f"{r[1] - r[0]:.2f} × {r[3] - r[2]:.2f}"
        corner = [(0, e10, 0, e4), (0, e10, b - e4, b)]
        g_rect = (0, e10, e4, b - e4)
        if roof == ROOFS[0]:
            kind = {"Sharp eaves": "sharp", "Parapets": "parapet", "Curved eaves": "curved",
                    "Mansard eaves": "mansard"}[inp["eave"]]
            ratio = {"sharp": 0.0, "parapet": inp["hp"] / inp["h"],
                     "curved": inp["r"] / inp["h"], "mansard": inp["am"]}[kind]
            if th == "0":
                label = {"sharp": "", "parapet": f"h_p/h = {ratio:.3f}",
                         "curved": f"r/h = {ratio:.3f}", "mansard": f"α = {ratio:g}°"}[kind]
                calc.text("Flat roof, {k} {l} (Table 7.2)", k=calc.tr(inp["eave"]).lower(),
                          l=label)
            c = W.flat_roof(kind, ratio)
            z = cls._expand("F", c["F"], corner, sz(corner[0]) + " ×2")
            z += cls._expand("G", c["G"], [g_rect], sz(g_rect))
            z += cls._expand("H", c["H"], [(e10, e2, 0, b)], sz((e10, e2, 0, b)))
            if e / 2 < d:
                z += cls._expand("I", W.FLAT_I, [(e / 2, d, 0, b)], sz((e / 2, d, 0, b)))
            return z
        if roof == ROOFS[1]:
            if th in ("0", "180"):
                tab = W.MONO_0 if th == "0" else W.MONO_180
                c = W.interp_signed(tab, alpha) if th == "0" else W.interp_zones(tab, alpha)
                z = cls._expand("F", c["F"], corner, sz(corner[0]) + " ×2")
                z += cls._expand("G", c["G"], [g_rect], sz(g_rect))
                z += cls._expand("H", c["H"], [(e10, d, 0, b)], sz((e10, d, 0, b)))
                return z
            c = W.interp_zones(W.MONO_90, alpha)
            z = cls._expand("Flow", c["Flow"], [corner[0]], sz(corner[0]))
            z += cls._expand("Fup", c["Fup"], [corner[1]], sz(corner[1]))
            z += cls._expand("G", c["G"], [g_rect], sz(g_rect))
            z += cls._expand("H", c["H"], [(e10, e2, 0, b)], sz((e10, e2, 0, b)))
            if e / 2 < d:
                z += cls._expand("I", c["I"], [(e / 2, d, 0, b)], sz((e / 2, d, 0, b)))
            return z
        if roof == ROOFS[2]:
            if th == "0":
                c = W.interp_signed(W.DUO_0, alpha)
                z = cls._expand("F", c["F"], corner, sz(corner[0]) + " ×2")
                z += cls._expand("G", c["G"], [g_rect], sz(g_rect))
                z += cls._expand("H", c["H"], [(e10, d / 2, 0, b)], sz((e10, d / 2, 0, b)))
                z += cls._expand("J", c["J"], [(d / 2, d / 2 + e10, 0, b)],
                                 sz((d / 2, d / 2 + e10, 0, b)))
                z += cls._expand("I", c["I"], [(d / 2 + e10, d, 0, b)],
                                 sz((d / 2 + e10, d, 0, b)))
                return z
            c = W.interp_zones(W.DUO_90, alpha)
            z = cls._expand("F", c["F"], corner, sz(corner[0]) + " ×2")
            z += cls._expand("G", c["G"], [g_rect], sz(g_rect))
            z += cls._expand("H", c["H"], [(e10, e2, 0, b)], sz((e10, e2, 0, b)))
            if e / 2 < d:
                z += cls._expand("I", c["I"], [(e / 2, d, 0, b)], sz((e / 2, d, 0, b)))
            return z
        if roof == ROOFS[4]:
            f = inp["f"] / 1000
            hw = h - f
            if th == "90":
                calc.text("Vaulted roof, θ = 90° (wind along the axis): Figure 7.11 does not apply;"
                          " the zones of a flat roof with sharp eaves are used as an approximation.")
                c = W.flat_roof("sharp", 0.0)
                z = cls._expand("F", c["F"], corner, sz(corner[0]) + " ×2")
                z += cls._expand("G", c["G"], [g_rect], sz(g_rect))
                z += cls._expand("H", c["H"], [(e10, e2, 0, b)], sz((e10, e2, 0, b)))
                if e / 2 < d:
                    z += cls._expand("I", W.FLAT_I, [(e / 2, d, 0, b)], sz((e / 2, d, 0, b)))
                return z
            v = W.vaulted(f / d, hw / d)
            calc.text("Vaulted roof: f/d = {fd:.3f}, h/d = {hd:.3f} (Figure 7.11, z_e = h + f). "
                      "Zones A, B, C taken as the windward quarter, the middle half and the "
                      "leeward quarter of the arc.", fd=f / d, hd=hw / d)
            z = []
            for zn, (u0, u1) in (("A", (0, d / 4)), ("B", (d / 4, 3 * d / 4)),
                                 ("C", (3 * d / 4, d))):
                vals = v[zn]
                for i, c in enumerate(vals):
                    name = zn + ((" (−)" if c < 0 else " (+)") if len(vals) > 1 else "")
                    z.append({"surface": "Roof", "zone": name, "cell": (c, c),
                              "rects": [(u0, u1, 0, b)], "size": sz((u0, u1, 0, b)),
                              "signed": len(vals) > 1})
            return z
        # hipped: the pitch of the windward face governs (Table 7.5 NOTE 3)
        a = alpha if th == "0" else inp["alpha90"]
        calc.text("Hipped roof: pitch of the windward face α = {a:g}° (Table 7.5, Figure 7.9).",
                  a=a)
        c = W.interp_signed(W.HIPPED, a)
        z = []
        for zn in "FGHIJKLMN":
            if th == "90" and zn == "K":
                continue  # zone K exists for θ = 0° only (Figure 7.9)
            z += cls._expand(zn, c[zn], [], "Fig. 7.9")
        return z

    @classmethod
    def _multispan(cls, calc, roof, th, inp, b, ds, h, e, n) -> list[dict]:
        """Span 1 with all zones (d = W/n); spans 2 … n zones H (and I) modified (Fig. 7.10)."""
        inp2 = dict(inp)
        if roof == ROOFS[2] and inp["alpha"] > 0:
            inp2["alpha"] = -inp["alpha"]
            calc.text("Multispan duopitch: treated as troughed spans α = −{a:g}° "
                      "(7.2.7(1), Figure 7.10 c, d).", a=inp["alpha"])
        first = cls._roof(calc, roof, th, inp2, b, ds, h, e)
        config = "d" if roof == ROOFS[2] else ("b" if th == "0" else "a")
        keep = ("H", "I") if roof == ROOFS[2] else ("H",)
        out = [{**z, "zone": z["zone"] + " ¹"} if z["zone"][0] in keep else z for z in first]
        for k in range(2, n + 1):
            for z in first:
                if z["zone"][0] not in keep:
                    continue
                how, v = W.multispan_factor(config, k, z["cell"][0])
                cell = (v, v) if how == "value" else (v * z["cell"][0], v * z["cell"][1])
                rects = [(u0 + (k - 1) * ds, u1 + (k - 1) * ds, v0, v1)
                         for (u0, u1, v0, v1) in z["rects"]]
                tag = f"{v:g}" if how == "value" else f"{v:g}·c_pe"
                out.append({**z, "zone": f"{z['zone']} {k}", "cell": cell, "rects": rects,
                            "size": f"{z['size']} ({tag})"})
        calc.text("Spans 2 … n: zones {z} with the factors of Figure 7.10 {c}; the span number "
                  "follows the zone letter.", z=", ".join(keep), c=config)
        return out

    # --------------------------------------------------------------------- canopy
    @classmethod
    def _canopy(cls, calc, inp, qp, L, Wd, h, fr) -> None:
        mono = inp["canopy"] == CANOPIES[0]
        alpha, phi = inp["alpha"], inp["phi"]
        tab = W.CANOPY_MONO if mono else W.CANOPY_DUO
        lo, hi = min(tab), max(tab)
        a = abs(alpha) if mono else alpha
        if not lo <= a <= hi:
            raise InputError(calc.tr("Canopy pitch outside Table {t}: {lo:g}° to {hi:g}°",
                                     t="7.6" if mono else "7.7", lo=lo, hi=hi), "alpha")
        mx, mn = W.canopy(tab, a, phi)
        b, d = L, Wd
        calc.heading("Monopitch canopy — Table 7.6" if mono else "Duopitch canopy — Table 7.7")
        calc.text("Blockage φ = {p:g}; minimum values interpolated between φ = 0 and φ = 1 "
                  "(7.3(3)). Downwind of the maximum blockage use φ = 0 (7.3(4)).", p=phi)
        zones = "ABC" if mono else "ABCD"
        calc.table(["", "c_f"] + [calc.tr("Zone {z}", z=z) for z in zones],
                   [[calc.tr("Maximum (downward)")] + [f"{v:+.2f}" for v in mx],
                    [calc.tr("Minimum (upward)")] + [f"{v:+.2f}" for v in mn]],
                   caption="c_f overall force coefficient, c_p,net net pressure coefficients")
        sizes = {"A": calc.tr("interior"), "B": f"{calc.tr('strips')} b/10 = {b / 10:.2f} m",
                 "C": f"{calc.tr('strips')} d/10 = {d / 10:.2f} m",
                 "D": f"{calc.tr('ridge strip')} d/5 = {d / 5:.2f} m"}
        calc.text("Zones: {z}", z="; ".join(f"{z}: {sizes[z]}" for z in zones))
        calc.formula("w_f,max", "c_f,max · q_p", mx[0] * qp, "kN/m²",
                     "Overall downward pressure (on the roof area)", ref="Eq. 5.3, c_s c_d = 1",
                     dp=3)
        calc.formula("w_f,min", "c_f,min · q_p", mn[0] * qp, "kN/m²",
                     "Overall upward pressure (uplift)", ref="Eq. 5.3, c_s c_d = 1", dp=3)
        calc.formula("F_w,max", "c_f,max · q_p · b · d", mx[0] * qp * b * d * 1e6, "kN",
                     "Resultant downward force", dp=1)
        calc.formula("F_w,min", "c_f,min · q_p · b · d", mn[0] * qp * b * d * 1e6, "kN",
                     "Resultant upward force", dp=1)
        if mono:
            calc.text("Monopitch canopy: the resultant acts at d/4 = {x:.2f} m from the windward "
                      "edge (Figure 7.16).", x=d / 4)
        else:
            calc.text("Duopitch canopy: resultant at the centre of each slope; also check one "
                      "slope loaded with the maximum or minimum and the other unloaded (7.3(6)).")
        calc.formula("w_net,max", "max c_p,net · q_p", max(mx[1:]) * qp, "kN/m²",
                     "Local net pressure, downward (roofing, fixings)", dp=3)
        calc.formula("w_net,min", "min c_p,net · q_p", min(mn[1:]) * qp, "kN/m²",
                     "Local net pressure, upward (roofing, fixings)", dp=3)
        calc.formula("F_fr", f"c_fr·q_p·2·d·b = {fr:g}·q_p·2·{d:.2f}·{b:.2f}",
                     fr * qp * 2 * d * b * 1e6, "kN", "Friction force (wind along the roof)",
                     ref="7.5, Figure 7.22", dp=2)
        if not mono and inp["bays"] > 1:
            nb = inp["bays"]
            rows = []
            for k in range(1, nb + 1):
                pos = min(k, nb + 1 - k)
                fmax, fmin = PSI_MC[min(pos, 3)]
                rows.append([str(k), f"{fmax:.1f}", f"{fmin:.1f}",
                             f"{kpa(fmax * mx[0] * qp):+.3f}", f"{kpa(fmin * mn[0] * qp):+.3f}"])
            calc.table(["Bay", "ψ_mc (max)", "ψ_mc (min)", "w_f,max [kN/m²]", "w_f,min [kN/m²]"],
                       rows, caption="Table 7.8 — multibay duopitch canopy (Figure 7.18)")
        calc.model3d = cls._canopy_scene(calc, mono, L, Wd, h, alpha, mn[0])

    # ------------------------------------------------------------- free walls
    @classmethod
    def _free_wall(cls, calc, inp, qp, l, h, fr, ze) -> None:
        phi, ret = inp["wphi"], inp["ret"] / 1000
        calc.heading("Free-standing wall or parapet — Table 7.9")
        calc.input("l", inp["L"], "m", "Length of the wall")
        calc.input("h", inp["h"], "m", "Height of the wall")
        calc.formula("z_e", "h_b + h" if inp["on_building"] else "h", ze * 1000, "m",
                     "Reference height", ref="7.4.1(2)", dp=2)
        cp = W.free_wall(l / h, phi, ret / h)
        both = phi < 1 or ret > 0
        calc.text("l/h = {lh:.2f}, φ = {p:g}, return corner {r:.2f} m (r/h = {rh:.2f}). {s}",
                  lh=l / h, p=phi, r=ret, rh=ret / h,
                  s=calc.tr("Both signs (±) must be considered." if both else
                            "Pressure on the windward face (no return corners, φ = 1)."))
        parts = [("A", 0, 0.3 * h), ("B", 0.3 * h, 2 * h), ("C", 2 * h, 4 * h), ("D", 4 * h, l)]
        psi = 1.0
        if inp["sheltered"]:
            psi = calc.formula("ψ_s", f"Figure 7.20, x/h = {inp['xs'] / inp['h']:.2f}, "
                               f"φ = {inp['phi_up']:g}", W.shelter(inp["xs"] / inp["h"],
                                                                     inp["phi_up"]), "",
                               "Shelter factor (not within h of the free end)",
                               ref="7.4.2, Eq. 7.7", dp=3)
        rows, total, zones = [], 0.0, []
        for (zn, u0, u1), c in zip(parts, cp):
            u1 = min(u1, l)
            if u1 <= u0:
                continue
            ps = psi if (inp["sheltered"] and u0 >= h) else 1.0
            cn = c * ps
            w = qp * cn
            F = w * (u1 - u0) * h * 1e6
            total += F
            zones.append((zn, u0, u1, cn))
            rows.append([zn, f"{u0:.2f} – {u1:.2f}", f"{c:.2f}", f"{ps:.2f}",
                         f"{('±' if both else '')}{kpa(w):.3f}", f"{kpa(w) * h:.3f}",
                         f"{F / 1e3:.2f}"])
        calc.table(["Zone", "From – to [m]", "c_p,net", "ψ_s", "w [kN/m²]", "w·h [kN/m]",
                    "F [kN]"], rows, caption="Zones from each free end (Figure 7.19)")
        calc.formula("w_A", "c_p,net,A · q_p", qp * cp[0], "kN/m²", "Net pressure, end zone A",
                     dp=3)
        calc.formula("w_inner", f"c_p,net,{zones[-1][0]} · q_p", qp * zones[-1][3], "kN/m²",
                     "Net pressure, inner zone", dp=3)
        calc.formula("F_w", "Σ w·A_zone (one free end, both ends similar)", total, "kN",
                     "Total wind force on the wall", dp=2)
        calc.formula("F_fr", f"c_fr·q_p·2·h·l = {fr:g}·q_p·2·{h:.2f}·{l:.2f}",
                     fr * qp * 2 * h * l * 1e6, "kN", "Friction force (wind along the wall)",
                     ref="7.5, Figure 7.22", dp=2)
        calc.note("Zones are measured from a free end; a wall with two free ends has the zones at "
                  "both ends. Porous fences with φ < 0.8: plane lattices (7.11).")
        sc = Scene3D("wind_wall", calc.tr)
        sc.layer("wall", "Wall")
        base = ze - h
        cmax = max(abs(c) for *_, c in zones) or 1
        for zn, u0, u1, c in zones:
            sc.box("wall", (u0 + (u1 - u0) / 2, base + h / 2, 0), (u1 - u0, h, 0.25),
                   heat_color(0.5 + 0.5 * c / cmax), opacity=0.95)
            sc.label("wall", f"{zn} {c:.2f}", (u0 + (u1 - u0) / 2, base + h + 0.3, 0), "result")
        if base > 0:
            sc.box("wall", (min(l, 4 * h) / 2, base / 2, 3), (min(l, 4 * h), base, 6), "#cfd5dc",
                   opacity=0.4)
        return_scene = sc.to_dict()
        calc.model3d = return_scene

    @classmethod
    def _signboard(cls, calc, inp, qp, b, h, ze, as_wall, fr) -> None:
        zg = inp["zg"] / 1000
        if as_wall:
            calc.text("z_g = {z:.2f} m < h/4 and b/h > 1: treated as a boundary wall of height "
                      "z_g + h (7.4.3(2)).", z=zg)
            inp2 = dict(inp, wphi=1.0, ret=0.0, on_building=False, sheltered=False)
            cls._free_wall(calc, inp2, qp, b, zg + h, fr, ze)
            return
        calc.heading("Signboard — 7.4.3")
        calc.input("b", inp["L"], "m", "Width of the signboard")
        calc.input("h", inp["h"], "m", "Height of the signboard")
        calc.input("z_g", inp["zg"], "m", "Clearance above ground")
        calc.formula("z_e", "z_g + h/2", ze * 1000, "m", "Reference height", ref="Figure 7.21",
                     dp=2)
        calc.formula("c_f", "Eq. 7.8", W.SIGN_CF, "", "Force coefficient", ref="7.4.3(1)", dp=2)
        F = calc.formula("F_w", "c_s c_d · c_f · q_p · b · h, c_s c_d = 1",
                         W.SIGN_CF * qp * b * h * 1e6, "kN", "Wind force on the signboard",
                         ref="Eq. 5.3", dp=2)
        ecc = calc.formula("e", "±0.25 b", 0.25 * b * 1000, "m", "Horizontal eccentricity",
                           ref="Eq. 7.9", dp=2)
        calc.formula("M_t", "F_w · e", F * ecc, "kNm", "Torsion about the vertical axis", dp=2)
        calc.formula("M_base", "F_w · z_e", F * ze * 1000, "kNm",
                     "Overturning moment at ground level", dp=2)
        calc.note("Check divergence and stall flutter (7.4.3). c_s c_d = 1 assumed (6.2(1)).")
        sc = Scene3D("wind_sign", calc.tr)
        sc.layer("sign", "Signboard")
        sc.box("sign", (0, zg + h / 2, 0), (b, h, 0.15), heat_color(0.9), opacity=0.95)
        for x in (-b / 4, b / 4):
            sc.box("sign", (x, zg / 2, 0), (0.2, zg, 0.2), "#7d8b99")
        sc.arrow("sign", (0.25 * b, zg + h / 2, -3), (0, 0, 1), 2.6, "#2a6f97")
        sc.label("sign", f"F_w = {F / 1e3:.1f} kN, e = ±{0.25 * b:.2f} m",
                 (0, zg + h + 0.5, 0), "result")
        calc.model3d = sc.to_dict()

    # ---------------------------------------------------------------------- 3D
    @staticmethod
    def _roof_y(roof, alpha, Wd, h, x, z, L, a90, n=1, f=0.0):
        t = math.tan(math.radians(alpha))
        if roof == ROOFS[0]:
            return h
        if roof == ROOFS[4]:
            return h - f + f * max(0.0, 1 - (2 * z / Wd) ** 2)
        if n > 1:
            ds = Wd / n
            zz = (z + Wd / 2) % ds if z < Wd / 2 - 1e-9 else ds
            if roof == ROOFS[1]:
                return h - (ds - zz) * t
            return h - abs(zz - ds / 2) * abs(t)
        if roof == ROOFS[1]:
            return h - (Wd / 2 - z) * t
        if alpha < 0:
            return h + (Wd / 2 - abs(z)) * t
        he = h - Wd / 2 * t
        y = he + (Wd / 2 - abs(z)) * t
        if roof == ROOFS[3]:
            t90 = math.tan(math.radians(a90))
            y = min(y, he + (L / 2 - abs(x)) * t90)
        return y

    @classmethod
    def _scene(cls, calc, roof, inp, L, Wd, h, zones, th, n=1) -> dict:
        sc = Scene3D("wind_pressures", calc.tr)
        sc.layer("walls", "Walls")
        sc.layer("roof", "Roof")
        sc.layer("wind", "Wind")
        alpha, a90 = inp["alpha"], inp["alpha90"]

        fv = inp["f"] / 1000 if roof == ROOFS[4] else 0.0

        def y(x, z):
            return cls._roof_y(roof, alpha, Wd, h, x, z, L, a90, n, fv)
        if roof == ROOFS[4]:
            he = h - fv
        elif n > 1:
            he = h - (Wd / n) * abs(math.tan(math.radians(alpha))) / (1 if roof == ROOFS[1] else 2)
        elif roof == ROOFS[1]:
            he = h - Wd * math.tan(math.radians(alpha))
        elif roof in (ROOFS[2], ROOFS[3]) and alpha > 0:
            he = h - Wd / 2 * math.tan(math.radians(alpha))
        else:
            he = h
        he = max(he, 0.3 * h)
        vals = [z["cpe"] for z in zones] or [0]
        cmax = max(1.0, max(abs(v) for v in vals))

        def col(c):
            return heat_color(0.5 + 0.5 * c / cmax)

        # wind frame (u along the wind, v across) → world (x along L, z along W)
        if th == "0":
            def world(u, v):
                return (-L / 2 + v, -Wd / 2 + u)
            b, d = L, Wd
        elif th == "180":
            def world(u, v):
                return (L / 2 - v, Wd / 2 - u)
            b, d = L, Wd
        else:
            def world(u, v):
                return (-L / 2 + u, -Wd / 2 + v)
            b, d = Wd, L
        t = 0.06
        for z in zones:
            c = col(z["cpe"])
            lab = f"{z['zone']} {z['cpe']:+.2f}"
            if z["surface"] == "Windward wall":
                (x0, z0), (x1, z1) = world(0, 0), world(0, b)
                cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
                sx, sz = (abs(x1 - x0) or t), (abs(z1 - z0) or t)
                sc.box("walls", (cx, he / 2, cz), (sx, he, sz), c, opacity=0.9)
                sc.label("walls", lab, (cx, he / 2, cz), "result")
            elif z["surface"] == "Leeward wall":
                (x0, z0), (x1, z1) = world(d, 0), world(d, b)
                cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
                sx, sz = (abs(x1 - x0) or t), (abs(z1 - z0) or t)
                sc.box("walls", (cx, he / 2, cz), (sx, he, sz), c, opacity=0.9)
                sc.label("walls", lab, (cx, he / 2, cz), "result")
            elif z["surface"] == "Side walls":
                u0, u1 = z["u"]
                for v in (0, b):
                    (x0, z0), (x1, z1) = world(u0, v), world(u1, v)
                    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
                    sx, sz = (abs(x1 - x0) or t), (abs(z1 - z0) or t)
                    sc.box("walls", (cx, he / 2, cz), (sx, he, sz), c, opacity=0.9)
                (x0, z0), (x1, z1) = world(u0, 0), world(u1, 0)
                sc.label("walls", lab, ((x0 + x1) / 2, he * 0.6, (z0 + z1) / 2), "")
        # roof surface (zones as coloured patches, or plain for hipped roofs)
        done = set()
        for z in zones:
            if roof == ROOFS[4] or n > 1:
                break
            if z["surface"] != "Roof" or not z.get("rects") or z["zone"][0] + z["zone"] in done:
                continue
            done.add(z["zone"][0] + z["zone"])
            if z.get("signed") and z["zone"].endswith("(+)"):
                continue  # draw the negative case
            for (u0, u1, v0, v1) in z["rects"]:
                for (a0, a1) in cls._split(u0, u1, v0, v1, world, roof):
                    pts = [world(*p) for p in (a0, (a0[0], a1[1]), a1, (a1[0], a0[1]))]
                    verts = [(px, y(px, pz) + 0.03, pz) for px, pz in pts]
                    sc.mesh("roof", verts, [(0, 1, 2), (0, 2, 3)], col(z["cpe"]), opacity=0.95)
            (u0, u1, v0, v1) = z["rects"][0]
            px, pz = world((u0 + u1) / 2, (v0 + v1) / 2)
            sc.label("roof", f"{z['zone']} {z['cpe']:+.2f}", (px, y(px, pz) + 0.3, pz), "result")
        if roof in (ROOFS[3], ROOFS[4]) or n > 1 or not any(
                z.get("rects") for z in zones if z["surface"] == "Roof"):
            n = 16
            verts, faces = [], []
            for i in range(n + 1):
                for j in range(n + 1):
                    px, pz = -L / 2 + L * i / n, -Wd / 2 + Wd * j / n
                    verts.append((px, y(px, pz), pz))
            for i in range(n):
                for j in range(n):
                    k = i * (n + 1) + j
                    faces += [(k, k + 1, k + n + 2), (k, k + n + 2, k + n + 1)]
            sc.mesh("roof", verts, faces, "#9aa5b1", opacity=0.9)
            roofz = [z for z in zones if z["surface"] == "Roof"]
            txt = ", ".join(f"{z['zone']} {z['cpe']:+.2f}" for z in roofz)
            sc.label("roof", txt, (0, h + 0.8, 0), "result")
        # wind arrow
        (x0, z0), (x1, z1) = world(-0.25 * d - 2, b / 2), world(-2, b / 2)
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz)
        sc.arrow("wind", (x0, h * 0.6, z0), (dx / ln, 0, dz / ln), ln, "#2a6f97")
        sc.label("wind", f"θ = {th}°", (x0, h * 0.6 + 0.6, z0), "")
        sc.legend_item(heat_color(0.0), calc.tr("suction (c_pe < 0)"))
        sc.legend_item(heat_color(1.0), calc.tr("pressure (c_pe > 0)"))
        return sc.to_dict()

    @staticmethod
    def _split(u0, u1, v0, v1, world, roof):
        """Split a plan rectangle at the ridge (z = 0) so each piece is planar."""
        if roof not in (ROOFS[2],):
            return [((u0, v0), (u1, v1))]
        zs = [world(u0, v0)[1], world(u1, v1)[1]]
        if min(zs) < 0 < max(zs):
            # ridge crossing: find the parameter along u or v where z = 0
            pu = world(u1, v0)[1] != world(u0, v0)[1]
            if pu:
                um = u0 + (u1 - u0) * (0 - zs[0]) / (zs[1] - zs[0])
                return [((u0, v0), (um, v1)), ((um, v0), (u1, v1))]
            vm = v0 + (v1 - v0) * (0 - zs[0]) / (zs[1] - zs[0])
            return [((u0, v0), (u1, vm)), ((u0, vm), (u1, v1))]
        return [((u0, v0), (u1, v1))]

    @staticmethod
    def _canopy_scene(calc, mono, L, Wd, h, alpha, cf_min) -> dict:
        sc = Scene3D("wind_canopy", calc.tr)
        sc.layer("roof", "Roof")
        sc.layer("wind", "Wind")
        t = math.tan(math.radians(alpha))
        if mono:
            ys = (h - Wd * abs(t), h)
            verts = [(-L / 2, ys[0], -Wd / 2), (L / 2, ys[0], -Wd / 2), (L / 2, ys[1], Wd / 2),
                     (-L / 2, ys[1], Wd / 2)]
            faces = [(0, 1, 2), (0, 2, 3)]
        else:
            hr = h if alpha >= 0 else h + Wd / 2 * t
            he = h - Wd / 2 * t if alpha >= 0 else h
            verts = [(-L / 2, he, -Wd / 2), (L / 2, he, -Wd / 2), (L / 2, hr, 0), (-L / 2, hr, 0),
                     (L / 2, he, Wd / 2), (-L / 2, he, Wd / 2)]
            faces = [(0, 1, 2), (0, 2, 3), (3, 2, 4), (3, 4, 5)]
        sc.mesh("roof", verts, faces, heat_color(0.15), opacity=0.9)
        for x in (-L / 2 + 0.2, L / 2 - 0.2):
            for z in (-Wd / 2 + 0.2, Wd / 2 - 0.2):
                top = min(v[1] for v in verts)
                sc.box("roof", (x, top / 2, z), (0.25, top, 0.25), "#7d8b99")
        sc.arrow("wind", (0, h * 0.7, -Wd / 2 - 4), (0, 0, 1), 3, "#2a6f97")
        sc.label("roof", f"c_f,min = {cf_min:+.2f}", (0, h + 0.8, 0), "result")
        return sc.to_dict()
