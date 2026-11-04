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
from .model import Msg
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
    # data for the design-results window (sketches, design forces, re-checks): e.g. the
    # design combinations of a column, or the sagging/hogging moments and links of a beam
    detail: dict = field(default_factory=dict)


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


def ulist(uls) -> list[tuple[str, StaticResult]]:
    """ULS combinations as [(name, result)]; a single result is accepted for convenience."""
    if isinstance(uls, (list, tuple)):
        return list(uls)
    return [("1.35G+1.5Q", uls)]


def _col_candidates() -> list[dict]:
    out = []
    for d in COL_BARS:
        for n in (2, 3, 4, 5):
            area = (4 * n - 4) * float(d) ** 2
            s = min(100.0, 5 * int(8 * float(d) / 5))
            out.append((area, {"dia": d, "nb": n, "nh": n, "link": "8", "s": s}))
    return [c for _, c in sorted(out, key=lambda t: t[0])]


def _beam_candidates() -> list[dict]:
    out = [(n * float(d) ** 2, {"n_bars": n, "dia": d}) for d in BEAM_BARS + ["32"]
           for n in (2, 3, 4, 5, 6, 7, 8)]
    return [c for _, c in sorted(out, key=lambda t: t[0])]


def design_columns(res: dict[str, StaticResult], seis: SeismicResult | None, uls: StaticResult,
                   quasi: StaticResult, b: float, h: float, beam_h: float, concrete: str,
                   storeys: dict[str, tuple[int, float]], project: dict | None = None,
                   fyk: float = 500.0, cover: float = 30.0,
                   sizes: dict[str, tuple[float, float]] | None = None) -> list[MemberDesign]:
    """``storeys`` maps column id → (storey index, storey height mm); ``sizes`` overrides
    (b, h) per column."""
    module = get_module("ec2_rc_column")
    cands = _col_candidates()
    out = []
    b0, h0 = b, h
    for mid, (k, hs) in storeys.items():
        b, h = (sizes or {}).get(mid, (b0, h0))
        base = {"b": b, "h": h, "cover": cover, "concrete": concrete, "fyk": fyk,
                "L": (hs - beam_h) / 1000, "k_h": 1.0, "k_b": 1.0, "braced": False,
                "seismic": seis is not None, "phi_ef": 0.8}
        combos, notes = [], []
        for nm, r_ in ulist(uls):
            combos.append((nm, {**base, **_col_actions(r_.forces(mid, 2), None, 1.0)}))
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
                                "ec2_rc_column", notes, rho,
                                {"combos": [(nm, {kk: (float(v) if isinstance(v, np.floating)
                                                       else v) for kk, v in c.items()})
                                            for nm, c in combos]}))
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
                 cover: float = 30.0,
                 sizes: dict[str, tuple[float, float]] | None = None, e_factor: float = 1.0,
                 dissipative: bool = True, sls: bool = True) -> list[MemberDesign]:
    """Bottom (sagging) and top (hogging) bars and links for each beam; ``beams``: id → storey;
    ``sizes`` overrides (b, h) per beam.

    Foundation beams: ``e_factor`` = γ_Rd·Ω on the seismic action (EN 1998-1 4.4.2.6),
    ``dissipative=False`` (no EN 1998-1 5.4.3.1.2 detailing, they stay elastic) and
    ``sls=False`` (no span/depth check: their deflection is the soil settlement)."""
    module = get_module("ec2_rc_beam")
    cands = _beam_candidates()
    out = []
    b0, h0 = b, h
    for mid, k in beams.items():
        b, h = (sizes or {}).get(mid, (b0, h0))
        an_ = ulist(uls)[0][1].analysis
        e = an_.elements[an_.member_index[mid]]
        a1, a2 = e.oi, e.L - e.oj   # faces of the supports (rigid zones of walls)

        def flex(f):  # keep the flexible part: design moments at the faces (EC2 5.3.2.2(3))
            keep = (f["x"] >= a1 - 1e-6) & (f["x"] <= a2 + 1e-6)
            return {k: v[keep] for k, v in f.items()}

        sag, hog, V = [], [], []
        for nm, r_ in ulist(uls):
            fu = flex(r_.forces(mid, 41))
            sag.append((nm, max(fu["My"].max(), 0.0)))
            hog.append((nm, max(-fu["My"].min(), 0.0)))
            V.append((nm, np.abs(fu["Vz"]).max()))
        if seis is not None:
            env = seis.member_envelope(mid) * e_factor
            fq = flex(quasi.forces(mid, 41))
            L = e.L
            for end, x in ((0, a1), (-1, a2)):
                # |M_E| between the ends ≤ linear interpolation of the end values
                ee = env[4] * (1 - x / L) + env[10] * x / L
                m = fq["My"][end]
                sag.append(("G+ψ2Q±E", max(m + ee, 0.0)))
                hog.append(("G+ψ2Q±E", max(-(m - ee), 0.0)))
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
        if seis is not None and dissipative:
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
        for ld in ("8", "10", "12"):           # thicker links only when Ø8 is not enough
            for s in LINK_S:
                p, u = _passes(module, {**inp_v, "link_dia": ld, "link_s": s}, project)
                if p:
                    s_ok, uv = s, u
                    inp_v["link_dia"] = ld
                    break
            if s_ok is not None:
                break
        if s_ok is None:
            ok = False
            s_ok, uv = LINK_S[-1], _passes(module, {**inp_v, "link_s": LINK_S[-1]}, project)[1]
            notes.append("Shear cannot be resisted with Ø8 links — increase the beam width/depth")
        # ---- SLS deflection: span/depth ratio, EN 1992-1-1 7.4.2
        fck = float(concrete.split("/")[0][1:])
        K = _continuity_K(an_, mid)
        area = lambda c: c["n_bars"] * np.pi * float(c["dia"]) ** 2 / 4  # noqa: E731
        d_b = h - cover - 8 - float(picks["bottom"]["dia"]) / 2
        Lspan = e.Lf
        Msag = max(v for _, v in sag)
        As_req = Msag / (0.9 * d_b * fyk / 1.15) if Msag > 0 else 0.0
        while sls:
            ratio, lim = span_depth(Lspan, d_b, b, area(picks["bottom"]), area(picks["top"]),
                                    As_req, fck, K)
            if ratio <= lim:
                break
            nxt = next((c for c in cands if area(c) > area(picks["bottom"])), None)
            if nxt is None or area(picks["bottom"]) >= 1.5 * max(As_req, 1.0):
                break                      # extra steel no longer helps (factor capped at 1.5)
            picks["bottom"] = nxt
            notes.append("Bottom bars increased for deflection (EN 1992-1-1 7.4.2(2))")
        u_defl = ratio / lim if sls else 0.0
        if u_defl > 1.0:
            ok = False
            notes.append(Msg("Deflection: l/d = {r:.1f} > {l:.1f} (EN 1992-1-1 7.4.2) — "
                             "increase the beam depth", r=ratio, l=lim))
        utils.append(u_defl)
        inp_v.update({**picks["bottom"]})
        reinf = (f"bottom {picks['bottom']['n_bars']}Ø{picks['bottom']['dia']}, "
                 f"top {picks['top']['n_bars']}Ø{picks['top']['dia']}, "
                 f"Ø{inp_v['link_dia']}/{s_ok:g}")
        if seis is not None and dissipative:
            # EN 1998-1 5.4.3.1.2(6): critical regions (length h_w at each end)
            dbl = min(float(picks["bottom"]["dia"]), float(picks["top"]["dia"]))
            s_cr = min(h / 4, 24 * 8, 225.0, 8 * dbl, s_ok)
            s_cr = 5 * int(s_cr // 5)
            reinf += f" (ends Ø8/{s_cr:g} over {h:g} mm)"
        As = sum(p["n_bars"] * np.pi * float(p["dia"]) ** 2 / 4 for p in picks.values())
        ms, mh = max(sag, key=lambda t: t[1]), max(hog, key=lambda t: t[1])
        detail = {"M_sag": float(ms[1]) / 1e6, "gov_sag": ms[0], "M_hog": float(mh[1]) / 1e6,
                  "gov_hog": mh[0], "V": float(Vmax) / 1e3,
                  "gov_V": max(V, key=lambda t: t[1])[0], "L": float(Lspan),
                  "bottom": dict(picks["bottom"]), "top": dict(picks["top"]),
                  "link_dia": inp_v["link_dia"], "s": float(s_ok),
                  "K": float(K), "sls": sls}
        if seis is not None and dissipative:
            detail.update({"s_cr": float(s_cr), "l_cr": float(h)})
        out.append(MemberDesign(mid, "beam", k, reinf, max(utils + [uv]), ok, gov_all,
                                {**inp_v, "link_s": s_ok}, "ec2_rc_beam",
                                list(dict.fromkeys(notes)), As / (b * h), detail))
    return out


def span_depth(L: float, d: float, b: float, As: float, As2: float, As_req: float,
               fck: float, K: float) -> tuple[float, float]:
    """EN 1992-1-1 7.4.2 — (l/d, limiting l/d).

    Eq. 7.16a/b with ρ = A_s/(b d), ρ' = A_s2/(b d); × A_s,prov/A_s,req ≤ 1.5 (7.4.2(2),
    Eq. 7.17); × 0.8 for flanged beams (b_eff/b_w > 3, the slab acts as flange); × 7/l_eff
    for spans over 7 m.
    """
    r0 = np.sqrt(fck) * 1e-3
    rho = max(As / (b * d), 1e-6)
    rp = As2 / (b * d)
    if rho <= r0:
        lim = 11 + 1.5 * np.sqrt(fck) * r0 / rho + 3.2 * np.sqrt(fck) * (r0 / rho - 1) ** 1.5
    else:
        lim = 11 + 1.5 * np.sqrt(fck) * r0 / max(rho - rp, 1e-6) + \
            np.sqrt(fck) / 12 * np.sqrt(rp / r0)
    lim *= K * 0.8
    if As_req > 0:
        lim *= min(As / As_req, 1.5)
    if L > 7000:
        lim *= 7000 / L
    return L / d, float(lim)


def _continuity_K(analysis, mid: str) -> float:
    """EN 1992-1-1 Table 7.4N: K = 1.0 simply supported, 1.3 end span, 1.5 interior span
    (continuity = a collinear beam framing into the same node)."""
    model = analysis.model
    m = model.members[mid]
    d0 = model.nodes[m.j].xyz - model.nodes[m.i].xyz
    d0 = d0 / np.linalg.norm(d0)
    cont = 0
    for end in (m.i, m.j):
        for o in model.members.values():
            if o.id == mid or end not in (o.i, o.j) or not o.id.startswith("B"):
                continue
            d1 = model.nodes[o.j].xyz - model.nodes[o.i].xyz
            if abs(abs(np.dot(d0, d1 / np.linalg.norm(d1))) - 1) < 1e-6:
                cont += 1
                break
    return {0: 1.0, 1: 1.3, 2: 1.5}[cont]


# --------------------------------------------------------------------- walls

WALL_BARS = ["14", "16", "18", "20", "22", "25"]
# web and boundary hoops of the walls (defaults of the EN 1998-1 wall module)
WALL_WEB = {"dh": "10", "sh": 85.0, "dv": "10", "sv": 200.0, "dhw": "12", "shw": 150.0}


def wall_reinf(p: dict, lc: float) -> str:
    return (f"2×{p['nbe']}Ø{p['dbe']} boundary (l_c = {lc:g} mm), "
            f"web Ø{p['dv']}/{float(p['sv']):g} + Ø{p['dhw']}/{float(p['shw']):g}, "
            f"hoops Ø{p['dh']}/{float(p['sh']):g}")


def design_walls(walls: dict[str, dict], seis: SeismicResult | None, uls: StaticResult,
                 quasi: StaticResult, concrete: str, heights: list[float], beam_h: float,
                 project=None, fyk: float = 500.0, cover: float = 30.0) -> list[MemberDesign]:
    """Critical region (base) of each wall with the EN 1998-1 ductile-wall module.

    ``walls`` maps the base wall member id → {"dir", "L", "t"} (mm).  Strong-axis
    bending: a wall along X bends in the local x–y plane (M_z), along Y in x–z (M_y).
    """
    module = get_module("ec8_rc_wall")
    out = []
    for mid, w in walls.items():
        strong = "Mz" if w["dir"] == "X" else "My"
        ie, je = (5, 11) if strong == "Mz" else (4, 10)
        iv = (1, 7) if strong == "Mz" else (2, 8)
        lw, bw = w["L"], w["t"]
        lc = 50 * np.ceil(max(0.15 * lw, 1.5 * bw) / 50)
        base = {"lw": lw / 1000, "bw": bw, "hs": (heights[0] - beam_h) / 1000,
                "Hw": sum(heights) / 1000, "storeys": len(heights), "concrete": concrete,
                "fyk": fyk, "cover": cover, "lc": lc}
        combos = []
        for nm, r_ in ulist(uls):
            fu = r_.forces(mid, 2)
            combos.append((nm, {**base, "NEd": max(-fu["N"][0], 1e3) / 1e3,
                                "MEd": abs(fu[strong][0]) / 1e6,
                                "VEd": np.abs(fu["Vy" if strong == "Mz" else "Vz"]).max() / 1e3}))
        if seis is not None:
            env = seis.member_envelope(mid)
            fq = quasi.forces(mid, 2)
            N = -fq["N"][0]
            M = abs(fq[strong][0]) + env[ie]
            V = np.abs(fq["Vy" if strong == "Mz" else "Vz"]).max() + max(env[iv[0]], env[iv[1]])
            for sgn, nm in ((-1, "G+ψ2Q−E (N min)"), (+1, "G+ψ2Q+E (N max)")):
                combos.append((nm, {**base, "NEd": max(N + sgn * env[0], 1e3) / 1e3,
                                    "MEd": M / 1e6, "VEd": V / 1e3}))
        cands = [{"nbe": n, "dbe": d} for d in WALL_BARS for n in (4, 6, 8, 10, 12, 14, 16)]
        cands.sort(key=lambda c: c["nbe"] * float(c["dbe"]) ** 2)
        idx, util, gov = _search(module, cands, combos, project)
        notes = []
        if idx < 0:
            notes.append("No boundary reinforcement passes — increase the wall length or "
                         "thickness")
            pick = cands[-1]
        else:
            pick = cands[idx]
        pick = {**WALL_WEB, **pick}
        reinf = wall_reinf(pick, lc)
        As = 2 * pick["nbe"] * np.pi * float(pick["dbe"]) ** 2 / 4
        gov_inp = {**(dict(combos)[gov] if gov else combos[0][1]), **pick}
        out.append(MemberDesign(mid, "wall", 1, reinf, util, idx >= 0, gov, gov_inp,
                                "ec8_rc_wall", notes, As / (lw * bw),
                                {"combos": [(nm, {k: (float(v) if isinstance(v, np.floating)
                                                      else v) for k, v in c.items()})
                                            for nm, c in combos]}))
    return out


# --------------------------------------------------------------------- capacity design


@dataclass
class JointCheck:
    node: str
    direction: str
    sum_MRc: float   # Nmm
    sum_MRb: float
    ratio: float     # ΣM_Rc / ΣM_Rb (≥ 1.3 required)
    ok: bool
    raised: bool = False  # column bars increased to satisfy the rule


def _beam_MRd(d: MemberDesign, b: float, h: float, fcd: float, fyd: float, cover: float):
    """(M_Rd hogging, M_Rd sagging) of a designed beam end, Nmm."""
    from ..design.ec2 import section_capacity

    i = d.inputs
    bot = i["n_bars"] * np.pi * float(i["dia"]) ** 2 / 4
    top = i["n_comp"] * np.pi * float(i["dia_comp"]) ** 2 / 4
    dl = float(i.get("link_dia", 8))
    d_bot = h - cover - dl - float(i["dia"]) / 2
    d_top = h - cover - dl - float(i["dia_comp"]) / 2
    sag = section_capacity(b, d_bot, bot, fcd, fyd, h - d_top, top)[0]
    hog = section_capacity(b, d_top, top, fcd, fyd, h - d_bot, bot)[0]
    return hog, sag


def _col_MRd(inp: dict, direction: str, NEd: float, fcd: float, fyd: float) -> float:
    """Column M_Rd for a frame in ``direction`` (X: depth = b along X; Y: depth = h)."""
    from ..design.ec2 import moment_resistance, section_layers

    b, h = inp["b"], inp["h"]
    dia, link = float(inp["dia"]), float(inp["link"])
    cb = inp["cover"] + link + dia / 2
    if direction == "X":   # bending across b (depth b, width h)
        layers = section_layers(h, b, inp["nh"], inp["nb"], dia, cb)
        return moment_resistance(h, b, layers, fcd, fyd, NEd)[0]
    layers = section_layers(b, h, inp["nb"], inp["nh"], dia, cb)
    return moment_resistance(b, h, layers, fcd, fyd, NEd)[0]


def capacity_design(columns: list[MemberDesign], beams: list[MemberDesign],
                    joints: list[dict], quasi: StaticResult, seis: SeismicResult,
                    col_bh: tuple[float, float], beam_bh: tuple[float, float], concrete: str,
                    fyk: float = 500.0, cover: float = 30.0,
                    gamma_c: float = 1.5, gamma_s: float = 1.15,
                    alpha_cc: float = 1.0) -> list[JointCheck]:
    """EN 1998-1 4.4.2.3(4): ΣM_Rc ≥ 1.3 ΣM_Rb at every beam–column joint (frames).

    ``joints``: {"node", "dir", "cols": [below, above], "beams": [left, right]}.
    Member sizes are read from each design record (``col_bh``/``beam_bh`` are kept for
    backward compatibility and are not used).
    When a joint fails, the bars of both columns are increased (same arrangement
    family as the automatic design) until the rule is met; the column design
    records are updated in place.
    """
    fck = float(concrete.split("/")[0][1:])
    fcd, fyd = alpha_cc * fck / gamma_c, fyk / gamma_s
    cd = {d.member: d for d in columns}
    bd = {d.member: d for d in beams}
    cands = _col_candidates()
    out = []
    for jt in joints:
        cols = [cd[c] for c in jt["cols"] if c in cd]
        bms = [bd[b] for b in jt["beams"] if b in bd]
        if len(cols) < 2 or not bms:
            continue
        hog_sag = [_beam_MRd(b, b.inputs["b"], b.inputs["h"], fcd, fyd, cover) for b in bms]
        if len(hog_sag) == 2:  # one beam hogging + the other sagging, worst sense
            sum_b = max(hog_sag[0][0] + hog_sag[1][1], hog_sag[0][1] + hog_sag[1][0])
        else:
            sum_b = max(hog_sag[0])
        # minimum compression of each column in the seismic situation
        Ns = []
        for c in cols:
            N = -quasi.forces(c.member, 2)["N"][0] - seis.member_envelope(c.member)[0]
            Ns.append(max(N, 0.0))

        def sum_c() -> float:
            return sum(_col_MRd(c.inputs, jt["dir"], N, fcd, fyd) for c, N in zip(cols, Ns))

        sc = sum_c()
        raised = False
        while sc < 1.3 * sum_b:
            nxt = []
            for c in cols:
                i = next((n for n, cand in enumerate(cands)
                          if cand["dia"] == c.inputs["dia"] and cand["nb"] == c.inputs["nb"]), -1)
                nxt.append(i + 1 if i + 1 < len(cands) else None)
            if any(n is None for n in nxt):
                break
            for c, n in zip(cols, nxt):
                c.inputs = {**c.inputs, **cands[n]}
                nb = 4 * cands[n]["nb"] - 4
                c.reinforcement = f"{nb}Ø{cands[n]['dia']}, Ø8/{cands[n]['s']:g}"
                c.rho = nb * np.pi * float(cands[n]["dia"]) ** 2 / 4 / (c.inputs["b"]
                                                                        * c.inputs["h"])
                if "Bars increased by capacity design (ΣM_Rc ≥ 1.3 ΣM_Rb)" not in c.notes:
                    c.notes.append("Bars increased by capacity design (ΣM_Rc ≥ 1.3 ΣM_Rb)")
            raised = True
            sc = sum_c()
        out.append(JointCheck(jt["node"], jt["dir"], sc, sum_b, sc / sum_b if sum_b else
                              float("inf"), sc >= 1.3 * sum_b - 1e-6, raised))
    return out


def capacity_shears(columns: list[MemberDesign], beams: list[MemberDesign],
                    quasi: StaticResult, col_clear: dict[str, float], concrete: str,
                    beam_bh: tuple[float, float], project=None, fyk: float = 500.0,
                    cover: float = 30.0, gamma_c: float = 1.5, gamma_s: float = 1.15,
                    alpha_cc: float = 1.0) -> None:
    """EN 1998-1 5.4.2.2 / 5.4.2.3 (DCM): shears from the flexural capacities.

    Beams: V = V_g+ψ2q + (M_Rb,1 + M_Rb,2)/l_cl (γ_Rd = 1.0);
    columns: V = 1.1 (M_Rc,top + M_Rc,bot)/l_cl.  The links are re-chosen with the
    member modules so that they resist these shears; records are updated in place.
    """
    fck = float(concrete.split("/")[0][1:])
    fcd, fyd = alpha_cc * fck / gamma_c, fyk / gamma_s
    bmod, cmod = get_module("ec2_rc_beam"), get_module("ec2_rc_column")
    for d in beams:
        e = quasi.analysis.elements[quasi.analysis.member_index[d.member]]
        lcl = e.Lf
        hog, sag = _beam_MRd(d, d.inputs["b"], d.inputs["h"], fcd, fyd, cover)
        Vg = np.abs(quasi.forces(d.member, 21)["Vz"]).max()
        V = Vg + (hog + sag) / lcl
        if V / 1e3 <= d.inputs["VEd"]:
            continue
        inp = {**d.inputs, "VEd": V / 1e3}
        ld0 = d.inputs.get("link_dia", "8")
        found = None
        for ld in [x for x in ("8", "10", "12") if float(x) >= float(ld0)]:
            for s in LINK_S:
                if ld == ld0 and s > d.inputs["link_s"]:
                    continue
                p, u = _passes(bmod, {**inp, "link_dia": ld, "link_s": s}, project)
                if p:
                    found = (ld, s, u)
                    break
            if found:
                break
        if not found:
            d.ok = False
            d.notes.append("Capacity-design shear exceeds the resistance with Ø8 links — "
                           "increase the beam width/depth")
            found = ("12", LINK_S[-1], _passes(bmod, {**inp, "link_dia": "12",
                                                      "link_s": LINK_S[-1]}, project)[1])
        ld, s, u = found
        old = d.inputs["link_s"]
        d.inputs = {**inp, "link_dia": ld, "link_s": s}
        d.utilisation = max(d.utilisation, u)
        d.reinforcement = d.reinforcement.replace(f"Ø{ld0}/{old:g}", f"Ø{ld}/{s:g}", 1)
        d.notes.append(Msg("links from the capacity-design shear V = {v:.0f} kN (5.4.2.2)",
                           v=V / 1e3))
    for d in columns:
        i = d.inputs
        N = i["NEd"] * 1e3
        Mx = _col_MRd(i, "X", N, fcd, fyd)
        My = _col_MRd(i, "Y", N, fcd, fyd)
        V = 1.1 * 2 * max(Mx, My) / (col_clear[d.member])
        if V / 1e3 <= i["VEd"]:
            continue
        inp = {**i, "VEd": V / 1e3}
        for s in (i["s"], 90.0, 75.0, 60.0, 50.0):
            if s > i["s"]:
                continue
            p, u = _passes(cmod, {**inp, "s": s}, project)
            if p:
                break
        else:
            d.ok = False
            d.notes.append("Capacity-design shear exceeds the resistance — increase the "
                           "column size")
            s, u = 50.0, _passes(cmod, {**inp, "s": 50.0}, project)[1]
        d.inputs = {**inp, "s": s}
        d.utilisation = max(d.utilisation, u)
        nb = 4 * i["nb"] - 4
        d.reinforcement = f"{nb}Ø{i['dia']}, Ø8/{s:g}"
        d.notes.append(Msg("links from the capacity-design shear V = {v:.0f} kN (5.4.2.3)",
                           v=V / 1e3))


# --------------------------------------------------------------------- slabs

SLAB_BARS = [(d, s) for d in ("8", "10", "12") for s in (200.0, 150.0, 125.0, 100.0)]


def design_slabs(panels: list[dict], slab_t: float, concrete: str, g_finish: float,
                 q_by_storey: dict[int, float], project=None, fyk: float = 500.0,
                 cover: float = 25.0) -> list[MemberDesign]:
    """Two-way slab panels with the EN 1992-1-1 slab module.

    ``panels``: {"id", "lx", "ly" (mm, along X and Y), "cont": {"x0","x1","y0","y1": bool}}
    — an edge is continuous when the neighbouring panel exists.  ``q_by_storey`` maps
    storey → imposed load (N/mm²); storeys with equal loads share one design.
    """
    module = get_module("ec2_rc_slab")
    cands = sorted(SLAB_BARS, key=lambda c: float(c[0]) ** 2 / c[1])
    edge = lambda c: "Fixed / continuous" if c else "Simply supported"  # noqa: E731
    out: list[MemberDesign] = []
    for q in sorted(set(q_by_storey.values())):
        storeys = [k for k, v in q_by_storey.items() if v == q]
        for p in panels:
            lx, ly, c = p["lx"], p["ly"], p["cont"]
            if lx <= ly:   # module: l_x = short span; e1/e2 at x = 0 / l_x, e3/e4 at y = 0 / l_y
                es = (c["x0"], c["x1"], c["y0"], c["y1"])
                short, long_ = lx, ly
            else:
                es = (c["y0"], c["y1"], c["x0"], c["x1"])
                short, long_ = ly, lx
            base = {"type": "Two-way panel", "lx": short / 1000, "ly": long_ / 1000,
                    "e1": edge(es[0]), "e2": edge(es[1]), "e3": edge(es[2]), "e4": edge(es[3]),
                    "h": slab_t, "cover": cover, "concrete": concrete, "fyk": fyk,
                    "g": (g_finish + p.get("g_extra", 0.0)) * 1e3,
                    "q": (q + p.get("q_extra", 0.0)) * 1e3, "punch": False}
            dense = cands[-1]
            pick_b = pick_t = None
            for cb in cands:
                if _passes(module, {**base, "dia_b": cb[0], "s_b": cb[1], "dia_t": dense[0],
                                    "s_t": dense[1]}, project)[0]:
                    pick_b = cb
                    break
            notes = []
            ok = pick_b is not None
            pick_b = pick_b or dense
            for ct in cands:
                if _passes(module, {**base, "dia_b": pick_b[0], "s_b": pick_b[1], "dia_t": ct[0],
                                    "s_t": ct[1]}, project)[0]:
                    pick_t = ct
                    break
            ok = ok and pick_t is not None
            pick_t = pick_t or dense
            inp = {**base, "dia_b": pick_b[0], "s_b": pick_b[1], "dia_t": pick_t[0],
                   "s_t": pick_t[1]}
            util = _passes(module, inp, project)[1]
            if not ok:
                notes.append("No slab reinforcement passes — increase the slab thickness")
            reinf = f"bottom Ø{pick_b[0]}/{pick_b[1]:g}, top Ø{pick_t[0]}/{pick_t[1]:g}"
            As = np.pi * float(pick_b[0]) ** 2 / 4 * 1000 / pick_b[1]
            for k in storeys:
                out.append(MemberDesign(f"S{k}.{p['id']}", "slab", k, reinf, util, ok,
                                        "1.35G+1.5Q", inp, "ec2_rc_slab", list(notes),
                                        As / (1000 * slab_t)))
    return sorted(out, key=lambda d: (d.storey, d.member))


# --------------------------------------------------------------------- foundations

FOOT_BARS = [(d, s) for d in ("12", "14", "16", "20") for s in (200.0, 150.0, 125.0, 100.0)]


def _omega(d: MemberDesign | None, seis: SeismicResult, quasi: StaticResult, fcd: float,
           fyd: float) -> float:
    """EN 1998-1 4.4.2.6(2), (4): γ_Rd·Ω for the footing of a column, Ω = M_Rd/M_Ed at
    the column base (≤ q), γ_Rd = 1.0 for q ≤ 3, 1.2 otherwise. Walls: from the flexure
    check of the wall design (Ω = 1/η_flexure)."""
    q = seis.q
    g_rd = 1.0 if q <= 3 else 1.2
    if d is None:
        return g_rd * q
    if d.kind == "wall":
        c = get_module("ec8_rc_wall").calculate(d.inputs)
        u = max((k.utilisation for k in c.checks if "Flexure" in k.description), default=0.0)
        om = 1 / u if u > 0 else q
    else:
        f = quasi.forces(d.member, 2)
        env = seis.member_envelope(d.member)
        N = max(-f["N"][0] - env[0], 0.0)
        oms = []
        for direction, mq, e in (("X", f["Mz"][0], env[5]), ("Y", f["My"][0], env[4])):
            MEd = abs(mq) + e
            if MEd > 1e3:
                oms.append(_col_MRd(d.inputs, direction, N, fcd, fyd) / MEd)
        om = min(oms) if oms else q
    return g_rd * min(max(om, 1.0), q)


def design_footings(bases: dict[str, dict], res: dict[str, StaticResult],
                    seis: SeismicResult | None, quasi: StaticResult, members: dict,
                    soil: dict, concrete: str, project=None, fyk: float = 500.0,
                    gamma_c: float = 1.5, gamma_s: float = 1.15,
                    alpha_cc: float = 1.0) -> list[MemberDesign]:
    """Pad footing under every column/wall with the EN 1997-1 footing module.

    ``bases``: grid → {"node", "member" (base member id), "cx", "cy" (mm)};
    ``soil``: {"phi", "c" (kPa), "gamma" (kN/m³), "D" (m), "approach"}.
    Seismic actions follow EN 1998-1 4.4.2.6: E_Fd = E_F,G + γ_Rd Ω E_F,E.
    """
    module = get_module("ec7_pad_footing")
    fck = float(concrete.split("/")[0][1:])
    fcd, fyd = alpha_cc * fck / gamma_c, fyk / gamma_s
    out = []
    for g, b in bases.items():
        n = b["node"]
        RG, RQ = res["G"].reaction(n), res["Q"].reaction(n)
        cx, cy = b["cx"], b["cy"]
        common = {"cx": cx / 1000, "cy": cy / 1000, "D": soil["D"], "phi": soil["phi"],
                  "c": soil["c"], "gamma": soil["gamma"], "approach": soil["approach"],
                  "concrete": concrete, "fyk": fyk,
                  "NG": max(RG[2], 0.0) / 1e3, "NQ": max(RQ[2], 0.0) / 1e3,
                  "MxG": abs(RG[4]) / 1e6, "MxQ": abs(RQ[4]) / 1e6,
                  "MyG": abs(RG[3]) / 1e6, "MyQ": abs(RQ[3]) / 1e6,
                  "HxG": np.hypot(RG[0], RG[1]) / 1e3, "HxQ": np.hypot(RQ[0], RQ[1]) / 1e3}
        combos = []
        if seis is None:
            combos.append(("1.35G+1.5Q", {**common, "seismic": False}))
        else:
            om = _omega(members.get(b["member"]), seis, quasi, fcd, fyd)
            Rq = quasi.reaction(n)
            E = seis.reaction_envelope(n) * om
            for sgn, nm in ((+1, "G+ψ2Q+ΩE (N max)"), (-1, "G+ψ2Q+ΩE (N min)")):
                combos.append((nm, {**common, "seismic": True,
                                    "NE": max(Rq[2] + sgn * E[2], 0.0) / 1e3,
                                    "MxE": (abs(Rq[4]) + E[4]) / 1e6,
                                    "MyE": (abs(Rq[3]) + E[3]) / 1e6,
                                    "HxE": (np.hypot(Rq[0], Rq[1]) + np.hypot(E[0], E[1])) / 1e3}))
        # plan size: smallest passing (bisection over B with dense bars), then the lightest bars
        c0 = max(cx, cy) / 1000
        sizes = [round(c0 + 0.6 + 0.1 * i, 2) for i in range(0, 60)]

        def geom(B):
            ext = B - c0                      # same overhang on every side
            Bx, By = cx / 1000 + ext, cy / 1000 + ext
            h = min(max(0.5, round(ext / 2 / 0.6 / 0.05) * 0.05 + 0.05), 1.5, soil["D"])
            return {"Bx": round(Bx, 2), "By": round(By, 2), "h": h}

        dense = {"dia_x": "20", "s_x": 100.0, "dia_y": "20", "s_y": 100.0}

        def ok_all(extra):
            return all(_passes(module, {**inp, **extra}, project)[0] for _, inp in combos)

        lo, hi, best = 0, len(sizes) - 1, None
        if ok_all({**geom(sizes[hi]), **dense}):
            while lo <= hi:
                mid_ = (lo + hi) // 2
                if ok_all({**geom(sizes[mid_]), **dense}):
                    best, hi = mid_, mid_ - 1
                else:
                    lo = mid_ + 1
        notes = []
        if best is None:
            gm = geom(sizes[-1])
            notes.append("No footing up to this size passes — use a strip footing or a raft, "
                         "or improve the soil data")
            bars, ok = dense, False
        else:
            gm = geom(sizes[best])
            bars, ok = None, True
            for d, s in sorted(FOOT_BARS, key=lambda c: float(c[0]) ** 2 / c[1]):
                cand = {"dia_x": d, "s_x": s, "dia_y": d, "s_y": s}
                if ok_all({**gm, **cand}):
                    bars = cand
                    break
            bars = bars or dense
        util, gov = 0.0, ""
        for nm, inp in combos:
            u = _passes(module, {**inp, **gm, **bars}, project)[1]
            if u >= util:
                util, gov = u, nm
        reinf = (f"{gm['Bx']:.2f}×{gm['By']:.2f}×{gm['h']:.2f} m, "
                 f"Ø{bars['dia_x']}/{bars['s_x']:g} both ways")
        gov_inp = {**dict(combos)[gov], **gm, **bars}
        out.append(MemberDesign(f"F.{g}", "footing", 0, reinf, util, ok, gov, gov_inp,
                                "ec7_pad_footing", notes, 0.0))
    return out



# --------------------------------------------------------------------- soil under foundation beams


def strip_bearing(B: float, D: float, phi: float, c: float, gamma: float, g_phi: float = 1.0,
                  g_c: float = 1.0, g_R: float = 1.0) -> float:
    """Design bearing resistance of a long strip, EN 1997-1 Annex D.4 (drained, vertical
    central load, s = i = 1): q_Rd = [c'_d N_c + γ D N_q + ½ γ B N_γ] / γ_R,v  (N/mm², mm)."""
    import math

    from ..design.geotech import bearing_factors

    phid = math.atan(math.tan(math.radians(phi)) / g_phi)
    Nq, Nc, Ng = bearing_factors(phid)
    return (c / g_c * Nc + gamma * D * Nq + 0.5 * gamma * B * Ng) / g_R


def soil_pressures(res: dict[str, StaticResult], quasi: StaticResult, seis: SeismicResult | None,
                   e_factor: float, springs: dict[str, float], B: float, D: float, soil: dict,
                   annex) -> list[dict]:
    """Bearing check under foundation beams for every EC7 combination of the annex and the
    seismic situation: p = R / (B·l_trib) at every spring node ≤ q_Rd of a strip of width B
    (EN 1997-1 6.5.2; seismic: EN 1998-5 5.4.1.1 with its material factors).

    ``springs``: node → tributary length (mm).  Returns one row per combination.
    """
    rows = []
    approach = annex.approach("National Annex")
    for combo in annex.combinations(approach):
        gG, _gGf, gQ, gphi, gc, gRv = annex.combos[combo][:6]
        qRd = strip_bearing(B, D, soil["phi"], soil["c"], soil["gamma"], gphi, gc, gRv)
        worst = max(((gG * res["G"].reaction(n)[2] + gQ * res["Q"].reaction(n)[2]) / (B * L), n)
                    for n, L in springs.items())
        rows.append({"combo": combo, "p": worst[0], "node": worst[1], "qRd": qRd})
    if seis is not None:
        qRd = strip_bearing(B, D, soil["phi"], soil["c"], soil["gamma"], annex.seismic_gamma_phi,
                            annex.seismic_gamma_c, 1.0)
        best, low = (-1.0, ""), (1e30, "")
        for n, L in springs.items():
            R0, E = quasi.reaction(n)[2], seis.reaction_envelope(n)[2] * e_factor
            best = max(best, ((R0 + E) / (B * L), n))
            low = min(low, ((R0 - E) / (B * L), n))
        rows.append({"combo": "G+ψ2Q+ΩE", "p": best[0], "node": best[1], "qRd": qRd,
                     "p_min": low[0], "node_min": low[1]})
    return rows


# ---------------------------------------------------------------- design-results window
def _bar_area(n, dia) -> float:
    return float(n) * np.pi * float(dia) ** 2 / 4


def _checks_of(module_id: str, inp: dict, project, lang: str, section: str = "",
               outputs: dict | None = None) -> list[dict]:
    """Checks of ``module_id`` run with ``inp``; without ``section`` each check is grouped
    under the heading it was written under in the calculation. ``outputs`` (if given)
    receives the computed quantities (display units)."""
    try:
        c = get_module(module_id).calculate(inp, project, lang)
    except InputError as exc:
        return [{"section": section, "d": str(exc), "u": 9.99, "ok": False, "ref": "",
                 "demand": None, "capacity": None, "unit": "", "hint": ""}]
    if outputs is not None:
        outputs.update({k: {"value": float(v["value"]), "unit": v["unit"],
                            "d": v.get("description", "")}
                        for k, v in c.outputs.items() if isinstance(v.get("value"), (int, float))})
    out, head = [], section
    for it in c.items:
        if it.kind == "heading" and not section:
            head = it.data["text"]
        if it.kind != "check":
            continue
        ch = it.data["check"]
        dd = ch.to_dict()                      # demand / capacity in display units
        out.append({"section": head, "d": ch.description, "u": float(ch.utilisation),
                    "ok": bool(ch.passed), "ref": ch.ref, "demand": float(dd["demand"]),
                    "capacity": float(dd["capacity"]), "unit": ch.unit, "hint": ch.hint,
                    "min": bool(ch.is_min)})
    return out


def member_checks(d: MemberDesign, project=None, lang: str = "en",
                  outputs: dict | None = None) -> list[dict]:
    """Every check of a designed member, as listed in its design-results window.

    Beams: the span section (sagging, bottom bars in tension) and the support sections
    (hogging, top bars in tension) plus the span/depth check; columns: the governing design
    combination; other members: the module run with their design inputs."""
    if not d.module:
        return []
    if d.kind == "beam" and d.detail:
        t, bt = d.detail["top"], d.detail["bottom"]
        sag = {**d.inputs, "MEd": max(d.detail["M_sag"], 1.0), "n_bars": bt["n_bars"],
               "dia": bt["dia"], "n_comp": t["n_bars"], "dia_comp": t["dia"]}
        hog = {**sag, "MEd": max(d.detail["M_hog"], 1.0), "n_bars": t["n_bars"],
               "dia": t["dia"], "n_comp": bt["n_bars"], "dia_comp": bt["dia"]}
        from ..i18n import tr
        out = _checks_of(d.module, sag, project, lang, "span")
        sup = [c for c in _checks_of(d.module, hog, project, lang, "support")
               if not str(c["ref"]).startswith(("6.2", "9.2.2"))]   # shear: once (span)
        if d.detail.get("s_cr"):               # EN 1998-1 5.4.3.1.2 (DCM beams)
            fck = float(str(d.inputs["concrete"]).split("/")[0][1:])
            fyk = float(d.inputs["fyk"])
            dd = d.inputs["h"] - d.inputs["cnom"] - 18
            As_min = 0.5 * 0.30 * fck ** (2 / 3) / fyk * d.inputs["b"] * dd
            A_t, A_b = _bar_area(t["n_bars"], t["dia"]), _bar_area(bt["n_bars"], bt["dia"])
            for face, A in (("top", A_t), ("bottom", A_b)):
                sup.append({"section": "ec8", "d": tr("ρ ≥ ρ_min = 0.5 f_ctm/f_yk ({f})", lang,
                                                       f=tr(f"{face} bars", lang)),
                            "u": As_min / A, "ok": A >= As_min, "ref": "EN 1998-1 5.4.3.1.2(5)",
                            "demand": As_min, "capacity": A, "unit": "mm²", "hint": "",
                            "min": True})
            for comp, A_c, A_tn in (("bottom", A_b, A_t), ("top", A_t, A_b)):
                need = 0.5 * A_tn
                sup.append({"section": "ec8", "d": tr("Compression steel ≥ 0.5 × tension steel "
                                                       "in the critical region ({f})", lang,
                                                       f=tr(f"{comp} bars", lang)),
                            "u": need / A_c, "ok": A_c >= need, "ref": "EN 1998-1 5.4.3.1.2(4)",
                            "demand": need, "capacity": A_c, "unit": "mm²", "hint": "",
                            "min": True})
        if d.detail.get("sls"):
            fck = float(str(d.inputs["concrete"]).split("/")[0][1:])
            h, b, cov = d.inputs["h"], d.inputs["b"], d.inputs["cnom"]
            d_b = h - cov - float(d.detail["link_dia"]) - float(bt["dia"]) / 2
            fyk = float(d.inputs["fyk"])
            M = d.detail["M_sag"] * 1e6
            As_req = M / (0.9 * d_b * fyk / 1.15) if M > 0 else 0.0
            r, lim = span_depth(d.detail["L"], d_b, b, _bar_area(bt["n_bars"], bt["dia"]),
                                _bar_area(t["n_bars"], t["dia"]), As_req, fck, d.detail["K"])
            out.append({"section": "span", "d": tr("Deflection: l/d ≤ (l/d)_lim", lang),
                        "u": r / lim,
                        "ok": r <= lim, "ref": "EN 1992-1-1 7.4.2", "demand": r,
                        "capacity": lim, "unit": "", "hint": "", "min": False})
        return out + sup
    if d.kind == "wall" and d.detail.get("combos"):
        # show the seismic design situation (largest moment) — it governs a ductile wall
        pick = {k: d.inputs[k] for k in ("nbe", "dbe", "dh", "sh", "dv", "sv", "dhw", "shw")
                if k in d.inputs}
        nm, c = max(d.detail["combos"], key=lambda t: float(t[1]["MEd"]))
        return _checks_of(d.module, {**c, **pick}, project, lang, outputs=outputs)
    return _checks_of(d.module, d.inputs, project, lang, outputs=outputs)


def member_results(d: MemberDesign, project=None, lang: str = "en") -> dict:
    """Checks, key computed quantities and (columns, walls) the N–M interaction diagram
    for the design-results window."""
    outs: dict = {}
    checks = member_checks(d, project, lang, outs)
    res = {"checks": checks, "outputs": outs}
    nm = interaction(d, project)
    if nm:
        res["nm"] = nm
    return res


def apply_override(d: MemberDesign, ov: dict, project=None) -> None:
    """Check mode: replace the automatic reinforcement of ``d`` by the engineer's ``ov`` and
    re-check it for every design situation that was used to design it."""
    if d.kind == "column" and d.detail.get("combos"):
        pick = {k: d.inputs[k] for k in ("dia", "nb", "nh", "link", "s") if k in d.inputs}
        pick.update({k: ov[k] for k in ("dia", "nb", "s", "link") if k in ov})
        pick["nb"] = int(pick["nb"])
        pick["nh"] = pick["nb"]
        pick["s"] = float(pick["s"])
        worst, gov, ok = -1.0, d.governing, True
        for nm, c in d.detail["combos"]:
            p, u = _passes(get_module("ec2_rc_column"), {**c, **pick}, project)
            ok &= p
            if u > worst:
                worst, gov = u, nm
        d.inputs = {**dict(d.detail["combos"]).get(gov, d.inputs), **pick}
        n_bars = 4 * int(d.inputs["nb"]) - 4
        d.reinforcement = f"{n_bars}Ø{d.inputs['dia']}, Ø{d.inputs.get('link', '8')}/{float(d.inputs['s']):g}"
        d.utilisation, d.ok, d.governing = worst, ok, gov
        d.rho = _bar_area(n_bars, d.inputs["dia"]) / (d.inputs["b"] * d.inputs["h"])
    elif d.kind == "beam" and d.detail:
        det = d.detail
        for face in ("bottom", "top"):
            if f"{face}_n" in ov:
                det[face] = {"n_bars": int(ov[f"{face}_n"]), "dia": str(ov[f"{face}_dia"])}
        if "s" in ov:
            det["s"] = float(ov["s"])
        if "link_dia" in ov:
            det["link_dia"] = str(ov["link_dia"])
        d.inputs = {**d.inputs, **det["bottom"], "n_comp": det["top"]["n_bars"],
                    "dia_comp": det["top"]["dia"], "link_s": det["s"],
                    "link_dia": det["link_dia"]}
        chk = [c for c in member_checks(d, project) if not c.get("min")]
        allc = member_checks(d, project)
        d.utilisation = max([c["u"] for c in chk] + [0.0])
        d.ok = all(c["ok"] for c in allc)
        d.reinforcement = (f"bottom {det['bottom']['n_bars']}Ø{det['bottom']['dia']}, "
                           f"top {det['top']['n_bars']}Ø{det['top']['dia']}, "
                           f"Ø{det['link_dia']}/{det['s']:g}")
        if det.get("s_cr"):
            d.reinforcement += f" (ends Ø{det['link_dia']}/{det['s_cr']:g} over {det['l_cr']:g} mm)"
        d.rho = (_bar_area(det["bottom"]["n_bars"], det["bottom"]["dia"]) +
                 _bar_area(det["top"]["n_bars"], det["top"]["dia"])) / \
            (d.inputs["b"] * d.inputs["h"])
    elif d.kind == "wall" and d.detail.get("combos"):
        keys = ("nbe", "dbe", "dh", "sh", "dv", "sv", "dhw", "shw")
        pick = {k: d.inputs[k] for k in keys if k in d.inputs}
        pick.update({k: ov[k] for k in keys if k in ov})
        pick["nbe"] = int(pick["nbe"])
        for k in ("sh", "sv", "shw"):
            pick[k] = float(pick[k])
        worst, gov, ok = -1.0, d.governing, True
        for nm, c in d.detail["combos"]:
            p, u = _passes(get_module("ec8_rc_wall"), {**c, **pick}, project)
            ok &= p
            if u > worst:
                worst, gov = u, nm
        d.inputs = {**dict(d.detail["combos"]).get(gov, d.inputs), **pick}
        d.reinforcement = wall_reinf(d.inputs, d.inputs["lc"])
        d.utilisation, d.ok, d.governing = worst, ok, gov
        d.rho = 2 * _bar_area(pick["nbe"], pick["dbe"]) / (d.inputs["lw"] * 1000 *
                                                            d.inputs["bw"])
    elif d.kind == "slab":
        keys = ("dia_b", "s_b", "dia_t", "s_t")
        d.inputs = {**d.inputs, **{k: (float(ov[k]) if k.startswith("s_") else str(ov[k]))
                                   for k in keys if k in ov}}
        ok, util = _passes(get_module("ec2_rc_slab"), d.inputs, project)
        d.ok, d.utilisation = ok, util
        i = d.inputs
        d.reinforcement = (f"bottom Ø{i['dia_b']}/{float(i['s_b']):g}, "
                           f"top Ø{i['dia_t']}/{float(i['s_t']):g}")
        d.rho = _bar_area(1, i["dia_b"]) * 1000 / float(i["s_b"]) / (1000 * i["h"])
    else:
        return
    d.notes = [n for n in d.notes if "increase" not in str(n).lower()]
    d.notes.append("Reinforcement set by the engineer (check mode)")
    d.detail["override"] = True


# ---------------------------------------------------------------- N–M interaction diagram
def _nm_points(b: float, h: float, bars: list[tuple[float, float]], fcd: float, fyd: float,
               n: int = 60) -> list[tuple[float, float]]:
    """Design N–M interaction curve of a rectangular section bent about the axis parallel
    to ``b`` (depth ``h``) — EN 1992-1-1 6.1: ε_cu = 3.5 ‰, rectangular stress block
    (λ = 0.8, η = 1), elastic–plastic steel (E_s = 200 GPa).  ``bars`` = (depth from the
    compressed face, area).  Returns (N [kN], M [kNm]) from pure tension to pure compression
    (N > 0 compression; M about the centre of the section)."""
    Es, ecu = 200000.0, 0.0035
    As_tot = sum(a for _, a in bars)
    pts = [(-fyd * As_tot / 1e3, 0.0)]
    xs = [h * 10 ** (k / n * 3 - 2) for k in range(n + 1)]     # 0.01 h … 10 h
    for x in xs:
        a = min(0.8 * x, h)
        N = fcd * b * a
        M = fcd * b * a * (h / 2 - a / 2)
        for y, A in bars:
            es = ecu * (x - y) / x
            sg = max(-fyd, min(fyd, Es * es))
            if y < a:                                   # bar inside the stress block
                sg -= fcd if sg > 0 else 0.0
            N += sg * A
            M += sg * A * (h / 2 - y)
        pts.append((float(N) / 1e3, float(M) / 1e6))
    Nmax = (fcd * b * h + min(fyd, Es * 0.002) * As_tot) / 1e3
    pts.append((float(Nmax), 0.0))
    return pts


def interaction(d: MemberDesign, project=None) -> dict | None:
    """N–M diagram data of a column (both axes) or a wall (strong axis) with the design
    points of every design situation (first-order actions from the analysis)."""
    from ..design.annex import get_annex
    na = get_annex((project or {}).get("annex") if isinstance(project, dict) else
                   getattr(project, "annex", None))
    i = d.inputs
    try:
        fck = float(str(i["concrete"]).split("/")[0][1:])
    except (KeyError, ValueError):
        return None
    fcd = na.alpha_cc * fck / na.gamma_c
    fyd = float(i.get("fyk", 500.0)) / na.gamma_s
    combos = d.detail.get("combos") or [(d.governing, i)]
    if d.kind == "column":
        b, h, cov = i["b"], i["h"], i["cover"]
        dia, n = float(i["dia"]), int(i["nb"])
        a1 = _bar_area(1, dia)
        e = cov + float(i.get("link", 8)) + dia / 2

        def rows(depth):
            ys = [e + (depth - 2 * e) * k / (n - 1) for k in range(n)]
            return [(y, a1 * (n if k in (0, n - 1) else 2)) for k, y in enumerate(ys)]
        curve_h = _nm_points(b, h, rows(h), fcd, fyd)
        curve_b = curve_h if b == h else _nm_points(h, b, rows(b), fcd, fyd)
        pts = []
        for nm, c in combos:
            pts.append({"name": nm, "N": float(c["NEd"]),
                        "Mh": max(abs(float(c["Mh_top"])), abs(float(c["Mh_bot"]))),
                        "Mb": max(abs(float(c["Mb_top"])), abs(float(c["Mb_bot"])))})
        return {"curves": {"h": curve_h, "b": curve_b}, "points": pts}
    if d.kind == "wall":
        lw, bw, lc = i["lw"] * 1000, i["bw"], i["lc"]
        cov, dbe, nbe = i["cover"], float(i["dbe"]), int(i["nbe"])
        e = cov + float(i.get("dh", 10)) + dbe / 2
        per = max(nbe // 2, 1)                      # bars per face in a boundary element
        bars = []
        for k in range(per):
            y = e + (lc - 2 * e) * (k / (per - 1) if per > 1 else 0.5)
            bars += [(y, 2 * _bar_area(1, dbe)), (lw - y, 2 * _bar_area(1, dbe))]
        sv, dv = float(i.get("sv", 200)), float(i.get("dv", 10))
        y = lc + sv / 2
        while y < lw - lc:
            bars.append((y, 2 * _bar_area(1, dv)))
            y += sv
        pts = [{"name": nm, "N": float(c["NEd"]), "M": float(c["MEd"])} for nm, c in combos]
        return {"curves": {"strong": _nm_points(bw, lw, bars, fcd, fyd)}, "points": pts}
    return None
