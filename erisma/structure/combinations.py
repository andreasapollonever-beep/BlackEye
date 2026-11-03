"""EN 1990 combinations of actions for the building (Annex A1, buildings).

Load cases carry a type — ``G`` permanent, ``Q`` imposed (with its use category for ψ) or
``S`` snow — and the combinations are generated with the partial factors and ψ factors of the
National Annex:

* ULS persistent/transient, Eq. 6.10: Σγ_G G + γ_Q Q_k,1 + Σγ_Q ψ_0,i Q_k,i, every variable
  action in turn as the leading one;
* SLS characteristic (6.14b), frequent (6.15b) and quasi-permanent (6.16b);
* seismic (6.12b): ΣG + Σψ_2,i Q_k,i — the gravity part of the seismic combination and,
  with φ, the mass (EN 1998-1 3.2.4).

User-defined combinations (name + factor per case) are added to the ULS set.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Case:
    name: str
    type: str                      # "G" | "Q" | "S"
    psi: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class Combination:
    name: str
    kind: str                      # "ULS" | "SLS-char" | "SLS-freq" | "SLS-qp" | "seismic" | "user"
    factors: dict[str, float]

    def text(self) -> str:
        return " + ".join(f"{f:g}·{c}" for c, f in self.factors.items() if f)


def generate(cases: list[Case], gG: float, gQ: float,
             custom: list[dict] | None = None) -> list[Combination]:
    G = [c for c in cases if c.type == "G"]
    V = [c for c in cases if c.type != "G"]
    out: list[Combination] = []
    base = {c.name: gG for c in G}
    if not V:
        out.append(Combination("ULS 1", "ULS", dict(base)))
    for n, lead in enumerate(V, 1):
        f = dict(base)
        for c in V:
            f[c.name] = gQ if c is lead else gQ * c.psi[0]
        out.append(Combination(f"ULS {n}", "ULS", f))
    sls = {c.name: 1.0 for c in G}
    for n, lead in enumerate(V or [None], 1):
        out.append(Combination(f"SLS-char {n}", "SLS-char",
                               {**sls, **{c.name: (1.0 if c is lead else c.psi[0]) for c in V}}))
        out.append(Combination(f"SLS-freq {n}", "SLS-freq",
                               {**sls, **{c.name: (c.psi[1] if c is lead else c.psi[2]) for c in V}}))
    qp = {**sls, **{c.name: c.psi[2] for c in V}}
    out.append(Combination("SLS-qp", "SLS-qp", qp))
    out.append(Combination("Seismic G+ψ2Q", "seismic", dict(qp)))
    for k, cu in enumerate(custom or [], 1):
        f = {c: float(v) for c, v in (cu.get("factors") or {}).items()
             if c in {x.name for x in cases} and v}
        if f:
            out.append(Combination(cu.get("name") or f"User {k}", "user", f))
    return out
