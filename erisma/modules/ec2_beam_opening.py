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
MODES = ["Simply supported beam with uniform load", "Given M_Ed and V_Ed at the opening"]
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
        Field("VEd", "Design shear at the opening centre V_Ed", "kN", 100.0, min=0,
              group="Actions", show_if="mode=Given M_Ed and V_Ed at the opening"),
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
              group="Opening"),
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
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        gc, gs, acc = na.gamma_c, na.gamma_s, na.alpha_cc
        fck = float(inp["concrete"].split("/")[0][1:])
        b, h, c = inp["b"], inp["h"], inp["cnom"]
        dl, db, dt = float(inp["dl"]), float(inp["db"]), float(inp["dt"])
        calc.note("EN 1992-1-1 has no clause dedicated to web openings: the opening is designed "
                  "as a Vierendeel panel / strut-and-tie model (6.5) and every chord is checked "
                  "with the clauses of EN 1992-1-1 named below.")

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
        if inp["shape"] == SHAPES[0]:
            l0 = h0 = inp["D"]
            calc.input("D", inp["D"], "mm", "Sleeve diameter")
            calc.text("Circular sleeve treated as a square opening D × D (conservative).")
        else:
            l0, h0 = inp["a"], inp["h0"]
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
        x = inp["x"]
        x1, x2 = x - l0 / 2, x + l0 / 2
        if inp["mode"] == MODES[0]:
            L = inp["L"]
            if not (0 < x1 and x2 < L):
                raise InputError("The opening must lie within the span", "x")
            gG, gQ = na.combos["DA1-C1"][0], na.combos["DA1-C1"][2]
            w = calc.formula("p_d", f"{gG:g} g_k + {gQ:g} q_k", gG * inp["gk"] + gQ * inp["qk"],
                             "kN/m", "Design load (EN 1990 Eq. 6.10)",
                             ref="EN 1990 Table A1.2(B)", dp=2)

            def M(s):
                return w * s * (L - s) / 2

            def V(s):
                return w * (L / 2 - s)
            calc.text("Simply supported span L = {L:.2f} m: M(s) = p_d s (L − s)/2, "
                      "V(s) = p_d (L/2 − s).", L=L / 1000)
            M1, M2 = M(x1), M(x2)
            V1, V2 = V(x1), V(x2)
            dist = min(x1, L - x2)
        else:
            Mc, Vc = inp["MEd"], inp["VEd"]
            M1, M2 = Mc - Vc * l0 / 2, Mc + Vc * l0 / 2
            V1 = V2 = Vc
            dist = x1
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
        calc.model3d = cls._scene(calc, inp, b, h, c, l0, h0, x, ht, hb, lens)

    # ------------------------------------------------------------------ 3D
    @staticmethod
    def _scene(calc, inp, b, h, c, l0, h0, x, ht, hb, lens) -> dict:
        m = lambda v: v / 1000  # noqa: E731
        sc = Scene3D("beam_opening", calc.tr)
        for key, label in (("concrete", "Concrete"), ("main", "Main reinforcement"),
                           ("opening", "Reinforcement at the opening")):
            sc.layer(key, label, toggle=key != "concrete")
        # a segment of the beam centred on the opening, long enough for the extra bars
        L = max(4 * m(h), m(max(lens.values(), default=l0)) + 4 * m(inp["sl"]), 2.0)
        x0 = L / 2  # opening centre in the scene
        bm, hm = m(b), m(h)
        yc = hm / 2 + m(inp["e"])
        sc.box("concrete", (L / 2, hm / 2, 0), (L, hm, bm), PALETTE["concrete"], opacity=0.22)
        if inp["shape"] == SHAPES[0]:
            sc.cylinder("concrete", (x0, yc, -bm / 2 - 0.02), (x0, yc, bm / 2 + 0.02),
                        m(inp["D"]) / 2, "#2f8fd8", opacity=0.75)
        else:
            sc.box("concrete", (x0, yc, 0), (m(l0), m(h0), bm + 0.04), "#2f8fd8", opacity=0.6)
        cc = m(inp["cnom"] + float(inp["dl"]))

        def bars(layer, n, d, y, x_a, x_b, color):
            for i in range(n):
                zz = -bm / 2 + cc + m(d) / 2 + i * (bm - 2 * cc - m(d)) / max(n - 1, 1)
                sc.cylinder(layer, (x_a, y, zz), (x_b, y, zz), m(d) / 2, color)
        db, dt = float(inp["db"]), float(inp["dt"])
        bars("main", inp["nb"], db, cc + m(db) / 2, 0.03, L - 0.03, "#8a5a2b")
        bars("main", inp["nt"], dt, hm - cc - m(dt) / 2, 0.03, L - 0.03, "#8a5a2b")
        hot = "#e03b3b"
        if "a" in lens:
            y = yc + m(h0) / 2 + m(inp["cnom"] + float(inp["dc"]) + float(inp["da"]) / 2)
            bars("opening", inp["na"], float(inp["da"]), y, x0 - m(lens["a"]) / 2,
                 x0 + m(lens["a"]) / 2, hot)
        if "u" in lens:
            y = yc - m(h0) / 2 - m(inp["cnom"] + float(inp["dc"]) + float(inp["du"]) / 2)
            bars("opening", inp["nu"], float(inp["du"]), y, x0 - m(lens["u"]) / 2,
                 x0 + m(lens["u"]) / 2, hot)
        o = m(inp["cnom"] + float(inp["dl"]) / 2)

        def link(layer, xx, y0, y1, color):
            sc.line(layer, [(xx, y0, -bm / 2 + o), (xx, y0, bm / 2 - o), (xx, y1, bm / 2 - o),
                            (xx, y1, -bm / 2 + o)], color, closed=True)
        # main links outside the opening zone (+ edge-link zone)
        ne, se = inp["ne"], 0.05
        clear = m(l0) / 2 + ne * se + 0.03
        s = m(inp["sl"])
        xx = s / 2
        while xx < L:
            if abs(xx - x0) > clear:
                link("main", xx, o, hm - o, "#5a6b7d")
            xx += s
        for k in range(ne):
            for sgn in (-1, 1):
                link("opening", x0 + sgn * (m(l0) / 2 + 0.025 + k * se), o, hm - o, "#d97706")
        # chord links over the opening length
        sc_ = m(inp["sc"])
        n_c = max(int(m(l0) / sc_) + 1, 2)
        for k in range(n_c):
            xx = x0 - m(l0) / 2 + k * m(l0) / (n_c - 1)
            link("opening", xx, yc + m(h0) / 2 + o, hm - o, "#2e9b5f")
            link("opening", xx, o, yc - m(h0) / 2 - o, "#2e9b5f")
        sc.label("opening", calc.tr("Opening {a:.0f} × {b:.0f} mm", a=l0, b=h0),
                 (x0, hm + 0.15, 0), "result")
        for key, xb in (("a", None), ("u", None)):
            if key in lens:
                yy = hm * (0.85 if key == "a" else 0.12)
                sc.label("opening", f"{inp['n' + key]}Ø{inp['d' + key]} L = {lens[key]:.0f} mm",
                         (x0 + m(lens[key]) / 2, yy, bm / 2 + 0.1), "")
        sc.label("opening", calc.tr("{n} × Ø{d} each side", n=inp["ne"], d=inp["de"]),
                 (x0 - m(l0) / 2 - 0.1, hm + 0.05, bm / 2), "")
        sc.legend_item(hot, calc.tr("Extra bars over/under the opening"))
        sc.legend_item("#2e9b5f", calc.tr("Chord links"))
        sc.legend_item("#d97706", calc.tr("Edge links (hang the shear)"))
        sc.legend_item("#8a5a2b", calc.tr("Main bars"))
        return sc.to_dict()
