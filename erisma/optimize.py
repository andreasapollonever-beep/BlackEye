"""Automatic design: search the design variables of a calculation for the cheapest design that
passes every check (cost from :mod:`erisma.quantities`).

Small searches are exhaustive; larger ones use coordinate descent (one variable at a time over
its whole range, repeated until nothing improves) starting from the user's design.
"""

from __future__ import annotations

import itertools
import math
import time
from typing import Any

from .core import InputError, get_module

# module -> variables: {"name", "lo", "hi", "step"} (display units) or {"name", "choices"}
SPECS: dict[str, list[dict[str, Any]]] = {
    "ec7_pad_footing": [{"name": "Bx", "lo": 1.0, "hi": 5.0, "step": 0.1},
                        {"name": "By", "lo": 1.0, "hi": 5.0, "step": 0.1},
                        {"name": "h", "lo": 0.3, "hi": 1.5, "step": 0.05}],
    "ec7_strip_footing": [{"name": "B", "lo": 0.5, "hi": 4.0, "step": 0.05},
                          {"name": "h", "lo": 0.25, "hi": 1.2, "step": 0.05}],
    "ec7_retaining_wall": [{"name": "toe", "lo": 0.3, "hi": 3.0, "step": 0.1},
                           {"name": "heel", "lo": 0.5, "hi": 5.0, "step": 0.1},
                           {"name": "t_base", "lo": 0.3, "hi": 1.2, "step": 0.05},
                           {"name": "t_bot", "lo": 0.25, "hi": 0.8, "step": 0.05}],
    "ec7_gravity_wall": [{"name": "B_body", "lo": 0.6, "hi": 4.0, "step": 0.1},
                         {"name": "toe", "lo": 0.0, "hi": 2.0, "step": 0.1},
                         {"name": "heel", "lo": 0.0, "hi": 2.0, "step": 0.1}],
    "ec2_rc_beam": [{"name": "h", "lo": 250, "hi": 1200, "step": 25},
                    {"name": "n_bars", "lo": 2, "hi": 8, "step": 1},
                    {"name": "dia", "choices": ["12", "14", "16", "20", "25"]}],
    "ec2_rc_column": [{"name": "b", "lo": 250, "hi": 800, "step": 50},
                      {"name": "h", "lo": 250, "hi": 800, "step": 50},
                      {"name": "dia", "choices": ["14", "16", "20", "25"]}],
    "ec2_rc_slab": [{"name": "h", "lo": 120, "hi": 350, "step": 10},
                    {"name": "s_b", "lo": 100, "hi": 250, "step": 25},
                    {"name": "s_t", "lo": 100, "hi": 250, "step": 25}],
    "ec2_tank": [{"name": "t", "lo": 150, "hi": 500, "step": 25},
                 {"name": "s_i", "lo": 75, "hi": 250, "step": 25},
                 {"name": "s_o", "lo": 75, "hi": 250, "step": 25}],
    "ec7_pile": [{"name": "D", "lo": 0.4, "hi": 1.5, "step": 0.1},
                 {"name": "L", "lo": 5.0, "hi": 40.0, "step": 0.5}],
    "ec7_embedded_wall": [{"name": "t", "lo": 1.0, "hi": 15.0, "step": 0.25},
                          {"name": "D", "lo": 0.4, "hi": 1.2, "step": 0.1}],
    "ec7_berlin_wall": [{"name": "section", "choices": "*"},
                        {"name": "t", "lo": 1.0, "hi": 10.0, "step": 0.25}],
    "ec3_steel_beam": [{"name": "section", "choices": "*"}],
    "ec3_steel_column": [{"name": "section", "choices": "*"}],
    "ec3_base_plate": [{"name": "tp", "lo": 10, "hi": 60, "step": 2}],
    "ec5_timber_beam": [{"name": "h", "lo": 100, "hi": 1200, "step": 20},
                        {"name": "b", "lo": 60, "hi": 300, "step": 20}],
    "ec6_masonry_wall": [{"name": "t", "lo": 100, "hi": 450, "step": 25}],
    "ec8_3_assessment": [{"name": "tj", "lo": 60, "hi": 250, "step": 10},
                         {"name": "shj", "lo": 50, "hi": 200, "step": 25}],
}


def spec(module_id: str) -> list[dict]:
    mod = get_module(module_id)
    fields = {f.name: f for f in mod.fields}
    out = []
    for v in SPECS.get(module_id, []):
        f = fields.get(v["name"])
        if f is None:
            continue
        d = dict(v)
        if v.get("choices") == "*":
            d["choices"] = list(f.choices or [])
        d.update(label=f.label, unit=f.unit, kind=f.kind)
        out.append(d)
    return out


def _values(v: dict) -> list:
    if v.get("choices"):
        return list(v["choices"])
    lo, hi, st = float(v["lo"]), float(v["hi"]), float(v["step"])
    n = max(int(math.floor((hi - lo) / st + 1e-9)) + 1, 1)
    vals = [round(lo + i * st, 10) for i in range(min(n, 400))]
    return [int(x) for x in vals] if v.get("kind") == "int" else vals


def optimise(module_id: str, inputs: dict, project: dict, variables: list[dict],
             lang: str = "en", budget: int = 2500, time_limit: float = 40.0) -> dict[str, Any]:
    mod = get_module(module_id)
    cache: dict[tuple, tuple] = {}
    t0 = time.time()
    names = [v["name"] for v in variables]

    def evaluate(assign: dict) -> tuple:
        key = tuple(assign[n] for n in names)
        if key in cache:
            return cache[key]
        trial = {**inputs, **assign}
        try:
            c = mod.calculate(trial, project, lang)
            cost = c.quantities["total"] if c.quantities else math.inf
            res = (c.passed, cost, c.max_utilisation)
        except (InputError, ValueError, ZeroDivisionError, ArithmeticError):
            res = (False, math.inf, math.inf)
        cache[key] = res
        return res

    def better(a, b) -> bool:  # feasible first, then cost, then lower utilisation
        if a[0] != b[0]:
            return a[0]
        if a[1] != b[1]:
            return a[1] < b[1]
        return a[2] < b[2]

    grids = [_values(v) for v in variables]
    start = {n: inputs.get(n, get_default(mod, n)) for n in names}
    base = evaluate(start)
    best_a, best = dict(start), base
    total = math.prod(len(g) for g in grids)
    if total <= budget:
        for combo in itertools.product(*grids):
            if time.time() - t0 > time_limit:
                break
            a = dict(zip(names, combo))
            r = evaluate(a)
            if better(r, best):
                best_a, best = a, r
        method = "exhaustive"
    else:
        method = "coordinate descent"
        for _ in range(5):
            improved = False
            for n, g in zip(names, grids):
                for val in g:
                    if time.time() - t0 > time_limit or len(cache) > budget * 3:
                        break
                    a = {**best_a, n: val}
                    r = evaluate(a)
                    if better(r, best):
                        best_a, best, improved = a, r, True
            if not improved:
                break
    return {"best": best_a, "start": start, "passed": best[0], "cost": _f(best[1]),
            "util": _f(best[2]), "start_passed": base[0], "start_cost": _f(base[1]),
            "start_util": _f(base[2]), "evaluations": len(cache), "method": method,
            "seconds": round(time.time() - t0, 1)}


def _f(x: float):
    return None if not math.isfinite(x) else float(x)


def get_default(mod, name):
    for f in mod.fields:
        if f.name == name:
            return f.default
    return None
