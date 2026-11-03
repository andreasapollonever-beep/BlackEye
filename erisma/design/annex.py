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
    # EN 1998-1 — help text for the seismic input
    zones_help: str = ""

    def approach(self, choice: str) -> str:
        return self.default_approach if choice in ("National Annex", "", None) else choice

    def combinations(self, choice: str) -> list[str]:
        return self.approaches[self.approach(choice)]

    def gRe(self, combo: str) -> float:
        return self.gamma_Re.get(combo, 1.0)


EN = Annex("EN", "EN recommended values", "EN 1990/1992/1997/1998 recommended values")

ANNEXES: dict[str, Annex] = {"EN": EN}


def get_annex(code: str | None) -> Annex:
    return ANNEXES.get(code or "EN", EN)


__all__ = ["Annex", "ANNEXES", "APPROACH_CHOICES", "EN", "get_annex", "replace"]
