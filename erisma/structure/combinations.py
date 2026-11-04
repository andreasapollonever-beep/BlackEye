"""EN 1990 combinations of actions for the building (Annex A1, buildings).

Load cases carry a type — ``G`` permanent, ``Q`` imposed (with its use category for ψ),
``S`` snow or ``W`` wind — and the combinations are generated with the partial factors and ψ factors of the
National Annex:

* ULS persistent/transient, Eq. 6.10: Σγ_G G + γ_Q Q_k,1 + Σγ_Q ψ_0,i Q_k,i, every variable
  action in turn as the leading one;
* SLS characteristic (6.14b), frequent (6.15b) and quasi-permanent (6.16b);
* seismic (6.12b): ΣG + Σψ_2,i Q_k,i — the gravity part of the seismic combination and,
  with φ, the mass (EN 1998-1 3.2.4).

Wind cases (one per axis) are mutually exclusive and act in both senses: every
combination is generated without wind and with each of ±W_X, ±W_Y (factor −γ for the
negative sense; the analysis is linear).

User-defined combinations (name + factor per case) are added to the ULS set.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Case:
    name: str
    type: str                      # "G" | "Q" | "S" | "W"
    psi: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class Combination:
    name: str
    kind: str                      # "ULS" | "SLS-char" | "SLS-freq" | "SLS-qp" | "seismic" | "user"
    factors: dict[str, float]

    def text(self) -> str:
        s = ""
        for c, f in self.factors.items():
            if f:
                s += (" − " if f < 0 else " + ") + f"{abs(f):g}·{c}"
        return s[3:] if s.startswith(" + ") else s.strip()


def generate(cases: list[Case], gG: float, gQ: float,
             custom: list[dict] | None = None) -> list[Combination]:
    G = [c for c in cases if c.type == "G"]
    W = [c for c in cases if c.type == "W"]
    V0 = [c for c in cases if c.type not in ("G", "W")]
    # alternatives: no wind, or one wind case in one sense
    alts = [(None, 1.0)] + [(w, s) for w in W for s in (1.0, -1.0)]
    out: list[Combination] = []
    base = {c.name: gG for c in G}
    sls = {c.name: 1.0 for c in G}
    n_uls = n_sls = 0
    for wc, sign in alts:
        V = V0 + ([wc] if wc else [])
        sg = {c.name: (sign if c is wc else 1.0) for c in V}
        if not V:
            n_uls += 1
            out.append(Combination(f"ULS {n_uls}", "ULS", dict(base)))
        for lead in V:
            f = dict(base)
            for c in V:
                f[c.name] = round(sg[c.name] * (gQ if c is lead else gQ * c.psi[0]), 6)
            n_uls += 1
            out.append(Combination(f"ULS {n_uls}", "ULS", f))
        for lead in V or [None]:
            n_sls += 1
            out.append(Combination(f"SLS-char {n_sls}", "SLS-char",
                                   {**sls, **{c.name: sg[c.name] * (1.0 if c is lead else c.psi[0])
                                              for c in V}}))
            out.append(Combination(f"SLS-freq {n_sls}", "SLS-freq",
                                   {**sls, **{c.name: sg[c.name] * (c.psi[1] if c is lead else
                                                                    c.psi[2]) for c in V}}))
    V = V0
    qp = {**sls, **{c.name: c.psi[2] for c in V}}
    out.append(Combination("SLS-qp", "SLS-qp", qp))
    out.append(Combination("Seismic G+ψ2Q", "seismic", dict(qp)))
    seen, uniq = set(), []                 # drop duplicates (e.g. wind with ψ2 = 0)
    for c in out:
        key = (c.kind, tuple(sorted((n, f) for n, f in c.factors.items() if f)))
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    out = sorted(uniq, key=lambda c: ("ULS", "SLS-char", "SLS-freq", "SLS-qp",
                                      "seismic").index(c.kind))
    for k, cu in enumerate(custom or [], 1):
        f = {c: float(v) for c, v in (cu.get("factors") or {}).items()
             if c in {x.name for x in cases} and v}
        if f:
            out.append(Combination(cu.get("name") or f"User {k}", "user", f))
    return out
