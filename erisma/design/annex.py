"""National Annexes: one table of nationally determined parameters (NDPs) per country.

Every calculation reads its partial factors from the annex selected in the
project details (``ProjectInfo.annex``).  Only values checked against the
published annex may be entered here — each annex records its source document.

To add a country: copy ``EN``, change only the NDPs the annex changes, set
``reference`` to the exact document and add hand-check tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# EN 1997-1 Annex A — (γG,unf, γG,fav, γQ, γφ', γc', γR,v, γR,h)
EN_COMBOS = {
    "DA1-C1": (1.35, 1.00, 1.50, 1.00, 1.00, 1.00, 1.00),
    "DA1-C2": (1.00, 1.00, 1.30, 1.25, 1.25, 1.00, 1.00),
    "DA2": (1.35, 1.00, 1.50, 1.00, 1.00, 1.40, 1.10),
    "DA3": (1.00, 1.00, 1.30, 1.25, 1.25, 1.00, 1.00),
}
EN_APPROACHES = {"DA1": ["DA1-C1", "DA1-C2"], "DA2": ["DA2"], "DA3": ["DA3"]}
APPROACH_CHOICES = ["National Annex", "DA1", "DA2", "DA3"]


@dataclass(frozen=True)
class Annex:
    code: str
    label: str
    reference: str
    # EN 1997-1
    combos: dict = field(default_factory=lambda: dict(EN_COMBOS))
    approaches: dict = field(default_factory=lambda: dict(EN_APPROACHES))
    default_approach: str = "DA1"
    equ: tuple = (1.10, 0.90, 1.50, 1.25, 1.25)  # γG,dst γG,stb γQ,dst γφ' γc' (A.1, A.2)
    gamma_Re: dict = field(default_factory=lambda: {"DA2": 1.4})  # earth resistance (A.13)
    slope_factors: tuple = (1.25, 1.25, 1.30)  # γφ', γc', γQ for slopes (DA1-C2 / DA3)
    # EN 1998-5 3.1(3) — material factors in the seismic design situation
    seismic_gamma_phi: float = 1.25
    seismic_gamma_c: float = 1.25
    # EN 1992-1-1
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    alpha_cc: float = 1.0
    alpha_cc_pl: float = 0.8
    punch_vmax: float = 0.4  # v_Rd,max = k ν f_cd at the column face (EN 1992-1-1 6.4.5(3))
    # EN 1997-1 8.6(4): ULS anchor load ≥ factor × SLS load (None = not required)
    anchor_sls_factor: float | None = None
    # Slopes: "M2" = factored strength (DA1-C2 / DA3); "DA2" = factored effects + γR,e
    slope_mode: str = "M2"
    slope_gRe: float = 1.0
    mandatory_approach: str | None = None
    # EN 1998-1 seismic zones: [(label, agR in g)]
    zones: tuple = ()
    # EN 1998-1 Table 3.2 — Type 1 spectrum: ground type -> (S, TB, TC, TD)
    spectrum: dict = field(default_factory=lambda: {
        "A": (1.0, 0.15, 0.4, 2.0), "B": (1.2, 0.15, 0.5, 2.0), "C": (1.15, 0.20, 0.6, 2.0),
        "D": (1.35, 0.20, 0.8, 2.0), "E": (1.4, 0.15, 0.5, 2.0)})
    gamma_I: dict = field(default_factory=lambda: {"I": 0.8, "II": 1.0, "III": 1.2, "IV": 1.4})
    spectrum_beta: float = 0.2
    # EN 1998-1 4.4.3.2(2): displacement reduction factor ν per importance class
    drift_nu: dict = field(default_factory=lambda: {"I": 0.5, "II": 0.5, "III": 0.4, "IV": 0.4})
    # EN 1990 Table A1.1 — ψ0, ψ1, ψ2
    psi: dict = field(default_factory=lambda: {
        "A": (0.7, 0.5, 0.3), "B": (0.7, 0.5, 0.3), "C": (0.7, 0.7, 0.6), "D": (0.7, 0.7, 0.6),
        "E": (1.0, 0.9, 0.8), "F": (0.7, 0.7, 0.6), "G": (0.7, 0.5, 0.3), "H": (0.0, 0.0, 0.0),
        "snow_high": (0.7, 0.5, 0.2), "snow_low": (0.5, 0.2, 0.0), "wind": (0.6, 0.2, 0.0),
        "temperature": (0.6, 0.5, 0.0)})
    # EN 1991-1-3: characteristic ground snow s_k(A) [kN/m²] or None (user input)
    snow_formula: str | None = None
    snow_max_altitude: float | None = None
    wind_map: bool = False
    air_density: float = 1.25
    # EN 1993-1-1 / -1-8
    gamma_M0: float = 1.0
    gamma_M1: float = 1.0
    gamma_M2: float = 1.25
    # EN 1998-3 Table 3.1 confidence factors
    CF: dict = field(default_factory=lambda: {"KL1": 1.35, "KL2": 1.20, "KL3": 1.00})
    # EN 1992-3 7.3.1(111): w_k1 = 0.2 mm (h_D/h ≤ 5) … 0.05 mm (h_D/h ≥ 35)
    wk1: tuple = (5.0, 0.2, 35.0, 0.05)
    # EN 1997-1 Table A.4 (M2): γ_cu (undrained strength) and γ_γ = 1.0
    gamma_cu_M2: float = 1.4
    # EN 1997-1 Tables A.6–A.8: pile type -> set -> (γ_b, γ_s, γ_t, γ_s,t)
    pile_R: dict = field(default_factory=lambda: {
        "Driven": {"R1": (1.0, 1.0, 1.0, 1.25), "R2": (1.1, 1.1, 1.1, 1.15),
                   "R3": (1.0, 1.0, 1.0, 1.1), "R4": (1.3, 1.3, 1.3, 1.6)},
        "Bored": {"R1": (1.25, 1.0, 1.15, 1.25), "R2": (1.1, 1.1, 1.1, 1.15),
                  "R3": (1.0, 1.0, 1.0, 1.1), "R4": (1.6, 1.3, 1.5, 1.6)},
        "CFA": {"R1": (1.1, 1.0, 1.1, 1.25), "R2": (1.1, 1.1, 1.1, 1.15),
                "R3": (1.0, 1.0, 1.0, 1.1), "R4": (1.45, 1.3, 1.4, 1.6)}})
    # resistance set of each combination for piles (A.3.3, 2.4.7.3.4): DA1-C2 = A2+M1+R4
    pile_sets: dict = field(default_factory=lambda: {"DA1-C1": "R1", "DA1-C2": "R4",
                                                     "DA2": "R2", "DA3": "R3"})
    # Table A.10: correlation factors for n profiles of ground tests
    xi3: dict = field(default_factory=lambda: {1: 1.40, 2: 1.35, 3: 1.33, 4: 1.31, 5: 1.29,
                                               7: 1.27, 10: 1.25})
    xi4: dict = field(default_factory=lambda: {1: 1.40, 2: 1.27, 3: 1.23, 4: 1.20, 5: 1.15,
                                               7: 1.12, 10: 1.08})
    # 7.6.2.3(8) "alternative method": minimum model factor on γ_b, γ_s (None = not set)
    pile_model_min: float | None = None
    # EN 1998-3 2.1(3)P: return periods [years] of the limit states NC, SD, DL
    ec83_return: dict = field(default_factory=lambda: {"NC": 2475, "SD": 475, "DL": 225})
    # EN 1998-3 2.2.1(7)P: brittle primary elements use the partial factors of EN 1998-1
    ec83_brittle_partial: bool = True
    # EN 1998-5 4.1.4(11): safety factor against liquefaction λ
    liq_lambda: float = 1.25
    # EN 1992-3 9.11.1(102): minimum wall thickness t1 (class 0), t2 (classes 1, 2) [mm]
    tank_tmin: tuple = (120.0, 150.0)
    # EN 1997-1 Table A.15 — UPL: (γ_G,dst, γ_G,stb, γ_Q,dst)
    upl: tuple = (1.0, 0.9, 1.5)
    # EN 1991-4 Annex B: partial factor for liquid pressure in tanks
    gamma_liquid: float = 1.2
    # EN 1996-1-1 Table NA.1 / 2.4.3: γ_M for masonry, row -> classes 1..5
    masonry_gM: dict = field(default_factory=lambda: {
        "Category I units, designed mortar": (1.5, 1.7, 2.0, 2.2, 2.5),
        "Category I units, prescribed mortar": (1.7, 2.0, 2.2, 2.5, 2.7),
        "Category II units, any mortar": (2.0, 2.2, 2.5, 2.7, 3.0)})
    masonry_fvk_max: float = 0.065  # × f_b (3.6.2(3))
    masonry_KE: float = 1000.0      # E = K_E f_k (3.7.2(2))
    masonry_lambda_c: float = 15.0  # 6.1.2.2(2)
    # EN 1995-1-1 Table 2.3 (no Cyprus annex available: EN recommended values)
    timber_gM: dict = field(default_factory=lambda: {"Solid timber": 1.3, "Glulam": 1.25})
    timber_na: bool = False
    # EN 1991-1-1:2002 — recommended values (underlined in Tables 6.2, 6.4, 6.8, 6.10, 6.12),
    # checked against the Greek translation of EN 1991-1-1:2002 (April 2002).
    # category -> (q_k [kN/m²], Q_k [kN]); the National Annex may choose other values.
    imposed: dict = field(default_factory=lambda: {
        "A_floor": (2.0, 2.0), "A_stairs": (2.0, 2.0), "A_balcony": (2.5, 2.0),
        "B": (3.0, 4.5), "C1": (3.0, 4.0), "C2": (4.0, 4.0), "C3": (5.0, 4.0),
        "C4": (5.0, 7.0), "C5": (5.0, 4.5), "D1": (4.0, 4.0), "D2": (5.0, 7.0),
        "E1": (7.5, 7.0), "F": (2.5, 20.0), "G": (5.0, 90.0), "H": (0.4, 1.0)})
    # Table 6.12 — horizontal line load on partition walls and parapets q_k [kN/m]
    parapet: dict = field(default_factory=lambda: {
        "A": 0.5, "B": 0.5, "C1": 0.5, "C2": 1.0, "C3": 1.0, "C4": 1.0, "D": 1.0,
        "C5": 3.0, "E": 2.0})
    imposed_A0: float = 10.0  # Eq. 6.1, A0 [m²]
    imposed_alphaA_min_CD: float = 0.6  # Eq. 6.1, categories C and D
    imposed_na: bool = False  # True once a National Annex to EN 1991-1-1 has been entered
    # EN 1992-1-1 7.3.1(5) Table 7.1N — w_max [mm], reinforced members, quasi-permanent
    # combination; 7.3.4(3) k3, k4 (recommended values = Table 7.1(CYS), NA 2.41, NA 2.43).
    crack_wmax: dict = field(default_factory=lambda: {
        "X0, XC1": 0.4, "XC2, XC3, XC4": 0.3, "XD1, XD2, XS1, XS2, XS3": 0.3})
    crack_k3: float = 3.4
    crack_k4: float = 0.425
    notes: tuple = ()

    def approach(self, choice: str) -> str:
        return self.default_approach if choice in ("National Annex", "", None) else choice

    def combinations(self, choice: str) -> list[str]:
        return self.approaches[self.approach(choice)]

    def gRe(self, combo: str) -> float:
        return self.gamma_Re.get(combo, 1.0)


EN = Annex("EN", "EN recommended values", "EN 1990/1992/1997/1998 recommended values")

# Cyprus — verified against the CYS National Annexes (approved 11/06/2010, Eurocodes
# Committee of ETEK, edition 01 March 2009):
#   NA to CYS EN 1997-1  NA 2.9 / NA 3.1: Design Approach 2; Tables A.1–A.4 (CYS) = EN values;
#                        A.5/A.13: γR,v 1.4, γR,h 1.1, γR,e 1.4; A.14 slopes γR,e 1.1;
#                        NA 2.5: seismic → all action/resistance factors 1.0;
#                        NA 2.28: ULS anchor load ≥ max(Pd, 1.35 Pk); A.12 γa 1.1.
#   NA to CYS EN 1998-5  NA 2.2: γφ' 1.25, γcu 1.4.
#   NA to CYS EN 1998-1  zonation map: Zone 1 0.15 g, Zone 2 0.20 g, Zone 3 0.25 g;
#                        NA 2.12 γI 0.8/1.0/1.2/1.4; Type 1 spectrum, S as EN Table 3.2.
#   NA to CYS EN 1992-1-1 NA 2.5 γc 1.5, γs 1.15; NA 2.8 αcc 1.0; NA 2.72 αcc,pl 0.8;
#                        NA 2.34(3) v_Rd,max = 0.5 ν f_cd.
#   NA to CYS EN 1990    Table A1.2(B): Eq. 6.10, γG 1.35/1.00, γQ 1.50.
#   NA to CYS EN 1992-1-1 NA 2.41 Table 7.1(CYS): w_max 0.4 (X0, XC1), 0.3 (XC2–XC4, XD, XS);
#                        NA 2.43 k3 = 3.4, k4 = 0.425; NA 2.45 k1 = 1, k2 = 5 mm (= EN).
CY = Annex(
    "CY", "Cyprus (CYS National Annexes)",
    "NA to CYS EN 1990:2002, EN 1992-1-1:2004, EN 1997-1:2004, EN 1998-1:2004, "
    "EN 1998-5:2004 (approved 11/06/2010)",
    default_approach="DA2", mandatory_approach="DA2",
    punch_vmax=0.5, anchor_sls_factor=1.35, slope_mode="DA2", slope_gRe=1.1,
    # NA to CYS EN 1997-1 NA 2.35 Tables A.6–A.8(CYS): R2 γb = γs = γt = 1.1, γs,t = 1.15;
    # NA 2.36 Tables A.9–A.11(CYS) = EN ξ values; NA 2.19: model factor ≥ 1.25.
    pile_model_min=1.25,
    # NA to CYS EN 1998-3: NA 2.2 return periods 2475/475/225 years, NA 2.3 partial factors
    # of CYS EN 1998-1 for brittle primary elements, NA 2.4 Table 3.1(CYS) CF 1.35/1.20/1.00,
    # NA 3.1 Annex A may be used.
    # NA to CYS EN 1997-1 NA 2.40 Table A.15(CYS) UPL 1.0/0.9/1.5 (= EN). NA to CYS
    # EN 1996-1-1 NA 2.1 Table 1(CYS) γ_M, NA 2.5 f_vk ≤ 0.065 f_b, NA 2.7 K_E = 1000,
    # NA 2.11 λ_c = 15 (= EN recommended). No CYS annex to EN 1995-1-1 or EN 1991-4 was
    # provided: EN recommended values are used and the report says so.
    # NA to CYS EN 1991-1-3 NA 2.5: Annex C, Mediterranean, Z = 1 everywhere → s_k =
    # 0.289 [1 + (A/452)²]; special study above 1500 m. NA to CYS EN 1991-1-4 NA 2.4:
    # v_b,0 from the isotach map (24/30/40 m/s), c_dir = c_season = 1.0, ρ = 1.25 kg/m³.
    snow_formula="0.289*(1+(A/452)**2)", snow_max_altitude=1500.0, wind_map=True,
    # NA to CYS EN 1990 Table A1.1, EN 1998-1 NA 2.7/2.9/2.12, EN 1993-1-1 NA 2.14,
    # EN 1998-3 Table 3.1 (CYS), EN 1992-3 NA 2.1 — equal to the EN recommended values.
    zones=(("Zone 1", 0.15), ("Zone 2", 0.20), ("Zone 3", 0.25)),
    notes=("Design Approach 2 is mandatory for STR/GEO (NA 2.9).",
           "Seismic zones: Zone 1 0.15 g, Zone 2 0.20 g, Zone 3 0.25 g (NA zonation map, "
           "10 % in 50 years)."),
)

# Greece — verified against the Greek National Annex to EN 1992-1-1 (ELOT, one page):
# "for the nationally determined parameters the values recommended in the notes of
# EN 1992-1-1 are adopted" → γc 1.5, γs 1.15, αcc 1.0, αcc,pl 0.8, v_Rd,max 0.4 ν f_cd
# (recommended value after EN 1992-1-1/AC:2010 — the lower, safe-side value).
# EN 1990 Table A1.1 / A1.2(B) and EN 1991-1-1 (Greek translation, Apr 2002) were checked
# against the texts; their Greek National Annexes (and those of EN 1997-1, EN 1998-1) were
# not provided: EN recommended values are used, no seismic zones are entered (a_g is a user
# input) and the report says so.
GR = replace(
    EN, code="GR", label="Greece (ELOT National Annexes)",
    reference="Greek NA to EN 1992-1-1 (recommended values adopted); EN 1990, EN 1991-1-1, "
              "EN 1997-1, EN 1998-1: EN recommended values (Greek NA not yet verified)",
    notes=("EN 1992-1-1: the Greek National Annex adopts the recommended values.",
           "EN 1990, EN 1997-1, EN 1998-1: Greek National Annex not yet verified — EN "
           "recommended values are used; enter a_g from the seismic zone of the site."),
)

ANNEXES: dict[str, Annex] = {"EN": EN, "CY": CY, "GR": GR}


def ground_snow(na: Annex, A: float) -> float | None:
    """Characteristic ground snow load s_k [kN/m²] at altitude A [m] (None = user input)."""
    if not na.snow_formula:
        return None
    return float(eval(na.snow_formula, {"__builtins__": {}}, {"A": A}))  # noqa: S307


def get_annex(code: str | None) -> Annex:
    return ANNEXES.get(code or "EN", EN)


def record_annex(calc) -> None:
    """Write the nationally determined parameters used to the report."""
    na = get_annex(calc.project.annex)
    calc.heading("National Annex parameters used")
    calc.text("{label} — {ref}", label=calc.tr(na.label), ref=na.reference)
    g = na.combos[na.default_approach if na.default_approach in na.combos else "DA2"]
    rows = [
        ["EN 1997-1 2.4.7.3.4", calc.tr("Design approach"), na.default_approach],
        ["EN 1997-1 A.3", "γ_G / γ_Q", " / ".join(f"{v:g}" for v in (g[0], g[2]))],
        ["EN 1997-1 A.2", "EQU γ_G,dst / γ_G,stb / γ_Q", " / ".join(f"{v:g}" for v in na.equ[:3])],
        ["EN 1997-1 A.5, A.13", "γ_R,v / γ_R,h (DA2)",
         " / ".join(f"{v:g}" for v in na.combos["DA2"][5:7])],
        ["EN 1997-1 A.13", "γ_R,e (DA2)", f"{na.gRe('DA2'):g}"],
        ["EN 1997-1 A.14", calc.tr("Slopes"),
         f"γ_R,e = {na.slope_gRe:g}" if na.slope_mode == "DA2" else
         f"γ_φ' = {na.slope_factors[0]:g}, γ_c' = {na.slope_factors[1]:g}"],
        ["EN 1998-5 3.1(3)", "γ_φ' / γ_c' (" + calc.tr("seismic") + ")",
         f"{na.seismic_gamma_phi:g} / {na.seismic_gamma_c:g}"],
        ["EN 1992-1-1 2.4.2.4", "γ_c / γ_s", f"{na.gamma_c:g} / {na.gamma_s:g}"],
        ["EN 1992-1-1 3.1.6, 12.3.1", "α_cc / α_cc,pl", f"{na.alpha_cc:g} / {na.alpha_cc_pl:g}"],
        ["EN 1992-1-1 6.4.5(3)", "v_Rd,max", f"{na.punch_vmax:g} ν f_cd"],
    ]
    if na.anchor_sls_factor:
        rows.append(["EN 1997-1 8.6(4)", calc.tr("Anchor design load"),
                     f"max(P_d, {na.anchor_sls_factor:g} P_k)"])
    if na.zones:
        rows.append(["EN 1998-1 3.2.1", "a_gR",
                     ", ".join(f"{calc.tr(z)} {a:g} g" for z, a in na.zones)])
    site = site_zone_row(calc, na)
    if site:
        rows.append(site)
    calc.table(["Clause", "Parameter", "Value"], rows, caption=na.label)
    if na.code == "GR":
        for n in na.notes:
            calc.note(n)


def site_zone_row(calc, na: Annex):
    """Seismic zone of the project site from the annex zonation map (if any)."""
    from . import sitezones

    p = calc.project
    try:
        lat, lon = float(p.lat), float(p.lon)
    except (TypeError, ValueError):
        return None
    if not sitezones.has_map(na.code):
        return None
    z = sitezones.zone_at(na.code, lat, lon)
    if not z["zone"]:
        return ["EN 1998-1 3.2.1", calc.tr("Site"), calc.tr("outside the zonation map")]
    txt = calc.tr("{site} ({lat:.4f}° N, {lon:.4f}° E): Zone {z}, a_gR = {ag:g} g",
                  site=p.site or "—", lat=lat, lon=lon, z=z["zone"], ag=z["ag"])
    if z["near_boundary"]:
        txt += " — " + calc.tr("near a zone boundary, the higher zone is used")
    return ["EN 1998-1 3.2.1", calc.tr("Site"), txt]


def check_approach(calc, na: Annex, choice: str) -> None:
    """Warn when the user overrides the approach required by the annex."""
    if na.mandatory_approach and na.approach(choice) != na.mandatory_approach:
        calc.warn("The {annex} requires {da}; the selected {sel} is not in accordance with it.",
                  annex=calc.tr(na.label), da=na.mandatory_approach, sel=na.approach(choice))


__all__ = ["Annex", "ANNEXES", "APPROACH_CHOICES", "CY", "EN", "GR", "check_approach", "get_annex",
           "replace"]
