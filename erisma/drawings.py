"""DXF drawings (plan / section with reinforcement and dimensions) for the main modules."""

from __future__ import annotations

import math
from typing import Callable

from .dxf import Drawing

_FN: dict[str, Callable] = {}


def drawing(mid: str):
    def deco(fn):
        _FN[mid] = fn
        return fn
    return deco


def supported(mid: str) -> bool:
    return mid in _FN


def _title(d: Drawing, calc, x: float, y: float, extra: str = "") -> None:
    p = calc.project
    d.title(x, y, [calc.title, f"{p.project}  {p.section}".strip(),
                   f"{p.company}  {p.job_no}  {p.date}".strip(),
                   extra or calc.standard])


@drawing("ec7_pad_footing")
def _pad(i, calc):
    d = Drawing()
    Bx, By, h, D, cx, cy = i["Bx"], i["By"], i["h"], i["D"], i["cx"], i["cy"]
    c = i["cover"]
    tr = calc.tr
    # plan
    d.rect(-Bx / 2, -By / 2, Bx, By)
    d.rect(-cx / 2, -cy / 2, cx, cy, "STEEL")
    sx, sy = i["s_x"], i["s_y"]
    y = -By / 2 + c
    while y <= By / 2 - c + 1e-6:
        d.line((-Bx / 2 + c, y), (Bx / 2 - c, y), "REBAR")
        y += sy
    x = -Bx / 2 + c
    while x <= Bx / 2 - c + 1e-6:
        d.line((x, -By / 2 + c), (x, By / 2 - c), "REBAR")
        x += sx
    d.dim((-Bx / 2, -By / 2), (Bx / 2, -By / 2), -250)
    d.dim((Bx / 2, -By / 2), (Bx / 2, By / 2), -250)
    d.text((0, By / 2 + 200), tr("PLAN"), 80, center=True)
    d.text((-Bx / 2, -By / 2 - 600), f"X: Ø{i['dia_x']}/{sx:.0f}   Y: Ø{i['dia_y']}/{sy:.0f}", 60,
           "REBAR")
    # section A-A (below the plan)
    oy = -By / 2 - 1600 - D
    d.line((-Bx / 2 - 600, oy + D), (Bx / 2 + 600, oy + D), "SOIL")
    d.rect(-Bx / 2, oy, Bx, h)
    d.rect(-cx / 2, oy + h, cx, D - h + 400, "STEEL")
    dia = float(i["dia_x"])
    d.bar_line((-Bx / 2 + c, oy + c + dia / 2), (Bx / 2 - c, oy + c + dia / 2),
               f"Ø{i['dia_x']}/{sx:.0f}")
    xx = -Bx / 2 + c
    while xx <= Bx / 2 - c + 1e-6:
        d.circle((xx, oy + c + dia * 1.5), float(i["dia_y"]) / 2)
        xx += sy
    d.dim((-Bx / 2, oy), (Bx / 2, oy), -250)
    d.dim((Bx / 2, oy), (Bx / 2, oy + h), -250)
    d.dim((-Bx / 2, oy), (-Bx / 2, oy + D), 400, f"D = {D:.0f}")
    d.text((0, oy + D + 600), tr("SECTION A-A"), 80, center=True)
    _title(d, calc, Bx / 2 + 1200, oy)
    return d


@drawing("ec7_strip_footing")
def _strip(i, calc):
    d = Drawing()
    B, h, D, bw, c = i["B"], i["h"], i["D"], i["bw"], i["cover"]
    d.line((-B / 2 - 800, D), (B / 2 + 800, D), "SOIL")
    d.rect(-B / 2, 0, B, h)
    d.rect(-bw / 2, h, bw, D - h + 600, "CONCRETE")
    dia = float(i["dia"])
    d.bar_line((-B / 2 + c, c + dia / 2), (B / 2 - c, c + dia / 2), f"Ø{i['dia']}/{i['s']:.0f}")
    x = -B / 2 + c
    while x <= B / 2 - c + 1e-6:
        d.circle((x, c + dia * 1.5), 6)
        x += 200
    d.dim((-B / 2, 0), (B / 2, 0), -250)
    d.dim((B / 2, 0), (B / 2, h), -250)
    d.dim((-B / 2, 0), (-B / 2, D), 400, f"D = {D:.0f}")
    d.text((0, D + 900), calc.tr("SECTION"), 80, center=True)
    _title(d, calc, B / 2 + 1200, 0)
    return d


def _wall_dwg(i, calc, bars: bool):
    from .core import get_module
    d = Drawing()
    g = get_module(calc.module_id).make_geometry(i)
    for _, poly in g.concrete:
        d.poly(poly)
    far = g.B + 2500
    d.line((g.B, g.zs(g.B)), (far, g.zs(far)), "SOIL")
    d.line((g.x0, g.top), (g.B, g.zs(g.B)), "SOIL")
    d.line((-1500, g.tb + g.df), (g.x_front, g.tb + g.df), "SOIL")
    d.dim((0, 0), (g.B, 0), -300)
    d.dim((g.B, 0), (g.B, g.top), -(far - g.B) - 300 + 2500)
    if bars and calc.module_id == "ec7_retaining_wall":
        c = i["cover_stem"]
        xb = g.back_face[-1][0] - c
        d.bar_line((xb, g.tb - i["cover_base"] + 0), (g.back_face[0][0] - c, g.top - 50),
                   None)
        d.bar_line((i["cover_base"], g.tb - i["cover_base"]), (g.B - i["cover_base"],
                                                                g.tb - i["cover_base"]))
        d.bar_line((i["cover_base"], i["cover_base"]), (g.B - i["cover_base"], i["cover_base"]))
        d.text((xb - 200, g.top / 2), f"Ø{i.get('stem_dia', '')}/{i['stem_s']:.0f}", 55, "REBAR",
               90)
    d.text((g.B / 2, g.top + 700), calc.tr("SECTION"), 80, center=True)
    _title(d, calc, far + 500, 0)
    return d


@drawing("ec7_retaining_wall")
def _rw(i, calc):
    return _wall_dwg(i, calc, True)


@drawing("ec7_gravity_wall")
def _gw(i, calc):
    return _wall_dwg(i, calc, False)


@drawing("ec7_gabion_wall")
def _gab(i, calc):
    return _wall_dwg(i, calc, False)


def _section(d, b, h, cov, link, bars, x0=0.0, y0=0.0):
    d.rect(x0 - b / 2, y0, b, h)
    o = cov + link / 2
    d.rect(x0 - b / 2 + o, y0 + o, b - 2 * o, h - 2 * o, "REBAR")
    for (x, y, dia) in bars:
        d.circle((x0 + x, y0 + y), dia / 2)
    d.dim((x0 - b / 2, y0), (x0 + b / 2, y0), -200)
    d.dim((x0 + b / 2, y0), (x0 + b / 2, y0 + h), -200)


@drawing("ec2_rc_beam")
def _rcb(i, calc):
    d = Drawing()
    b, h, c = i["b"], i["h"], i["cnom"]
    dl, dia, dia2 = float(i["link_dia"]), float(i["dia"]), float(i["dia_comp"])
    n, n2 = i["n_bars"], i["n_comp"]
    o = c + dl + dia / 2
    bars = [(-b / 2 + o + k * (b - 2 * o) / max(n - 1, 1), o, dia) for k in range(n)]
    o2 = c + dl + dia2 / 2
    bars += [(-b / 2 + o2 + k * (b - 2 * o2) / max(n2 - 1, 1), h - o2, dia2) for k in range(n2)]
    _section(d, b, h, c, dl, bars)
    d.text((0, -450), f"{n}Ø{dia:g} + {n2}Ø{dia2:g}  —  Ø{dl:g}/{i['link_s']:.0f}", 45, "REBAR",
           center=True)
    d.text((0, h + 200), calc.tr("SECTION"), 70, center=True)
    _title(d, calc, b / 2 + 600, 0)
    return d


@drawing("ec2_rc_column")
def _col(i, calc):
    d = Drawing()
    b, h, c = i["b"], i["h"], i["cover"]
    dl, dia = float(i["link"]), float(i["dia"])
    o = c + dl + dia / 2
    bars = []
    for k in range(i["nb"]):
        x = -b / 2 + o + k * (b - 2 * o) / (i["nb"] - 1)
        bars += [(x, o, dia), (x, h - o, dia)]
    for k in range(1, i["nh"] - 1):
        y = o + k * (h - 2 * o) / (i["nh"] - 1)
        bars += [(-b / 2 + o, y, dia), (b / 2 - o, y, dia)]
    _section(d, b, h, c, dl, bars)
    d.text((0, -450), f"{len(bars)}Ø{dia:g}  —  Ø{dl:g}/{i['s']:.0f}", 45, "REBAR", center=True)
    d.text((0, h + 200), calc.tr("SECTION"), 70, center=True)
    _title(d, calc, b / 2 + 600, 0)
    return d


@drawing("ec7_pile")
def _pile(i, calc):
    d = Drawing()
    D, L = i["D"], i["L"]
    d.rect(-D / 2, -L, D, L)
    d.line((-3 * D, 0), (3 * D, 0), "SOIL")
    top = 0.0
    for r in i["layers"]:
        top -= r["h"]
        if -top > L + 3000:
            break
        d.line((-3 * D, top), (3 * D, top), "SOIL")
        d.text((1.6 * D, top + r["h"] / 2), f"{calc.tr(r['soil'])}", 60, "SOIL")
    d.dim((-D / 2, -L), (-D / 2, 0), 400, f"L = {L:.0f}")
    # section
    n, dia = i["nbar"], float(i["dia"])
    cx, cy = 3.5 * D, -D
    d.circle((cx, cy), D / 2, "CONCRETE")
    rs = D / 2 - i["cover"]
    for k in range(n):
        a = 2 * math.pi * k / n
        d.circle((cx + rs * math.cos(a), cy + rs * math.sin(a)), dia / 2)
    d.circle((cx, cy), rs + dia / 2 + 5, "REBAR")
    d.text((cx, cy - D / 2 - 200), f"Ø{D:.0f} — {n}Ø{dia:g}", 55, "REBAR", center=True)
    _title(d, calc, 2 * D, -L)
    return d


@drawing("ec2_tank")
def _tank(i, calc):
    d = Drawing()
    Lx, Ly, H, t, tb, toe = i["Lx"], i["Ly"], i["H"], i["t"], i["tb"], i["toe"]
    # plan
    d.rect(-Lx / 2 - t, -Ly / 2 - t, Lx + 2 * t, Ly + 2 * t)
    d.rect(-Lx / 2, -Ly / 2, Lx, Ly)
    d.rect(-Lx / 2 - t - toe, -Ly / 2 - t - toe, Lx + 2 * t + 2 * toe, Ly + 2 * t + 2 * toe, "AXIS")
    d.dim((-Lx / 2, -Ly / 2), (Lx / 2, -Ly / 2), 300)
    d.dim((Lx / 2, -Ly / 2), (Lx / 2, Ly / 2), 300)
    d.text((0, Ly / 2 + t + 400), calc.tr("PLAN"), 100, center=True)
    # section
    oy = -Ly / 2 - t - toe - 2500 - H
    W = Lx + 2 * t + 2 * toe
    d.rect(-W / 2, oy - tb, W, tb)
    for sx in (-1, 1):
        x0 = sx * (Lx / 2) if sx > 0 else -Lx / 2 - t
        d.rect(x0, oy, t, H)
    d.line((-Lx / 2, oy + i["hw"]), (Lx / 2, oy + i["hw"]), "AXIS")
    d.text((0, oy + i["hw"] + 80), "▽ " + calc.tr("Water"), 70, "AXIS", center=True)
    c = i["cover"]
    for sx in (-1, 1):
        xi = sx * (Lx / 2 - c) if sx > 0 else -Lx / 2 + c
        d.bar_line((xi, oy - tb + c), (xi, oy + H - c))
    d.dim((-W / 2, oy - tb), (W / 2, oy - tb), -300)
    d.dim((W / 2, oy - tb), (W / 2, oy + H), -300)
    d.text((0, oy - tb - 700), f"{calc.tr('Vertical bars, inside face Ø')} {i['dia_i']}/{i['s_i']:.0f}"
           f" — {calc.tr('Vertical bars, outside face Ø')} {i['dia_o']}/{i['s_o']:.0f}", 70, "REBAR",
           center=True)
    _title(d, calc, W / 2 + 1500, oy - tb)
    return d


@drawing("ec2_rc_slab")
def _slab(i, calc):
    d = Drawing()
    lx = i["lx"]
    ly = i["ly"] if i["type"] == "Two-way panel" else lx * i["spans"]
    d.rect(0, 0, lx, ly)
    d.bar_line((150, ly * 0.35), (lx - 150, ly * 0.35), f"Ø{i['dia_b']}/{i['s_b']:.0f} (x)")
    d.bar_line((lx * 0.35, 150), (lx * 0.35, ly - 150), None)
    d.text((lx * 0.35 + 100, ly * 0.6), f"Ø{i['dia_b']}/{i['s_b']:.0f} (y)", 70, "REBAR", 90)
    d.text((lx / 2, ly + 300), f"{calc.tr('Top bars Ø (supports)')} {i['dia_t']}/{i['s_t']:.0f}",
           70, "REBAR", center=True)
    d.dim((0, 0), (lx, 0), -350)
    d.dim((lx, 0), (lx, ly), -350)
    d.text((lx / 2, -800), f"h = {i['h']:.0f} mm", 80, center=True)
    _title(d, calc, lx + 900, 0)
    return d


def make(calc, inputs) -> bytes | None:
    fn = _FN.get(calc.module_id)
    if not fn:
        return None
    return fn(inputs, calc).dumps_bytes()
