"""Material quantities and a cost estimate for each calculation.

Quantities come from the actual geometry and the reinforcement chosen in the calculation.
Where the bar layout is not modelled in detail (walls, tanks) a typical reinforcement ratio is
used and stated.  Prices are editable per project (``ProjectInfo.prices``, JSON).
"""

from __future__ import annotations

import json
import math
from typing import Any, Callable

RHO_S = 7850.0  # kg/m³

# item -> (unit, default price €/unit, English label)
ITEMS: dict[str, tuple[str, float, str]] = {
    "concrete": ("m³", 130.0, "Concrete (supply and placing)"),
    "rebar": ("kg", 1.30, "Reinforcement (supply and fixing)"),
    "steel": ("kg", 3.20, "Structural steel (fabricated, erected)"),
    "timber": ("m³", 950.0, "Structural timber"),
    "masonry": ("m³", 160.0, "Masonry"),
    "gabion": ("m³", 95.0, "Gabions (baskets and stone)"),
    "formwork": ("m²", 25.0, "Formwork"),
    "excavation": ("m³", 12.0, "Excavation"),
    "drilling": ("m", 70.0, "Pile boring"),
    "anchor": ("m", 90.0, "Ground anchors (drilling, tendon, grout)"),
    "frp": ("m²", 120.0, "FRP wrapping (per layer)"),
}


def prices(project) -> dict[str, float]:
    out = {k: v[1] for k, v in ITEMS.items()}
    try:
        out.update({k: float(v) for k, v in json.loads(project.prices or "{}").items()
                    if k in out})
    except (ValueError, TypeError, AttributeError):
        pass
    return out


def _bar(d: float) -> float:
    return math.pi * d**2 / 4


def _kg(area_mm2: float, length_mm: float) -> float:
    return area_mm2 * length_mm * 1e-9 * RHO_S


Q = dict[str, float]
_FN: dict[str, Callable[[dict, Any], tuple[Q, str]]] = {}


def quantity(mid: str):
    def deco(fn):
        _FN[mid] = fn
        return fn
    return deco


def m3(*mm: float) -> float:
    v = 1.0
    for x in mm:
        v *= x / 1000
    return v


@quantity("ec7_pad_footing")
def _pad(i, c):
    Bx, By, h, D = i["Bx"], i["By"], i["h"], i["D"]
    Asx = _bar(float(i["dia_x"])) * By / i["s_x"]
    Asy = _bar(float(i["dia_y"])) * Bx / i["s_y"]
    return {"concrete": m3(Bx, By, h), "rebar": _kg(Asx, Bx) + _kg(Asy, By),
            "formwork": 2 * (Bx + By) * h / 1e6,
            "excavation": m3(Bx + 600, By + 600, D)}, "per footing"


@quantity("ec7_strip_footing")
def _strip(i, c):
    B, h, D = i["B"], i["h"], i["D"]
    As = _bar(float(i["dia"])) * 1000 / i["s"]
    return {"concrete": m3(B, h, 1000), "rebar": _kg(As, B) * 1.2, "formwork": 2 * h / 1e3,
            "excavation": m3(B + 600, D, 1000)}, "per metre run"


@quantity("ec2_rc_beam")
def _rcb(i, c):
    b, h = i["b"], i["h"]
    As = i["n_bars"] * _bar(float(i["dia"])) + i["n_comp"] * _bar(float(i["dia_comp"]))
    per = 2 * (b + h - 4 * i["cnom"])
    links = i["link_legs"] / 2 * _bar(float(i["link_dia"])) * per * 1000 / i["link_s"]
    return {"concrete": m3(b, h, 1000), "rebar": _kg(As, 1000) + _kg(links, 1),
            "formwork": (b + 2 * h) / 1e3}, "per metre"


@quantity("ec2_rc_column")
def _col(i, c):
    b, h, L = i["b"], i["h"], i["L"]
    n = 2 * i["nb"] + 2 * max(i["nh"] - 2, 0)
    As = n * _bar(float(i["dia"]))
    links = _bar(float(i["link"])) * 2 * (b + h) * L / i["s"]
    return {"concrete": m3(b, h, L), "rebar": _kg(As, L * 1.1) + _kg(links, 1),
            "formwork": 2 * (b + h) * L / 1e6}, "per column"


@quantity("ec2_rc_slab")
def _slab(i, c):
    lx = i["lx"]
    ly = i["ly"] if i["type"] == "Two-way panel" else lx * i["spans"]
    h = i["h"]
    Ab = _bar(float(i["dia_b"])) * 1000 / i["s_b"]
    At = _bar(float(i["dia_t"])) * 1000 / i["s_t"]
    area = lx * ly / 1e6
    return {"concrete": m3(lx, ly, h),
            "rebar": (2 * Ab + 0.6 * At) * 1e-6 * RHO_S * area,
            "formwork": area}, "per panel / slab"


@quantity("ec2_tank")
def _tank(i, c):
    Lx, Ly, H, t, tb, toe = i["Lx"], i["Ly"], i["H"], i["t"], i["tb"], i["toe"]
    walls = m3(2 * (Lx + Ly + 2 * t), t, H)
    base = m3(Lx + 2 * t + 2 * toe, Ly + 2 * t + 2 * toe, tb)
    return {"concrete": walls + base, "rebar": 110 * (walls + base),
            "formwork": 2 * 2 * (Lx + Ly + 2 * t) * H / 1e6,
            "excavation": m3(Lx + 2 * t + 2 * toe + 1000, Ly + 2 * t + 2 * toe + 1000,
                             tb + i["hs"])}, "per tank (rebar 110 kg/m³ assumed)"


def _wall(i, c, rate):
    from .core import get_module
    from .design.geotech import poly_props
    g = get_module(c.module_id).make_geometry(i)
    A = sum(poly_props(p)[0] for _, p in g.concrete) / 1e6  # m² per m
    return A, g


@quantity("ec7_retaining_wall")
def _rw(i, c):
    A, g = _wall(i, c, 80)
    return {"concrete": A, "rebar": 80 * A, "formwork": (2 * i["H_stem"] + 2 * i["t_base"]) / 1e3,
            "excavation": (g.B + 1000) / 1e3 * (g.top + 300) / 1e3 * 0.6},\
        "per metre run (rebar 80 kg/m³ assumed)"


@quantity("ec7_gravity_wall")
def _gw(i, c):
    A, g = _wall(i, c, 0)
    return {"concrete": A, "formwork": 2 * g.top / 1e3,
            "excavation": (g.B + 1000) / 1e3 * (g.top + 300) / 1e3 * 0.6}, "per metre run"


@quantity("ec7_gabion_wall")
def _gab(i, c):
    A, g = _wall(i, c, 0)
    return {"gabion": A, "excavation": (g.B + 1000) / 1e3 * (g.df + 300) / 1e3}, "per metre run"


@quantity("ec7_pile")
def _pile(i, c):
    D, L = i["D"], i["L"]
    As = i["nbar"] * _bar(float(i["dia"]))
    return {"concrete": math.pi * (D / 1000) ** 2 / 4 * L / 1000 * 1.05,
            "rebar": _kg(As, L) * 1.15, "drilling": L / 1000}, "per pile"


@quantity("ec7_embedded_wall")
def _emb(i, c):
    D, a, H, t = i["D"], i["a"], i["H"], i["t"]
    L = H + t
    n = 1000 / a
    As = i["nbar"] * _bar(float(i["dia"]))
    anchors = sum((r["Lfr"] + 6000) / r["sh"] for r in i["anchors"])
    return {"concrete": n * math.pi * (D / 1000) ** 2 / 4 * L / 1000 * 1.05,
            "rebar": n * _kg(As, L) * 1.15, "drilling": n * L / 1000, "anchor": anchors},\
        "per metre of wall (anchors: free length + 6 m bond)"


@quantity("ec7_berlin_wall")
def _berlin(i, c):
    from .sections.steel import get_section
    sec = get_section(i["section"])
    L = i["H"] + i["t"]
    return {"steel": sec.mass * L / 1000 * 1000 / i["a"], "timber": m3(i["H"], i["t_lag"], 1000),
            "drilling": L / i["a"],
            "anchor": 14000 / i["a"] if i["support"] != "Cantilever" else 0.0},\
        "per metre of wall (anchor length 14 m assumed)"


@quantity("ec3_steel_beam")
def _sb(i, c):
    from .sections.steel import get_section
    return {"steel": get_section(i["section"]).mass * i["L"] / 1000 * 1.05}, "per beam (+5 % connections)"


@quantity("ec3_steel_column")
def _sc(i, c):
    from .sections.steel import get_section
    return {"steel": get_section(i["section"]).mass * i["L"] / 1000 * 1.05}, "per column (+5 % connections)"


@quantity("ec3_base_plate")
def _bp(i, c):
    return {"steel": m3(i["bp"], i["lp"], i["tp"]) * RHO_S + 4 * i["nt"] * 0.5 *
            _bar(float(i["d"][1:])) * 1e-6 * RHO_S, "concrete": 0.0}, "per base"


@quantity("ec5_timber_beam")
def _tb(i, c):
    return {"timber": m3(i["b"], i["h"], i["L"])}, "per beam"


@quantity("ec6_masonry_wall")
def _mw(i, c):
    return {"masonry": m3(i["t"], i["h"], i["lw"])}, "per wall"


@quantity("ec8_3_assessment")
def _ass(i, c):
    L = 2 * i["Lv"]
    if i["strengthen"] == "RC jacket":
        b2, h2 = i["b"] + 2 * i["tj"], i["h"] + 2 * i["tj"]
        conc = m3(b2, h2, L) - m3(i["b"], i["h"], L)
        n = 4 * (i["nbj"] - 1)
        links = _bar(i["dhj"]) * 2 * (b2 + h2) * L / i["shj"]
        return {"concrete": conc, "rebar": _kg(n * _bar(i["diaj"]), L) + _kg(links, 1),
                "formwork": 2 * (b2 + h2) * L / 1e6}, "per member"
    if i["strengthen"] == "FRP wrapping":
        return {"frp": i["nf"] * 2 * (i["b"] + i["h"]) * L / 1e6}, "per member"
    return {}, ""


def estimate(calc, inputs: dict) -> dict | None:
    fn = _FN.get(calc.module_id)
    if not fn:
        return None
    try:
        q, basis = fn(inputs, calc)
    except Exception:  # noqa: BLE001 — quantities must never break a calculation
        return None
    q = {k: float(v) for k, v in q.items() if v and v > 1e-9}
    if not q:
        return None
    pr = prices(calc.project)
    rows = [{"item": k, "unit": ITEMS[k][0], "qty": v, "price": pr[k], "cost": v * pr[k]}
            for k, v in q.items()]
    return {"basis": calc.tr(basis) if basis else "", "rows": rows,
            "total": sum(r["cost"] for r in rows)}


def record(calc, inputs: dict) -> None:
    """Attach the estimate to the calculation and add a table to the report."""
    est = estimate(calc, inputs)
    calc.quantities = est
    if not est:
        return
    calc.heading("Quantities and cost estimate")
    calc.table(["Item", "Quantity", "Unit price", "Cost"],
               [[calc.tr(ITEMS[r["item"]][2]), f"{r['qty']:.2f} {r['unit']}",
                 f"{r['price']:.2f} €/{r['unit']}", f"{r['cost']:.0f} €"] for r in est["rows"]]
               + [[calc.tr("Total"), "", "", f"{est['total']:.0f} €"]],
               caption=calc.tr("Estimate {b} — prices editable in the project details",
                               b=est["basis"]))
