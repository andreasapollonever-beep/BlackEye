"""General continuous beam analysis module."""

from __future__ import annotations

from ..analysis import UDL, Beam, PointLoad, PointMoment, Support
from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..report.svg import beam_diagrams

MATERIALS = {"Steel (E = 210 GPa)": 210000.0, "Concrete C25/30 (E = 31 GPa)": 31000.0,
             "Timber C24 (E = 11 GPa)": 11000.0, "Aluminium (E = 70 GPa)": 70000.0}


@register
class BeamAnalysis(DesignModule):
    id = "beam_analysis"
    title = "Continuous beam analysis"
    category = "Analysis"
    standard = "Stiffness method"
    description = ("Linear elastic analysis of single or multi-span beams with any number of "
                   "supports, point loads, UDLs and moments. Gives reactions, shear, moment "
                   "and deflection diagrams.")

    fields = [
        Field("L", "Total length", "m", 10.0, min=0.1, group="Geometry"),
        Field("material", "Material", kind="choice", choices=list(MATERIALS),
              default="Steel (E = 210 GPa)", group="Section"),
        Field("I", "Second moment of area I", "cm⁴", 8356.0, min=0.001, group="Section"),
        Field("supports", "Supports", kind="table", group="Supports", default=[
            {"x": 0.0, "kind": "pinned"}, {"x": 5.0, "kind": "pinned"},
            {"x": 10.0, "kind": "pinned"}],
            columns=[Field("x", "Position", "m", 0.0, min=0),
                     Field("kind", "Type", kind="choice", choices=["pinned", "fixed"],
                           default="pinned")]),
        Field("udls", "Distributed loads", kind="table", group="Loads", default=[
            {"x1": 0.0, "x2": 10.0, "w": 15.0}],
            columns=[Field("x1", "Start", "m", 0.0, min=0), Field("x2", "End", "m", 1.0, min=0),
                     Field("w", "w (down +)", "kN/m", 0.0)]),
        Field("points", "Point loads", kind="table", group="Loads", default=[
            {"x": 2.5, "P": 20.0}],
            columns=[Field("x", "Position", "m", 0.0, min=0),
                     Field("P", "P (down +)", "kN", 0.0)]),
        Field("moments", "Applied moments", kind="table", group="Loads", default=[],
              columns=[Field("x", "Position", "m", 0.0, min=0),
                       Field("M", "M (clockwise +)", "kNm", 0.0)]),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        L = inp["L"]
        E = MATERIALS[inp["material"]]
        calc.heading("Model")
        calc.input("L", L, "m", "Beam length")
        calc.label("Material", inp["material"])
        calc.input("E", E, "GPa", "Modulus of elasticity")
        calc.input("I", inp["I"], "cm⁴", "Second moment of area")
        try:
            beam = Beam(
                L, E, inp["I"],
                supports=[Support(s["x"], s["kind"]) for s in inp["supports"]],
                point_loads=[PointLoad(p["x"], p["P"]) for p in inp["points"]],
                udls=[UDL(u["x1"], u["x2"], u["w"]) for u in inp["udls"]],
                moments=[PointMoment(m["x"], m["M"]) for m in inp["moments"]],
            )
            res = beam.solve()
        except (ValueError, ArithmeticError) as exc:
            raise InputError(str(exc)) from exc
        except Exception as exc:  # singular stiffness matrix etc.
            raise InputError(f"Analysis failed: {exc}") from exc

        calc.table(["Support", "x [m]", "Type"],
                   [[i + 1, f"{from_base(s.x, 'm'):.3f}", s.kind]
                    for i, s in enumerate(beam.supports)], caption="Supports")
        load_rows = [["UDL", f"{from_base(u.x1, 'm'):.2f} – {from_base(u.x2, 'm'):.2f}",
                      f"{from_base(u.w, 'kN/m'):.2f} kN/m"] for u in beam.udls]
        load_rows += [["Point", f"{from_base(p.x, 'm'):.2f}", f"{from_base(p.P, 'kN'):.2f} kN"]
                      for p in beam.point_loads]
        load_rows += [["Moment", f"{from_base(m.x, 'm'):.2f}", f"{from_base(m.M, 'kNm'):.2f} kNm"]
                      for m in beam.moments]
        if load_rows:
            calc.table(["Load", "Position [m]", "Magnitude"], load_rows, caption="Loads")

        calc.heading("Results")
        calc.table(["x [m]", "Reaction R [kN] (up +)", "Moment [kNm] (acw +)"],
                   [[f"{from_base(x, 'm'):.3f}", f"{from_base(R, 'kN'):.2f}",
                     f"{from_base(M, 'kNm'):.2f}"] for x, R, M in res.reactions],
                   caption="Support reactions")
        Ms, xs = res.max_sagging
        Mh, xh = res.max_hogging
        V, xv = res.max_shear
        dmax, xdm = res.max_deflection
        calc.formula("M_max,sag", f"at x = {from_base(xs, 'm'):.2f} m", max(Ms, 0.0), "kNm",
                     "Maximum sagging moment")
        calc.formula("M_max,hog", f"at x = {from_base(xh, 'm'):.2f} m", min(Mh, 0.0), "kNm",
                     "Maximum hogging moment")
        calc.formula("V_max", f"at x = {from_base(xv, 'm'):.2f} m", abs(V), "kN",
                     "Maximum shear force")
        calc.formula("δ_max", f"at x = {from_base(xdm, 'm'):.2f} m", dmax, "mm",
                     "Maximum deflection (down +)")
        calc.figure(beam_diagrams(res, deflection=True), "Shear, moment and deflection")
