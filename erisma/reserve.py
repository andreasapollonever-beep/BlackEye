"""Reserve factor λ on the loads and inverse solution on any input.

* **Reserve factor** — the chosen loads (permanent G, variable Q, seismic E or design actions)
  are multiplied by λ and the *whole* calculation is run again; λ is the largest factor for
  which every load-dependent check still passes.  Checks whose utilisation does not change
  with the loads (minimum reinforcement, detailing) are reported separately and do not limit λ.
* **Inverse solution** — one input is varied over its range and the interval of values for
  which all checks pass is found (e.g. the lowest concrete strength, the longest span, the
  highest water table).

Both searches scan first (so that a non-monotonic response is not missed) and then refine the
boundary by bisection.  Every result carries its own verification: the calculation at the
boundary value passes, the calculation just beyond it fails, with the governing check named.
"""

from __future__ import annotations

import math
import time
from typing import Any, Callable

from .core import InputError, get_module

G, Q, E, A = "G", "Q", "E", "A"
GROUP_LABELS = {G: "Permanent loads G", Q: "Variable loads Q", E: "Seismic action E",
                A: "Design actions (all)"}

# module -> [(field, group)] or [("table.column", group)]; only applied loads / actions.
LOADS: dict[str, list[tuple[str, str]]] = {
    "ec2_pile_cap": [("NEd", A), ("Mx", A), ("My", A)],
    "ec2_rc_beam": [("MEd", A), ("VEd", A)],
    "ec2_beam_opening": [("gk", G), ("qk", Q), ("MEd", A), ("VEd", A), ("cases.M", A),
                         ("cases.V", A)],
    "ec2_rc_column": [("NEd", A), ("Mh_top", A), ("Mh_bot", A), ("Mb_top", A), ("Mb_bot", A),
                      ("VEd", A)],
    "ec8_rc_wall": [("NEd", A), ("MEd", A), ("VEd", A)],
    "ec2_rc_slab": [("g", G), ("q", Q), ("VEd", A)],
    "ec2_rc_stair": [("g", G), ("q", Q)],
    "ec2_tank": [("q", Q)],
    "ec8_3_assessment": [("N", A), ("VE", E), ("thE_NC", E), ("thE_SD", E), ("thE_DL", E)],
    "ec5_fire": [("g", G), ("q", Q)],
    "ec7_berlin_wall": [("q", Q), ("ag", E)],
    "ec7_retaining_wall": [("q", Q), ("ag", E)],
    "ec7_embedded_wall": [("q", Q), ("ag", E)],
    "ec7_settlement": [("q", A)],
    "ec7_gabion_wall": [("q", Q), ("ag", E)],
    "ec7_gravity_wall": [("q", Q), ("ag", E)],
    "ec8_5_liquefaction": [("ag", E)],
    "ec7_pad_footing": [("NG", G), ("MxG", G), ("MyG", G), ("HxG", G), ("NQ", Q), ("MxQ", Q),
                        ("MyQ", Q), ("HxQ", Q), ("NE", E), ("MxE", E), ("MyE", E), ("HxE", E)],
    "ec7_raft": [("N", A), ("Nk", A)],
    "ec7_pile": [("G", G), ("HG", G), ("Q", Q), ("T", Q), ("HQ", Q)],
    "ec7_slope_stability": [("q", Q), ("ag", E)],
    "ec7_strip_footing": [("NG", G), ("MG", G), ("HG", G), ("NQ", Q), ("MQ", Q), ("HQ", Q),
                          ("NE", E), ("ME", E), ("HE", E), ("N1", A), ("N2", A)],
    "ec6_masonry_wall": [("NEd", A), ("VEd", A)],
    "ec3_bolted_connection": [("V", A), ("Ft", A)],
    "ec3_base_plate": [("NEd", A), ("MEd", A), ("VEd", A)],
    "ec3_weld": [("N", A), ("V", A), ("M", A)],
    "ec3_steel_beam": [("gk", G), ("Gk_pt", G), ("qk", Q), ("Qk_pt", Q)],
    "ec3_steel_column": [("NEd", A), ("My_top", A), ("My_bot", A), ("Mz_top", A),
                         ("Mz_bot", A), ("VEd", A)],
    "ec5_timber_beam": [("g", G), ("q", Q)],
}

SCAN = 16          # points of the first scan
BISECT = 40        # maximum bisection steps
TOL = 1e-4         # relative width of the final bracket (λ to 4 significant decimals)
TIME_LIMIT = 40.0  # seconds


class Evaluator:
    """Runs the module on modified inputs and summarises the checks."""

    def __init__(self, module_id: str, inputs: dict, project: dict, lang: str = "en"):
        self.mod = get_module(module_id)
        self.base = {**self.mod.defaults(), **(inputs or {})}
        self.project = project or {}
        self.lang = lang
        self.calls = 0
        self.t0 = time.time()

    def run(self, inputs: dict) -> dict:
        self.calls += 1
        try:
            c = self.mod.calculate(inputs, self.project, self.lang)
        except InputError as exc:
            return {"error": str(exc), "field": exc.field, "checks": []}
        except (ValueError, ZeroDivisionError, ArithmeticError) as exc:
            return {"error": str(exc), "field": None, "checks": []}
        return {"error": None, "checks": [(k.description, k.utilisation, k.ref or "")
                                          for k in c.checks]}

    def out_of_time(self) -> bool:
        return time.time() - self.t0 > TIME_LIMIT


def _keyed(checks):
    seen: dict[str, int] = {}
    out = {}
    for desc, u, ref in checks:
        n = seen.get(desc, 0)
        seen[desc] = n + 1
        out[(desc, n)] = (u, ref)
    return out


def _search(passes: Callable[[float], bool], lo: float, hi: float, scan: int = SCAN,
            stop: Callable[[], bool] = lambda: False) -> tuple[float, float] | None:
    """First change from passing to failing in [lo, hi] — scan, then bisect.

    ``passes(lo)`` must be True.  Returns (last passing, first failing) or None if every scanned
    point passes.
    """
    prev = lo
    for i in range(1, scan + 1):
        x = lo + (hi - lo) * i / scan
        if not passes(x):
            a, b = prev, x
            for _ in range(BISECT):
                if stop() or abs(b - a) <= TOL * max(abs(b), 1e-9):
                    break
                m = (a + b) / 2
                if passes(m):
                    a = m
                else:
                    b = m
            return a, b
        prev = x
        if stop():
            break
    return None


# ------------------------------------------------------------------- reserve
def scaled(base: dict, fields: list[str], lam: float) -> dict:
    out = dict(base)
    for f in fields:
        if "." in f:
            t, col = f.split(".", 1)
            out[t] = [{**r, col: (r.get(col) or 0) * lam} for r in (out.get(t) or [])]
        else:
            out[f] = (out.get(f) or 0) * lam
    return out


def reserve(module_id: str, inputs: dict, project: dict, groups: list[str],
            lang: str = "en") -> dict[str, Any]:
    spec = LOADS.get(module_id)
    if not spec:
        raise ValueError("This calculation has no loads to scale")
    fields = [f for f, g in spec if g in groups]
    if not fields:
        raise ValueError("Choose at least one kind of load")
    ev = Evaluator(module_id, inputs, project, lang)
    r1 = ev.run(ev.base)
    if r1["error"]:
        raise ValueError(r1["error"])
    k1 = _keyed(r1["checks"])
    # load-dependent checks: utilisation changes when the loads change
    probe = ev.run(scaled(ev.base, fields, 1.5))
    kp = _keyed(probe["checks"]) if not probe["error"] else {}
    dep = {k for k, (u, _) in k1.items()
           if k not in kp or abs(kp[k][0] - u) > 1e-9 * max(1.0, abs(u))}
    fixed = [(k[0], u) for k, (u, _) in k1.items() if k not in dep]
    if not dep:
        raise ValueError("No check of this calculation depends on the chosen loads")

    def summary(lam):
        r = ev.run(scaled(ev.base, fields, lam))
        if r["error"]:
            return {"ok": False, "umax": math.inf, "gov": r["error"], "ref": "", "error": True}
        kk = _keyed(r["checks"])
        items = [(u, k[0], ref) for k, (u, ref) in kk.items() if k in dep or k not in k1]
        if not items:
            return {"ok": True, "umax": 0.0, "gov": "", "ref": "", "error": False}
        u, desc, ref = max(items)
        return {"ok": u <= 1.0 + 1e-9, "umax": u, "gov": desc, "ref": ref, "error": False}

    cache: dict[float, dict] = {}

    def s(lam):
        if lam not in cache:
            cache[lam] = summary(lam)
        return cache[lam]

    def passes(lam):
        return s(lam)["ok"]

    curve = []
    if passes(1.0):
        lo, hi = 1.0, 2.0
        while passes(hi) and hi < 1000 and not ev.out_of_time():
            lo, hi = hi, hi * 2
        if passes(hi):
            res = {"lam": None, "beyond": hi}
        else:
            br = _search(passes, lo, hi, stop=ev.out_of_time) or (lo, hi)
            res = {"lam": br[0], "fail": br[1]}
        # also confirm that nothing fails below 1 (it passes at 1 by definition)
    else:
        br = None
        # failing now: largest passing λ in (0, 1)
        lo = 1e-3
        if not passes(lo):
            raise ValueError("The calculation fails even with almost no load — the limit is "
                             "not caused by these loads")
        br = _search(passes, lo, 1.0, stop=ev.out_of_time) or (lo, 1.0)
        res = {"lam": br[0], "fail": br[1]}
    for lam in sorted(cache):
        v = cache[lam]
        curve.append({"lam": lam, "umax": None if math.isinf(v["umax"]) else v["umax"],
                      "gov": v["gov"]})
    out: dict[str, Any] = {"fields": fields, "groups": groups, "fixed": fixed,
                           "evaluations": ev.calls, "seconds": round(time.time() - ev.t0, 2),
                           "curve": curve}
    if res.get("lam") is None:
        out.update(lam=None, beyond=res["beyond"])
        return out
    at, beyond = s(res["lam"]), s(res["fail"])
    out.update(lam=res["lam"], lam_fail=res["fail"],
               verify={"at": {"lam": res["lam"], "umax": at["umax"], "gov": at["gov"]},
                       "beyond": {"lam": res["fail"], "umax": None if math.isinf(beyond["umax"])
                                  else beyond["umax"], "gov": beyond["gov"],
                                  "ref": beyond["ref"], "error": beyond["error"]}},
               governing=beyond["gov"], ref=beyond["ref"], limit_is_error=beyond["error"])
    return out


# ------------------------------------------------------------------- inverse
def inverse(module_id: str, inputs: dict, project: dict, field: str,
            lang: str = "en") -> dict[str, Any]:
    ev = Evaluator(module_id, inputs, project, lang)
    f = next((x for x in ev.mod.fields if x.name == field), None)
    if f is None:
        raise ValueError("Unknown input")
    cur = ev.base.get(field)
    first = ev.run(ev.base)
    if not first["error"] and not first["checks"]:
        raise ValueError("This calculation has no checks — there is nothing to solve for")

    def summary(v):
        r = ev.run({**ev.base, field: v})
        if r["error"]:
            return {"ok": False, "umax": None, "gov": r["error"], "error": True}
        if not r["checks"]:
            return {"ok": True, "umax": 0.0, "gov": "", "error": False}
        u, desc, ref = max((u, d, rf) for d, u, rf in r["checks"])
        return {"ok": u <= 1.0 + 1e-9, "umax": u, "gov": desc, "ref": ref, "error": False}

    if f.kind == "choice":
        rows = [{"value": c, **summary(c)} for c in f.choices]
        return {"field": field, "kind": "choice", "current": cur, "rows": rows,
                "passing": [r["value"] for r in rows if r["ok"]],
                "evaluations": ev.calls}
    if f.kind not in ("float", "int"):
        raise ValueError("Only numeric or choice inputs can be solved for")
    cur = float(cur)
    lo_lim = f.min if f.min is not None else (0.0 if cur >= 0 else cur * 10)
    hi_lim = f.max if f.max is not None else (abs(cur) * 10 if cur else 10.0)
    if f.kind == "int":
        vals = list(range(int(math.ceil(lo_lim)), int(math.floor(hi_lim)) + 1))
        if len(vals) > 200:
            vals = vals[:200]
        rows = [{"value": v, **summary(v)} for v in vals]
        ok = [r["value"] for r in rows if r["ok"]]
        return {"field": field, "kind": "int", "current": cur,
                "min_pass": min(ok) if ok else None, "max_pass": max(ok) if ok else None,
                "rows": rows, "evaluations": ev.calls}
    cache: dict[float, dict] = {}

    def s(v):
        if v not in cache:
            cache[v] = summary(v)
        return cache[v]

    def passes(v):
        return s(v)["ok"]

    start = cur
    if not passes(start):  # find a passing value on a coarse grid first
        grid = [lo_lim + (hi_lim - lo_lim) * i / 40 for i in range(41)]
        okv = [v for v in grid if passes(v)]
        if not okv:
            return {"field": field, "kind": "float", "current": cur, "low": None, "high": None,
                    "message": "No value in the range of this input makes every check pass",
                    "evaluations": ev.calls}
        start = min(okv, key=lambda v: abs(v - cur))
    up = _search(passes, start, hi_lim, scan=SCAN, stop=ev.out_of_time)
    # downward: search on the mirrored variable
    down = _search(lambda t: passes(start - t), 0.0, start - lo_lim, scan=SCAN,
                   stop=ev.out_of_time) if start > lo_lim else None

    def bound(br, sign):
        if br is None:
            return None
        a, b = (br if sign > 0 else (start - br[0], start - br[1]))
        sa, sb = s(a), s(b)
        lim = hi_lim if sign > 0 else lo_lim
        range_end = sb["error"] and abs(b - lim) <= 1e-6 * max(1.0, abs(lim)) + abs(b - a)
        return {"value": a, "fail_at": b, "umax": sa["umax"], "gov": sb["gov"],
                "umax_beyond": sb["umax"], "error": sb["error"], "range_end": bool(range_end)}
    return {"field": field, "kind": "float", "current": cur, "start": start,
            "low": bound(down, -1), "high": bound(up, 1), "range": [lo_lim, hi_lim],
            "evaluations": ev.calls, "seconds": round(time.time() - ev.t0, 2)}


def spec(module_id: str) -> dict[str, Any]:
    mod = get_module(module_id)
    groups = sorted({g for _, g in LOADS.get(module_id, [])}, key="GQEA".index)
    fields = [{"name": f.name, "label": f.label, "unit": f.unit, "kind": f.kind}
              for f in mod.fields if f.kind in ("float", "int", "choice")]
    return {"groups": groups, "group_labels": {g: GROUP_LABELS[g] for g in groups},
            "fields": fields}
