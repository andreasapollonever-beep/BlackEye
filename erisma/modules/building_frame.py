"""Whole RC building: 3D frame analysis, EN 1998-1 modal spectrum checks and member design.

Front end of :mod:`erisma.structure` — the engineer describes the grid and
the loads, everything else (model, slab load distribution, diaphragms,
masses, modal analysis, accidental torsion, drift, θ, reinforcement of every
beam and column) is done automatically and written step by step.
"""

from __future__ import annotations

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..report.scene3d import PALETTE, Scene3D, heat_color
from ..report.svg import spectrum_plot
from ..structure import (StructureError, analyse, analyse_pdelta, critical_load_factor,
                         modal)
from ..structure.builder import BuildingSpec, build
from ..structure.builder import grid_label
from ..structure.design import (MemberDesign, capacity_design, capacity_shears, design_beams,
                                design_columns, design_footings, design_slabs, design_walls)
from ..structure.combinations import Case, generate
from ..structure.modal import ec8_spectrum
from ..structure.model import Msg
from ..structure.seismic import seismic_check

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50"]
DRIFT = {"Brittle non-structural elements (α = 0.005)": 0.005,
         "Ductile non-structural elements (α = 0.0075)": 0.0075,
         "No interfering non-structural elements (α = 0.010)": 0.010}
CATEGORY = ["A", "B", "C", "D", "E"]


@register
class BuildingFrame(DesignModule):
    id = "building_frame"
    title = "RC building — 3D analysis and design"
    category = "Analysis"
    standard = "EN 1998-1 / EN 1992-1-1"
    description = ("Give the grid, storeys, sizes and loads: 3D model, modal response spectrum "
                   "analysis, drift and θ checks and the reinforcement of every beam and column.")
    has_3d = True
    uses_annex = True
    fields = [
        Field("x_spans", "Spans along X", kind="table", group="Grid",
              default=[{"L": 5.0}, {"L": 4.5}, {"L": 5.0}],
              columns=[Field("L", "Span", "m", 5.0, min=1.0, max=15.0)],
              help="Grid lines 1, 2, 3… along X; one row per bay."),
        Field("y_spans", "Spans along Y", kind="table", group="Grid",
              default=[{"L": 5.0}, {"L": 5.0}],
              columns=[Field("L", "Span", "m", 5.0, min=1.0, max=15.0)],
              help="Grid lines A, B, C… along Y; one row per bay."),
        Field("storeys", "Storeys (bottom up)", kind="table", group="Grid",
              default=[{"h": 3.2}, {"h": 3.0}, {"h": 3.0}],
              columns=[Field("h", "Storey height", "m", 3.0, min=2.0, max=8.0)],
              help="Floor-to-floor heights; the base is fixed."),
        Field("walls", "Shear walls", kind="table", group="Grid",
              default=[{"at": "B1", "dir": "Y", "L": 2.0, "t": 250.0},
                       {"at": "B4", "dir": "Y", "L": 2.0, "t": 250.0},
                       {"at": "A2", "dir": "X", "L": 2.0, "t": 250.0},
                       {"at": "C3", "dir": "X", "L": 2.0, "t": 250.0}],
              columns=[Field("at", "Grid point", kind="text", default="A1"),
                       Field("dir", "Direction", kind="choice", choices=["X", "Y"], default="X"),
                       Field("L", "Length", "m", 2.0, min=1.0, max=10.0),
                       Field("t", "Thickness", "mm", 250.0, min=150, max=600)],
              help="A wall replaces the column at that grid point (e.g. B1). Beams framing "
                   "along the wall get rigid end zones of half its length."),
        Field("loads", "Load cases and combinations", kind="json", default={}, group="Loads",
              help="Extra load cases (permanent, imposed, snow) with area, line and point loads, "
                   "and user combinations — edited in Erisma Structure."),
        Field("layout", "Plan layout", kind="json", default={}, group="Grid",
              help="Missing columns/beams, slab openings and member sizes — drawn in "
                   "Erisma Structure."),
        Field("col_b", "Column side along X", "mm", 400.0, min=200, max=1500, group="Members"),
        Field("col_h", "Column side along Y", "mm", 400.0, min=200, max=1500, group="Members"),
        Field("beam_b", "Beam width", "mm", 250.0, min=150, max=800, group="Members"),
        Field("beam_h", "Beam depth (incl. slab)", "mm", 500.0, min=250, max=1500,
              group="Members"),
        Field("slab_t", "Slab thickness", "mm", 180.0, min=100, max=400, group="Members"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C25/30",
              group="Members"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Members"),
        Field("cover", "Cover to links", "mm", 30.0, min=15, max=60, group="Members"),
        Field("g_finish", "Finishes and partitions g", "kN/m²", 1.5, min=0, max=20,
              group="Loads", help="Floor finishes, screed, light partitions."),
        Field("q", "Imposed load q", "kN/m²", 2.0, min=0, max=20, group="Loads",
              help="EN 1991-1-1: dwellings 2.0, offices 3.0, assembly 4.0–5.0 kN/m²."),
        Field("q_roof", "Roof imposed load", "kN/m²", 2.0, min=0, max=20, group="Loads"),
        Field("g_wall", "Facade walls on perimeter beams", "kN/m", 8.0, min=0, max=40,
              group="Loads", help="e.g. 3.6 kN/m² brick wall × 2.2 m = 8 kN/m. Not on the roof."),
        Field("category", "Use category (ψ factors)", kind="choice", choices=CATEGORY,
              default="A", group="Loads",
              help="EN 1990 Table A1.1: A dwellings, B offices, C assembly, D shopping, E storage."),
        Field("seismic", "Seismic design (EN 1998-1)", kind="bool", default=True,
              group="Seismic"),
        Field("ag", "Reference ground acceleration a_gR", "", 0.16, min=0, max=0.6,
              group="Seismic", show_if="seismic",
              help="In g. Pick a zone with the buttons of the selected National Annex."),
        Field("ground", "Ground type", kind="choice", choices=list("ABCDE"), default="B",
              group="Seismic", show_if="seismic"),
        Field("importance", "Importance class", kind="choice", choices=["I", "II", "III", "IV"],
              default="II", group="Seismic", show_if="seismic"),
        Field("q_factor", "Behaviour factor q", "", 3.9, min=1.0, max=6.0, group="Seismic",
              show_if="seismic", help="RC frame DCM multi-storey: 3.0·αu/α1 = 3.0·1.3 = 3.9."),
        Field("phi_E", "φ for ψ_E = φ ψ_2 (mass)", "", 1.0, min=0.5, max=1.0, group="Seismic",
              show_if="seismic", help="EN 1998-1 Table 4.2: 1.0 roof, 0.8 correlated storeys, "
                                      "0.5 independently occupied storeys."),
        Field("drift", "Non-structural elements (drift limit)", kind="choice", choices=list(DRIFT),
              default=list(DRIFT)[0], group="Seismic", show_if="seismic"),
        Field("cracked", "Cracked stiffness factor", "", 0.5, min=0.3, max=1.0, group="Seismic",
              show_if="seismic", help="EN 1998-1 4.3.1(7): 50 % of the uncracked stiffness."),
        Field("regularity", "Apply EC8 regularity consequences to q", kind="bool", default=True,
              group="Seismic", show_if="seismic",
              help="Not regular in elevation: q × 0.8 (4.2.3.1(7)); torsionally flexible: "
                   "q ≤ 2.0 (Table 5.1)."),
        Field("n_modes", "Number of modes", kind="int", default=12, min=3, max=60,
              group="Seismic", show_if="seismic"),
        Field("pdelta", "P-Δ effects (geometric stiffness)", kind="bool", default=False,
              group="Seismic", show_if="seismic",
              help="Include the destabilising effect of the gravity loads G + ψ2Q in the "
                   "stiffness (all analyses)."),
        Field("design", "Design the reinforcement of all members", kind="bool", default=True,
              group="Design"),
        Field("slabs", "Design the slabs (EN 1992-1-1)", kind="bool", default=True,
              group="Design", show_if="design",
              help="Every slab panel as a two-way slab, continuous where a neighbour panel "
                   "exists; bottom and top bars are chosen automatically."),
        Field("foundations", "Design the footings (EN 1997-1)", kind="bool", default=True,
              group="Foundations", show_if="design",
              help="A pad footing under every column and wall, sized for bearing, sliding and "
                   "eccentricity; seismic actions with capacity design (EN 1998-1 4.4.2.6)."),
        Field("found_type", "Foundation type", kind="choice", group="Foundations",
              choices=["Raft (Winkler)", "Foundation beams (Winkler)", "Isolated pad footings"],
              default="Raft (Winkler)",
              help="Raft: a plate under the whole building on elastic soil springs, analysed with "
                   "finite elements together with the frame. Foundation beams along the grid "
                   "lines on springs, or pad footings under a fixed base."),
        Field("raft_t", "Raft thickness", "mm", 800.0, min=300, max=2000, group="Foundations",
              show_if="found_type=Raft (Winkler)"),
        Field("raft_over", "Raft overhang beyond the outer grid lines", "m", 1.0, min=0.0,
              max=3.0, group="Foundations", show_if="found_type=Raft (Winkler)"),
        Field("raft_mesh", "Raft mesh size", "m", 1.0, min=0.3, max=2.0, group="Foundations",
              show_if="found_type=Raft (Winkler)",
              help="Finite-element size; smaller is more accurate but slower."),
        Field("fb_B", "Foundation beam flange width B", "m", 1.2, min=0.4, max=4.0,
              group="Foundations", show_if="found_type=Foundation beams (Winkler)"),
        Field("fb_bw", "Foundation beam web width b_w", "mm", 500.0, min=250, max=1000,
              group="Foundations", show_if="found_type=Foundation beams (Winkler)"),
        Field("fb_h", "Foundation beam depth h", "mm", 1200.0, min=500, max=2500,
              group="Foundations", show_if="found_type=Foundation beams (Winkler)"),
        Field("ks", "Modulus of subgrade reaction k_s", "MN/m³", 40.0, min=5, max=300,
              group="Foundations",
              help="Typical: loose sand 10–25, medium sand 25–60, dense sand 60–120, stiff "
                   "clay 25–50 MN/m³ (or from a plate-load test / the geotechnical report)."),
        Field("D_found", "Founding depth D", "m", 1.2, min=0.5, max=5.0, group="Foundations",
              show_if="foundations"),
        Field("phi_soil", "Soil φ'k", "°", 30.0, min=15, max=45, group="Foundations",
              show_if="foundations"),
        Field("c_soil", "Soil c'k", "kN/m²", 5.0, min=0, max=100, group="Foundations",
              show_if="foundations"),
        Field("gamma_soil", "Soil γ", "kN/m³", 19.0, min=14, max=23, group="Foundations",
              show_if="foundations"),
        Field("capacity", "Capacity design (EN 1998-1 DCM)", kind="bool", default=True,
              group="Design", show_if="design",
              help="ΣM_Rc ≥ 1.3 ΣM_Rb at the joints (4.4.2.3) and shears from the flexural "
                   "capacities (5.4.2.2, 5.4.2.3)."),
    ]

    # ------------------------------------------------------------------ run
    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        for key in ("x_spans", "y_spans", "storeys"):
            if not inp[key]:
                raise InputError("Add at least one row", key)
        seismic = inp["seismic"]
        spec = BuildingSpec(
            [r["L"] for r in inp["x_spans"]], [r["L"] for r in inp["y_spans"]],
            [r["h"] for r in inp["storeys"]], inp["col_b"], inp["col_h"], inp["beam_b"],
            inp["beam_h"], inp["slab_t"], float(inp["concrete"].split("/")[0][1:]),
            inp["cracked"] if seismic else 1.0, inp["g_finish"], inp["q"], inp["q_roof"],
            inp["g_wall"],
            [{"at": r["at"], "dir": r["dir"], "L": r["L"], "t": r["t"]} for r in inp["walls"]],
            inp["layout"],
            {"B": inp["fb_B"], "bw": inp["fb_bw"], "h": inp["fb_h"], "ks": inp["ks"], "n": 6}
            if inp["found_type"].startswith("Foundation beams") else
            {"type": "raft", "t": inp["raft_t"], "over": inp["raft_over"], "ks": inp["ks"],
             "mesh": inp["raft_mesh"]} if inp["found_type"].startswith("Raft") else None,
            cls._user_cases(inp))
        if inp["beam_h"] <= inp["slab_t"]:
            raise InputError("The beam depth must be greater than the slab thickness", "beam_h")
        calc.issues = []   # machine-readable failures, used by the automatic sizing
        g_unf, _, g_q = na.combos["DA1-C1"][:3]
        psi0, psi1, psi2 = na.psi[inp["category"]]
        pdelta = seismic and inp["pdelta"]
        cases = cls._cases(inp, na, spec)
        combos = generate(cases, g_unf, g_q, (inp["loads"] or {}).get("combos"))
        qp = next(c for c in combos if c.kind == "SLS-qp").factors
        try:
            model, info = build(spec)
            an = analyse_pdelta(model, qp) if pdelta else analyse(model)
            lin = analyse(model) if pdelta else an
            acr = critical_load_factor(lin, qp)
        except StructureError as exc:
            fld = "walls" if "Wall" in exc.text else "layout" if (
                "Layout" in exc.text or "Slab panel" in exc.text or "Beam {g}" in exc.text) else None
            raise InputError(exc.message(calc.lang), fld) from exc
        res = an.run_all()
        ulss = [(c.name, an.combine(res, c.factors, c.name)) for c in combos
                if c.kind in ("ULS", "user")]
        uls = ulss
        quasi = an.combine(res, qp, "G+ψ2Q")
        # characteristic sums for the foundation modules (permanent / variable)
        gsum = {c.name: 1.0 for c in cases if c.type == "G"}
        qsum = {c.name: 1.0 for c in cases if c.type != "G"}
        res_agg = {"G": an.combine(res, gsum, "ΣG"),
                   "Q": an.combine(res, qsum, "ΣQ") if qsum else res["G"].scaled(0.0, "ΣQ")}
        calc.combos, calc.cases, calc._res_agg = combos, cases, res_agg

        cls._model_section(calc, spec, info, an, res)
        cls._loads_section(calc, cases, combos, res)
        calc.heading("Global stability")
        calc.formula("α_cr", calc.tr("eigenvalue of (K + α K_G) φ = 0 for G + {p:g}Q", p=psi2),
                     acr, "", "Elastic critical load factor", ref="EN 1993-1-1 5.2.1(3)", dp=1)
        if not pdelta:
            calc.check_min("α_cr ≥ 10 (first-order analysis sufficient)", acr, 10.0, "",
                           "EN 1993-1-1 Eq. 5.1",
                           hint="Switch on P-Δ effects, or stiffen the structure.")
            if acr < 10:
                calc.issues.append({"type": "acr"})
        if pdelta:
            calc.note("P-Δ: the geometric stiffness of the axial forces from G + {p:g}Q is "
                      "included in every analysis below.", p=psi2)
        seis = None
        if seismic:
            seis = cls._seismic_section(calc, inp, na, an, psi2, info, cases)
        designs = []
        if inp["design"]:
            designs = cls._design_section(calc, inp, spec, info, res, seis, uls, quasi,
                                          (g_unf, g_q, psi2))
        calc.building_qty = cls._quantities(spec, info, an, designs)
        calc.structure = cls._results(calc, info, seis, designs)
        calc._uls, calc._quasi = uls[0][1], quasi
        calc.model3d = cls._scene(calc, spec, info, an, seis, designs)

    # ---------------------------------------------------------------- model
    @staticmethod
    def _model_section(calc, spec, info, an, res):
        xs, ys, zs = info["xs"], info["ys"], info["zs"]
        calc.heading("Structural model")
        calc.text("3D frame of {nx}×{ny} grid lines and {ns} storeys: {nc} columns and {nb} beams, "
                  "fixed at the base, a rigid diaphragm at every floor (EN 1998-1 4.3.1(4)).",
                  nx=len(xs), ny=len(ys), ns=len(spec.heights), nc=len(info["columns"]),
                  nb=len(info["beams_x"]) + len(info["beams_y"]))
        calc.input("L_x × L_y", xs[-1], "m", calc.tr("Plan {x:.2f} × {y:.2f} m",
                                                    x=xs[-1] / 1000, y=ys[-1] / 1000))
        calc.input("H", zs[-1], "m", "Height above the base")
        conc = info["concrete"]
        calc.formula("E_cm", "22 000 ((f_ck + 8)/10)^0.3", conc.E / spec.cracked, "N/mm²",
                     "Modulus of elasticity", ref="EN 1992-1-1 Table 3.1", dp=0)
        if spec.cracked != 1.0:
            calc.formula("E_eff", f"{spec.cracked:g} E_cm", conc.E, "N/mm²",
                         "Cracked stiffness", ref="EN 1998-1 4.3.1(7)", dp=0)
        calc.text("Timoshenko 3D beam elements (bending, shear, axial and torsional stiffness); "
                  "{n} unknown displacements.", n=an.dofmap.n)
        calc.heading("Gravity loads")
        g_slab = calc.formula("g_slab", "25 kN/m³ · t + g_finish",
                              25e-6 * spec.slab_t + spec.g_finish, "kN/m²",
                              "Slab self-weight and finishes")
        del g_slab
        calc.text("Slab loads reach the beams by the 45° rule (triangles on the short sides, "
                  "trapezoids on the long sides). Beam self-weight is taken below the slab only; "
                  "columns with their full section.")
        rows = []
        for case in res:
            r = res[case]
            R = sum(v[2] for v in r.reactions.values())
            rows.append([case, f"{-r.applied[2] / 1e3:.1f}", f"{R / 1e3:.1f}",
                         f"{np.abs(r.equilibrium()[:3]).max():.2e}"])
        calc.table(["Load case", "Σ loads [kN]", "Σ reactions [kN]", "Residual [N]"], rows,
                   caption="Equilibrium check — the reactions balance the applied loads")
        A = info["plan_area"] / 1e6 * len(spec.heights)
        calc.formula("G/A", "Σ G / (n A)", res["G"].applied[2] * -1 / (A * 1e6), "kN/m²",
                     "Average dead load per floor area", dp=2)

    # -------------------------------------------------------------- seismic
    @staticmethod
    def _user_cases(inp) -> list[dict]:
        """User load cases from the json field, converted to N and mm."""
        out = []
        for c in (inp["loads"] or {}).get("cases", []):
            name = str(c.get("name", "")).strip()
            if not name or name in ("G", "Q"):
                raise InputError("Load case names must be unique and different from G and Q",
                                 "loads")
            loads = []
            for ld in c.get("loads", []):
                k = ld.get("kind")
                d = {**ld}
                if k == "area":
                    d["q"] = float(ld.get("q", 0)) * 1e-3          # kN/m² → N/mm²
                elif k == "line":
                    d["w"] = float(ld.get("w", 0))                 # kN/m = N/mm
                elif k == "point":
                    d["F"] = float(ld.get("F", 0)) * 1e3           # kN → N
                else:
                    continue
                loads.append(d)
            out.append({"name": name, "type": c.get("type", "G"),
                        "category": c.get("category", "A"), "loads": loads})
        return out

    @staticmethod
    def _cases(inp, na, spec) -> list:
        cases = [Case("G", "G"), Case("Q", "Q", tuple(na.psi[inp["category"]]))]
        for c in spec.cases:
            if c["type"] == "G":
                cases.append(Case(c["name"], "G"))
            elif c["type"] == "S":
                cases.append(Case(c["name"], "S", tuple(na.psi["snow_low"])))
            else:
                cases.append(Case(c["name"], "Q", tuple(na.psi.get(c.get("category", "A"),
                                                                   na.psi["A"]))))
        return cases

    @staticmethod
    def _loads_section(calc, cases, combos, res) -> None:
        calc.heading("Load cases and combinations (EN 1990)")
        tname = {"G": calc.tr("permanent"), "Q": calc.tr("imposed"), "S": calc.tr("snow")}
        calc.table(["Load case", "Type", "ψ0", "ψ1", "ψ2", "Σ F_z [kN]"],
                   [[c.name, tname[c.type], *([f"{v:g}" for v in c.psi] if c.type != "G" else
                                              ["—"] * 3),
                     f"{-res[c.name].applied[2] / 1e3:.1f}"] for c in cases],
                   caption="G: self-weight, slabs and finishes; Q: imposed load of the floors; "
                           "further cases as defined by the engineer")
        kinds = {"ULS": calc.tr("ULS 6.10"), "user": calc.tr("user"),
                 "SLS-char": calc.tr("SLS characteristic"), "SLS-freq": calc.tr("SLS frequent"),
                 "SLS-qp": calc.tr("SLS quasi-permanent"), "seismic": calc.tr("seismic 6.12b")}
        calc.table(["Combination", "Kind", "Expression"],
                   [[c.name, kinds[c.kind], c.text()] for c in combos],
                   caption="Members are designed for the envelope of all ULS combinations and "
                           "of the seismic combination G + Σψ2Q ± E")

    @staticmethod
    def _regularity_section(calc, inp, an, md, info) -> float:
        """EN 1998-1 4.2.3: regularity in plan and elevation, torsional flexibility → q."""
        from ..structure.regularity import regularity
        reg = regularity(an, md, info)
        calc.heading("Structural regularity (EN 1998-1 4.2.3)")
        ok = lambda b: "✓" if b else "✗"  # noqa: E731
        calc.table(["Floor", "x_CM [m]", "y_CM [m]", "x_CR [m]", "y_CR [m]", "e_0x [m]", "e_0y [m]",
                    "r_x [m]", "r_y [m]", "l_s [m]", "e_0 ≤ 0.3 r", "r ≥ l_s"],
                   [[str(f.index), f"{f.cm[0] / 1e3:.2f}", f"{f.cm[1] / 1e3:.2f}",
                     f"{f.cr[0] / 1e3:.2f}", f"{f.cr[1] / 1e3:.2f}", f"{f.e0x / 1e3:.2f}",
                     f"{f.e0y / 1e3:.2f}", f"{f.rx / 1e3:.2f}", f"{f.ry / 1e3:.2f}",
                     f"{f.ls / 1e3:.2f}", ok(f.ok_ecc), ok(f.ok_radius)] for f in reg.floors],
                   caption="Centre of mass CM, centre of stiffness CR, torsional radii r and radius "
                           "of gyration l_s per floor (4.2.3.2(6)); CR, r from the 3×3 floor "
                           "flexibility under unit loads at that floor")
        calc.table(["Criterion", "Value", "Limit", ""],
                   [[calc.tr("Compactness: recesses / floor area"), f"{reg.compact_ratio:.1%}",
                     "5 %", ok(reg.compact_ratio <= 0.05)],
                    [calc.tr("Slenderness λ = L_max / L_min"), f"{reg.slenderness:.2f}", "4",
                     ok(reg.slenderness <= 4)]],
                   caption="EN 1998-1 4.2.3.2(4), (5)")
        rows = []
        for n, m_ in enumerate(reg.storey_m):
            rows.append([str(n + 1), f"{m_ * 1e3:.0f}", f"{reg.storey_k['X'][n] / 1e3:.0f}",
                         f"{reg.storey_k['Y'][n] / 1e3:.0f}"])
        calc.table(["Storey", "m [t]", "K_X [kN/mm]", "K_Y [kN/mm]"], rows,
                   caption="Storey mass and lateral stiffness (V_i / interstorey drift under the "
                           "lateral-force pattern). EN 1998-1 4.2.3.3(3) gives no numerical "
                           "limits; flagged here: stiffness < 70 % of the storey above or mass > "
                           "150 % of the storey above (indicative)")
        verdict = calc.tr("regular") if reg.plan_regular else calc.tr("not regular")
        calc.label("Plan", verdict, "Regularity in plan (4.2.3.2)")
        calc.label("Elevation", calc.tr("regular") if reg.elevation_regular else
                   calc.tr("not regular"), "Regularity in elevation (4.2.3.3)")
        calc.label("Torsion", calc.tr("torsionally flexible") if reg.torsionally_flexible else
                   calc.tr("torsionally stiff"), "r ≥ l_s in both directions (5.1.2)")
        q = inp["q_factor"]
        q_used = reg.q_effective(q) if inp["regularity"] else q
        if not reg.plan_regular:
            calc.note("Not regular in plan: a spatial model is required (Table 4.1) — used here.")
        if q_used < q - 1e-9:
            calc.formula("q", calc.tr("{q:g} reduced for irregularity (4.2.3.1(7), Table 5.1)",
                                      q=q), q_used, "", "Behaviour factor used", dp=2)
        elif not inp["regularity"] and (not reg.elevation_regular or reg.torsionally_flexible):
            calc.warn("The EC8 regularity consequences on q are switched off — justify q.")
        calc.regularity = reg
        calc.q_used = q_used
        return q_used

    @classmethod
    def _seismic_section(cls, calc, inp, na, an, psi2, info, cases):
        psiE = inp["phi_E"] * psi2
        calc.heading("Masses and modal analysis")
        calc.formula("ψ_E", "φ ψ_2", psiE, "", "Combination coefficient for the mass",
                     ref="EN 1998-1 4.2.4", dp=2)
        source = {c.name: (1.0 if c.type == "G" else inp["phi_E"] * c.psi[2]) for c in cases}
        md = modal(an, source, n_modes=inp["n_modes"])
        calc.formula("M", "Σ (G + ψ_E Q) / g", md.total_mass["X"] * 1e3, "",
                     "Seismic mass above the base [t]", dp=1)
        kind = {"X": calc.tr("translation X"), "Y": calc.tr("translation Y"),
                "RZ": calc.tr("torsion")}
        table = md.table()
        rows = [[str(r["mode"]), f"{r['T']:.3f}", f"{r['mX'] * 100:.1f}", f"{r['sumX'] * 100:.1f}",
                 f"{r['mY'] * 100:.1f}", f"{r['sumY'] * 100:.1f}",
                 f"{r.get('mRZ', 0.0) * 100:.1f}", kind.get(r["type"], "")] for r in table]
        calc.table(["Mode", "T [s]", "m_X [%]", "Σm_X [%]", "m_Y [%]", "Σm_Y [%]", "m_RZ [%]",
                    "Type"], rows,
                   caption="Periods, effective modal masses (translation and rotation about the "
                           "vertical axis) and the character of each mode")
        calc.modes_table = table
        if table and table[0]["type"] == "RZ":
            calc.warn("The first mode is torsional: the building is torsionally sensitive — add "
                      "stiffness (walls) at the perimeter.")
        for d in ("X", "Y"):
            calc.check_min(calc.tr("Σ effective mass in {d} ≥ 90 %", d=d),
                           float(md.cumulative(d)[-1]), 0.90, "", "EN 1998-1 4.3.3.3.1(3)",
                           hint="Increase the number of modes.")
            if md.cumulative(d)[-1] < 0.90:
                calc.issues.append({"type": "modes"})

        q_used = cls._regularity_section(calc, inp, an, md, info)
        calc.heading("Design spectrum")
        sp = ec8_spectrum(inp["ag"], inp["ground"], q_used, inp["importance"],
                          calc.project.annex)
        calc.input("a_gR", inp["ag"], "", "Reference peak ground acceleration [g]", dp=3)
        calc.formula("a_g", "γ_I a_gR", sp.ag, "", "Design ground acceleration [g]",
                     ref="3.2.1(3)", dp=3)
        calc.table(["Ground type", "S", "T_B [s]", "T_C [s]", "T_D [s]", "q"],
                   [[inp["ground"], f"{sp.S:g}", f"{sp.TB:g}", f"{sp.TC:g}", f"{sp.TD:g}",
                     f"{sp.q:g}"]], caption="EN 1998-1 Table 3.2 (National Annex), Type 1")
        T = np.linspace(0, 4, 161)
        T1 = float(md.periods[0])
        calc.figure(spectrum_plot(T, sp(T), T1, float(sp([T1])[0]),
                                  calc.tr("Design spectrum S_d(T) [g]")),
                    "Design spectrum and fundamental period")

        alpha = DRIFT[inp["drift"]]
        seis = seismic_check(an, md, sp, inp["importance"], calc.project.annex, alpha=alpha)
        calc.heading("Response spectrum analysis")
        calc.text("Modal responses combined with CQC (5 % damping), both horizontal directions; "
                  "accidental eccentricity ±0.05 L (4.3.2) as storey torsional moments "
                  "(4.3.3.3.3); E = max(E_X + 0.3 E_Y, 0.3 E_X + E_Y) (4.3.3.5.1).")
        for d in ("X", "Y"):
            calc.formula(f"F_b,{d}", "CQC", seis.base_shear[d], "kN",
                         calc.tr("Base shear in {d}", d=d), ref="4.3.3.3")
        calc.heading("Storey checks")
        calc.formula("ν", "", seis.nu, "", "Displacement reduction factor", ref="4.4.3.2(2)",
                     dp=2)
        calc.input("α", alpha, "", "Drift limit ratio", dp=4)
        rows = []
        for s in seis.storeys:
            rows.append([str(s.index), f"{s.z / 1000:.2f}", f"{s.mass * 1e3:.0f}",
                         f"{s.V['X'] / 1e3:.0f}", f"{s.V['Y'] / 1e3:.0f}",
                         f"{s.drift['X']:.1f}", f"{s.drift['Y']:.1f}",
                         f"{s.theta['X']:.3f}", f"{s.theta['Y']:.3f}"])
        calc.table(["Storey", "z [m]", "m [t]", "V_X [kN]", "V_Y [kN]", "d_r,X [mm]",
                    "d_r,Y [mm]", "θ_X", "θ_Y"], rows,
                   caption="d_r = q d_e (4.3.4) at the most stressed column line; "
                           "θ = P_tot d_r / (V_tot h) (Eq. 4.28)")
        for s in seis.storeys:
            for d in ("X", "Y"):
                calc.check(calc.tr("Storey {i} drift {d}: d_r ν ≤ α h", i=s.index, d=d),
                           s.drift[d] * seis.nu, alpha * s.h, "mm", "EN 1998-1 4.4.3.2",
                           hint="Increase the column sizes or add walls to stiffen the building.")
                if s.drift[d] * seis.nu > alpha * s.h:
                    calc.issues.append({"type": "drift", "dir": d, "storey": s.index})
        th = seis.theta_max
        calc.check("Second-order sensitivity θ ≤ 0.30", th, 0.30, "", "EN 1998-1 4.4.2.2(4)",
                   hint="Stiffen the structure (larger columns or walls).")
        if th > 0.3:
            calc.issues.append({"type": "drift", "dir": "X", "storey": 0})
            calc.issues.append({"type": "drift", "dir": "Y", "storey": 0})
        for d in ("X", "Y"):
            if seis.amplification[d] > 1.0:
                calc.note("θ > 0.10 in {d}: seismic effects multiplied by 1/(1 − θ) = {a:.3f} "
                          "(4.4.2.2(3)).", d=d, a=seis.amplification[d])
        if th <= 0.10:
            calc.note("θ ≤ 0.10 in every storey: second-order effects need not be considered.")
        for w in seis.warnings:
            calc.warn(w.text, **w.kw)
        return seis

    # --------------------------------------------------------------- design
    @classmethod
    def _design_section(cls, calc, inp, spec, info, res, seis, uls, quasi, factors):
        g, gq, psi2 = factors
        calc.heading("Member design")
        combos = calc.tr("ULS {g:g}G + {q:g}Q (EN 1990 6.10)", g=g, q=gq)
        if seis is not None:
            combos += "; " + calc.tr("seismic G + {p:g}Q ± E (6.12b)", p=psi2)
        calc.text("Every beam and column is designed with the EN 1992/1998 modules of this "
                  "program; the lightest bars that pass all checks are chosen. Combinations: {c}.",
                  c=combos)
        calc.note("Columns: braced = no (r_m = 1), l_0 = clear height.")
        if seis is not None and not inp["capacity"]:
            calc.warn("Capacity design is switched off: ΣM_Rc ≥ 1.3 ΣM_Rb (4.4.2.3) and the "
                      "capacity-design shears are not checked.")
        project = calc.project
        cols = {}
        for c in info["columns"]:
            k = int(c[1:c.index(".")])
            cols[c] = (k, spec.heights[k - 1])
        dc = design_columns(res, seis, uls, quasi, spec.col_b, spec.col_h, spec.beam_h,
                            inp["concrete"], cols, project, inp["fyk"], inp["cover"],
                            sizes=info["sizes"])
        beams = {b: int(b[1:b.index(".")]) for b in info["beams_x"] + info["beams_y"]}
        db = design_beams(beams, seis, uls, quasi, spec.beam_b, spec.beam_h, inp["concrete"],
                          project, inp["fyk"], inp["cover"], sizes=info["sizes"])
        walls = {f"W1.{g}": w for g, w in info["wall_spec"].items()}
        dw = design_walls(walls, seis, uls, quasi, inp["concrete"], spec.heights, spec.beam_h,
                          project, inp["fyk"], inp["cover"])
        if seis is not None and inp["capacity"]:
            cls._capacity(calc, inp, spec, info, dc, db, quasi, seis, project)
        ds = cls._slabs(inp, spec, info, project) if inp["slabs"] else []
        df = []
        if inp["foundations"] and info.get("raft"):
            df = cls._raft(calc, inp, spec, info, calc._res_agg, seis, uls, quasi, dc + dw, psi2)
        elif inp["foundations"] and info["fbeams"]:
            df = cls._fbeams(calc, inp, spec, info, calc._res_agg, seis, uls, quasi, dc + dw,
                             project)
        elif inp["foundations"]:
            df = cls._footings(calc, inp, spec, info, calc._res_agg, seis, quasi, dc + dw,
                               project)
        for title, items, hint in (
                ("Columns", dc, "Increase the column size or the concrete class."),
                ("Beams", db, "Increase the beam size or the concrete class."),
                ("Walls (critical region at the base)", dw,
                 "Increase the wall length or thickness."),
                ("Slabs", ds, "Increase the slab thickness."),
                ("Footings", [d for d in df if d.kind == "footing"],
                 "Increase the founding depth or use a strip footing / raft."),
                ("Foundation beams", [d for d in df if d.kind == "fbeam"],
                 "Increase the foundation beam depth or width.")):  # raft: own section
            if not items:
                continue
            calc.heading(title, 2)
            calc.table(["Member", "Reinforcement", "ρ [%]", "Governing", "η", ""],
                       [[d.member, cls._reinf(calc, d.reinforcement), f"{100 * d.rho:.2f}",
                         calc.tr(d.governing, quiet=True), f"{d.utilisation:.2f}",
                         "✓" if d.ok else "✗"] for d in items],
                       caption="η = strength utilisation of the chosen bars (minimum-detailing "
                               "rules are satisfied separately)")
            for k in sorted({d.storey for d in items}):
                grp = [d for d in items if d.storey == k]
                worst = max(grp, key=lambda d: d.utilisation)
                calc.check(calc.tr("{t}, storey {k}: max utilisation ({m})", t=calc.tr(title),
                                   k=k, m=worst.member),
                           worst.utilisation if worst.ok else max(worst.utilisation, 1.01), 1.0,
                           "", None, hint=hint)
            for d in items:
                for n in d.notes:
                    txt = n.message(calc.lang) if hasattr(n, "message") else calc.tr(n)
                    if d.ok:
                        calc.note("Member {m}: {n}", m=d.member, n=txt)
                    else:
                        calc.warn("Member {m}: {n}", m=d.member, n=txt)
        # full step-by-step calculation of the most utilised column and beam
        from ..core import get_module
        for items, label in ((dc, "Critical column {m} — full calculation"),
                             (db, "Critical beam {m} — full calculation"),
                             (dw, "Critical wall {m} — full calculation"),
                             (ds, "Critical slab panel {m} — full calculation"),
                             ([d for d in df if d.kind == "footing"],
                              "Critical footing {m} — full calculation"),
                             ([d for d in df if d.kind == "fbeam"],
                              "Critical foundation beam {m} — full calculation")):
            if not items:
                continue
            d = max(items, key=lambda d: d.utilisation)
            sub = get_module(d.module).calculate(d.inputs, calc.project, calc.lang)
            calc.heading(calc.tr(label, m=d.member))
            calc.text("Design actions from the combination {c}.", c=calc.tr(d.governing,
                                                                             quiet=True))
            for it in sub.items:
                if it.kind == "heading":
                    it.data["level"] = 2
                calc.items.append(it)
        return dc + db + dw + ds + df

    @staticmethod
    def _slabs(inp, spec, info, project):
        xs, ys, op = info["xs"], info["ys"], info["openings"]
        nx, ny = len(xs), len(ys)

        def exists(i, j):
            return 0 <= i < nx - 1 and 0 <= j < ny - 1 and grid_label(i, j) not in op

        panels = []
        for i in range(nx - 1):
            for j in range(ny - 1):
                if not exists(i, j):
                    continue
                panels.append({"id": grid_label(i, j), "lx": xs[i + 1] - xs[i],
                               "ly": ys[j + 1] - ys[j],
                               "cont": {"x0": exists(i - 1, j), "x1": exists(i + 1, j),
                                        "y0": exists(i, j - 1), "y1": exists(i, j + 1)}})
        ns = len(spec.heights)
        qs = {k: (spec.q_roof if k == ns else spec.q) for k in range(1, ns + 1)}
        # user area loads: the largest per panel over the storeys (conservative)
        from ..structure.builder import _sel
        for p_ in panels:
            for c in spec.cases:
                for ld in c["loads"]:
                    if ld.get("kind") == "area" and _sel(ld.get("panels"), p_["id"]):
                        key = "g_extra" if c["type"] == "G" else "q_extra"
                        p_[key] = p_.get(key, 0.0) + ld["q"]
        return design_slabs(panels, spec.slab_t, inp["concrete"], spec.g_finish, qs, project,
                            inp["fyk"])

    @staticmethod
    def _raft(calc, inp, spec, info, res, seis, uls, quasi, vertical, psi2):
        """Raft on Winkler springs: Wood–Armer bending, shear, punching, soil, settlement."""
        from ..structure.design import _omega
        from ..structure.raft import design_raft
        na = get_annex(calc.project.annex)
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyd = na.alpha_cc * fck / na.gamma_c, inp["fyk"] / na.gamma_s
        an = res["G"].analysis
        ef = 1.0
        vd = {d.member: d for d in vertical}
        if seis is not None:
            ef = max(_omega(vd.get(mid), seis, quasi, fcd, fyd)
                     for mid in info["columns"] + info["walls"] if mid[1:3] == "1.")
        cols = {c.split(".", 1)[1]: (f"{c.split('.', 1)[1]}@0", c, *info["sizes"][c])
                for c in info["columns"] if c.startswith("C1.")}
        walls = {}
        for w in info["walls"]:
            if w.startswith("W1."):
                g = w.split(".", 1)[1]
                ws = info["wall_spec"][g]
                walls[g] = (f"{g}@0", ws["L"], ws["t"], ws["dir"])
        soil = {"phi": inp["phi_soil"], "c": inp["c_soil"], "gamma": inp["gamma_soil"]}
        r = design_raft(info["raft"], an, res, uls, quasi, seis, ef, cols, walls,
                        inp["concrete"], inp["fyk"], na, soil, inp["D_found"], psi2)
        calc.raft = r
        x0, x1, y0, y1 = info["raft"]["bounds"]
        calc.heading("Raft foundation", 2)
        calc.text("Raft {a:.2f} × {b:.2f} m, t = {t:g} mm, MITC4 plate finite elements "
                  "({n} elements) on Winkler springs k_s = {k:g} MN/m³, analysed together with "
                  "the frame. Design moments by Wood–Armer.", a=(x1 - x0) / 1000,
                  b=(y1 - y0) / 1000, t=inp["raft_t"], n=len(r["elements"]), k=inp["ks"] * 1e3)
        if seis is not None:
            calc.formula("γ_Rd Ω", "γ_Rd · min(M_Rd/M_Ed of the columns, q)", ef, "",
                         "Overstrength of the seismic action on the foundation",
                         ref="EN 1998-1 4.4.2.6", dp=2)
        names = {"bottom": calc.tr("bottom face"), "top": calc.tr("top face")}
        rows, ok = [], True
        for (face, dirn), m in r["mesh"].items():
            add = f"+ Ø{m['add'][0]}/{m['add'][1]:g}" if m["add"] else "—"
            rows.append([f"{names[face]} {dirn}", f"Ø{m['base'][0]}/{m['base'][1]:g}", add,
                         f"{m['d']:.0f}", f"{m['As_min'] * 1000:.0f}", f"{m['peak'] * 1000:.0f}",
                         f"{m['cap'] * 1000:.0f}"])
        calc.table(["Face / direction", "Basic mesh", "Additional bars", "d [mm]",
                    "A_s,min [mm²/m]", "A_s,req,max [mm²/m]", "A_s,prov [mm²/m]"], rows,
                   caption="EN 1992-1-1 6.1, 9.2.1.1, 9.3.1.1 — additional bars where the "
                           "Wood–Armer demand exceeds the basic mesh")
        for (face, dirn), m in r["mesh"].items():
            calc.check_min(calc.tr("Raft {f} {d}: A_s,prov ≥ A_s,req", f=names[face], d=dirn),
                           m["cap"] * 1000, m["peak"] * 1000, "mm²/m", "EN 1992-1-1 6.1",
                           hint="Increase the raft thickness.")
        sh = r["shear"]
        calc.check("Raft shear away from the columns: V_Ed ≤ V_Rd,c", sh["V"], sh["VRd"], "kN/m",
                   "EN 1992-1-1 6.2.2", hint="Increase the raft thickness.")
        pr = [p for p in r["punching"]]
        calc.table(["Column", "Combination", "V_Ed [kN]", "ΔV_Ed [kN]", "u₁ [mm]", "β",
                    "v_Ed [MPa]", "v_Rd,c [MPa]", "η"],
                   [[p["grid"], p["combo"], f"{p['V'] / 1e3:.0f}", f"{p['dV'] / 1e3:.0f}",
                     f"{p['u1']:.0f}", f"{p['beta']:g}", f"{p['vEd']:.3f}", f"{p['vRd']:.3f}",
                     f"{p['util']:.2f}"] for p in pr],
                   caption="Punching at 2d, EN 1992-1-1 6.4.4 (V_Ed,red = V_Ed − ΔV_Ed, soil "
                           "reaction inside u₁) and at the column face 6.4.5(3)")
        if pr:
            w = max(pr, key=lambda p: p["util"])
            calc.check(calc.tr("Raft punching at column {g}", g=w["grid"]), w["util"], 1.0, "",
                       "EN 1992-1-1 6.4", hint="Increase the raft thickness under the columns.")
        calc.table(["Combination", "p_avg [kPa]", "p_peak [kPa]", "q_Rd [kPa]"],
                   [[s_["combo"], f"{s_['p'] * 1e3:.0f}", f"{s_['peak'] * 1e3:.0f}",
                     f"{s_['qRd'] * 1e3:.0f}"] for s_ in r["soil"]],
                   caption="EN 1997-1 6.5.2 / Annex D, B × L raft with shape factors")
        soil_ok = True
        for s_ in r["soil"]:
            calc.check(calc.tr("Soil bearing under the raft ({c})", c=s_["combo"]), s_["p"],
                       s_["qRd"], "kN/m²", "EN 1997-1 6.5.2",
                       hint="Enlarge the raft overhang or found deeper.")
            soil_ok &= s_["p"] <= s_["qRd"]
        if r["uplift"]:
            calc.warn("Uplift under the raft at {n} in the seismic situation (p_min = {p:.0f} kPa)"
                      ": the linear springs carry tension there — check it or enlarge the raft.",
                      n=r["uplift"]["node"], p=r["uplift"]["p"] * 1e3)
        st = r["settlement"]
        calc.check(calc.tr("Relative rotation between columns {a}–{b} ≤ 1/500", a=st["pair"][0],
                           b=st["pair"][1]) if st["pair"][0] else
                   calc.tr("Relative rotation between columns ≤ 1/500"),
                   st["rot"], 1 / 500, "", "EN 1997-1 Annex H",
                   hint="Increase the raft thickness or improve the soil.")
        calc.check("Total settlement (G + ψ₂Q) ≤ 50 mm", st["w_max"], 50.0, "mm",
                   "EN 1997-1 Annex H", hint="Improve the soil or enlarge the raft.")
        # records for the workspace and the automatic sizing
        bend_ok = not r["fail"]
        sh_ok = sh["V"] <= sh["VRd"]
        punch_ok = all(p["util"] <= 1 for p in pr)
        set_ok = st["rot"] <= 1 / 500 and st["w_max"] <= 50
        if not (bend_ok and sh_ok and punch_ok and set_ok):
            calc.issues.append({"type": "raft"})
        if not soil_ok:
            calc.issues.append({"type": "raft_soil"})
        mesh_txt = "; ".join(f"{names[f]} {d}: Ø{m['base'][0]}/{m['base'][1]:g}" +
                             (f" + Ø{m['add'][0]}/{m['add'][1]:g}" if m["add"] else "")
                             for (f, d), m in r["mesh"].items())
        util = max([max(p["util"] for p in pr) if pr else 0.0, sh["V"] / sh["VRd"],
                    max(m["peak"] / m["cap"] for m in r["mesh"].values()),
                    st["rot"] * 500])
        out = [MemberDesign("R.raft", "raft", 0, mesh_txt, util,
                            bend_ok and sh_ok and punch_ok and set_ok and soil_ok,
                            "ULS / G+ψ2Q+ΩE", {}, "", [], 0.0)]
        out[0]._mesh = r["mesh"]
        spec.D_found = inp["D_found"]
        for p in pr:
            out.append(MemberDesign(f"PU.{p['grid']}", "punching", 0,
                                    f"v_Ed = {p['vEd']:.3f} MPa, β = {p['beta']:g}", p["util"],
                                    p["util"] <= 1.0, p["combo"], {}, "", [], 0.0))
        return out

    @staticmethod
    def _fbeams(calc, inp, spec, info, res, seis, uls, quasi, vertical, project):
        """Foundation beams: EC2 design of every segment (elastic, EN 1998-1 4.4.2.6) and the
        EC7 bearing check of the soil under them."""
        from ..structure.design import _omega, soil_pressures
        na = get_annex(calc.project.annex)
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd, fyd = na.alpha_cc * fck / na.gamma_c, inp["fyk"] / na.gamma_s
        ef = 1.0
        if seis is not None:
            vd = {d.member: d for d in vertical}
            ef = max(_omega(vd.get(mid), seis, quasi, fcd, fyd)
                     for mid in info["columns"] + info["walls"] if mid[1:3] == "1.")
        calc.heading("Foundation beams", 2)
        calc.text("Foundation beams B = {B:g} m, b_w × h = {bw:g} × {h:g} mm on Winkler springs "
                  "k_s = {k:g} MN/m³ along the grid lines (part of the 3D model).",
                  B=inp["fb_B"] / 1000, bw=inp["fb_bw"], h=inp["fb_h"], k=inp["ks"] * 1e3)
        if seis is not None:
            calc.formula("γ_Rd Ω", "γ_Rd · min(M_Rd/M_Ed of the columns, q)", ef, "",
                         "Overstrength of the seismic action on the foundation",
                         ref="EN 1998-1 4.4.2.6", dp=2)
        subs = {mid: 0 for ids in info["fbeams"].values() for mid in ids}
        dsub = design_beams(subs, seis, uls, quasi, inp["fb_bw"], inp["fb_h"], inp["concrete"],
                            project, inp["fyk"], 50.0, e_factor=ef, dissipative=False, sls=False)
        by = {d.member: d for d in dsub}
        out = []
        area = lambda n, d: n * np.pi * float(d) ** 2 / 4  # noqa: E731
        for key, ids in info["fbeams"].items():
            parts = [by[i] for i in ids]
            gov = max(parts, key=lambda d: d.utilisation)
            bot = max(parts, key=lambda d: area(d.inputs["n_bars"], d.inputs["dia"])).inputs
            top = max(parts, key=lambda d: area(d.inputs["n_comp"], d.inputs["dia_comp"])).inputs
            s_min = min(d.inputs["link_s"] for d in parts)
            ld = max(d.inputs.get("link_dia", "8") for d in parts)
            reinf = (f"bottom {bot['n_bars']}Ø{bot['dia']}, top {top['n_comp']}Ø{top['dia_comp']}, "
                     f"Ø{ld}/{s_min:g}")
            notes = list(dict.fromkeys(n for d in parts for n in d.notes))
            As = area(bot["n_bars"], bot["dia"]) + area(top["n_comp"], top["dia_comp"])
            out.append(MemberDesign(f"FB.{key}", "fbeam", 0, reinf, gov.utilisation,
                                    all(d.ok for d in parts), gov.governing, gov.inputs,
                                    "ec2_rc_beam", notes, As / (inp["fb_bw"] * inp["fb_h"])))
        # soil pressures under the beams
        an = res["G"].analysis
        springs = {n: s.springs[2] / (inp["ks"] * inp["fb_B"]) for n, s in an.model.supports.items()
                   if s.springs[2]}
        soil = {"phi": inp["phi_soil"], "c": inp["c_soil"], "gamma": inp["gamma_soil"]}
        rows = soil_pressures(res, quasi, seis, ef, springs, inp["fb_B"], inp["D_found"], soil, na)
        calc.table(["Combination", "p_max [kPa]", "Node", "q_Rd [kPa]"],
                   [[r["combo"], f"{r['p'] * 1e3:.0f}", r["node"], f"{r['qRd'] * 1e3:.0f}"]
                    for r in rows],
                   caption="Soil pressure p = R/(B·l) at the spring nodes; q_Rd of a strip of "
                           "width B, EN 1997-1 Annex D (seismic: EN 1998-5 material factors)")
        for r in rows:
            calc.check(calc.tr("Soil bearing under the foundation beams ({c})", c=r["combo"]),
                       r["p"], r["qRd"], "kN/m²", "EN 1997-1 6.5.2",
                       hint="Widen the foundation beams (B), deepen them or use a raft.")
            if r["p"] > r["qRd"]:
                calc.issues.append({"type": "soil"})
            if r.get("p_min", 0.0) < 0:
                calc.warn("Uplift under the foundation beams at {n} in the seismic situation "
                          "(p_min = {p:.0f} kPa): the linear springs carry tension there — "
                          "check the uplift or widen the beams.", n=r["node_min"],
                          p=r["p_min"] * 1e3)
        return out

    @staticmethod
    def _footings(calc, inp, spec, info, res, seis, quasi, vertical, project):
        na = get_annex(calc.project.annex)
        bases = {}
        for mid in info["columns"] + info["walls"]:
            if not mid.startswith(("C1.", "W1.")):
                continue
            g = mid.split(".", 1)[1]
            w = info["wall_spec"].get(g) if mid.startswith("W") else None
            cx, cy = ((w["L"], w["t"]) if w["dir"] == "X" else (w["t"], w["L"])) if w \
                else info["sizes"][mid]
            bases[g] = {"node": f"{g}@0", "member": mid, "cx": cx, "cy": cy}
        soil = {"phi": inp["phi_soil"], "c": inp["c_soil"] * 1e3, "gamma": inp["gamma_soil"] * 1e6,
                "D": inp["D_found"] / 1000, "approach": "National Annex"}
        df = design_footings(bases, res, seis, quasi, {d.member: d for d in vertical}, soil,
                             inp["concrete"], project, inp["fyk"], na.gamma_c, na.gamma_s,
                             na.alpha_cc)
        # neighbouring footings must not overlap (otherwise a strip footing or raft is needed)
        xs, ys = info["xs"], info["ys"]
        by = {d.member.split(".", 1)[1]: d for d in df}
        from ..structure.builder import grid_label as gl
        for g, d in by.items():
            i = next(i for i in range(len(xs)) for j in range(len(ys)) if gl(i, j) == g)
            j = next(j for i2 in range(len(xs)) for j in range(len(ys)) if gl(i2, j) == g)
            for (i2, j2, gap, key) in ((i + 1, j, (xs[i + 1] - xs[i]) / 1000 if i + 1 < len(xs)
                                        else 0, "Bx"),
                                       (i, j + 1, (ys[j + 1] - ys[j]) / 1000 if j + 1 < len(ys)
                                        else 0, "By")):
                o = by.get(gl(i2, j2)) if gap else None
                if o and (d.inputs[key] + o.inputs[key]) / 2 > gap - 0.1:
                    d.notes.append(Msg("Footings {a} and {b} overlap — use a strip footing or "
                                       "a raft", a=g, b=gl(i2, j2)))
        return df

    @staticmethod
    def _capacity(calc, inp, spec, info, dc, db, quasi, seis, project):
        xs, ys, ns = info["xs"], info["ys"], len(spec.heights)
        walls = set(info["wall_spec"])
        joints = []
        for k in range(1, ns):
            for i in range(len(xs)):
                for j in range(len(ys)):
                    g = grid_label(i, j)
                    if g in walls:
                        continue
                    cols = [f"C{k}.{g}", f"C{k + 1}.{g}"]
                    bx = ([f"B{k}.{grid_label(i - 1, j)}-{g}"] if i else []) + \
                         ([f"B{k}.{g}-{grid_label(i + 1, j)}"] if i < len(xs) - 1 else [])
                    by = ([f"B{k}.{grid_label(i, j - 1)}-{g}"] if j else []) + \
                         ([f"B{k}.{g}-{grid_label(i, j + 1)}"] if j < len(ys) - 1 else [])
                    joints.append({"node": f"{g}@{k}", "storey": k, "dir": "X", "cols": cols,
                                   "beams": bx})
                    joints.append({"node": f"{g}@{k}", "storey": k, "dir": "Y", "cols": cols,
                                   "beams": by})
        na = get_annex(calc.project.annex)
        res = capacity_design(dc, db, joints, quasi, seis, (spec.col_b, spec.col_h),
                              (spec.beam_b, spec.beam_h), inp["concrete"], inp["fyk"],
                              inp["cover"], na.gamma_c, na.gamma_s, na.alpha_cc)
        clear = {d.member: spec.heights[d.storey - 1] - spec.beam_h for d in dc}  # conservative
        capacity_shears(dc, db, quasi, clear, inp["concrete"], (spec.beam_b, spec.beam_h),
                        project, inp["fyk"], inp["cover"], na.gamma_c, na.gamma_s, na.alpha_cc)
        calc.heading("Capacity design", 2)
        calc.text("Strong columns – weak beams at every joint below the roof (EN 1998-1 "
                  "4.4.2.3(4)); beam and column links from the capacity-design shears "
                  "(5.4.2.2, 5.4.2.3, γ_Rd = 1.0 / 1.1).")
        calc.table(["Joint", "Direction", "ΣM_Rc [kNm]", "ΣM_Rb [kNm]", "ΣM_Rc/ΣM_Rb", ""],
                   [[r.node, r.direction, f"{r.sum_MRc / 1e6:.0f}", f"{r.sum_MRb / 1e6:.0f}",
                     f"{r.ratio:.2f}", ("✓" if r.ok else "✗") + (" ↑" if r.raised else "")]
                    for r in res],
                   caption="↑ = column bars increased to satisfy the rule")
        by_storey: dict[int, list] = {}
        for r in res:
            by_storey.setdefault(int(r.node.split("@")[1]), []).append(r)
            if not r.ok:
                calc.issues.append({"type": "joint", "grid": r.node.split("@")[0]})
        for k, rows in sorted(by_storey.items()):
            worst = min(rows, key=lambda r: r.ratio)
            calc.check_min(calc.tr("Storey {k}: ΣM_Rc ≥ 1.3 ΣM_Rb (joint {j})", k=k,
                                   j=worst.node), worst.ratio, 1.3, "", "EN 1998-1 4.4.2.3(4)",
                           hint="Increase the column size or reduce the beam reinforcement.")

    @staticmethod
    def _results(calc, info, seis, designs) -> dict:
        """Per-member results for the graphical workspace (Erisma Structure)."""
        out = {"members": {}, "storeys": [], "periods": [], "issues": getattr(calc, "issues", [])}
        for d in designs:
            out["members"][d.member] = {
                "kind": d.kind, "storey": d.storey, "ok": d.ok, "util": d.utilisation,
                "rho": d.rho, "reinforcement": BuildingFrame._reinf(calc, d.reinforcement),
                "governing": calc.tr(d.governing, quiet=True), "module": d.module,
                "inputs": d.inputs,
                "notes": [n.message(calc.lang) if hasattr(n, "message") else calc.tr(n)
                          for n in d.notes]}
        r = getattr(calc, "raft", None)
        if r:
            out["raft"] = {"elements": [{k: (round(float(v), 3) if not isinstance(v, (str, bool))
                                             else v) for k, v in e.items()
                                         if k in ("id", "x0", "x1", "y0", "y1", "util")}
                                        for e in r["elements"]],
                           "punching": [{"grid": p["grid"], "util": float(p["util"])}
                                        for p in r["punching"]]}
        if getattr(calc, "combos", None):
            out["cases"] = [{"name": c.name, "type": c.type} for c in calc.cases]
            out["combos"] = [{"name": c.name, "kind": c.kind, "text": c.text()} for c in calc.combos]
        mt = getattr(calc, "modes_table", None)
        if mt:
            out["modes"] = [{k: (v if isinstance(v, (str, int)) else round(float(v), 4))
                             for k, v in r.items()} for r in mt]
        reg = getattr(calc, "regularity", None)
        if reg is not None:
            out["regularity"] = {
                "plan": reg.plan_regular, "elevation": reg.elevation_regular,
                "torsional": reg.torsionally_flexible, "q_used": getattr(calc, "q_used", None),
                "floors": [{"index": f.index, "cm": [f.cm[0] / 1e3, f.cm[1] / 1e3],
                            "cr": [f.cr[0] / 1e3, f.cr[1] / 1e3], "rx": f.rx / 1e3,
                            "ry": f.ry / 1e3, "ls": f.ls / 1e3, "e0x": f.e0x / 1e3,
                            "e0y": f.e0y / 1e3} for f in reg.floors]}
        if seis is not None:
            out["periods"] = [float(t) for t in seis.modes.periods[:6]]
            out["base_shear"] = {d: v / 1e3 for d, v in seis.base_shear.items()}
            for s in seis.storeys:
                out["storeys"].append({"index": s.index, "drift": {d: v / s.h for d, v in
                                                                   s.drift.items()},
                                       "theta": s.theta})
        return out

    @staticmethod
    def _ghosts(sc, spec, info, m) -> None:
        """Translucent boxes at empty column positions and missing beams, so the 3D view can
        be used to add them back (pick ids as in the plan editor)."""
        xs, ys, zs = info["xs"], info["ys"], info["zs"]
        lay = spec.layout or {}
        walls = {str(w["at"]).upper() for w in spec.walls}
        g = "#8fb3d9"
        for i, x in enumerate(xs):
            for j, y in enumerate(ys):
                gid = grid_label(i, j)
                if gid in set(lay.get("omit_columns", [])) and gid not in walls:
                    for z0, z1 in zip(zs[:-1], zs[1:]):
                        sc.box("ghost", (m(x), m((z0 + z1) / 2), m(y)), (0.25, m(z1 - z0), 0.25),
                               g, opacity=0.12, edges=False, pick=f"point:{gid}")
        for key in lay.get("omit_beams", []):
            a, b = key.split("-")
            ia = next((i, j) for i in range(len(xs)) for j in range(len(ys)) if grid_label(i, j) == a)
            ib = next((i, j) for i in range(len(xs)) for j in range(len(ys)) if grid_label(i, j) == b)
            x0, y0, x1, y1 = xs[ia[0]], ys[ia[1]], xs[ib[0]], ys[ib[1]]
            for z in zs[1:]:
                size = (m(abs(x1 - x0)) or 0.2, 0.2, m(abs(y1 - y0)) or 0.2)
                sc.box("ghost", (m((x0 + x1) / 2), m(z) - 0.15, m((y0 + y1) / 2)), size, g,
                       opacity=0.12, edges=False, pick=f"beam:{key}")

    @staticmethod
    def _diagrams(sc, res, frame, m, ext) -> None:
        """M, V and N diagrams of the ULS combination drawn on the members (tension side)."""
        an = res.analysis
        comps = {"dM": ("My", "Mz"), "dV": ("Vz", "Vy"), "dN": ("N", None)}
        colors = {"dM": "#e03b3b", "dV": "#2e9b5f", "dN": "#8e6cc4"}
        data = {}
        for mem in frame:
            data[mem.id] = res.forces(mem.id, 11)
        for layer, (major, minor) in comps.items():
            vmax = max((np.abs(f[k]).max() for f in data.values() for k in (major, minor) if k),
                       default=0.0) or 1.0
            scale = 0.08 * ext / vmax
            peak = (0.0, None)
            for mem in frame:
                f = data[mem.id]
                e = an.elements[an.member_index[mem.id]]
                ex, ey, ez = e.R
                key, axis = major, -ez
                if minor and np.abs(f[minor]).max() > np.abs(f[major]).max():
                    key, axis = minor, -ey
                if layer == "dN":
                    axis = ey if abs(ex[2]) < 0.5 else np.array([1.0, 0.0, 0.0])
                if layer == "dV":
                    axis = -axis
                pi = an.model.nodes[mem.i].xyz
                verts, faces = [], []
                for x, v in zip(f["x"], f[key]):
                    p = pi + ex * x
                    q = p + axis * v * scale
                    verts += [(m(p[0]), m(p[2]), m(p[1])), (m(q[0]), m(q[2]), m(q[1]))]
                for k in range(len(f["x"]) - 1):
                    a = 2 * k
                    faces += [(a, a + 1, a + 3), (a, a + 3, a + 2)]
                sc.mesh(layer, verts, faces, colors[layer], opacity=0.55)
                k_ = int(np.argmax(np.abs(f[key])))
                if abs(f[key][k_]) > abs(peak[0]):
                    peak = (f[key][k_], verts[2 * k_ + 1])
            if peak[1] is not None:
                unit = "kN" if layer != "dM" else "kNm"
                val = peak[0] / (1e6 if layer == "dM" else 1e3)
                sc.label(layer, f"{val:.0f} {unit}", peak[1], "result")

    @staticmethod
    def _quantities(spec, info, an, designs) -> dict:
        inp_D = lambda i: i["D"] * 1000  # noqa: E731  (founding depth, m → mm)
        spec_D = lambda sp: getattr(sp, "D_found", 1200.0)  # noqa: E731
        """Concrete, formwork and (if designed) reinforcement of the whole frame."""
        model = an.model
        rho_s = 7850e-9  # kg/mm³
        conc = form = steel = 0.0
        des = {d.member: d for d in designs}
        fb = (spec.foundation or {})
        for mem in model.members.values():
            if mem.id.startswith("RL."):      # rigid links wall → raft (no material)
                continue
            L = model.length(mem)
            vertical = abs(model.nodes[mem.i].z - model.nodes[mem.j].z) > 1
            if mem.id.startswith("FB."):      # foundation beam (inverted T)
                hf = min(250.0, fb["h"] / 3)
                conc += (fb["bw"] * fb["h"] + (fb["B"] - fb["bw"]) * hf) * L
                form += 2 * fb["h"] * L
                d = des.get("FB." + mem.id.split(".")[1])
                if d:
                    i = d.inputs
                    As = (i["n_bars"] * float(i["dia"]) ** 2 + i["n_comp"]
                          * float(i["dia_comp"]) ** 2) * np.pi / 4
                    per = 2 * (fb["bw"] + fb["h"] - 4 * 50.0)
                    steel += As * L * 1.1 + 50.3 * per * L / i["link_s"]
                continue
            if vertical:
                g = mem.id.split(".", 1)[1]
                w = info["wall_spec"].get(g) if mem.id.startswith("W") else None
                b, h = (w["L"], w["t"]) if w else info["sizes"][mem.id]
                Lc = L - spec.beam_h
                conc += b * h * Lc
                form += 2 * (b + h) * Lc
                d = des.get(mem.id) or (des.get(f"W1.{g}") if w else None)
                if d and d.kind == "column":
                    i = d.inputs
                    n = 4 * i["nb"] - 4
                    As = n * np.pi * float(i["dia"]) ** 2 / 4
                    per = 2 * (b + h - 4 * 30.0)  # link perimeter (cover ≈ 30 mm)
                    steel += As * L * 1.1 + 50.3 * per * Lc / i["s"]
                elif d and d.kind == "wall":
                    i = d.inputs
                    As = 2 * i["nbe"] * np.pi * float(i["dbe"]) ** 2 / 4
                    web = 2 * 78.5 * (b / 200) * L + 2 * 78.5 * (L / 200) * b  # Ø10/200 ×2
                    steel += As * L * 1.1 + web
            else:
                bb, hb = info["sizes"][mem.id]
                b, hw = bb, hb - spec.slab_t
                Lb = L - spec.col_b
                conc += b * hw * Lb
                form += (b + 2 * hw) * Lb
                d = des.get(mem.id)
                if d:
                    i = d.inputs
                    As = (i["n_bars"] * float(i["dia"]) ** 2 + i["n_comp"]
                          * float(i["dia_comp"]) ** 2) * np.pi / 4
                    per = 2 * (bb + hb - 4 * 30.0)
                    steel += As * L * 1.15 + 50.3 * per * Lb / i["link_s"]
        A = info["plan_area"] * len(spec.heights)
        conc += A * spec.slab_t
        form += A
        exc = 0.0
        for d in designs:
            if d.kind == "slab":   # bottom bars both ways everywhere, top bars ≈ half the area
                i = d.inputs
                xs_, ys_ = info["xs"], info["ys"]
                gi = d.member.split(".", 1)[1]
                area = next(((xs_[a + 1] - xs_[a]) * (ys_[b + 1] - ys_[b])
                             for a in range(len(xs_) - 1) for b in range(len(ys_) - 1)
                             if grid_label(a, b) == gi), 0.0)
                ab = np.pi * float(i["dia_b"]) ** 2 / 4 / i["s_b"]
                at = np.pi * float(i["dia_t"]) ** 2 / 4 / i["s_t"]
                steel += area * (2 * ab + at)
            elif d.kind == "footing":
                i = d.inputs
                Bx, By, hf = i["Bx"] * 1000, i["By"] * 1000, i["h"] * 1000
                conc += Bx * By * hf
                form += 2 * (Bx + By) * hf
                a = np.pi * float(i["dia_x"]) ** 2 / 4
                steel += a * (By / i["s_x"]) * Bx + a * (Bx / i["s_y"]) * By
                exc += (Bx + 600) * (By + 600) * inp_D(i)
        rf = info.get("raft")
        if rf:
            x0, x1, y0, y1 = rf["bounds"]
            A = (x1 - x0) * (y1 - y0)
            conc += A * rf["t"]
            form += 2 * ((x1 - x0) + (y1 - y0)) * rf["t"]
            exc += A * spec_D(spec)
            rd = next((d for d in designs if d.kind == "raft"), None)
            mesh = getattr(rd, "_mesh", None)
            if mesh:
                for m in mesh.values():
                    a = np.pi * float(m["base"][0]) ** 2 / 4 / m["base"][1]
                    steel += a * A
                    if m["add"]:
                        steel += np.pi * float(m["add"][0]) ** 2 / 4 / m["add"][1] * A * 0.15
        out = {"concrete": conc * 1e-9, "formwork": form * 1e-6}
        if exc:
            out["excavation"] = exc * 1e-9
        if steel:
            out["rebar"] = steel * rho_s
        return out

    @staticmethod
    def _reinf(calc, text: str) -> str:
        if calc.lang != "el":
            return text
        for en, el in (("bottom ", "κάτω "), ("top ", "άνω "), ("ends ", "άκρα "),
                       (" over ", " σε μήκος ")):
            text = text.replace(en, el)
        return text

    # ------------------------------------------------------------------ 3D
    @staticmethod
    def _scene(calc, spec, info, an, seis, designs) -> dict:
        sc = Scene3D("building", calc.tr)
        has_design = bool(designs)
        sc.layer("frame", "Frame (colour = reinforcement ratio ρ)" if has_design else "Frame")
        sc.layer("slabs", "Slabs")
        if spec.foundation:
            sc.layer("found", "Foundation beams")
        sc.layer("ghost", "Empty positions (click to add)")
        for key, label in (("dM", "Bending moments M (ULS)"), ("dV", "Shear forces V (ULS)"),
                           ("dN", "Axial forces N (ULS)"), ("defl", "Deformed shape (G+ψ2Q)")):
            sc.layer(key, label, visible=False)
        if seis is not None:
            for n in range(min(6, seis.modes.n_modes)):
                sc.layer(f"mode{n + 1}", calc.tr("Mode {n} (deformed)", n=n + 1), visible=False)
        sc.layer("grid", "Grid labels")
        des = {d.member: d for d in designs}
        for mid in an.model.members:  # every wall storey shows its base design
            if mid.startswith("W") and mid not in des and f"W1.{mid.split('.', 1)[1]}" in des:
                des[mid] = des[f"W1.{mid.split('.', 1)[1]}"]
        m = lambda v: v / 1000  # noqa: E731
        model = an.model
        fb = spec.foundation or {}
        for mem in model.members.values():
            if mem.id.startswith("RL."):
                continue
            a, b = model.nodes[mem.i], model.nodes[mem.j]
            c = ((a.x + b.x) / 2, (a.z + b.z) / 2, (a.y + b.y) / 2)
            vertical = abs(a.z - b.z) > 1
            if mem.id.startswith("FB."):
                L = model.length(mem)
                along_x = abs(a.x - b.x) > 1
                size = (L, fb["h"], fb["B"]) if along_x else (fb["B"], fb["h"], L)
                c = (c[0], -fb["h"] / 2, c[2])
                d = des.get("FB." + mem.id.split(".")[1])
                col = PALETTE["concrete"] if d is None else "#e03b3b" if not d.ok else \
                    heat_color(0.85 * min(d.rho / 0.03, 1.0))
                sc.box("found", tuple(m(v) for v in c), tuple(m(v) for v in size), col)
                continue
            if vertical:
                w = info["wall_spec"].get(mem.id.split(".", 1)[1]) if mem.id.startswith("W") \
                    else None
                bx, by = ((w["L"], w["t"]) if w["dir"] == "X" else (w["t"], w["L"])) if w \
                    else info["sizes"][mem.id]
                size = (bx, abs(a.z - b.z), by)
            elif abs(a.x - b.x) > 1:
                bb, hb = info["sizes"][mem.id]
                size = (abs(a.x - b.x), hb, bb)
                c = (c[0], c[1] - hb / 2, c[2])
            else:
                bb, hb = info["sizes"][mem.id]
                size = (bb, hb, abs(a.y - b.y))
                c = (c[0], c[1] - hb / 2, c[2])
            d = des.get(mem.id)
            if d is None:
                col = PALETTE["concrete"]
            elif not d.ok:
                col = "#e03b3b"
            else:  # columns ρ 1 → 4 %, beams ρ (top + bottom) 0 → 3 %, walls (boundary) 0 → 2 %
                t = ((d.rho - 0.01) / 0.03 if d.kind == "column" else
                     d.rho / 0.02 if d.kind == "wall" else d.rho / 0.03)
                col = heat_color(0.85 * min(max(t, 0.0), 1.0))
            pk = mem.id.split(".", 1)[1]
            pick = {"C": "column", "W": "wall", "B": "beam"}.get(mem.id[0])
            tip = None
            if pick:
                kname = {"column": "Column", "wall": "Wall", "beam": "Beam"}[pick]
                st = mem.id[1:mem.id.index(".")]
                tip = f"{calc.tr(kname)} {pk} · {calc.tr('Storey')} {st}"
                if not mem.id.startswith("W"):
                    tip += f"\n{size[0]:g}×{size[2]:g}" if pick == "column" else \
                        f"\n{min(size[0], size[2]):g}×{size[1]:g}"
                if d is not None:
                    tip += f"\n{BuildingFrame._reinf(calc, d.reinforcement)}\nη = {d.utilisation:.2f}"
            sc.box("frame", tuple(m(v) for v in c), tuple(m(v) for v in size), col,
                   pick=f"{pick}:{pk}" if pick else None, tip=tip)
        xs, ys, zs = info["xs"], info["ys"], info["zs"]
        rf = info.get("raft")
        if rf:
            sc.layer("found", "Raft")
            x0, x1, y0, y1 = rf["bounds"]
            rd = next((d for d in designs if d.kind == "raft"), None)
            col = "#e03b3b" if rd is not None and not rd.ok else PALETTE["concrete"]
            sc.box("found", (m((x0 + x1) / 2), -rf["t"] / 2000, m((y0 + y1) / 2)),
                   (m(x1 - x0), rf["t"] / 1000, m(y1 - y0)), col, opacity=0.85)
        pads = [d for d in designs if d.kind == "footing"]
        if pads:
            sc.layer("found", "Footings")
        for d in pads:
            g = d.member.split(".", 1)[1]
            n = model.nodes.get(f"{g}@0")
            if n is None:
                continue
            i = d.inputs
            col = "#e03b3b" if not d.ok else PALETTE["concrete"]
            sc.box("found", (m(n.x), -i["h"] / 2, m(n.y)), (i["Bx"], i["h"], i["By"]), col)
        for z in zs[1:]:
            for i in range(len(xs) - 1):
                for j in range(len(ys) - 1):
                    if grid_label(i, j) in info["openings"]:
                        continue
                    sc.box("slabs", (m((xs[i] + xs[i + 1]) / 2), m(z - spec.slab_t / 2),
                                     m((ys[j] + ys[j + 1]) / 2)),
                           (m(xs[i + 1] - xs[i]), m(spec.slab_t), m(ys[j + 1] - ys[j])),
                           PALETTE["concrete"], opacity=0.35, edges=False, pick=f"panel:{grid_label(i, j)}")
        ext = max(xs[-1], ys[-1], zs[-1])
        BuildingFrame._ghosts(sc, spec, info, m)
        dm = an.dofmap
        frame = [mm for mm in model.members.values() if mm.id[0] in "CWB" and "." in mm.id]

        def deformed(layer, u_nodes, scale, color):
            """Animated shape (viewer: base + amplitude·sin ωt) over the undeformed frame."""
            segs, amps = [], []
            for mem in frame:
                seg, amp = [], []
                for nid in (mem.i, mem.j):
                    n = model.nodes[nid]
                    u = u_nodes[dm.index[nid]] * scale
                    seg.append((m(n.x), m(n.z), m(n.y)))
                    amp.append((m(u[0]), m(u[2]), m(u[1])))
                segs.append(seg)
                amps.append(amp)
                sc.line(layer, seg, "#8a96a8", dashed=True)
            sc.anim(layer, segs, amps, color)

        if seis is not None:
            kinds = {"X": "X", "Y": "Y", "RZ": calc.tr("torsion")}
            for n in range(min(6, seis.modes.n_modes)):
                deformed(f"mode{n + 1}", seis.modes.mode_shape(n), 0.08 * ext, PALETTE["seismic"])
                sc.label(f"mode{n + 1}", calc.tr("Mode {n}: T = {t:.3f} s ({k})", n=n + 1,
                                                 t=float(seis.modes.periods[n]),
                                                 k=kinds.get(seis.modes.mode_type(n), "")),
                         (m(xs[-1] / 2), m(zs[-1]) + 1.2, m(ys[-1] / 2)), "result")
        quasi, uls = getattr(calc, "_quasi", None), getattr(calc, "_uls", None)
        if quasi is not None:
            umax = np.abs(quasi.u[:, :3]).max() or 1.0
            deformed("defl", quasi.u, 0.04 * ext / umax, "#2f8fd8")
            sc.label("defl", calc.tr("max |u| = {u:.1f} mm", u=umax),
                     (m(xs[-1] / 2), m(zs[-1]) + 0.8, m(ys[-1] / 2)), "result")
        if uls is not None:
            BuildingFrame._diagrams(sc, uls, frame, m, ext)
        for i, x in enumerate(xs):
            sc.label("grid", str(i + 1), (m(x), -0.4, -1.0))
        for j, y in enumerate(ys):
            sc.label("grid", grid_label(0, j)[:-1], (-1.0, -0.4, m(y)))
        if has_design:
            sc.legend_item(heat_color(0.0), calc.tr("Light reinforcement"))
            sc.legend_item(heat_color(0.85), calc.tr("Heavy reinforcement"))
            if any(not d.ok for d in designs):
                sc.legend_item("#e03b3b", calc.tr("Fails — resize"))
        return sc.to_dict()
