"""Floor and roof loads — EN 1991-1-1:2002 (self-weight from the layer build-up, imposed loads
by category of use, reduction factors α_A / α_n, movable partitions, parapet loads).

Values checked against the Greek translation of EN 1991-1-1:2002 (April 2002): Tables 6.1–6.12,
Eq. 6.1 and 6.2, 6.3.1.2(8) and Annex A (Tables A.1–A.7, A.12).  The imposed-load NDPs are
read from :mod:`erisma.design.annex` (``imposed``, ``parapet``).
"""

from __future__ import annotations

from ..core import Calculation, DesignModule, Field, InputError, register
from ..core.units import from_base, to_base
from ..design.annex import get_annex
from ..report.scene3d import Scene3D

# category of use (label shown to the user) -> annex key
CATEGORIES = {
    "A — residential: floors": "A_floor",
    "A — residential: stairs": "A_stairs",
    "A — residential: balconies": "A_balcony",
    "B — offices": "B",
    "C1 — areas with tables (schools, cafés, restaurants)": "C1",
    "C2 — fixed seats (churches, theatres, cinemas)": "C2",
    "C3 — no obstacles to moving people (museums, halls, lobbies)": "C3",
    "C4 — physical activities (dance halls, gymnasia, stages)": "C4",
    "C5 — large crowds (concert halls, stands, terraces)": "C5",
    "D1 — general retail shops": "D1",
    "D2 — department stores": "D2",
    "E1 — storage (incl. books and documents)": "E1",
    "F — garages, vehicles ≤ 30 kN": "F",
    "G — traffic areas, vehicles 30–160 kN": "G",
    "H — roofs not accessible except for maintenance": "H",
}
CLAUSE = {"A_floor": "Table 6.2", "A_stairs": "Table 6.2", "A_balcony": "Table 6.2",
          "B": "Table 6.2", "C1": "Table 6.2", "C2": "Table 6.2", "C3": "Table 6.2",
          "C4": "Table 6.2", "C5": "Table 6.2", "D1": "Table 6.2", "D2": "Table 6.2",
          "E1": "Table 6.4", "F": "Table 6.8", "G": "Table 6.8", "H": "Table 6.10"}

# EN 1991-1-1 Annex A — nominal densities γ [kN/m³].  Where the table gives a range the
# upper value is used (conservative for gravity loads; EN 1991-1-1 4.1 NOTE).
MATERIALS = {
    "Reinforced concrete (normal weight)": (25.0, "Table A.1: 24.0 + 1.0 for reinforcement"),
    "Plain concrete (normal weight)": (24.0, "Table A.1"),
    "Lightweight concrete LC 1.0": (10.0, "Table A.1: 9.0–10.0"),
    "Lightweight concrete LC 1.2": (12.0, "Table A.1: 10.0–12.0"),
    "Lightweight concrete LC 1.4": (14.0, "Table A.1: 12.0–14.0"),
    "Lightweight concrete LC 1.6": (16.0, "Table A.1: 14.0–16.0"),
    "Lightweight concrete LC 1.8": (18.0, "Table A.1: 16.0–18.0"),
    "Lightweight concrete LC 2.0": (20.0, "Table A.1: 18.0–20.0"),
    "Cement mortar (screed)": (23.0, "Table A.1: 19.0–23.0"),
    "Gypsum mortar (plaster)": (18.0, "Table A.1: 12.0–18.0"),
    "Lime-cement mortar": (20.0, "Table A.1: 18.0–20.0"),
    "Lime mortar": (18.0, "Table A.1: 12.0–18.0"),
    "Terra cotta (ceramic tiles)": (21.0, "Table A.2"),
    "Granite, syenite, porphyry": (30.0, "Table A.2: 27.0–30.0"),
    "Basalt, diorite, gabbro": (31.0, "Table A.2: 27.0–31.0"),
    "Sandstone": (27.0, "Table A.2: 21.0–27.0"),
    "Dense limestone": (29.0, "Table A.2: 20.0–29.0"),
    "Other limestone": (20.0, "Table A.2"),
    "Slate": (28.0, "Table A.2"),
    "Timber C24": (4.2, "Table A.3"),
    "Timber C30": (4.6, "Table A.3"),
    "Glued laminated timber GL24h": (3.7, "Table A.3"),
    "Plywood (softwood)": (5.0, "Table A.3"),
    "Particle board": (8.0, "Table A.3: 7.0–8.0"),
    "Cement-bonded particle board": (12.0, "Table A.3"),
    "Steel": (78.0, "Table A.4: 77.0–78.0"),
    "Aluminium": (27.0, "Table A.4"),
    "Glass in sheets": (25.0, "Table A.5"),
    "Acrylic sheet": (12.0, "Table A.5"),
    "Expanded polystyrene, granules": (0.3, "Table A.5"),
    "Gravel and sand, bulk (e.g. roof garden)": (20.0, "Table A.7: 15.0–20.0"),
    "Sand": (19.0, "Table A.7: 14.0–19.0"),
    "Water": (10.0, "Table A.7"),
    "Pitch, asphalt": (14.0, "Table A.12"),
    "Other material (enter γ)": (None, "value entered by the user"),
}
PARTITIONS = {
    "None": None,
    "Movable partitions ≤ 1.0 kN/m": 0.5,
    "Movable partitions ≤ 2.0 kN/m": 0.8,
    "Movable partitions ≤ 3.0 kN/m": 1.2,
    "Heavier partitions (> 3.0 kN/m)": "heavy",
}
MODES = ["Recommended values (National Annex)", "My own values"]
ELEMENTS = ["Floor, beam or slab", "Column or wall (several storeys)"]


def letter(key: str) -> str:
    """EN 1990 Table A1.1 category (A … H) of an annex key."""
    return key[0]


@register
class ImposedLoadsEN1991(DesignModule):
    id = "ec1_imposed_loads"
    title = "Floor and roof loads"
    category = "Loads"
    standard = "EN 1991-1-1"
    uses_annex = True
    has_3d = True
    description = ("Self-weight of the floor build-up from the material densities of Annex A, "
                   "imposed load by category of use (Tables 6.1–6.10), reduction factors α_A "
                   "and α_n, movable partitions, parapet loads, and the design values.")

    fields = [
        Field("cat", "Category of use", kind="choice", choices=list(CATEGORIES),
              default="A — residential: floors", group="Use",
              help="EN 1991-1-1 Tables 6.1, 6.3, 6.7 and 6.9. Areas with several uses: take "
                   "the most unfavourable category (6.3.1.2(7))."),
        Field("mode", "Values of q_k and Q_k", kind="choice", choices=MODES, default=MODES[0],
              group="Use", help="Where Table 6.2 gives a range the National Annex chooses the "
                                "value; the recommended (underlined) value is used otherwise."),
        Field("qk_user", "Imposed load q_k", "kN/m²", 2.0, min=0, group="Use",
              show_if="mode=My own values"),
        Field("Qk_user", "Concentrated load Q_k", "kN", 2.0, min=0, group="Use",
              show_if="mode=My own values"),
        Field("partitions", "Movable partitions", kind="choice", choices=list(PARTITIONS),
              default="Movable partitions ≤ 2.0 kN/m", group="Use",
              help="Self-weight per metre length of wall; taken as an extra uniform imposed load "
                   "(6.3.1.2(8)). Heavier partitions must be modelled where they stand."),
        Field("element", "Load for", kind="choice", choices=ELEMENTS, default=ELEMENTS[0],
              group="Reduction"),
        Field("A", "Loaded area A of the member", "m²", 20.0, min=0.1, group="Reduction",
              show_if="element=Floor, beam or slab",
              help="Area that loads the member under consideration (α_A, Eq. 6.1)."),
        Field("n", "Storeys of the same category above the member", "", 3, kind="int", min=1,
              max=60, group="Reduction", show_if="element=Column or wall (several storeys)",
              help="α_n reduces the imposed load from several storeys (Eq. 6.2, n > 2)."),
        Field("reduce", "Apply the reduction factor", kind="bool", default=True,
              group="Reduction",
              help="When the imposed load is an accompanying action only one of ψ and α_n may "
                   "be used (3.3.2(2)P)."),
        Field("layers", "Floor build-up (permanent)", kind="table", group="Self-weight",
              default=[
                  {"name": "Floor tiles", "material": "Terra cotta (ceramic tiles)", "t": 20.0,
                   "gamma": 20.0},
                  {"name": "Screed", "material": "Cement mortar (screed)", "t": 50.0,
                   "gamma": 20.0},
                  {"name": "RC slab", "material": "Reinforced concrete (normal weight)",
                   "t": 180.0, "gamma": 25.0},
                  {"name": "Plaster (soffit)", "material": "Gypsum mortar (plaster)", "t": 15.0,
                   "gamma": 18.0}],
              columns=[Field("name", "Layer", kind="text", default="Layer"),
                       Field("material", "Material (EN 1991-1-1 Annex A)", kind="choice",
                             choices=list(MATERIALS), default="Cement mortar (screed)"),
                       Field("t", "Thickness", "mm", 50.0, min=0),
                       Field("gamma", "γ (only for 'Other material')", "kN/m³", 20.0, min=0)],
              help="Paste from Excel or add rows. Ranges in Annex A: the upper value is used."),
        Field("g_extra", "Other permanent loads (ceiling, services)", "kN/m²", 0.0, min=0,
              group="Self-weight"),
        Field("parapet", "Horizontal load on parapets / partitions", kind="bool", default=True,
              group="Parapets", help="Table 6.12 (height ≤ 1.20 m) and Annex B for car parks."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        key = CATEGORIES[inp["cat"]]
        cat = letter(key)
        if not inp["layers"]:
            raise InputError("Add at least one layer to the floor build-up", "layers")
        if not na.imposed_na and na.code != "EN":
            calc.note("No National Annex to EN 1991-1-1 has been entered for {a}: the EN "
                      "recommended values are used. Check them against the National Annex.",
                      a=calc.tr(na.label))

        # ------------------------------------------------------------ self-weight
        calc.heading("Permanent load — floor build-up")
        rows, gk = [], 0.0
        for i, ly in enumerate(inp["layers"], 1):
            gamma, src = MATERIALS[ly["material"]]
            if gamma is None:
                if ly["gamma"] <= 0:
                    raise InputError("Layer {i}: enter the density γ of 'Other material'", "layers")
                g = ly["gamma"]
                src = calc.tr("value entered by the user")
            else:
                g = to_base(gamma, "kN/m³")
                src = calc.tr(src, quiet=True)
            w = g * ly["t"]
            gk += w
            rows.append([calc.tr(ly["name"], quiet=True), calc.tr(ly["material"]), f"{ly['t']:g} mm",
                         f"{from_base(g, 'kN/m³'):g} kN/m³", src, f"{from_base(w, 'kN/m²'):.2f}"])
        calc.table(["Layer", "Material", "Thickness", "γ", "Source", "g [kN/m²]"], rows,
                   caption="EN 1991-1-1 Annex A — nominal densities")
        g_layers = calc.formula("g_layers", "Σ γ_i t_i", gk, "kN/m²", "Self-weight of the layers",
                                ref="5.1, Annex A", dp=2)
        g_extra = inp["g_extra"]
        if g_extra > 0:
            calc.input("g_extra", g_extra, "kN/m²", "Other permanent loads (ceiling, services)")
        gk = calc.formula("g_k", "g_layers + g_extra", g_layers + g_extra, "kN/m²",
                          "Characteristic permanent load", ref="5.2", dp=2)

        # --------------------------------------------------------------- imposed
        calc.heading("Imposed load — category of use")
        calc.label("Category", inp["cat"])
        if inp["mode"] == MODES[1]:
            qk, Qk = inp["qk_user"], inp["Qk_user"]
            qk = calc.input("q_k", qk, "kN/m²", "Imposed load (user value)")
            Qk = calc.input("Q_k", Qk, "kN", "Concentrated load (user value)")
        else:
            q0, Q0 = na.imposed[key]
            qk = calc.formula("q_k", CLAUSE[key], to_base(q0, "kN/m²"), "kN/m²",
                              "Uniformly distributed imposed load", ref=CLAUSE[key], dp=2)
            Qk = calc.formula("Q_k", CLAUSE[key], to_base(Q0, "kN"), "kN",
                              "Concentrated load (local checks, acting alone)", ref=CLAUSE[key],
                              dp=1)
        area = {"F": "100 × 100 mm", "G": "200 × 200 mm"}.get(key, "50 × 50 mm")
        calc.note("Q_k acts alone on a square of {a} at the most unfavourable position, and is "
                  "not combined with q_k (6.2.1(3)P, 6.3.1.2(5)P, 6.3.3.2(2)).", a=area)
        if key == "H":
            calc.note("Roofs: q_k, snow and wind are not applied together (3.3.2(1)). Roofs "
                      "other than metal sheeting must also carry 1.5 kN on a 50 mm square "
                      "(6.3.4.2(4)).")
        if key in ("C4", "C5"):
            calc.warn("Categories C4 and C5: examine dynamic effects (6.3.1.1(2)P, EN 1990).")
        if key in ("F", "G"):
            calc.note("Vehicle loads: Q_k as one axle of two square loads 1.80 m apart "
                      "(Figure 6.2).")

        psi0, psi1, psi2 = na.psi[cat]
        calc.text("ψ factors for category {c} (EN 1990 Table A1.1): ψ0 = {a:g}, ψ1 = {b:g}, "
                  "ψ2 = {d:g}", c=cat, a=psi0, b=psi1, d=psi2)

        # ------------------------------------------------------------- reduction
        alpha = 1.0
        if inp["reduce"]:
            if inp["element"] == ELEMENTS[0]:
                if cat in "ABCDE":
                    A = from_base(inp["A"], "m²")
                    calc.input("A", inp["A"], "m²", "Loaded area")
                    raw = 5.0 / 7.0 * psi0 + na.imposed_A0 / A
                    alpha = min(raw, 1.0)
                    if cat in "CD":
                        alpha = max(alpha, na.imposed_alphaA_min_CD)
                    expr = "min(5/7·ψ0 + A0/A; 1.0)"
                    if cat in "CD":
                        expr = "max(" + expr + "; 0.6)"
                    expr += f" = 5/7·{psi0:g} + {na.imposed_A0:g}/{A:g}"
                    alpha = calc.formula("α_A", expr, alpha, "", "Area reduction factor",
                                         ref="6.3.1.2(10), Eq. 6.1", dp=3)
                else:
                    calc.text("α_A applies to categories A to E only.")
            else:
                n = inp["n"]
                if cat in "ABCD" and n > 2:
                    alpha = calc.formula("α_n", f"(2 + (n − 2)·ψ0)/n = (2 + ({n} − 2)·{psi0:g})/{n}",
                                         (2 + (n - 2) * psi0) / n, "",
                                         "Reduction factor for several storeys",
                                         ref="6.3.1.2(11), Eq. 6.2", dp=3)
                    calc.note("If the imposed load is an accompanying action, use either ψ or "
                              "α_n, not both (3.3.2(2)P).")
                elif cat not in "ABCD":
                    calc.text("α_n applies to categories A to D only.")
                else:
                    calc.text("α_n applies for more than two storeys (n > 2); no reduction.")
        q_red = calc.formula("q_k,red", "α · q_k", alpha * qk, "kN/m²",
                             "Imposed load after reduction", dp=2) if alpha < 1.0 else qk

        # ------------------------------------------------------------ partitions
        part = PARTITIONS[inp["partitions"]]
        q_part = 0.0
        if part == "heavy":
            calc.warn("Partitions heavier than 3.0 kN/m: model them as line loads where they "
                      "stand (6.3.1.2(9)).")
        elif part is not None:
            if cat in "ABCD":
                q_part = calc.formula("q_k,part", inp["partitions"], to_base(part, "kN/m²"),
                                      "kN/m²", "Allowance for movable partitions (imposed)",
                                      ref="6.3.1.2(8)", dp=2)
            else:
                calc.text("The partition allowance of 6.3.1.2(8) applies to floors of "
                          "categories A to D.")
        q_tot = calc.formula("q_k,tot", "q_k,red + q_k,part", q_red + q_part, "kN/m²",
                             "Total characteristic imposed load", dp=2)

        # ---------------------------------------------------------- design values
        calc.heading("Design values per m²")
        gG, gQ = na.combos["DA1-C1"][0], na.combos["DA1-C1"][2]
        pEd = calc.formula("p_Ed", f"{gG:g}·g_k + {gQ:g}·q_k,tot", gG * gk + gQ * q_tot, "kN/m²",
                           "Design load, ULS (EN 1990 Eq. 6.10)", ref="EN 1990 Table A1.2(B)",
                           dp=2)
        calc.formula("p_k", "g_k + q_k,tot", gk + q_tot, "kN/m²",
                     "Characteristic combination (SLS)", ref="EN 1990 Eq. 6.14b", dp=2)
        calc.formula("p_qp", f"g_k + ψ2·q_k,tot = g_k + {psi2:g}·q_k,tot", gk + psi2 * q_tot,
                     "kN/m²", "Quasi-permanent combination (SLS, long-term deflection)",
                     ref="EN 1990 Eq. 6.16b", dp=2)
        calc.note("For seismic masses EN 1998-1 3.2.4 uses ψ_E,i = φ·ψ2,i.")

        # ---------------------------------------------------------------- parapets
        q_par = None
        if inp["parapet"]:
            calc.heading("Horizontal load on parapets and partition walls")
            pkey = {"A_floor": "A", "A_stairs": "A", "A_balcony": "A", "D1": "D",
                    "D2": "D", "E1": "E"}.get(key, key)
            if pkey in na.parapet:
                q_par = calc.formula("q_k,par", "Table 6.12", to_base(na.parapet[pkey], "kN/m"),
                                     "kN/m", "Horizontal line load at the top (height ≤ 1.20 m)",
                                     ref="6.4, Table 6.12", dp=2)
            elif key == "F":
                F = 0.5 * 1500 * 4.5**2 / (100 / 1000)  # B(2)-(3): m 1500 kg, v 4.5 m/s, δc 100 mm
                calc.formula("F_B", "0.5·m·v²/(δ_c + δ_b) = 0.5·1500·4.5²/0.100", F, "kN",
                             "Vehicle barrier force, rigid barrier (δ_b = 0)", ref="Annex B(2)",
                             dp=1)
                calc.text("Annex B(3): for vehicles ≤ 2500 kg and a rigid barrier F = 150 kN, "
                          "uniformly over 1.5 m, at 375 mm above the floor (B(5)); ramps: half "
                          "at 610 mm (B(6)).")
            elif key == "G":
                calc.text("Annex B(4): use the actual vehicle mass m in F = 0.5·m·v²/(δ_c + δ_b) "
                          "with v = 4.5 m/s and δ_c = 100 mm.")
            else:
                calc.text("Table 6.12 gives no parapet load for this category.")
        calc.model3d = cls._scene(calc, inp, gk, q_tot, q_par)

    @staticmethod
    def _scene(calc, inp, gk, q_tot, q_par) -> dict:
        sc = Scene3D("floor_loads", calc.tr)
        sc.layer("layers", "Floor build-up")
        sc.layer("loads", "Loads")
        cols = ["#c9b28a", "#9aa5b1", "#7d8b99", "#e6e1d6", "#b9c7d6", "#d8c3a5"]
        L, B = 3.0, 2.0
        y = 0.0
        scale = 4.0  # thicknesses exaggerated ×4 for legibility
        for i, ly in enumerate(reversed(inp["layers"])):
            h = max(ly["t"] / 1000 * scale, 0.02)
            sc.box("layers", (0, y + h / 2, 0), (L, h, B), cols[i % len(cols)])
            sc.label("layers", f"{calc.tr(ly['name'], quiet=True)} — {ly['t']:g} mm", (L / 2 + 0.15, y + h / 2, B / 2),
                     "")
            y += h
        qd = from_base(q_tot, "kN/m²")
        for x in (-1.2, -0.4, 0.4, 1.2):
            for z in (-0.6, 0.6):
                sc.arrow("loads", (x, y + 1.0, z), (0, -1, 0), 0.9, "#e03b3b")
        sc.label("loads", f"g_k = {from_base(gk, 'kN/m²'):.2f} kN/m² · q_k = {qd:.2f} kN/m²",
                 (0, y + 1.3, 0), "result")
        if q_par is not None:
            sc.box("layers", (0, y + 0.55, -B / 2 + 0.05), (L, 1.1, 0.1), "#b0b8c2", opacity=0.6)
            sc.arrow("loads", (0, y + 1.1, -B / 2 - 0.9), (0, 0, 1), 0.8, "#2a6f97")
            sc.label("loads", f"q_k,par = {from_base(q_par, 'kN/m'):.2f} kN/m",
                     (0, y + 1.3, -B / 2 - 0.9), "")
        sc.legend_item("#e03b3b", calc.tr("Imposed load"))
        return sc.to_dict()
