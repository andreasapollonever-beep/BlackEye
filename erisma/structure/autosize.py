"""Automatic sizing: change member sizes and analysis options until every Eurocode check of
the building passes (or nothing more can be done).

Each round runs the complete calculation (analysis, EC8 checks, design of every member,
slab and foundation) and applies simple, conservative engineering rules to what failed:

* a failing column / beam / wall / slab / foundation element is enlarged in 50 mm steps
  (beams deeper first, walls thicker then longer, slabs 20 mm thicker, foundation beams deeper
  then wider, isolated footings replaced by foundation beams);
* storey drift or θ too large → all columns 50 mm larger in that direction;
* strong-column/weak-beam failure at a joint → the columns of that grid line 50 mm larger;
* Σ effective mass < 90 % → more modes; α_cr < 10 → P-Δ analysis switched on;
* soil bearing under foundation beams → wider flange.

Inputs are in the module's display units (m, mm, kN/m²…), as edited by the engineer.
"""

from __future__ import annotations

import copy

from ..core import InputError, get_module
from ..i18n import tr

CAP_COL, CAP_BEAM_H, CAP_BEAM_B, CAP_WALL_T, CAP_SLAB = 1200, 1000, 600, 400, 300
CAP_FB_H, CAP_FB_BW, CAP_FB_B = 2500, 1000, 4.0


def _grid(member: str) -> str:
    return member.split(".", 1)[1]


def _adjust(inp: dict, calc, lang: str) -> list[str]:
    """Apply one round of changes; returns the (translated) log lines."""
    log: list[str] = []
    lay = inp.setdefault("layout", {})
    cols = lay.setdefault("col_sizes", {})
    beams = lay.setdefault("beam_sizes", {})
    members = (getattr(calc, "structure", None) or {}).get("members", {})
    issues = (getattr(calc, "structure", None) or {}).get("issues", [])
    say = lambda text, **kw: log.append(tr(text, lang, **kw))  # noqa: E731
    col_size = lambda g: list(cols.get(g, [inp["col_b"], inp["col_h"]]))  # noqa: E731

    def grow_col(g: str, db: float = 50, dh: float = 50) -> None:
        b, h = col_size(g)
        nb, nh = min(b + db, CAP_COL), min(h + dh, CAP_COL)
        if (nb, nh) != (b, h):
            cols[g] = [nb, nh]
            say("Column {g}: {a:g}×{b:g} → {c:g}×{d:g} mm", g=g, a=b, b=h, c=nb, d=nh)

    done: set[str] = set()
    slab = fb = False
    for mid, r in members.items():
        if r["ok"]:
            continue
        kind = r["kind"]
        if kind == "column":
            g = _grid(mid)
            if g not in done:
                done.add(g)
                grow_col(g)
        elif kind == "beam":
            key = _grid(mid)
            if key in done:
                continue
            done.add(key)
            b, h = beams.get(key, [inp["beam_b"], inp["beam_h"]])
            nb, nh = (b, h + 50) if h + 50 <= CAP_BEAM_H else (min(b + 50, CAP_BEAM_B), h)
            if (nb, nh) != (b, h):
                beams[key] = [nb, nh]
                say("Beam {g}: {a:g}×{b:g} → {c:g}×{d:g} mm", g=key, a=b, b=h, c=nb, d=nh)
        elif kind == "wall":
            g = _grid(mid)
            w = next((w for w in inp["walls"] if str(w["at"]).upper() == g), None)
            if w and g not in done:
                done.add(g)
                if w["t"] + 50 <= CAP_WALL_T:
                    say("Wall {g}: thickness {a:g} → {b:g} mm", g=g, a=w["t"], b=w["t"] + 50)
                    w["t"] += 50
                else:
                    say("Wall {g}: length {a:g} → {b:g} m", g=g, a=w["L"], b=w["L"] + 0.5)
                    w["L"] += 0.5
        elif kind == "slab" and not slab:
            slab = True
            if inp["slab_t"] + 20 <= CAP_SLAB:
                say("Slabs: thickness {a:g} → {b:g} mm", a=inp["slab_t"], b=inp["slab_t"] + 20)
                inp["slab_t"] += 20
        elif kind == "fbeam" and not fb:
            fb = True
            if inp["fb_h"] + 100 <= CAP_FB_H:
                say("Foundation beams: depth {a:g} → {b:g} mm", a=inp["fb_h"], b=inp["fb_h"] + 100)
                inp["fb_h"] += 100
            elif inp["fb_bw"] + 100 <= CAP_FB_BW:
                say("Foundation beams: web {a:g} → {b:g} mm", a=inp["fb_bw"], b=inp["fb_bw"] + 100)
                inp["fb_bw"] += 100
        elif kind == "footing" and "found" not in done:
            done.add("found")
            inp["found_type"] = "Foundation beams (Winkler)"
            say("Isolated footings do not suffice: foundation beams are used instead")
    for it in issues:
        t = it["type"]
        if t == "drift" and ("drift" + it["dir"]) not in done:
            done.add("drift" + it["dir"])
            key = "col_b" if it["dir"] == "X" else "col_h"
            if inp[key] + 50 <= CAP_COL:
                say("Storey drift in {d}: all columns {a:g} → {b:g} mm in {d}", d=it["dir"],
                    a=inp[key], b=inp[key] + 50)
                inp[key] += 50
                n = 0 if it["dir"] == "X" else 1
                for g, s in cols.items():
                    s[n] = min(s[n] + 50, CAP_COL)
        elif t == "joint" and it["grid"] not in done:
            done.add(it["grid"])
            grow_col(it["grid"])
        elif t == "modes" and "modes" not in done:
            done.add("modes")
            if inp["n_modes"] + 6 <= 60:
                say("Modes: {a} → {b}", a=inp["n_modes"], b=inp["n_modes"] + 6)
                inp["n_modes"] += 6
        elif t == "acr" and not inp.get("pdelta"):
            inp["pdelta"] = True
            say("α_cr < 10: P-Δ analysis switched on")
        elif t == "soil" and "soil" not in done:
            done.add("soil")
            if inp["fb_B"] + 0.2 <= CAP_FB_B:
                say("Foundation beams: flange {a:g} → {b:g} m", a=inp["fb_B"], b=inp["fb_B"] + 0.2)
                inp["fb_B"] = round(inp["fb_B"] + 0.2, 2)
    return log


def autosize(inputs: dict, project=None, lang: str = "en", max_rounds: int = 12) -> dict:
    """Run → adjust → run… Returns {"inputs", "log" (per round), "passed", "rounds",
    "max_utilisation", "failing"}."""
    mod = get_module("building_frame")
    inp = copy.deepcopy(inputs)
    defaults = mod.defaults()
    for k, v in defaults.items():
        inp.setdefault(k, copy.deepcopy(v))
    rounds: list[list[str]] = []
    calc = None
    for _ in range(max_rounds):
        try:
            calc = mod.calculate(inp, project, lang)
        except InputError as exc:
            return {"inputs": inp, "log": rounds, "passed": False, "rounds": len(rounds),
                    "error": str(exc), "failing": []}
        if calc.passed:
            break
        changes = _adjust(inp, calc, lang)
        if not changes:
            break
        rounds.append(changes)
    failing = [c.description for c in calc.checks if not c.passed] if calc else []
    return {"inputs": inp, "log": rounds, "passed": bool(calc and calc.passed),
            "rounds": len(rounds), "max_utilisation": calc.max_utilisation if calc else None,
            "failing": failing}
