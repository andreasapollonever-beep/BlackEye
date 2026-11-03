"""RC slab — one-way continuous (pattern loading) or two-way rectangular panel (plate FD),
EN 1992-1-1 flexure, shear, span/depth (7.4.2) and optional punching at a column."""

from __future__ import annotations

import math

import numpy as np

from ..analysis import UDL, Beam, Support
from ..analysis.plate import solve_plate
from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base
from ..design.annex import get_annex
from ..design.ec2 import bar_area, design_flexure, section_capacity, shear_no_links
from ..report.scene3d import Scene3D, heat_color

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45"]
BARS = ["8", "10", "12", "14", "16"]
EDGE = ["Simply supported", "Fixed / continuous"]
HINT_BARS = "Use larger bars or reduce the spacing (or increase the slab thickness)."
HINT_DEFL = "Increase the slab thickness or the tension reinforcement."


def ld_limit(K: float, fck: float, rho: float) -> float:
    """EN 1992-1-1 Eq. 7.16a/b (ρ' = 0)."""
    r0 = math.sqrt(fck) * 1e-3
    rho = max(rho, 1e-6)
    if rho <= r0:
        return K * (11 + 1.5 * math.sqrt(fck) * r0 / rho + 3.2 * math.sqrt(fck) * (r0 / rho - 1) ** 1.5)
    return K * (11 + 1.5 * math.sqrt(fck) * r0 / rho)


@register
class RCSlabEC2(DesignModule):
    id = "ec2_rc_slab"
    title = "RC slab"
    category = "Concrete"
    standard = "EN 1992-1-1"
    uses_annex = True
    has_3d = True
    description = ("One-way continuous slabs with pattern loading, or two-way rectangular panels "
                   "with any edge condition (plate analysis); bottom/top reinforcement, shear, "
                   "deflection (span/depth) and punching at a column.")

    fields = [
        Field("type", "Slab type", kind="choice", choices=["Two-way panel", "One-way continuous"],
              default="Two-way panel", group="Geometry"),
        Field("lx", "Short span l_x", "m", 4.5, min=1, group="Geometry"),
        Field("ly", "Long span l_y (two-way)", "m", 6.0, min=1, group="Geometry"),
        Field("spans", "Number of equal spans (one-way)", kind="int", default=3, min=1, max=8,
              group="Geometry"),
        Field("e1", "Edge x = 0", kind="choice", choices=EDGE, default="Fixed / continuous",
              group="Edges (two-way)"),
        Field("e2", "Edge x = l_x", kind="choice", choices=EDGE, default="Simply supported",
              group="Edges (two-way)"),
        Field("e3", "Edge y = 0", kind="choice", choices=EDGE, default="Fixed / continuous",
              group="Edges (two-way)"),
        Field("e4", "Edge y = l_y", kind="choice", choices=EDGE, default="Simply supported",
              group="Edges (two-way)"),
        Field("h", "Slab thickness h", "mm", 180.0, min=100, group="Section"),
        Field("cover", "Cover", "mm", 25.0, min=15, group="Section"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C25/30",
              group="Section"),
        Field("fyk", "Reinforcement fyk", "N/mm²", 500.0, min=400, max=600, group="Section"),
        Field("g", "Superimposed permanent load (excl. self weight)", "kN/m²", 2.0, min=0,
              group="Loads", help="Finishes, screed, partitions."),
        Field("q", "Imposed load", "kN/m²", 2.0, min=0, group="Loads",
              help="EN 1991-1-1: residential 1.5–2.0, offices 3.0, balconies 4.0."),
        Field("dia_b", "Bottom bars Ø", kind="choice", choices=BARS, default="10",
              group="Reinforcement"),
        Field("s_b", "Bottom bar spacing", "mm", 150.0, min=75, max=400, group="Reinforcement"),
        Field("dia_t", "Top bars Ø (supports)", kind="choice", choices=BARS, default="12",
              group="Reinforcement"),
        Field("s_t", "Top bar spacing", "mm", 150.0, min=75, max=400, group="Reinforcement"),
        Field("punch", "Check punching at a column (flat slab)", kind="bool", default=False,
              group="Punching"),
        Field("c1", "Column size c1", "mm", 400.0, min=150, group="Punching", show_if="punch"),
        Field("c2", "Column size c2", "mm", 400.0, min=150, group="Punching", show_if="punch"),
        Field("VEd", "Column reaction V_Ed", "kN", 450.0, min=0, group="Punching",
              show_if="punch"),
        Field("pos", "Column position", kind="choice", choices=["Internal", "Edge", "Corner"],
              default="Internal", group="Punching", show_if="punch",
              help="β = 1.15 / 1.4 / 1.5 (EN 1992-1-1 Fig. 6.21N)."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        def pm(sym, expr, v, desc):  # moment per metre strip (b = 1000 mm), shown in kNm/m
            return 1000 * calc.formula(sym, expr, v / 1000, "kNm/m", desc)

        na = get_annex(calc.project.annex)
        fck = float(inp["concrete"].split("/")[0][1:])
        fcd = na.alpha_cc * fck / na.gamma_c
        fyk = inp["fyk"]
        fyd = fyk / na.gamma_s
        h = inp["h"]
        db, dt = float(inp["dia_b"]), float(inp["dia_t"])
        d = h - inp["cover"] - db / 2
        d2 = h - inp["cover"] - db - db / 2  # second (inner) layer for two-way
        dtop = h - inp["cover"] - dt / 2
        gk = 25e-6 * h + inp["g"]
        qk = inp["q"]
        calc.heading("Loads")
        calc.formula("g_k", "25 h + g_2", gk, "kN/m²", "Permanent load incl. self weight")
        calc.input("q_k", qk, "kN/m²", "Imposed load")
        pd = calc.formula("p_d", "1.35 g_k + 1.5 q_k", 1.35 * gk + 1.5 * qk, "kN/m²",
                          "ULS design load", ref="EN 1990 Eq. 6.10")
        lx, ly = inp["lx"], inp["ly"]
        two_way = inp["type"] == "Two-way panel"
        if two_way:
            if ly < lx:
                raise InputError("l_y must be the longer span", "ly")
            edges = tuple("fixed" if inp[k].startswith("Fixed") else "ss"
                          for k in ("e1", "e2", "e3", "e4"))
            calc.heading("Plate analysis (two-way panel)")
            calc.text("Kirchhoff plate, finite differences (28 × 28), ν = 0.2; edges: {e}.",
                      e=", ".join(calc.tr(inp[k]) for k in ("e1", "e2", "e3", "e4")))
            r = solve_plate(lx, ly, pd, 1.0, 0.2, edges)
            # moments per unit width (N·mm/mm) -> per metre (×1000)
            Mxs = pm("m_x,span", "plate FD", r["mx_span"] * 1000,
                               "Span moment in x (per m)")
            Mys = pm("m_y,span", "plate FD", r["my_span"] * 1000,
                               "Span moment in y (per m)")
            Mxsup = pm("m_x,sup", "plate FD", -min(r["mx_sup"], 0) * 1000,
                                 "Support moment in x (per m)")
            Mysup = pm("m_y,sup", "plate FD", -min(r["my_sup"], 0) * 1000,
                                 "Support moment in y (per m)")
            cases = [("Bottom, x direction (outer layer)", Mxs, d, db, inp["s_b"]),
                     ("Bottom, y direction (inner layer)", Mys, d2, db, inp["s_b"])]
            if Mxsup > 0:
                cases.append(("Top over supports, x", Mxsup, dtop, dt, inp["s_t"]))
            if Mysup > 0:
                cases.append(("Top over supports, y", Mysup, dtop, dt, inp["s_t"]))
            V = pd * lx / 2 * 1.15 * 1000  # per metre width (approx. reaction)
            nfix = sum(e == "fixed" for e in edges)
            K = 1.0 if nfix == 0 else (1.3 if nfix <= 2 else 1.5)
            span = lx
            res_plate = r
        else:
            n = inp["spans"]
            calc.heading("Continuous one-way slab — pattern loading")
            L = n * lx
            env_pos, env_neg, Vmax = 0.0, 0.0, 0.0
            patterns = {"all": range(n), "odd": range(0, n, 2), "even": range(1, n, 2)}
            for name, loaded in patterns.items():
                udls = []
                for k in range(n):
                    w = 1.35 * gk + (1.5 * qk if k in loaded else 0.0)
                    udls.append(UDL(k * lx, (k + 1) * lx, w * 1000))
                beam = Beam(L, 30000.0, 1000 * h**3 / 12,
                            [Support(k * lx, "pinned") for k in range(n + 1)], udls=udls)
                res = beam.solve()
                env_pos = max(env_pos, res.max_sagging[0])
                env_neg = min(env_neg, res.max_hogging[0])
                Vmax = max(Vmax, abs(res.max_shear[0]))
            Mxs = pm("M_span", "envelope (all / odd / even spans loaded)", env_pos,
                               "Maximum span moment (per m)")
            Msup = pm("M_sup", "envelope", -env_neg,
                                "Maximum support moment (per m)")
            cases = [("Bottom (span)", Mxs, d, db, inp["s_b"])]
            if Msup > 0:
                cases.append(("Top over supports", Msup, dtop, dt, inp["s_t"]))
            V = Vmax
            K = 1.0 if n == 1 else 1.3
            span = lx
            res_plate = None
        rho_gov = 0.0
        for label, M, dd, dia, s in cases:
            calc.heading(label, 2)
            res = design_flexure(calc, 1000, dd, M, fck, fcd, fyk, fyd, h,
                                 allow_compression=False, per_metre=True)
            As = bar_area(dia) * 1000 / s
            calc.formula("A_s,prov", f"Ø{dia:g} @ {s:g} mm", As * 1e-3, "mm²/m")
            if math.isfinite(res["As"]):
                calc.check_min("Reinforcement: A_s,prov ≥ A_s,req", As * 1e-3, res["As"] * 1e-3,
                               "mm²/m", "6.1", hint=HINT_BARS)
            calc.check_min("Minimum reinforcement: A_s,prov ≥ A_s,min", As * 1e-3,
                           res["As_min"] * 1e-3, "mm²/m", "9.3.1.1", hint=HINT_BARS)
            MRd, _ = section_capacity(1000, dd, As, fcd, fyd)
            calc.check("Bending: M_Ed ≤ M_Rd", M / 1000, MRd / 1000, "kNm/m", "6.1", hint=HINT_BARS)
            calc.check_limit("Bar spacing at max. moment: s ≤ min(2h, 250)", s,
                             min(2 * h, 250.0), "mm", "9.3.1.1(3)", hint="Reduce the bar spacing.")
            if label.startswith("Bottom") and rho_gov == 0.0:
                rho_gov = As / (1000 * dd)
                As_req = res["As"]
                As_prov = As
        calc.heading("Shear (no shear reinforcement)")
        shear_no_links(calc, 1000, d, bar_area(db) * 1000 / inp["s_b"], fck, na.gamma_c, V,
                       per_metre=True)
        calc.checks[-1].hint = calc.tr("Increase the slab thickness.")

        calc.heading("Deflection — span/depth ratio (7.4.2)")
        lim = ld_limit(K, fck, rho_gov)
        fac = min(As_prov / max(As_req, 1e-9), 1.5) if math.isfinite(As_req) else 1.0
        lim = calc.formula("(l/d)_lim", "K [11 + 1.5√f_ck ρ0/ρ + 3.2√f_ck (ρ0/ρ − 1)^1.5] ×"
                           " A_s,prov/A_s,req", lim * fac, "",
                           calc.tr("K = {k:g}, ρ = {r:.4f}", k=K, r=rho_gov), ref="Eq. 7.16", dp=1)
        calc.check_limit("Span/depth: l/d ≤ (l/d)_lim", span / d, lim, "", "7.4.2",
                         hint=HINT_DEFL)

        if inp["punch"]:
            cls._punching(calc, inp, d, fck, fcd, na, db)
        calc.model3d = cls._scene(calc, inp, res_plate, two_way)

    @staticmethod
    def _punching(calc, inp, d, fck, fcd, na, db):
        calc.heading("Punching at a column (6.4)")
        c1, c2, V = inp["c1"], inp["c2"], inp["VEd"]
        beta = {"Internal": 1.15, "Edge": 1.4, "Corner": 1.5}[inp["pos"]]
        calc.input("β", beta, "", inp["pos"], dp=2)
        u0 = {"Internal": 2 * (c1 + c2), "Edge": c2 + 3 * d + 2 * c1,
              "Corner": 3 * d + c1 + c2}[inp["pos"]]
        u0 = min(u0, 2 * (c1 + c2))
        u1 = {"Internal": 2 * (c1 + c2) + 4 * math.pi * d,
              "Edge": 2 * c1 + c2 + 2 * math.pi * d, "Corner": c1 + c2 + math.pi * d}[inp["pos"]]
        calc.formula("u_1", "basic control perimeter at 2d", u1, "mm", ref="6.4.2")
        rho = min(bar_area(float(inp["dia_t"])) / inp["s_t"] / d, 0.02)
        k = min(1 + math.sqrt(200 / d), 2.0)
        vRdc = calc.formula("v_Rd,c", "C_Rd,c k (100ρ f_ck)^(1/3) ≥ v_min",
                            max(0.18 / na.gamma_c * k * (100 * rho * fck) ** (1 / 3),
                                0.035 * k**1.5 * math.sqrt(fck)), "N/mm²", ref="Eq. 6.47", dp=3)
        vEd = calc.formula("v_Ed", "β V_Ed / (u_1 d)", beta * V / (u1 * d), "N/mm²",
                           ref="Eq. 6.38", dp=3)
        calc.check("Punching: v_Ed ≤ v_Rd,c", vEd, vRdc, "N/mm²", "6.4.4",
                   hint="Increase the slab thickness, add a drop panel or punching shear "
                        "reinforcement.")
        nu = 0.6 * (1 - fck / 250)
        vmax = na.punch_vmax * nu * fcd
        v0 = calc.formula("v_Ed,0", "β V_Ed / (u_0 d)", beta * V / (u0 * d), "N/mm²", dp=3)
        calc.check("Column face: v_Ed,0 ≤ v_Rd,max", v0, vmax, "N/mm²", "6.4.5(3)",
                   hint="Increase the column size or the slab thickness.")

    @staticmethod
    def _scene(calc, inp, r, two_way) -> dict:
        m = lambda v: from_base(v, "m")  # noqa: E731
        sc = Scene3D("rc_slab", calc.tr)
        sc.layer("slab", "Slab")
        sc.layer("moment", "Moment m_x (colour map)")
        lx = m(inp["lx"])
        ly = m(inp["ly"]) if two_way else m(inp["lx"]) * inp["spans"]
        h = m(inp["h"])
        sc.box("slab", (lx / 2, h / 2, ly / 2), (lx, h, ly), "#b4b8bf", opacity=0.35)
        if r is not None:
            mx = r["mx"]
            mmax = float(np.max(np.abs(mx))) or 1.0
            n = r["nx"]
            verts, cols, faces = [], [], []
            for i in range(n + 1):
                for j in range(n + 1):
                    verts.append((lx * i / n, h + 0.01 + 0.4 * r["w"][i, j] / (r["w_max"] or 1),
                                  ly * j / n))
                    cols.append(heat_color(0.5 + 0.5 * mx[i, j] / mmax))
            for i in range(n):
                for j in range(n):
                    a0 = i * (n + 1) + j
                    faces += [(a0, a0 + n + 1, a0 + n + 2), (a0, a0 + n + 2, a0 + 1)]
            sc.mesh("moment", verts, faces, opacity=0.9, colors=cols)
            sc.legend_item(heat_color(1.0), calc.tr("Sagging (bottom tension)"))
            sc.legend_item(heat_color(0.0), calc.tr("Hogging (top tension)"))
        return sc.to_dict()
