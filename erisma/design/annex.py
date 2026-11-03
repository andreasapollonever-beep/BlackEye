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
CY = Annex(
    "CY", "Cyprus (CYS National Annexes)",
    "NA to CYS EN 1990:2002, EN 1992-1-1:2004, EN 1997-1:2004, EN 1998-1:2004, "
    "EN 1998-5:2004 (approved 11/06/2010)",
    default_approach="DA2", mandatory_approach="DA2",
    punch_vmax=0.5, anchor_sls_factor=1.35, slope_mode="DA2", slope_gRe=1.1,
    zones=(("Zone 1", 0.15), ("Zone 2", 0.20), ("Zone 3", 0.25)),
    notes=("Design Approach 2 is mandatory for STR/GEO (NA 2.9).",
           "Seismic zones: Zone 1 0.15 g, Zone 2 0.20 g, Zone 3 0.25 g (NA zonation map, "
           "10 % in 50 years)."),
)

ANNEXES: dict[str, Annex] = {"EN": EN, "CY": CY}


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
    calc.table(["Clause", "Parameter", "Value"], rows, caption=na.label)


def check_approach(calc, na: Annex, choice: str) -> None:
    """Warn when the user overrides the approach required by the annex."""
    if na.mandatory_approach and na.approach(choice) != na.mandatory_approach:
        calc.warn("The {annex} requires {da}; the selected {sel} is not in accordance with it.",
                  annex=calc.tr(na.label), da=na.mandatory_approach, sel=na.approach(choice))


__all__ = ["Annex", "ANNEXES", "APPROACH_CHOICES", "CY", "EN", "check_approach", "get_annex",
           "replace"]
