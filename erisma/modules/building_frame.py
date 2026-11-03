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
from ..structure.design import (capacity_design, capacity_shears, design_beams, design_columns,
                                design_walls)
from ..structure.modal import ec8_spectrum
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
        Field("n_modes", "Number of modes", kind="int", default=12, min=3, max=60,
              group="Seismic", show_if="seismic"),
        Field("pdelta", "P-Δ effects (geometric stiffness)", kind="bool", default=False,
              group="Seismic", show_if="seismic",
              help="Include the destabilising effect of the gravity loads G + ψ2Q in the "
                   "stiffness (all analyses)."),
        Field("design", "Design the reinforcement of all members", kind="bool", default=True,
              group="Design"),
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
            inp["layout"])
        if inp["beam_h"] <= inp["slab_t"]:
            raise InputError("The beam depth must be greater than the slab thickness", "beam_h")
        g_unf, _, g_q = na.combos["DA1-C1"][:3]
        psi0, psi1, psi2 = na.psi[inp["category"]]
        pdelta = seismic and inp["pdelta"]
        try:
            model, info = build(spec)
            an = analyse_pdelta(model, {"G": 1.0, "Q": psi2}) if pdelta else analyse(model)
            lin = analyse(model) if pdelta else an
            acr = critical_load_factor(lin, {"G": 1.0, "Q": psi2})
        except StructureError as exc:
            fld = "walls" if "Wall" in exc.text else "layout" if (
                "Layout" in exc.text or "Slab panel" in exc.text or "Beam {g}" in exc.text) else None
            raise InputError(exc.message(calc.lang), fld) from exc
        res = an.run_all()
        uls = an.combine(res, {"G": g_unf, "Q": g_q}, "ULS")
        quasi = an.combine(res, {"G": 1.0, "Q": psi2}, "G+ψ2Q")

        cls._model_section(calc, spec, info, an, res)
        calc.heading("Global stability")
        calc.formula("α_cr", calc.tr("eigenvalue of (K + α K_G) φ = 0 for G + {p:g}Q", p=psi2),
                     acr, "", "Elastic critical load factor", ref="EN 1993-1-1 5.2.1(3)", dp=1)
        calc.check_min("α_cr ≥ 10 (first-order analysis sufficient)", acr, 10.0, "",
                       "EN 1993-1-1 Eq. 5.1",
                       hint="Switch on P-Δ effects, or stiffen the structure.")
        if pdelta:
            calc.note("P-Δ: the geometric stiffness of the axial forces from G + {p:g}Q is "
                      "included in every analysis below.", p=psi2)
        seis = None
        if seismic:
            seis = cls._seismic_section(calc, inp, na, an, psi2)
        designs = []
        if inp["design"]:
            designs = cls._design_section(calc, inp, spec, info, res, seis, uls, quasi,
                                          (g_unf, g_q, psi2))
        calc.building_qty = cls._quantities(spec, info, an, designs)
        calc.structure = cls._results(calc, info, seis, designs)
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
        for case in ("G", "Q"):
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
    @classmethod
    def _seismic_section(cls, calc, inp, na, an, psi2):
        psiE = inp["phi_E"] * psi2
        calc.heading("Masses and modal analysis")
        calc.formula("ψ_E", "φ ψ_2", psiE, "", "Combination coefficient for the mass",
                     ref="EN 1998-1 4.2.4", dp=2)
        md = modal(an, {"G": 1.0, "Q": psiE}, n_modes=inp["n_modes"])
        calc.formula("M", "Σ (G + ψ_E Q) / g", md.total_mass["X"] * 1e3, "",
                     "Seismic mass above the base [t]", dp=1)
        rows = [[str(r["mode"]), f"{r['T']:.3f}", f"{r['mX'] * 100:.1f}", f"{r['sumX'] * 100:.1f}",
                 f"{r['mY'] * 100:.1f}", f"{r['sumY'] * 100:.1f}"] for r in md.table()]
        calc.table(["Mode", "T [s]", "m_X [%]", "Σm_X [%]", "m_Y [%]", "Σm_Y [%]"], rows,
                   caption="Periods and effective modal masses")
        for d in ("X", "Y"):
            calc.check_min(calc.tr("Σ effective mass in {d} ≥ 90 %", d=d),
                           float(md.cumulative(d)[-1]), 0.90, "", "EN 1998-1 4.3.3.3.1(3)",
                           hint="Increase the number of modes.")

        calc.heading("Design spectrum")
        sp = ec8_spectrum(inp["ag"], inp["ground"], inp["q_factor"], inp["importance"],
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
        th = seis.theta_max
        calc.check("Second-order sensitivity θ ≤ 0.30", th, 0.30, "", "EN 1998-1 4.4.2.2(4)",
                   hint="Stiffen the structure (larger columns or walls).")
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
        for title, items, hint in (
                ("Columns", dc, "Increase the column size or the concrete class."),
                ("Beams", db, "Increase the beam size or the concrete class."),
                ("Walls (critical region at the base)", dw,
                 "Increase the wall length or thickness.")):
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
                             (dw, "Critical wall {m} — full calculation")):
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
        return dc + db + dw

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
        for k, rows in sorted(by_storey.items()):
            worst = min(rows, key=lambda r: r.ratio)
            calc.check_min(calc.tr("Storey {k}: ΣM_Rc ≥ 1.3 ΣM_Rb (joint {j})", k=k,
                                   j=worst.node), worst.ratio, 1.3, "", "EN 1998-1 4.4.2.3(4)",
                           hint="Increase the column size or reduce the beam reinforcement.")

    @staticmethod
    def _results(calc, info, seis, designs) -> dict:
        """Per-member results for the graphical workspace (Erisma Structure)."""
        out = {"members": {}, "storeys": [], "periods": []}
        for d in designs:
            out["members"][d.member] = {
                "kind": d.kind, "storey": d.storey, "ok": d.ok, "util": d.utilisation,
                "rho": d.rho, "reinforcement": BuildingFrame._reinf(calc, d.reinforcement),
                "governing": calc.tr(d.governing, quiet=True), "module": d.module,
                "inputs": d.inputs,
                "notes": [n.message(calc.lang) if hasattr(n, "message") else calc.tr(n)
                          for n in d.notes]}
        if seis is not None:
            out["periods"] = [float(t) for t in seis.modes.periods[:6]]
            out["base_shear"] = {d: v / 1e3 for d, v in seis.base_shear.items()}
            for s in seis.storeys:
                out["storeys"].append({"index": s.index, "drift": {d: v / s.h for d, v in
                                                                   s.drift.items()},
                                       "theta": s.theta})
        return out

    @staticmethod
    def _quantities(spec, info, an, designs) -> dict:
        """Concrete, formwork and (if designed) reinforcement of the whole frame."""
        model = an.model
        rho_s = 7850e-9  # kg/mm³
        conc = form = steel = 0.0
        des = {d.member: d for d in designs}
        for mem in model.members.values():
            L = model.length(mem)
            vertical = abs(model.nodes[mem.i].z - model.nodes[mem.j].z) > 1
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
        out = {"concrete": conc * 1e-9, "formwork": form * 1e-6}
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
        if seis is not None:
            sc.layer("mode", "Mode 1 (deformed)", visible=False)
        sc.layer("grid", "Grid labels")
        des = {d.member: d for d in designs}
        for mid in an.model.members:  # every wall storey shows its base design
            if mid.startswith("W") and mid not in des and f"W1.{mid.split('.', 1)[1]}" in des:
                des[mid] = des[f"W1.{mid.split('.', 1)[1]}"]
        m = lambda v: v / 1000  # noqa: E731
        model = an.model
        for mem in model.members.values():
            a, b = model.nodes[mem.i], model.nodes[mem.j]
            c = ((a.x + b.x) / 2, (a.z + b.z) / 2, (a.y + b.y) / 2)
            vertical = abs(a.z - b.z) > 1
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
            sc.box("frame", tuple(m(v) for v in c), tuple(m(v) for v in size), col)
        xs, ys, zs = info["xs"], info["ys"], info["zs"]
        for z in zs[1:]:
            for i in range(len(xs) - 1):
                for j in range(len(ys) - 1):
                    if grid_label(i, j) in info["openings"]:
                        continue
                    sc.box("slabs", (m((xs[i] + xs[i + 1]) / 2), m(z - spec.slab_t / 2),
                                     m((ys[j] + ys[j + 1]) / 2)),
                           (m(xs[i + 1] - xs[i]), m(spec.slab_t), m(ys[j + 1] - ys[j])),
                           PALETTE["concrete"], opacity=0.35, edges=False)
        if seis is not None:
            shape = seis.modes.mode_shape(0)
            scale = 0.08 * max(xs[-1], ys[-1], zs[-1])
            dm = an.dofmap
            for mem in model.members.values():
                pts = []
                for nid in (mem.i, mem.j):
                    n = model.nodes[nid]
                    u = shape[dm.index[nid]] * scale
                    pts.append((m(n.x + u[0]), m(n.z + u[2]), m(n.y + u[1])))
                sc.line("mode", pts, PALETTE["seismic"])
            sc.label("mode", calc.tr("T_1 = {t:.3f} s", t=float(seis.modes.periods[0])),
                     (m(xs[-1] / 2), m(zs[-1]) + 1.2, m(ys[-1] / 2)), "result")
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
