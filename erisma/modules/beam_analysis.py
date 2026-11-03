"""General continuous beam analysis module."""

from __future__ import annotations

from ..analysis import UDL, Beam, PointLoad, PointMoment, Support
from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..report import scene_beam as sb
from ..report.scene3d import PALETTE, Scene3D
from ..report.svg import beam_diagrams

MATERIALS = {"Steel (E = 210 GPa)": 210000.0, "Concrete C25/30 (E = 31 GPa)": 31000.0,
             "Timber C24 (E = 11 GPa)": 11000.0, "Aluminium (E = 70 GPa)": 70000.0}


@register
class BeamAnalysis(DesignModule):
    id = "beam_analysis"
    title = "Continuous beam analysis"
    category = "Analysis"
    standard = "Stiffness method"
    has_3d = True
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
            raise InputError(str(exc), "supports") from exc
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
        calc.formula("M_max,sag", calc.tr("at x = {x:.2f} m", x=from_base(xs, "m")), max(Ms, 0.0), "kNm",
                     "Maximum sagging moment")
        calc.formula("M_max,hog", calc.tr("at x = {x:.2f} m", x=from_base(xh, "m")), min(Mh, 0.0), "kNm",
                     "Maximum hogging moment")
        calc.formula("V_max", calc.tr("at x = {x:.2f} m", x=from_base(xv, "m")), abs(V), "kN",
                     "Maximum shear force")
        calc.formula("δ_max", calc.tr("at x = {x:.2f} m", x=from_base(xdm, "m")), dmax, "mm",
                     "Maximum deflection (down +)")
        calc.figure(beam_diagrams(res, deflection=True), "Shear, moment and deflection")
        calc.model3d = cls._scene(calc, beam, res)

    @staticmethod
    def _scene(calc, beam, res) -> dict:
        L = beam.length / 1000
        h, w = max(0.25, L / 25), 0.25
        sc = Scene3D("beam", calc.tr)
        for key, label in (("beam", "Beam"), ("supports", "Supports"), ("loads", "Loads"),
                           ("defl", "Deflected shape"), ("moment", "Bending moment")):
            sc.layer(key, label, toggle=key != "beam")
        sc.box("beam", (L / 2, h / 2, 0), (L, h, w), PALETTE["steel"])
        sb.supports(sc, "supports", [(s.x / 1000, s.kind) for s in beam.supports], h, w)
        for x, R, _ in res.reactions:
            sc.label("supports", calc.tr("R = {r:.1f} kN", r=R / 1000), (x / 1000, -0.6, 0.3),
                     "result")
        wmax = max([abs(u.w) for u in beam.udls] or [1.0])
        for u in beam.udls:
            sb.udl_arrows(sc, "loads", u.x1 / 1000, u.x2 / 1000, u.w, h, wmax,
                          f"{u.w:.1f} kN/m")
        Pmax = max([abs(p.P) for p in beam.point_loads] or [1.0])
        for p in beam.point_loads:
            sb.point_arrow(sc, "loads", p.x / 1000, p.P / 1000, h, Pmax / 1000,
                           f"{p.P / 1000:.1f} kN")
        dmax = float(max(abs(res.deflection).max(), 1e-9))
        sb.deflected(sc, "defl", res.xd / 1000, res.deflection, 0.12 * L / dmax / 3, w / 2 + 0.02,
                     h / 2)
        sc.label("defl", calc.tr("δ_max = {d:.1f} mm", d=float(res.max_deflection[0])),
                 (float(res.max_deflection[1]) / 1000, -0.3, w / 2), "result")
        sb.moment_ribbon(sc, "moment", res.x / 1000, res.moment / 1e6, -w / 2 - 0.3, L / 8)
        return sc.to_dict()

