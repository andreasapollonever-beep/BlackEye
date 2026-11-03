"""From analysis to reinforcement: design every RC beam and column of a building.

Each member is designed by the *same* EC2/EC8 modules the engineer uses one
at a time (``ec2_rc_beam``, ``ec2_rc_column``), so every result can be opened
and audited step by step.  Reinforcement is chosen automatically: the
lightest bar arrangement (then the widest link spacing) that passes every
check under every design combination.

Design combinations (EN 1990):

* ULS persistent (6.10): γ_G·G + γ_Q·Q, factors from the National Annex
  (Table A1.2(B), the ``A1`` set);
* seismic (6.12b): G + ψ_2·Q ± E, with E the EN 1998-1 envelope
  (both components, accidental torsion, θ amplification).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..core import InputError, get_module
from .seismic import SeismicResult
from .solver import StaticResult

COL_BARS = ["14", "16", "18", "20", "22", "25", "28"]
BEAM_BARS = ["12", "14", "16", "20", "25"]
LINK_S = [250.0, 200.0, 150.0, 125.0, 100.0, 75.0]


@dataclass
class MemberDesign:
    """Result for one member; ``rho`` = longitudinal steel ratio A_s / A_c."""

    member: str
    kind: str                       # "column" | "beam"
    storey: int
    reinforcement: str
    utilisation: float
    ok: bool
    governing: str                  # combination name
    inputs: dict                    # module inputs of the governing combination
    module: str
    notes: list[str] = field(default_factory=list)
    rho: float = 0.0


def _passes(module, inp: dict, project: dict | None) -> tuple[bool, float]:
    """(all checks pass, strength utilisation).

    The utilisation reported excludes minimum-detailing checks (ρ_min, …): with
    automatic bar selection those are always ≈ 1 and would hide how hard the
    member actually works.
    """
    try:
        c = module.calculate(inp, project)
    except InputError:
        return False, float("inf")
    util = max((k.utilisation for k in c.checks if not k.is_min), default=0.0)
    return c.passed, util


def _search(module, candidates: list[dict], combos: list[tuple[str, dict]],
            project: dict | None) -> tuple[int, float, str]:
    """Lightest candidate passing all combinations.

    A linear scan in order of steel area: pass/fail is not monotonic (too many
    bars stop fitting in the width, ρ_max), so bisection would be wrong.
    Returns (index or −1, utilisation, governing combination); for −1 the
    values of the candidate with the lowest utilisation.
    """
    best_fail = (float("inf"), "")
    for idx, cand in enumerate(candidates):
        ok, util, gov = True, 0.0, ""
        for name, inp in combos:
            p, u = _passes(module, {**inp, **cand}, project)
            if u > util:
                util, gov = u, name
            if not p:
                ok = False
                break
        if ok:
            return idx, util, gov
        if util < best_fail[0]:
            best_fail = (util, gov)
    return -1, best_fail[0], best_fail[1]


def _col_candidates() -> list[dict]:
    out = []
    for d in COL_BARS:
        for n in (2, 3, 4, 5):
            area = (4 * n - 4) * float(d) ** 2
            s = min(100.0, 5 * int(8 * float(d) / 5))
            out.append((area, {"dia": d, "nb": n, "nh": n, "link": "8", "s": s}))
    return [c for _, c in sorted(out, key=lambda t: t[0])]


def _beam_candidates() -> list[dict]:
    out = [(n * float(d) ** 2, {"n_bars": n, "dia": d}) for d in BEAM_BARS for n in (2, 3, 4, 5)]
    return [c for _, c in sorted(out, key=lambda t: t[0])]


def design_columns(res: dict[str, StaticResult], seis: SeismicResult | None, uls: StaticResult,
                   quasi: StaticResult, b: float, h: float, beam_h: float, concrete: str,
                   storeys: dict[str, tuple[int, float]], project: dict | None = None,
                   fyk: float = 500.0, cover: float = 30.0) -> list[MemberDesign]:
    """``storeys`` maps column id → (storey index, storey height mm)."""
    module = get_module("ec2_rc_column")
    cands = _col_candidates()
    out = []
    for mid, (k, hs) in storeys.items():
        base = {"b": b, "h": h, "cover": cover, "concrete": concrete, "fyk": fyk,
                "L": (hs - beam_h) / 1000, "k_h": 1.0, "k_b": 1.0, "braced": False,
                "seismic": seis is not None, "phi_ef": 0.8}
        combos, notes = [], []
        f = uls.forces(mid, 2)
        combos.append(("1.35G+1.5Q", {**base, **_col_actions(f, None, 1.0)}))
        if seis is not None:
            env = seis.member_envelope(mid)
            fq = quasi.forces(mid, 2)
            for sgn, nm in ((+1, "G+ψ2Q+E (N max)"), (-1, "G+ψ2Q−E (N min)")):
                act = _col_actions(fq, env, sgn)
                if act["NEd"] <= 1.0:
                    notes.append("Column in tension under the seismic combination — "
                                 "check it as a tie")
                    act["NEd"] = 1.0
                combos.append((nm, {**base, **act}))
        idx, util, gov = _search(module, cands, combos, project)
        if idx < 0:
            pick = cands[-1]
            notes.append("No bar arrangement passes — increase the column size")
        else:
            pick = cands[idx]
        n_bars = 4 * pick["nb"] - 4
        reinf = f"{n_bars}Ø{pick['dia']}, Ø8/{pick['s']:g}"
        gov_inp = {**(dict(combos)[gov] if gov else combos[0][1]), **pick}
        rho = n_bars * np.pi * float(pick["dia"]) ** 2 / 4 / (b * h)
        out.append(MemberDesign(mid, "column", k, reinf, util, idx >= 0, gov, gov_inp,
                                "ec2_rc_column", notes, rho))
    return out


def _col_actions(f: dict, env: np.ndarray | None, sgn: int) -> dict:
    """Module inputs (kN, kNm) from diagrams of a column (local y = X ⇒ 'h' = My)."""
    N = -f["N"][0]                  # compression positive
    Mh_b, Mh_t = f["My"][0], f["My"][-1]
    Mb_b, Mb_t = f["Mz"][0], f["Mz"][-1]
    V = max(abs(f["Vy"]).max(), abs(f["Vz"]).max())
    if env is not None:
        def plus(m, e):
            return float(np.sign(m) or 1.0) * (abs(m) + e)
        N += sgn * env[0]
        Mh_b, Mh_t = plus(Mh_b, env[4]), plus(Mh_t, env[10])
        Mb_b, Mb_t = plus(Mb_b, env[5]), plus(Mb_t, env[11])
        V += max(env[1], env[2], env[7], env[8])
    return {"NEd": N / 1e3, "Mh_top": Mh_t / 1e6, "Mh_bot": Mh_b / 1e6, "Mb_top": Mb_t / 1e6,
            "Mb_bot": Mb_b / 1e6, "VEd": V / 1e3}


def design_beams(beams: dict[str, int], seis: SeismicResult | None, uls: StaticResult,
                 quasi: StaticResult, b: float, h: float, concrete: str,
                 project: dict | None = None, fyk: float = 500.0,
                 cover: float = 30.0) -> list[MemberDesign]:
    """Bottom (sagging) and top (hogging) bars and links for each beam; ``beams``: id → storey."""
    module = get_module("ec2_rc_beam")
    cands = _beam_candidates()
    out = []
    for mid, k in beams.items():
        fu = uls.forces(mid, 41)
        sag = [("1.35G+1.5Q", max(fu["My"].max(), 0.0))]
        hog = [("1.35G+1.5Q", max(-fu["My"].min(), 0.0))]
        V = [("1.35G+1.5Q", np.abs(fu["Vz"]).max())]
        if seis is not None:
            env = seis.member_envelope(mid)
            fq = quasi.forces(mid, 41)
            for end, e in ((0, env[4]), (-1, env[10])):
                m = fq["My"][end]
                sag.append(("G+ψ2Q±E", max(m + e, 0.0)))
                hog.append(("G+ψ2Q±E", max(-(m - e), 0.0)))
            sag.append(("G+ψ2Q±E", max(fq["My"].max(), 0.0)))
            V.append(("G+ψ2Q±E", np.abs(fq["Vz"]).max() + max(env[2], env[8])))
        Vmax = max(v for _, v in V)
        base = {"b": b, "h": h, "cnom": cover, "concrete": concrete, "fyk": fyk,
                "link_dia": "8", "link_legs": 2, "link_s": LINK_S[-1], "VEd": Vmax / 1e3}
        notes = []
        picks, utils, ok, gov_all = {}, [], True, ""
        for face, demands in (("bottom", sag), ("top", hog)):
            Mmax = max(demands, key=lambda t: t[1])
            inp = {**base, "MEd": max(Mmax[1], 1e6) / 1e6, "n_comp": 2, "dia_comp": "12"}
            idx, util, _ = _search(module, cands, [(Mmax[0], inp)], project)
            if idx < 0:
                ok = False
                notes.append(f"No {face} bar arrangement passes — increase the beam size")
                idx = len(cands) - 1
            picks[face] = cands[idx]
            utils.append(util)
            if util >= max(utils):
                gov_all = f"{Mmax[0]} ({face})"
        if seis is not None:
            # EN 1998-1 5.4.3.1.2: ρ_min = 0.5 f_ctm/f_yk on both faces (4a) and, in the
            # critical regions, compression steel ≥ half the tension steel (4)
            fck = float(concrete.split("/")[0][1:])
            d_eff = h - cover - 8 - 10
            As_min = 0.5 * 0.30 * fck ** (2 / 3) / fyk * b * d_eff
            area = lambda c: c["n_bars"] * np.pi * float(c["dia"]) ** 2 / 4  # noqa: E731
            for face, other in (("top", "bottom"), ("bottom", "top")):
                need = max(As_min, 0.5 * area(picks[other]))
                if area(picks[face]) < need:
                    picks[face] = next((c for c in cands if area(c) >= need), cands[-1])
                    notes.append(f"{face.capitalize()} bars increased for EN 1998-1 "
                                 "5.4.3.1.2 (ρ_min, ρ' ≥ 0.5ρ)")
        # widest link spacing passing with the chosen bottom bars
        inp_v = {**base, "MEd": max(max(v for _, v in sag), 1e6) / 1e6, **picks["bottom"],
                 "n_comp": picks["top"]["n_bars"], "dia_comp": picks["top"]["dia"]}
        s_ok = None
        for s in LINK_S:
            p, u = _passes(module, {**inp_v, "link_s": s}, project)
            if p:
                s_ok, uv = s, u
                break
        if s_ok is None:
            ok = False
            s_ok, uv = LINK_S[-1], _passes(module, {**inp_v, "link_s": LINK_S[-1]}, project)[1]
            notes.append("Shear cannot be resisted with Ø8 links — increase the beam width/depth")
        reinf = (f"bottom {picks['bottom']['n_bars']}Ø{picks['bottom']['dia']}, "
                 f"top {picks['top']['n_bars']}Ø{picks['top']['dia']}, Ø8/{s_ok:g}")
        if seis is not None:
            # EN 1998-1 5.4.3.1.2(6): critical regions (length h_w at each end)
            dbl = min(float(picks["bottom"]["dia"]), float(picks["top"]["dia"]))
            s_cr = min(h / 4, 24 * 8, 225.0, 8 * dbl, s_ok)
            s_cr = 5 * int(s_cr // 5)
            reinf += f" (ends Ø8/{s_cr:g} over {h:g} mm)"
        As = sum(p["n_bars"] * np.pi * float(p["dia"]) ** 2 / 4 for p in picks.values())
        out.append(MemberDesign(mid, "beam", k, reinf, max(utils + [uv]), ok, gov_all,
                                {**inp_v, "link_s": s_ok}, "ec2_rc_beam", notes, As / (b * h)))
    return out
