"""RC beam with a horizontal web opening (sleeve, duct) — EN 1992-1-1 checks.

EN 1992-1-1 has no clause dedicated to web openings.  The opening is designed with the method
used in practice for openings in the web (Vierendeel panel / strut-and-tie, 6.5): over the
length l0 of the opening the beam is split into a top and a bottom chord.  The global moment
gives an axial force N = M/z in the chords (z between chord centroids), the shear is shared
between the chords and causes secondary moments V_c·l0/2 (contraflexure at mid-length).  Every
chord is then checked with EN 1992-1-1: bending with axial force (6.1, strain compatibility),
shear with axial force (6.2.2 Eq. 6.2a, 6.2.3), and the full shear is hung by vertical links at
both edges of the opening (tie of a strut-and-tie model, 6.5.4).  Bar spacing (8.2), anchorage
of the bars over and under the opening (8.4) and minimum links (9.2.2) are checked.  A
circular sleeve of diameter D is treated, conservatively, as a square opening D × D.
"""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design.annex import get_annex
from ..design.ec2 import bar_area, moment_resistance
from ..report.scene3d import PALETTE, Scene3D

CONCRETE = ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "C45/55", "C50/60"]
BARS = ["8", "10", "12", "14", "16", "20", "25"]
LINKS = ["6", "8", "10", "12"]
SHAPES = ["Circular sleeve (diameter D)", "Rectangular opening (a × h0)"]
MODES = ["Simply supported beam with uniform load", "Given M_Ed and V_Ed at the opening",
         "Envelope of actions (several combinations)"]
DUCTILITY = ["DCM (l_cr = h_w)", "DCH (l_cr = 1.5 h_w)"]
EXPOSURE = ["X0, XC1", "XC2, XC3, XC4", "XD1, XD2, XS1, XS2, XS3"]
SHARE = ["In proportion to the chord areas", "Each chord takes the full shear (conservative)"]


def plastic_centroid(b, hc, layers, fcd, fyd, compression: bool) -> float:
    """Depth from the top of the chord of the line of action of its full axial resistance."""
    if compression:
        F = b * hc * fcd + sum(a * fyd for a, _ in layers)
        return (b * hc * fcd * hc / 2 + sum(a * fyd * d for a, d in layers)) / F
    A = sum(a for a, _ in layers)
    return sum(a * d for a, d in layers) / A if A else hc / 2


def chord_util(b, hc, layers, fcd, fyd, N, Mends):
    """Utilisation of a chord for axial force N (compression +) and the end moments Mends
    (about the chord centroid, + compresses the top face): M must lie in [−M_Rd⁻, M_Rd⁺]."""
    mpos, _ = moment_resistance(b, hc, layers, fcd, fyd, N)
    mneg, _ = moment_resistance(b, hc, [(a, hc - d) for a, d in layers], fcd, fyd, N)
    u = 0.0
    for M in Mends:
        cap = mpos if M >= 0 else mneg
        u = max(u, math.inf if cap <= 0 else abs(M) / cap)
    return u, mpos, mneg


@register
class BeamOpeningEC2(DesignModule):
    id = "ec2_beam_opening"
    title = "RC beam with a web opening (sleeve)"
    category = "Concrete"
    standard = "EN 1992-1-1 §6.1, 6.2, 6.5, 8.2, 8.4, 9.2"
    uses_annex = True
    has_3d = True
    description = ("Horizontal sleeve or rectangular opening through the web of a beam: chords "
                   "above and below the opening checked for axial force, bending and shear, "
                   "links that hang the shear at both edges, extra bars over and under the "
                   "opening with their anchorage — and the reinforcement drawn in 3D.")

    fields = [
        Field("mode", "Actions", kind="choice", choices=MODES, default=MODES[0], group="Actions"),
        Field("L", "Span L", "m", 6.0, min=1, max=30, group="Actions",
              show_if="mode=Simply supported beam with uniform load"),
        Field("gk", "Permanent load g_k (incl. self-weight)", "kN/m", 25.0, min=0,
              group="Actions", show_if="mode=Simply supported beam with uniform load"),
        Field("qk", "Variable load q_k", "kN/m", 15.0, min=0, group="Actions",
              show_if="mode=Simply supported beam with uniform load"),
        Field("MEd", "Design moment at the opening centre M_Ed", "kNm", 150.0,
              group="Actions", show_if="mode=Given M_Ed and V_Ed at the opening",
              help="Sagging positive. The moment at the two edges is M_Ed ± V_Ed·l0/2."),
        Field("VEd", "Design shear at the opening centre V_Ed", "kN", 100.0,
              group="Actions", show_if="mode=Given M_Ed and V_Ed at the opening",
              help="With its sign (dM/dx): the edges get M_Ed ± V_Ed·l0/2."),
        Field("cases", "Combinations at the opening centre", kind="table", group="Actions",
              show_if="mode=Envelope of actions (several combinations)",
              default=[{"name": "ULS 6.10", "M": 150.0, "V": 100.0},
                       {"name": "Seismic +E", "M": 120.0, "V": 140.0},
                       {"name": "Seismic −E", "M": -30.0, "V": -40.0}],
              columns=[Field("name", "Combination", kind="text", default="Combination"),
                       Field("M", "M_Ed (sagging +)", "kNm", 0.0),
                       Field("V", "V_Ed", "kN", 0.0)],
              help="Paste the M and V of every combination at the opening from the frame "
                   "analysis; the edges get M ± V·l0/2. Every row is checked."),
        Field("Lc", "Clear span between column faces (given actions)", "m", 6.0, min=1, max=30,
              group="Actions", show_if="mode!=Simply supported beam with uniform load", help="Used with given actions or an envelope for the distance of "
                                    "the opening from the far column face (EN 1998-1 l_cr)."),
        Field("b", "Width b", "mm", 300.0, min=150, group="Beam"),
        Field("h", "Overall depth h", "mm", 600.0, min=300, group="Beam"),
        Field("cnom", "Nominal cover to links", "mm", 30.0, min=15, group="Beam"),
        Field("concrete", "Concrete class", kind="choice", choices=CONCRETE, default="C25/30",
              group="Beam"),
        Field("fyk", "Reinforcement f_yk", "N/mm²", 500.0, min=400, max=600, group="Beam"),
        Field("dg", "Maximum aggregate size d_g", "mm", 16.0, min=8, max=32, group="Beam",
              help="For the minimum clear distance between bars, 8.2(2)."),
        Field("nb", "Bottom bars (number)", "", 4, kind="int", min=2, max=10,
              group="Main reinforcement"),
        Field("db", "Bottom bars Ø", kind="choice", choices=BARS, default="20",
              group="Main reinforcement"),
        Field("nt", "Top bars (number)", "", 2, kind="int", min=2, max=10,
              group="Main reinforcement"),
        Field("dt", "Top bars Ø", kind="choice", choices=BARS, default="12",
              group="Main reinforcement"),
        Field("dl", "Links Ø", kind="choice", choices=LINKS, default="8",
              group="Main reinforcement"),
        Field("sl", "Link spacing (outside the opening)", "mm", 150.0, min=50, max=400,
              group="Main reinforcement"),
        Field("shape", "Opening", kind="choice", choices=SHAPES, default=SHAPES[0],
              group="Opening"),
        Field("D", "Sleeve diameter D (outside)", "mm", 150.0, min=20, group="Opening",
              show_if="shape=Circular sleeve (diameter D)",
              help="Treated as a square D × D (conservative)."),
        Field("a", "Opening length a", "mm", 300.0, min=20, group="Opening",
              show_if="shape=Rectangular opening (a × h0)"),
        Field("h0", "Opening height h0", "mm", 150.0, min=20, group="Opening",
              show_if="shape=Rectangular opening (a × h0)"),
        Field("x", "Position of the opening centre from the support", "m", 1.5, min=0,
              group="Opening", help="Measured from the face of the left support / column."),
        Field("n_open", "Number of openings in a row", "", 1, kind="int", min=1, max=6,
              group="Opening", help="Identical openings at the same height."),
        Field("s_open", "Centre-to-centre spacing of the openings", "mm", 600.0, min=50,
              group="Opening", help="Openings closer than d (clear) are checked as one opening "
                                    "spanning the whole group."),
        Field("e", "Height of the opening centre above mid-depth", "mm", 0.0, group="Opening",
              help="0 = opening at mid-depth; positive upwards."),
        Field("share", "Shear between the chords", kind="choice", choices=SHARE,
              default=SHARE[0], group="Opening"),
        Field("na", "Extra bars over the opening (number)", "", 2, kind="int", min=0, max=8,
              group="Reinforcement at the opening",
              help="Bottom layer of the top chord, longer than the opening by l_bd each side."),
        Field("da", "Extra bars over the opening Ø", kind="choice", choices=BARS, default="12",
              group="Reinforcement at the opening"),
        Field("nu", "Extra bars under the opening (number)", "", 2, kind="int", min=0, max=8,
              group="Reinforcement at the opening",
              help="Top layer of the bottom chord, longer than the opening by l_bd each side."),
        Field("du", "Extra bars under the opening Ø", kind="choice", choices=BARS, default="12",
              group="Reinforcement at the opening"),
        Field("dc", "Chord links Ø", kind="choice", choices=LINKS, default="8",
              group="Reinforcement at the opening",
              help="Closed links in each chord over the length of the opening."),
        Field("sc", "Chord link spacing", "mm", 75.0, min=25, max=300,
              group="Reinforcement at the opening"),
        Field("ne", "Edge links on each side (number)", "", 3, kind="int", min=1, max=10,
              group="Reinforcement at the opening",
              help="Full-depth links next to each edge of the opening that hang the shear."),
        Field("de", "Edge links Ø", kind="choice", choices=LINKS, default="10",
              group="Reinforcement at the opening"),
        Field("legs", "Legs per edge link", "", 2, kind="int", min=2, max=6,
              group="Reinforcement at the opening"),
        Field("seismic", "Primary seismic beam (EN 1998-1)", kind="bool", default=True,
              group="Seismic", help="Openings are not allowed in the critical regions next to "
                                    "the columns (5.4.3.1.2, 5.5.3.1.3)."),
        Field("duct", "Ductility class", kind="choice", choices=DUCTILITY, default=DUCTILITY[0],
              group="Seismic", show_if="seismic"),
        Field("sls", "Check crack width at the opening (SLS)", kind="bool", default=True,
              group="Serviceability"),
        Field("exposure", "Exposure class", kind="choice", choices=EXPOSURE,
              default="XC2, XC3, XC4", group="Serviceability", show_if="sls",
              help="w_max of EN 1992-1-1 Table 7.1N / National Annex."),
        Field("psi2", "ψ2 of the variable load", "", 0.3, min=0, max=1, group="Serviceability",
              show_if="mode=Simply supported beam with uniform load", help="Used with the simply supported beam: p_qp = g_k + ψ2 q_k "
                                  "(EN 1990 Table A1.1, category A: 0.3)."),
        Field("creep", "Creep coefficient φ(∞, t0)", "", 2.0, min=0, max=5,
              group="Serviceability", show_if="sls",
              help="Long-term E_c,eff = E_cm/(1 + φ) (Eq. 7.20) for the steel stress; ≈ 2 for "
                   "indoor members loaded at 28 days (Figure 3.1)."),
        Field("Mqp", "M at the opening, quasi-permanent combination", "kNm", 70.0,
              group="Serviceability", show_if="mode!=Simply supported beam with uniform load",
              help="Used with given actions or an envelope (sagging +)."),
        Field("Vqp", "V at the opening, quasi-permanent combination", "kN", 45.0,
              group="Serviceability", show_if="mode!=Simply supported beam with uniform load",
              help="Used with given actions or an envelope."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        h = inp["h"]
        calc.note("EN 1992-1-1 has no clause dedicated to web openings: the opening is designed "
                  "as a Vierendeel panel / strut-and-tie model (6.5) and every chord is checked "
                  "with the clauses of EN 1992-1-1 named below.")
        if inp["shape"] == SHAPES[0]:
            l0 = h0 = inp["D"]
        else:
            l0, h0 = inp["a"], inp["h0"]
        d_glob = h - (inp["cnom"] + float(inp["dl"]) + float(inp["db"]) / 2)

        # ------------------------------------------------------------ openings
        n = inp["n_open"]
        sp = inp["s_open"]
        centres = [inp["x"] + i * sp for i in range(n)]
        group = False
        if n > 1:
            calc.heading("Several openings")
            calc.text("{n} openings at {s:.0f} mm centres, clear distance {c:.0f} mm, d = {d:.0f} "
                      "mm.", n=n, s=sp, c=sp - l0, d=d_glob)
            if sp - l0 < d_glob:
                group = True
                calc.text("Clear distance < d: the edge-link zones (d/2 each side) overlap, so the "
                          "openings are checked as ONE opening of length (n − 1)·s + l_0 = {L:.0f} mm "
                          "(conservative).", L=(n - 1) * sp + l0)
                openings = [(inp["x"] + (n - 1) * sp / 2, (n - 1) * sp + l0)]
            else:
                calc.text("Clear distance ≥ d: each opening is checked with its own actions.")
                openings = [(xc, l0) for xc in centres]
        else:
            openings = [(inp["x"], l0)]

        # ------------------------------------------------------------ actions
        mode = inp["mode"]
        cases = []
        if mode == MODES[0]:
            L = inp["L"]
            gG, gQ = na.combos["DA1-C1"][0], na.combos["DA1-C1"][2]
            w = gG * inp["gk"] + gQ * inp["qk"]
            wq = inp["gk"] + inp["psi2"] * inp["qk"]
            for i, (xc, lo) in enumerate(openings):
                x1, x2 = xc - lo / 2, xc + lo / 2
                if not (0 < x1 and x2 < L):
                    raise InputError("The opening must lie within the span", "x")
                lab = calc.tr("Opening {i}", i=i + 1) if len(openings) > 1 else calc.tr("ULS 6.10")
                cases.append({"label": lab, "xc": xc, "l0": lo,
                              "M": (w * x1 * (L - x1) / 2, w * x2 * (L - x2) / 2),
                              "V": (w * (L / 2 - x1), w * (L / 2 - x2)),
                              "Mqp": max(wq * x1 * (L - x1) / 2, wq * x2 * (L - x2) / 2),
                              "Vqp": max(abs(wq * (L / 2 - x1)), abs(wq * (L / 2 - x2))),
                              "w": w, "wq": wq})
            Lspan = L
        else:
            rows = ([{"name": calc.tr("Given"), "M": inp["MEd"], "V": inp["VEd"]}]
                    if mode == MODES[1] else inp["cases"])
            if not rows:
                raise InputError("Add at least one combination", "cases")
            for r in rows:
                for i, (xc, lo) in enumerate(openings):
                    lab = r["name"] + (f" — {calc.tr('Opening {i}', i=i + 1)}"
                                       if len(openings) > 1 else "")
                    Mc, Vc = r["M"], r["V"]
                    cases.append({"label": lab, "xc": xc, "l0": lo,
                                  "M": (Mc - Vc * lo / 2, Mc + Vc * lo / 2), "V": (Vc, Vc),
                                  "Mqp": inp["Mqp"] + abs(inp["Vqp"]) * lo / 2 *
                                  (1 if inp["Mqp"] >= 0 else -1),
                                  "Vqp": abs(inp["Vqp"])})
            Lspan = inp["Lc"]
            for xc, lo in openings:
                if not (0 < xc - lo / 2 and xc + lo / 2 < Lspan):
                    raise InputError("The opening must lie within the span", "x")

        # ------------------------------------------------------------ EN 1998-1
        if inp["seismic"]:
            calc.heading("Seismic critical regions (EN 1998-1)")
            dch = inp["duct"] == DUCTILITY[1]
            lcr = calc.formula("l_cr", "1.5 h_w" if dch else "h_w", (1.5 if dch else 1.0) * h, "mm",
                               "Length of the critical region at each column face",
                               ref="EN 1998-1 5.5.3.1.3(1)P" if dch else "EN 1998-1 5.4.3.1.2(1)P",
                               dp=0)
            first = min(xc - lo / 2 for xc, lo in openings)
            last = max(xc + lo / 2 for xc, lo in openings)
            calc.check_min("Opening outside the critical region (left column face)", first, lcr,
                           "mm", "EN 1998-1 5.4.3.1.2",
                           hint="Move the opening away from the column: at least l_cr from its "
                                "face.")
            calc.check_min("Opening outside the critical region (right column face)",
                           Lspan - last, lcr, "mm", "EN 1998-1 5.4.3.1.2",
                           hint="Move the opening away from the column: at least l_cr from its "
                                "face.")
            calc.note("Critical regions also exist on both sides of any other section liable to "
                      "yield in the seismic design situation (EN 1998-1 5.4.3.1.2(1)P).")

        # ------------------------------------------------------------ all cases
        if len(cases) > 1:
            res = []
            for cs in cases:
                sub = Calculation(cls.title, cls.id, cls.standard, calc.project, lang=calc.lang)
                try:
                    cls._design(sub, inp, cs, detail=False)
                    u, g = max(((k.utilisation, k.description) for k in sub.checks),
                               default=(0.0, ""))
                except InputError as exc:
                    u, g = math.inf, str(exc)
                res.append((u, g, cs))
            calc.heading("All cases")
            calc.table(["Case", "M_1 [kNm]", "M_2 [kNm]", "V [kN]", "U_max", "Governing check"],
                       [[cs["label"], f"{cs['M'][0] / 1e6:.1f}", f"{cs['M'][1] / 1e6:.1f}",
                         f"{max(abs(cs['V'][0]), abs(cs['V'][1])) / 1e3:.1f}", f"{u:.2f}", g]
                        for u, g, cs in res],
                       caption="Every combination at every opening; the governing one is shown "
                               "in full below")
            gov = max(res, key=lambda r: r[0])[2]
            calc.heading(calc.tr("Detailed calculation — governing case: {c}", c=gov["label"]))
        else:
            gov = cases[0]
        cls._design(calc, inp, gov, detail=True)
        calc.model3d = cls._scene(calc, inp, h, l0, h0, openings, group, calc._lens)

    @classmethod
    def _design(cls, calc: Calculation, inp: dict, cs: dict, detail: bool) -> None:
        na = get_annex(calc.project.annex)
        gc, gs, acc = na.gamma_c, na.gamma_s, na.alpha_cc
        fck = float(inp["concrete"].split("/")[0][1:])
        b, h, c = inp["b"], inp["h"], inp["cnom"]
        dl, db, dt = float(inp["dl"]), float(inp["db"]), float(inp["dt"])

        # ------------------------------------------------------------- materials
        calc.heading("Materials")
        calc.input("f_ck", fck, "N/mm²", "Characteristic strength")
        fcd = calc.formula("f_cd", f"α_cc f_ck / γ_c = {acc:g}·{fck:g}/{gc:g}", acc * fck / gc,
                           "N/mm²", ref="3.1.6", dp=2)
        fyd = calc.formula("f_yd", f"f_yk / γ_s = {inp['fyk']:g}/{gs:g}", inp["fyk"] / gs,
                           "N/mm²", ref="3.2.7", dp=1)
        fctm = 0.30 * fck ** (2 / 3)
        fctd = calc.formula("f_ctd", f"α_ct 0.7 f_ctm / γ_c, f_ctm = {fctm:.2f}",
                            1.0 * 0.7 * fctm / gc, "N/mm²", ref="3.1.6(2), Table 3.1", dp=3)

        # ------------------------------------------------------------- opening
        calc.heading("Opening and chords")
        l0 = cs["l0"]
        if inp["shape"] == SHAPES[0]:
            h0 = inp["D"]
            calc.input("D", inp["D"], "mm", "Sleeve diameter")
            calc.text("Circular sleeve treated as a square opening D × D (conservative).")
        else:
            h0 = inp["h0"]
        calc.input("l_0", l0, "mm", "Length of the opening")
        calc.input("h_0", h0, "mm", "Height of the opening")
        ht = calc.formula("h_t", "h/2 − e − h_0/2", h / 2 - inp["e"] - h0 / 2, "mm",
                          "Depth of the top chord")
        hb = calc.formula("h_b", "h/2 + e − h_0/2", h / 2 + inp["e"] - h0 / 2, "mm",
                          "Depth of the bottom chord")
        if ht <= 0 or hb <= 0:
            raise InputError("The opening does not fit in the depth of the beam", "e")

        # ------------------------------------------------------------- actions
        calc.heading("Actions at the edges of the opening")
        M1, M2 = cs["M"]
        V1, V2 = cs["V"]
        if "w" in cs:
            calc.formula("p_d", "γ_G g_k + γ_Q q_k", cs["w"], "kN/m",
                         "Design load (EN 1990 Eq. 6.10)", ref="EN 1990 Table A1.2(B)", dp=2)
            calc.text("Simply supported span L = {L:.2f} m: M(s) = p_d s (L − s)/2, "
                      "V(s) = p_d (L/2 − s).", L=inp["L"] / 1000)
        else:
            calc.text("Actions at the opening centre: M ± V·l_0/2 at the two edges.")
        x1 = cs["xc"] - l0 / 2
        x2 = cs["xc"] + l0 / 2
        Lsp = inp["L"] if "w" in cs else inp["Lc"]
        dist = min(x1, Lsp - x2)
        calc.formula("M_1", "M at the left edge", M1, "kNm", dp=2)
        calc.formula("M_2", "M at the right edge", M2, "kNm", dp=2)
        Mmax = M1 if abs(M1) >= abs(M2) else M2
        Vmax = calc.formula("V_Ed", "max |V| at the edges", max(abs(V1), abs(V2)), "kN",
                            "Shear at the opening", dp=2)
        if dist < h:
            calc.warn("The opening is closer than h to the support: the end region carries the "
                      "support strut — this method does not cover it; move the opening or design "
                      "the end region with a strut-and-tie model (6.5).")

        # ------------------------------------------------------------- reinforcement
        ca = c + dl
        At = inp["nt"] * bar_area(dt)
        Ab = inp["nb"] * bar_area(db)
        da, du = float(inp["da"]), float(inp["du"])
        dc = float(inp["dc"])
        Aa = inp["na"] * bar_area(da)
        Au = inp["nu"] * bar_area(du)
        # chord cover: the chord links lie inside the main links where the main links pass,
        # and at the opening face the cover is the nominal cover to the chord link
        ct1 = ca + dt / 2                  # top bars, from the top face
        ct2 = c + dc + da / 2              # bars over the opening, from the opening face
        cb1 = ca + db / 2
        cb2 = c + dc + du / 2
        top_layers = [(At, ct1), (Aa, ht - ct2)]
        bot_layers = [(Au, cb2), (Ab, hb - cb1)]

        # ------------------------------------------------------------- chord forces
        calc.heading("Chord forces (Vierendeel panel)")
        sag = Mmax >= 0
        pt = plastic_centroid(b, ht, top_layers, fcd, fyd, compression=sag)
        pb = plastic_centroid(b, hb, bot_layers, fcd, fyd, compression=not sag)
        calc.formula("p_t", "plastic centroid of the top chord (" +
                     ("compression: concrete + steel" if sag else "tension: steel") + ")", pt,
                     "mm", "Depth from the top face", dp=1)
        calc.formula("p_b", "plastic centroid of the bottom chord (" +
                     ("tension: steel" if sag else "compression: concrete + steel") + ")", pb,
                     "mm", "Depth from the top of the bottom chord", dp=1)
        z = calc.formula("z", "(h − h_b + p_b) − p_t", h - hb + pb - pt, "mm",
                         "Lever arm of the chord forces")
        Nt = calc.formula("N_t", "M / z (compression +)", Mmax / z, "kN",
                          "Axial force, top chord", dp=2)
        Nb = calc.formula("N_b", "−M / z", -Mmax / z, "kN", "Axial force, bottom chord", dp=2)
        et = calc.formula("e_t", "h_t/2 − p_t", ht / 2 - pt, "mm",
                          "Eccentricity of N_t from the top chord centroid", dp=1)
        eb = calc.formula("e_b", "h_b/2 − p_b", hb / 2 - pb, "mm",
                          "Eccentricity of N_b from the bottom chord centroid", dp=1)
        if inp["share"] == SHARE[0]:
            Vt = calc.formula("V_t", "V_Ed h_t / (h_t + h_b)", Vmax * ht / (ht + hb), "kN",
                              "Shear in the top chord (in proportion to the areas)", dp=2)
            Vb = calc.formula("V_b", "V_Ed h_b / (h_t + h_b)", Vmax * hb / (ht + hb), "kN",
                              "Shear in the bottom chord", dp=2)
        else:
            Vt = calc.formula("V_t", "V_Ed", Vmax, "kN", "Shear in the top chord (full)", dp=2)
            Vb = calc.formula("V_b", "V_Ed", Vmax, "kN", "Shear in the bottom chord (full)", dp=2)
        Mt = calc.formula("M_t", "V_t l_0 / 2", Vt * l0 / 2, "kNm",
                          "Secondary moment at the ends of the top chord", dp=3)
        Mb = calc.formula("M_b", "V_b l_0 / 2", Vb * l0 / 2, "kNm",
                          "Secondary moment at the ends of the bottom chord", dp=3)

        calc.heading("Beam section at the opening (without opening)")
        from ..design.ec2 import section_capacity
        d_glob = h - cb1
        MRg, _ = section_capacity(b, d_glob, Ab if Mmax >= 0 else At, fcd, fyd,
                                  ct1 if Mmax >= 0 else cb1, At if Mmax >= 0 else Ab)
        calc.formula("M_Rd", "strain compatibility, A_s = bottom bars, A_s2 = top bars", MRg,
                     "kNm", "Moment resistance of the full section", ref="6.1", dp=2)
        calc.check("Full section: |M_Ed| ≤ M_Rd", abs(Mmax), MRg, "kNm", "6.1",
                   hint="More or larger main bars, or a deeper beam.")

        calc.heading("Bar spacing in the chords")
        smin = calc.formula("s_min", "max(k_1 Ø, d_g + k_2, 20 mm), k_1 = 1, k_2 = 5 mm",
                            max(max(dt, da, db, du), inp["dg"] + 5, 20.0), "mm",
                            "Minimum clear distance between bar layers", ref="8.2(2)", dp=0)
        if inp["na"]:
            calc.check_min("Top chord: clear distance between the layers",
                           ht - ct1 - ct2 - dt / 2 - da / 2, smin, "mm", "8.2(2)",
                           hint="Lower the opening, make it smaller or use fewer bar layers.")
        if inp["nu"]:
            calc.check_min("Bottom chord: clear distance between the layers",
                           hb - cb1 - cb2 - db / 2 - du / 2, smin, "mm", "8.2(2)",
                           hint="Raise the opening, make it smaller or use fewer bar layers.")

        # ------------------------------------------------------------- chord bending
        calc.heading("Chords — bending with axial force (6.1)")
        calc.text("Chord end moments about the chord centroid: ±V_c l_0/2 + N e (+ compresses "
                  "the top face); each must lie between −M_Rd⁻ and M_Rd⁺ of the chord for its "
                  "axial force (strain compatibility, 3.1.7, 6.1).")
        for tag, T, hc, layers, N, ecc, Mc in (("Top", "t", ht, top_layers, Nt, et, Mt),
                                               ("Bottom", "b", hb, bot_layers, Nb, eb, Mb)):
            ends = (Mc + N * ecc, -Mc + N * ecc)
            u, mp, mn = chord_util(b, hc, layers, fcd, fyd, N, ends)
            calc.formula(f"M_Rd,{T}⁺", f"N = {N / 1e3:.1f} kN, top face compressed", mp, "kNm",
                         ref="6.1", dp=3)
            calc.formula(f"M_Rd,{T}⁻", f"N = {N / 1e3:.1f} kN, bottom face compressed", mn,
                         "kNm", ref="6.1", dp=3)
            calc.text("{c} chord end moments: {a:.2f} and {b:.2f} kNm.", c=calc.tr(tag),
                      a=ends[0] / 1e6, b=ends[1] / 1e6)
            calc.check(calc.tr("{c} chord: bending with axial force", c=calc.tr(tag)), u, 1.0, "",
                       "6.1", hint=("Deeper top chord (lower or smaller opening), more bars over "
                                    "the opening or larger top bars." if T == "t" else
                                    "More or larger bottom bars, more bars under the opening, or "
                                    "a deeper bottom chord (raise or reduce the opening)."))

        # ------------------------------------------------------------- chord shear
        calc.heading("Chords — shear (6.2)")
        Asw_c = 2 * bar_area(dc)
        cot = 1.0
        nu1 = 0.6 * (1 - fck / 250)
        rho_wmin = 0.08 * math.sqrt(fck) / inp["fyk"]
        for tag, hc, V, N, layers in (("top", ht, Vt, Nt, top_layers),
                                      ("bottom", hb, Vb, Nb, bot_layers)):
            T = "t" if tag == "top" else "b"
            calc.heading(calc.tr("{c} chord", c=calc.tr(tag.capitalize())), 2)
            d = max(d for _, d in layers if _ > 0) if any(a > 0 for a, _ in layers) else hc / 2
            As_l = min(a for a, _ in layers if a > 0) if all(a > 0 for a, _ in layers) else 0.0
            d = calc.formula(f"d_{T}", "depth to the outer bar layer", d, "mm", dp=0)
            k = min(1 + math.sqrt(200 / d), 2.0)
            rho = min(As_l / (b * d), 0.02)
            scp = min(N / (b * hc), 0.2 * fcd)
            vmin = 0.035 * k ** 1.5 * math.sqrt(fck)
            VRc = calc.formula(
                f"V_Rd,c,{T}",
                f"[0.18/γ_c k (100 ρ_l f_ck)^(1/3) + 0.15 σ_cp] b d ≥ (v_min + 0.15 σ_cp) b d, "
                f"k = {k:.3f}, ρ_l = {rho:.4f}, σ_cp = {scp:.3f}",
                max(max(0.18 / gc * k * (100 * rho * fck) ** (1 / 3), vmin) + 0.15 * scp, 0.0)
                * b * d, "kN", "Shear resistance without links (axial force included)",
                ref="6.2.2(1) Eq. 6.2", dp=2)
            zc = 0.9 * d
            VRs = calc.formula(f"V_Rd,s,{T}", f"A_sw/s z f_ywd cot θ, cot θ = {cot:g}, "
                               f"A_sw = 2·Ø{dc:g}", Asw_c / inp["sc"] * zc * fyd * cot, "kN",
                               "Shear resistance of the chord links", ref="6.2.3 Eq. 6.8", dp=2)
            VRmax = calc.formula(f"V_Rd,max,{T}", "α_cw b z ν_1 f_cd / (cot θ + tan θ)",
                                 b * zc * nu1 * fcd / (cot + 1 / cot), "kN",
                                 ref="6.2.3 Eq. 6.9", dp=2)
            calc.check(calc.tr("{c} chord: V ≤ max(V_Rd,c; V_Rd,s)", c=calc.tr(tag.capitalize())),
                       V, max(VRc, VRs), "kN", "6.2.2, 6.2.3",
                       hint="Closer or larger chord links, or a deeper chord.")
            calc.check(calc.tr("{c} chord: V ≤ V_Rd,max", c=calc.tr(tag.capitalize())), V, VRmax,
                       "kN", "6.2.3(3)", hint="Deeper chord or higher concrete class.")
        calc.check_min("Chord links: ρ_w ≥ ρ_w,min", Asw_c / (inp["sc"] * b), rho_wmin, "",
                       "9.2.2(5) Eq. 9.5N", hint="Closer or larger chord links.")

        # ------------------------------------------------------------- edge links
        calc.heading("Links at the edges of the opening (tie, 6.5.4)")
        Areq = calc.formula("A_sw,req", "V_Ed / f_ywd", Vmax / fyd, "mm²",
                            "Vertical tie at each edge that hangs the full shear",
                            ref="6.5.4", dp=0)
        Aprov = calc.formula("A_sw,prov", f"{inp['ne']} · {inp['legs']} · π Ø{inp['de']}²/4",
                             inp["ne"] * inp["legs"] * bar_area(float(inp["de"])), "mm²",
                             "Provided on each side", dp=0)
        calc.check_min("Edge links: A_sw,prov ≥ V_Ed / f_ywd", Aprov, Areq, "mm²", "6.5.4",
                       hint="More or larger links next to the opening.")
        zone = (h - ct1 - cb1) / 2
        calc.formula("s_e", "d/2 (placed within d/2 from each edge)", zone, "mm",
                     "Zone for the edge links", dp=0)
        if (inp["ne"] - 1) * 50 > zone:
            calc.warn("The edge links do not fit at 50 mm spacing within d/2 of the opening: "
                      "use fewer, larger links or more legs.")

        # ------------------------------------------------------------- anchorage
        calc.heading("Bars over and under the opening — anchorage (8.4)")
        lens = {}
        for name, n_, d_, eta1, txt in (("a", inp["na"], da, 0.7, "over"),
                                        ("u", inp["nu"], du, 1.0, "under")):
            if not n_:
                continue
            fbd = 2.25 * eta1 * 1.0 * fctd
            lb = d_ / 4 * fyd / fbd
            lbd = calc.formula(f"l_bd,{name}", f"Ø/4 · f_yd / f_bd, f_bd = 2.25 η_1 η_2 f_ctd, "
                               f"η_1 = {eta1:g}", max(lb, 10 * d_, 100.0), "mm",
                               calc.tr("Anchorage length of the bars {t} the opening (σ_sd = f_yd,"
                                       " α = 1)", t=calc.tr(txt)),
                               ref="8.4.2, 8.4.3, 8.4.4", dp=0)
            lens[name] = calc.formula(f"L_{name}", "l_0 + 2 l_bd", l0 + 2 * lbd, "mm",
                                      calc.tr("Length of the bars {t} the opening", t=calc.tr(txt)),
                                      dp=0)
        calc.note("η_1 = 0.7 is taken for the bars over the opening (top half, 8.4.2(2)); the bars "
                  "are anchored straight beyond each edge.")
        calc._lens = lens

        # ------------------------------------------------------------- SLS crack width
        if inp["sls"]:
            cls._crack(calc, inp, cs, na, b, h, ht, hb, l0, fck, top_layers, bot_layers,
                       (ct1, ct2, cb1, cb2), (dt, da, db, du), fcd, fyd)

    @staticmethod
    def _crack(calc, inp, cs, na, b, h, ht, hb, l0, fck, top_layers, bot_layers, covers, dias,
               fcd, fyd) -> None:
        """EN 1992-1-1 7.3.4 at the opening, quasi-permanent combination.

        Steel stresses from the cracked section at the opening edge (plane sections, concrete in
        tension and the opening ignored, compression only in the compressed chord, long-term
        modular ratio from E_c,eff of Eq. 7.20) plus the secondary moment of the tension chord
        shared by its two bar layers."""
        ct1, ct2, cb1, cb2 = covers
        dt, da, db, du = dias
        calc.heading("Crack width at the opening (7.3.4)")
        Mq, Vq = cs["Mqp"], cs["Vqp"]
        if "wq" in cs:
            calc.formula("p_qp", f"g_k + ψ2 q_k, ψ2 = {inp['psi2']:g}", cs["wq"], "kN/m",
                         "Quasi-permanent load", ref="EN 1990 Eq. 6.16b", dp=2)
        calc.formula("M_qp", "M at the more stressed edge (quasi-permanent)", Mq, "kNm", dp=2)
        calc.formula("V_qp", "V at the opening (quasi-permanent)", Vq, "kN", dp=2)
        Ecm = 22000 * ((fck + 8) / 10) ** 0.3
        fctm = 0.30 * fck ** (2 / 3)
        phi_c = inp["creep"]
        ae_l = calc.formula("α_e,L", "E_s (1 + φ) / E_cm", 200000 * (1 + phi_c) / Ecm, "",
                            "Long-term modular ratio (E_c,eff = E_cm/(1 + φ))", ref="Eq. 7.20",
                            dp=2)
        sag = Mq >= 0
        # (area, depth from the compressed face, Ø, key) — compressed face: top if sagging
        At, Aa = top_layers[0][0], top_layers[1][0]
        Au, Ab = bot_layers[0][0], bot_layers[1][0]
        lay = [(At, ct1, dt, "top"), (Aa, ht - ct2, da, "over"),
               (Au, h - hb + cb2, du, "under"), (Ab, h - cb1, db, "bottom")]
        hcomp = ht
        if not sag:
            lay = [(a, h - d, f, k) for a, d, f, k in lay]
            hcomp = hb
        lay = [r for r in lay if r[0] > 0]

        def conc(x):
            """(first moment, second moment) of the compressed concrete about the neutral axis:
            only the compressed chord (depth hcomp) — the opening carries nothing."""
            y = min(x, hcomp)
            return b * y * (x - y / 2), b * y ** 3 / 12 + b * y * (x - y / 2) ** 2

        def first_moment(x):
            sm = conc(x)[0]
            for a, d, _, _ in lay:
                sm += ((ae_l - 1) if d < x else ae_l) * a * (x - d)
            return sm
        lo, hi = 1e-6, h - (hb if sag else ht)
        for _ in range(100):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if first_moment(mid) < 0 else (lo, mid)
        x = (lo + hi) / 2
        if x > hcomp:
            calc.text("The neutral axis lies in the opening (x > depth of the compressed chord): "
                      "the whole compressed chord is in compression, the opening carries nothing.")
        Icr = conc(x)[1] + sum(((ae_l - 1) if d < x else ae_l) * a * (d - x) ** 2
                               for a, d, _, _ in lay)
        calc.formula("x", "Σ first moments = 0 (cracked, transformed; concrete only in the "
                     "compressed chord)", x, "mm",
                     "Neutral axis depth from the compressed face", ref="7.3.4(2)", dp=1)
        calc.formula("I_cr", "I_c (compressed chord) + Σ α_e A (d − x)²", Icr / 1e4, "cm⁴",
                     "Second moment of the cracked section", dp=0)
        tens = [r for r in lay if r[1] > x and r[3] in (("under", "bottom") if sag else
                                                         ("top", "over"))]
        tens.sort(key=lambda r: r[1])
        hc = hb if sag else ht
        Vc = Vq * hc / (ht + hb) if inp["share"] == SHARE[0] else Vq
        Mc = calc.formula("M_c,qp", "V_c,qp l_0 / 2", Vc * l0 / 2, "kNm",
                          "Secondary moment in the tension chord", dp=3)
        rows = []
        for a, d, phi, key in tens:
            sg = ae_l * abs(Mq) * (d - x) / Icr
            if len(tens) == 2:
                sg += Mc / (tens[1][1] - tens[0][1]) / a
            else:
                sg += Mc / (0.9 * hc) / a
            rows.append((sg, a, d, phi, key))
        if not rows:
            calc.text("No tension reinforcement at the opening edge.")
            return
        calc.table(["Layer", "A_s [mm²]", "d [mm]", "σ_s [N/mm²]"],
                   [[calc.tr(k), f"{a:.0f}", f"{d:.0f}", f"{sg:.1f}"] for sg, a, d, _, k in rows],
                   caption="σ_s = α_e M_qp (d − x)/I_cr + M_c,qp/(lever · A_s) (unfavourable "
                           "sign of the secondary moment)")
        worst = max(rows, key=lambda r: r[0])
        sig, As, d, phi, key = worst
        other = [r for r in rows if r is not worst]
        sig2 = other[0][0] if other else 0.0
        sig = calc.formula("σ_s", calc.tr("layer: {k}", k=calc.tr(key)), sig, "N/mm²", dp=1)
        k2 = (sig + sig2) / (2 * sig) if sig2 > 0 else 0.5
        calc.formula("k_2", "(ε_1 + ε_2)/(2 ε_1) from the two layers of the chord (0.5 in "
                     "bending)", k2, "", ref="7.3.4(3) Eq. 7.13", dp=3)
        face_dist = (h - d) if sag else d   # distance from the nearer outer face
        if key in ("over", "under"):        # layer next to the opening face
            face_dist = (cb2 if key == "under" else ct2)
        cov = face_dist - phi / 2
        hef = min(2.5 * face_dist, hc / 2)
        rho = calc.formula("ρ_p,eff", f"A_s / (b h_c,ef), h_c,ef = min(2.5(c + Ø/2); h_c/2) = "
                           f"{hef:.0f} mm", As / (b * hef), "", ref="7.3.2(3), Eq. 7.10", dp=4)
        ae = 200000 / Ecm
        de = calc.formula("ε_sm − ε_cm", "max([σ_s − k_t f_ct,eff/ρ (1 + α_e ρ)]/E_s; 0.6 σ_s/E_s), "
                          f"k_t = 0.4, f_ct,eff = f_ctm = {fctm:.2f}, α_e = E_s/E_cm = {ae:.2f}",
                          max((sig - 0.4 * fctm / rho * (1 + ae * rho)) / 200000,
                              0.6 * sig / 200000), "", ref="Eq. 7.9", dp=6)
        cc = inp["cnom"] + float(inp["dl"])
        nbar = {"top": inp["nt"], "over": inp["na"], "under": inp["nu"], "bottom": inp["nb"]}[key]
        spacing = (b - 2 * cc - phi) / max(nbar - 1, 1)
        if spacing <= 5 * (cov + phi / 2):
            sr = calc.formula("s_r,max", f"k_3 c + k_1 k_2 k_4 Ø/ρ, k_3 = {na.crack_k3:g}, "
                              f"k_1 = 0.8, k_4 = {na.crack_k4:g}, c = {cov:.0f} mm",
                              na.crack_k3 * cov + 0.8 * k2 * na.crack_k4 * phi / rho, "mm",
                              ref="Eq. 7.11", dp=0)
        else:
            sr = calc.formula("s_r,max", "1.3 (h − x), h − x = depth of the tension chord",
                              1.3 * hc, "mm", ref="Eq. 7.14", dp=0)
        wk = calc.formula("w_k", "s_r,max (ε_sm − ε_cm)", sr * de, "mm", "Crack width",
                          ref="Eq. 7.8", dp=3)
        wmax = calc.formula("w_max", calc.tr("exposure {e}", e=inp["exposure"]),
                            na.crack_wmax[inp["exposure"]], "mm", ref="7.3.1(5), Table 7.1N",
                            dp=2)
        calc.check("Crack width at the opening: w_k ≤ w_max", wk, wmax, "mm", "7.3.1, 7.3.4",
                   hint="More or smaller bars in the tension chord (lower steel stress and "
                        "closer cracks), or a deeper chord.")

    # ------------------------------------------------------------------ 3D
    @staticmethod
    def _scene(calc, inp, h, l0, h0, openings, group, lens) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        sc = Scene3D("beam_opening", calc.tr)
        for key, label in (("concrete", "Concrete"), ("main", "Main reinforcement"),
                           ("opening", "Reinforcement at the opening")):
            sc.layer(key, label, toggle=key != "concrete")
        b = inp["b"]
        bm, hm = m(b), m(h)
        n, sp = inp["n_open"], inp["s_open"]
        holes = [inp["x"] + i * sp for i in range(n)]          # actual sleeves (mm)
        first = min(xc - lo / 2 for xc, lo in openings)
        last = max(xc + lo / 2 for xc, lo in openings)
        lmax = max(lens.values(), default=0.0)
        pad = max(m(lmax) / 2, 2 * m(h), 0.6)
        x_shift = m(first) - pad
        L = m(last) - m(first) + 2 * pad
        X = lambda xmm: m(xmm) - x_shift  # noqa: E731
        yc = hm / 2 + m(inp["e"])
        sc.box("concrete", (L / 2, hm / 2, 0), (L, hm, bm), PALETTE["concrete"], opacity=0.22)
        for xh in holes:
            if inp["shape"] == SHAPES[0]:
                sc.cylinder("concrete", (X(xh), yc, -bm / 2 - 0.02), (X(xh), yc, bm / 2 + 0.02),
                            m(inp["D"]) / 2, "#2f8fd8", opacity=0.75)
            else:
                sc.box("concrete", (X(xh), yc, 0), (m(inp["a"]), m(h0), bm + 0.04), "#2f8fd8",
                       opacity=0.6)
        cc = m(inp["cnom"] + float(inp["dl"]))

        def bars(layer, nb, d, y, x_a, x_b, color):
            for i in range(nb):
                zz = -bm / 2 + cc + m(d) / 2 + i * (bm - 2 * cc - m(d)) / max(nb - 1, 1)
                sc.cylinder(layer, (x_a, y, zz), (x_b, y, zz), m(d) / 2, color)
        db, dt = float(inp["db"]), float(inp["dt"])
        bars("main", inp["nb"], db, cc + m(db) / 2, 0.03, L - 0.03, "#8a5a2b")
        bars("main", inp["nt"], dt, hm - cc - m(dt) / 2, 0.03, L - 0.03, "#8a5a2b")
        hot = "#e03b3b"
        o = m(inp["cnom"] + float(inp["dl"]) / 2)

        def link(layer, xx, y0, y1, color):
            sc.line(layer, [(xx, y0, -bm / 2 + o), (xx, y0, bm / 2 - o), (xx, y1, bm / 2 - o),
                            (xx, y1, -bm / 2 + o)], color, closed=True)
        ne, se = inp["ne"], 0.05
        busy = []
        for xc, lo in openings:
            x0 = X(xc)
            for key, sgn in (("a", 1), ("u", -1)):
                if key not in lens:
                    continue
                dd = float(inp["d" + key])
                y = yc + sgn * (m(h0) / 2 + m(inp["cnom"] + float(inp["dc"]) + dd / 2))
                Lmm = lens[key] - l0 + lo
                bars("opening", inp["n" + key], dd, y, x0 - m(Lmm) / 2, x0 + m(Lmm) / 2, hot)
                sc.label("opening", f"{inp['n' + key]}Ø{inp['d' + key]} L = {Lmm:.0f} mm",
                         (x0 + m(Lmm) / 2, hm * (0.85 if sgn > 0 else 0.12), bm / 2 + 0.1), "")
            for k in range(ne):
                for sgn in (-1, 1):
                    link("opening", x0 + sgn * (m(lo) / 2 + 0.025 + k * se), o, hm - o, "#d97706")
            sc.label("opening", calc.tr("{n} × Ø{d} each side", n=ne, d=inp["de"]),
                     (x0 - m(lo) / 2 - 0.1, hm + 0.05, bm / 2), "")
            n_c = max(int(m(lo) / m(inp["sc"])) + 1, 2)
            for k in range(n_c):
                xx = x0 - m(lo) / 2 + k * m(lo) / (n_c - 1)
                link("opening", xx, yc + m(h0) / 2 + o, hm - o, "#2e9b5f")
                link("opening", xx, o, yc - m(h0) / 2 - o, "#2e9b5f")
            busy.append((x0 - m(lo) / 2 - ne * se - 0.03, x0 + m(lo) / 2 + ne * se + 0.03))
        s = m(inp["sl"])
        xx = s / 2
        while xx < L:
            if not any(a < xx < b_ for a, b_ in busy):
                link("main", xx, o, hm - o, "#5a6b7d")
            xx += s
        txt = calc.tr("Opening {a:.0f} × {b:.0f} mm", a=l0, b=h0)
        if n > 1:
            txt += f" ×{n}" + (" — " + calc.tr("checked as one opening") if group else "")
        sc.label("opening", txt, (X((first + last) / 2), hm + 0.15, 0), "result")
        sc.legend_item(hot, calc.tr("Extra bars over/under the opening"))
        sc.legend_item("#2e9b5f", calc.tr("Chord links"))
        sc.legend_item("#d97706", calc.tr("Edge links (hang the shear)"))
        sc.legend_item("#8a5a2b", calc.tr("Main bars"))
        return sc.to_dict()
