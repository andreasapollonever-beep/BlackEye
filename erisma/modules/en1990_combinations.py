"""Load combinations — EN 1990 (Eq. 6.10, 6.12b, 6.14b–6.16b) with ψ from the National Annex."""

from __future__ import annotations

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..report.scene3d import Scene3D

KINDS = ["Permanent G", "Imposed Q", "Snow S", "Wind W", "Temperature T", "Seismic AEd"]
CATS = ["A", "B", "C", "D", "E", "F", "G", "H"]


@register
class CombinationsEN1990(DesignModule):
    id = "en1990_combinations"
    title = "Load combinations"
    category = "Loads"
    standard = "EN 1990 Annex A1"
    uses_annex = True
    has_3d = True
    description = ("Generates all ULS (6.10), seismic (6.12b) and SLS (characteristic, frequent, "
                   "quasi-permanent) combinations from your actions, with the ψ factors of the "
                   "National Annex, and finds the governing values.")

    fields = [
        Field("actions", "Actions (characteristic values, one effect e.g. N, M or V)", kind="table",
              group="Actions", default=[
                  {"name": "Self weight + finishes", "kind": "Permanent G", "cat": "A",
                   "value": 250.0},
                  {"name": "Imposed (residential)", "kind": "Imposed Q", "cat": "A", "value": 80.0},
                  {"name": "Snow", "kind": "Snow S", "cat": "A", "value": 10.0},
                  {"name": "Wind", "kind": "Wind W", "cat": "A", "value": 35.0},
                  {"name": "Seismic (design)", "kind": "Seismic AEd", "cat": "A", "value": 120.0}],
              columns=[Field("name", "Name", kind="text", default="Action"),
                       Field("kind", "Type", kind="choice", choices=KINDS, default="Imposed Q"),
                       Field("cat", "Category (imposed)", kind="choice", choices=CATS,
                             default="A"),
                       Field("value", "Value", "", 0.0)]),
        Field("A", "Site altitude (for snow ψ)", "", 100.0, min=0, group="Site", help="m"),
        Field("unit", "Unit of the values", kind="choice", choices=["kN", "kNm", "kN/m", "kN/m²"],
              default="kN", group="Site"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        acts = inp["actions"]
        if not acts:
            raise InputError("Add at least one action", "actions")
        u = inp["unit"]
        snow_key = "snow_high" if inp["A"] > 1000 else "snow_low"

        def psi(a):
            k = a["kind"]
            if k == "Imposed Q":
                return na.psi[a["cat"]]
            return {"Snow S": na.psi[snow_key], "Wind W": na.psi["wind"],
                    "Temperature T": na.psi["temperature"]}.get(k, (0, 0, 0))

        G = [a for a in acts if a["kind"] == "Permanent G"]
        Q = [a for a in acts if a["kind"] in ("Imposed Q", "Snow S", "Wind W", "Temperature T")]
        E = [a for a in acts if a["kind"] == "Seismic AEd"]
        val = lambda a: float(a["value"])  # noqa: E731  (unit-free: values as entered)
        calc.heading("Actions and ψ factors")
        calc.table(["Action", "Type", "Value", "ψ0", "ψ1", "ψ2"],
                   [[a["name"], calc.tr(a["kind"]), f"{val(a):g} {u}"] +
                    [f"{v:g}" for v in psi(a)] for a in acts],
                   caption="EN 1990 Table A1.1 (National Annex)")
        gG, gGf, gQ = 1.35, 1.0, 1.5  # Table A1.2(B), Eq. 6.10 (same in the Cyprus NA)
        sumG = sum(val(a) for a in G)
        rows, results = [], []

        def add(kind, label, value, expr):
            rows.append([calc.tr(kind), label, expr, f"{value:.2f} {u}"])
            results.append((kind, label, value))

        calc.heading("Ultimate limit state — Eq. 6.10 (STR/GEO, set B)")
        for lead in (Q or [None]):
            for gfac in (gG, gGf):
                v = gfac * sumG
                expr = f"{gfac:g}·ΣG"
                if lead:
                    v += gQ * val(lead)
                    expr += f" + {gQ:g}·{lead['name']}"
                for o in Q:
                    if o is not lead and val(o) > 0:
                        v += gQ * psi(o)[0] * val(o)
                        expr += f" + {gQ:g}·{psi(o)[0]:g}·{o['name']}"
                label = calc.tr("leading: {n}", n=lead["name"]) if lead else "G"
                add("ULS", label + (" (γG,inf)" if gfac == gGf else ""), v, expr)
        if E:
            calc.heading("Seismic design situation — Eq. 6.12b")
            for sign in (1, -1):
                v = sumG + sign * sum(val(e) for e in E) + sum(psi(o)[2] * val(o) for o in Q)
                add("Seismic", "G ± AEd + Σψ2Q" if sign > 0 else "G − AEd + Σψ2Q", v,
                    f"ΣG {'+' if sign > 0 else '−'} AEd + Σψ2·Q")
        calc.heading("Serviceability limit states")
        for lead in (Q or [None]):
            v = sumG + (val(lead) if lead else 0) + sum(psi(o)[0] * val(o) for o in Q
                                                         if o is not lead)
            add("SLS characteristic", lead["name"] if lead else "G", v, "ΣG + Q1 + Σψ0·Qi")
            v = sumG + (psi(lead)[1] * val(lead) if lead else 0) + sum(
                psi(o)[2] * val(o) for o in Q if o is not lead)
            add("SLS frequent", lead["name"] if lead else "G", v, "ΣG + ψ1·Q1 + Σψ2·Qi")
        add("SLS quasi-permanent", "—", sumG + sum(psi(o)[2] * val(o) for o in Q),
            "ΣG + Σψ2·Qi")
        calc.table(["Situation", "Combination", "Expression", "Effect"], rows,
                   caption="All combinations")
        calc.heading("Governing values")
        for kind in ("ULS", "Seismic", "SLS characteristic", "SLS quasi-permanent"):
            vals = [r for r in results if r[0] == kind]
            if vals:
                mx = max(vals, key=lambda r: r[2])
                mn = min(vals, key=lambda r: r[2])
                calc.text("{k}: max {mx:.2f} {u} ({lx}); min {mn:.2f} {u} ({ln})",
                          k=calc.tr(kind), mx=mx[2], lx=mx[1], mn=mn[2], ln=mn[1], u=u)
        calc.values["E_d,max"] = max(r[2] for r in results if r[0] == "ULS")
        calc.model3d = cls._scene(calc, results, u)

    @staticmethod
    def _scene(calc, results, unit) -> dict:
        cols = {"ULS": "#e03b3b", "Seismic": "#8e6cc4", "SLS characteristic": "#2a6f97",
                "SLS frequent": "#2e9b5f", "SLS quasi-permanent": "#c47a2c"}
        sc = Scene3D("combinations", calc.tr)
        for k in cols:
            if any(r[0] == k for r in results):
                sc.layer(k, k)
        vmax = max(abs(r[2]) for r in results) or 1.0
        x, prev = 0.0, None
        for kind, label, v in results:
            if prev is not None and kind != prev:
                x += 0.8
            hgt = 6.0 * v / vmax
            sc.box(kind, (x, hgt / 2, 0), (0.6, abs(hgt) or 0.01, 0.6), cols[kind])
            prev = kind
            x += 0.9
        for kind in cols:
            vals = [(i, r) for i, r in enumerate(results) if r[0] == kind]
            if not vals:
                continue
            i, r = max(vals, key=lambda t: t[1][2])
            xs = 0.0
            p2 = None
            for j, (kk, _, _) in enumerate(results):
                if p2 is not None and kk != p2:
                    xs += 0.8
                if j == i:
                    break
                p2 = kk
                xs += 0.9
            sc.label(kind, f"{calc.tr(kind)}: {r[2]:.1f} {unit}", (xs, 6.0 * r[2] / vmax + 0.4, 0),
                     "result")
            sc.legend_item(cols[kind], calc.tr(kind))
        return sc.to_dict()

