"""Dependency-free SVG drawings for calculation reports."""

from __future__ import annotations

import math
from html import escape

import numpy as np

W = 720
PAD_L, PAD_R = 60, 20


def _plot(x: np.ndarray, y: np.ndarray, top: float, height: float, colour: str,
          label: str, unit: str, scale: float, L: float, invert: bool = False) -> str:
    vals = y / scale
    vmax = float(np.max(np.abs(vals))) or 1.0
    sx = (W - PAD_L - PAD_R) / L
    band = 18  # reserved for the plot label
    mid = top + band + (height - band) / 2
    sy = ((height - band) / 2 - 14) / vmax
    sign = 1 if invert else -1  # SVG y grows downwards
    pts = [(PAD_L + xi * sx, mid + sign * v * sy) for xi, v in zip(x, vals)]
    poly = [(PAD_L, mid)] + pts + [(PAD_L + L * sx, mid)]
    path = " ".join(f"{px:.1f},{py:.1f}" for px, py in poly)
    out = [
        f'<text x="8" y="{top + 14:.1f}" class="lbl">{escape(label)} [{escape(unit)}]</text>',
        f'<line x1="{PAD_L}" y1="{mid:.1f}" x2="{W - PAD_R}" y2="{mid:.1f}" class="axis"/>',
        f'<polygon points="{path}" fill="{colour}" fill-opacity="0.18" stroke="{colour}" '
        f'stroke-width="1.6"/>',
    ]
    for idx in {int(np.argmax(vals)), int(np.argmin(vals))}:
        v = vals[idx]
        if abs(v) < 1e-9 * vmax and len(vals) > 1:
            continue
        px, py = pts[idx]
        dy = -5 if (sign * v) < 0 else 13
        anchor = "start" if px < W / 2 else "end"
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.5" fill="{colour}"/>')
        out.append(f'<text x="{px + (4 if anchor == "start" else -4):.1f}" y="{py + dy:.1f}" '
                   f'class="val" text-anchor="{anchor}">{v:.2f}</text>')
    return "\n".join(out)


def beam_diagrams(res, deflection: bool = False, title: str = "") -> str:
    """Shear / moment (/ deflection) diagrams for a :class:`BeamResult`."""
    L = float(res.xd[-1])
    rows = 3 if deflection else 2
    h_plot = 150
    height = 60 + rows * h_plot
    sx = (W - PAD_L - PAD_R) / L
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
             f'class="diagram" role="img">',
             "<style>.lbl{font:600 12px sans-serif;fill:#334}.val{font:11px sans-serif;"
             "fill:#223}.axis{stroke:#99a;stroke-width:1}.tick{font:10px sans-serif;"
             "fill:#667}</style>"]
    # beam line with supports
    y0 = 30
    parts.append(f'<line x1="{PAD_L}" y1="{y0}" x2="{PAD_L + L * sx}" y2="{y0}" '
                 'stroke="#223" stroke-width="4"/>')
    for x, _, _ in res.reactions:
        px = PAD_L + x * sx
        parts.append(f'<polygon points="{px:.1f},{y0 + 2} {px - 7:.1f},{y0 + 14} '
                     f'{px + 7:.1f},{y0 + 14}" fill="#2a6f97"/>')
    for i in range(0, 11):
        px = PAD_L + i * L / 10 * sx
        parts.append(f'<text x="{px:.1f}" y="{y0 - 8}" class="tick" text-anchor="middle">'
                     f'{i * L / 10 / 1000:.2f}</text>')
    top = 55
    parts.append(_plot(res.x, res.shear, top, h_plot, "#2a6f97", "Shear V", "kN", 1e3, L))
    top += h_plot
    parts.append(_plot(res.x, res.moment, top, h_plot, "#c0392b", "Moment M", "kNm", 1e6, L,
                       invert=True))
    if deflection:
        top += h_plot
        parts.append(_plot(res.xd, res.deflection, top, h_plot, "#2e8b57", "Deflection δ",
                           "mm", 1.0, L, invert=True))
    parts.append("</svg>")
    return "\n".join(parts)


def rc_section(b: float, h: float, cover: float, link: float, dia: float, n: int,
               dia2: float = 0.0, n2: int = 2) -> str:
    """Cross-section sketch of a rectangular RC beam."""
    scale = min(220 / h, 220 / b)
    wb, hb = b * scale, h * scale
    ox, oy = 60, 20
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {wb + 160:.0f} '
             f'{hb + 60:.0f}" class="diagram section" role="img">',
             "<style>.dim{font:11px sans-serif;fill:#334}</style>",
             f'<rect x="{ox}" y="{oy}" width="{wb:.1f}" height="{hb:.1f}" fill="#e8e6e1" '
             'stroke="#556" stroke-width="1.5"/>']
    c = (cover + link / 2) * scale
    parts.append(f'<rect x="{ox + c:.1f}" y="{oy + c:.1f}" width="{wb - 2 * c:.1f}" '
                 f'height="{hb - 2 * c:.1f}" rx="{2 * link * scale:.1f}" fill="none" '
                 f'stroke="#8a5a2b" stroke-width="{max(link * scale, 1):.1f}"/>')
    r = dia / 2 * scale
    inner = (cover + link + dia / 2) * scale
    span = wb - 2 * inner
    for i in range(n):
        cx = ox + inner + (span * i / (n - 1) if n > 1 else span / 2)
        parts.append(f'<circle cx="{cx:.1f}" cy="{oy + hb - inner:.1f}" r="{r:.1f}" '
                     'fill="#333"/>')
    r2 = (dia2 / 2 * scale) if dia2 else max(r * 0.6, 2)
    inner2 = (cover + link + (dia2 or dia * 0.6) / 2) * scale
    span2 = wb - 2 * inner2
    for i in range(max(n2, 2)):  # top / compression bars
        cx = ox + inner2 + span2 * i / (max(n2, 2) - 1)
        parts.append(f'<circle cx="{cx:.1f}" cy="{oy + inner2:.1f}" r="{r2:.1f}" '
                     'fill="#555"/>')
    parts.append(f'<text x="{ox + wb / 2:.1f}" y="{oy + hb + 18:.1f}" class="dim" '
                 f'text-anchor="middle">b = {b:g} mm</text>')
    parts.append(f'<text x="{ox + wb + 10:.1f}" y="{oy + hb / 2:.1f}" class="dim">'
                 f'h = {h:g} mm</text>')
    parts.append("</svg>")
    return "\n".join(parts)


__all__ = ["beam_diagrams", "rc_section", "math"]


_PCOL = {"earth": "#b5651d", "surcharge": "#7d5ba6", "water": "#1f77b4", "seismic": "#d62728"}


def wall_section(o: dict, pressures: list[dict], bearing: list, note: str = "") -> str:
    """Cross-section of a retaining wall with pressure and base-pressure diagrams.

    ``o`` is the outline from :meth:`WallModule._outline` (metres); ``bearing`` is
    a list of (x [mm], q [N/mm²]) in base units.
    """
    B, hv, hw, tb, far = o["B"], o["hv"], o["hw"], o["tb"], o["far"]
    qb = [(x / 1000, q * 1000) for x, q in bearing]
    pmax = max([p for pr in pressures for _, p in pr["points"]] + [1.0])
    stack_w = 0.9 * max(hv, B) * 0.55
    qmax = max([q for _, q in qb] + [1.0])
    q_depth = 0.25 * hv
    xmin, xmax = -0.8, far + 0.3 + stack_w * max(len(pressures), 1) ** 0.5 + 1.4
    zmin, zmax = -q_depth - 0.6, hv + 0.8
    Wpx = 720.0
    s = (Wpx - 40) / (xmax - xmin)
    Hpx = (zmax - zmin) * s + 20
    X = lambda x: 20 + (x - xmin) * s  # noqa: E731
    Z = lambda z: 10 + (zmax - z) * s  # noqa: E731
    pts = lambda P: " ".join(f"{X(x):.1f},{Z(z):.1f}" for x, z in P)  # noqa: E731
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Wpx:.0f} {Hpx:.0f}" '
           'class="diagram" role="img"><style>.t{font:11px sans-serif;fill:#223}'
           '.tb{font:600 11px sans-serif}</style>']
    out.append(f'<polygon points="{pts(o["back"])}" fill="#e9d8b8" stroke="none"/>')
    if o.get("front"):
        out.append(f'<polygon points="{pts(o["front"])}" fill="#efe3cc"/>')
    out.append(f'<line x1="{X(xmin):.1f}" y1="{Z(0):.1f}" x2="{X(far):.1f}" y2="{Z(0):.1f}" '
               'stroke="#a08060" stroke-dasharray="3 3"/>')
    if hw > 0:
        out.append(f'<line x1="{X(o["xbb"]):.1f}" y1="{Z(hw):.1f}" x2="{X(far):.1f}" '
                   f'y2="{Z(hw):.1f}" stroke="#1f77b4" stroke-width="1.5"/>'
                   f'<text x="{X(far) - 4:.1f}" y="{Z(hw) - 4:.1f}" class="t" '
                   'text-anchor="end" fill="#1f77b4">▽ GWL</text>')
    for P in o["concrete"]:
        out.append(f'<polygon points="{pts(P)}" fill="#b9bcc2" stroke="#4a4f57" '
                   'stroke-width="1.5"/>')
    out.append(f'<line x1="{X(B):.1f}" y1="{Z(0):.1f}" x2="{X(B):.1f}" y2="{Z(hv):.1f}" '
               'stroke="#555" stroke-dasharray="6 4"/>')
    x_start = far + 0.3
    w_each = stack_w / max(len(pressures), 1) ** 0.5
    for pr in pressures:
        col = _PCOL.get(pr["key"], "#555")
        sc = w_each / pmax
        poly = [(x_start, 0)] + [(x_start + p * sc, z) for z, p in pr["points"]] + \
               [(x_start, pr["points"][-1][0])]
        out.append(f'<polygon points="{pts(poly)}" fill="{col}" fill-opacity="0.25" '
                   f'stroke="{col}" stroke-width="1.4"/>')
        zt, pt = max(pr["points"], key=lambda a: a[1])
        out.append(f'<text x="{X(x_start + pt * sc) + 3:.1f}" y="{Z(zt) + 4:.1f}" '
                   f'class="t" fill="{col}">{pt:.1f}</text>')
        x_start += max(pt * sc, 0.3) + 0.7
    if qb:
        sc = q_depth / qmax
        poly = [(0, 0)] + [(x, -q * sc) for x, q in qb] + [(B, 0)]
        out.append(f'<polygon points="{pts(poly)}" fill="#2e8b57" fill-opacity="0.25" '
                   'stroke="#2e8b57" stroke-width="1.4"/>')
        xq, qm = max(qb, key=lambda a: a[1])
        out.append(f'<text x="{X(xq) + 4:.1f}" y="{Z(-qm * sc) + 12:.1f}" class="t" '
                   f'fill="#2e8b57">q = {qm:.0f} kN/m²</text>')
    out.append(f'<text x="{X(B / 2):.1f}" y="{Z(zmin) - 2:.1f}" class="tb" '
               f'text-anchor="middle">B = {B:.2f} m</text>')
    out.append(f'<text x="{X(o["x_front"]) - 4:.1f}" y="{Z(o["top"] / 2):.1f}" class="tb" '
               f'text-anchor="end">H = {o["top"]:.2f} m</text>')
    out.append(f'<text x="{X(xmax) - 6:.1f}" y="18" class="t" text-anchor="end">'
               f'{escape(note)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def footing_plan(Bx: float, By: float, cx: float, cy: float, Bp: float, Lp: float,
                 ex: float, ey: float, a: float, t_eff: str = "effective area",
                 t_punch: str = "punching perimeter") -> str:
    """Plan view of a pad footing (metres)."""
    W = 420.0
    s = (W - 80) / max(Bx, By)
    ox, oy = 40 + (W - 80 - Bx * s) / 2, 30
    X = lambda x: ox + (x + Bx / 2) * s  # noqa: E731
    Y = lambda y: oy + (By / 2 - y) * s  # noqa: E731
    H = By * s + 70
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
           'class="diagram section" role="img"><style>.t{font:11px sans-serif;fill:#223}'
           '</style>',
           f'<rect x="{X(-Bx / 2):.1f}" y="{Y(By / 2):.1f}" width="{Bx * s:.1f}" '
           f'height="{By * s:.1f}" fill="#e3e4e6" stroke="#4a4f57" stroke-width="1.5"/>']
    if Bp > 0 and Lp > 0:
        out.append(f'<rect x="{X(ex - Bp / 2):.1f}" y="{Y(ey + Lp / 2):.1f}" '
                   f'width="{Bp * s:.1f}" height="{Lp * s:.1f}" fill="#2e8b57" '
                   'fill-opacity="0.15" stroke="#2e8b57" stroke-dasharray="5 3"/>')
    if a > 0:
        r = a * s
        x1, x2, y1, y2 = X(-cx / 2), X(cx / 2), Y(cy / 2), Y(-cy / 2)
        out.append(f'<path d="M{x1:.1f},{y1 - r:.1f} H{x2:.1f} A{r:.1f},{r:.1f} 0 0 1 '
                   f'{x2 + r:.1f},{y1:.1f} V{y2:.1f} A{r:.1f},{r:.1f} 0 0 1 {x2:.1f},'
                   f'{y2 + r:.1f} H{x1:.1f} A{r:.1f},{r:.1f} 0 0 1 {x1 - r:.1f},{y2:.1f} '
                   f'V{y1:.1f} A{r:.1f},{r:.1f} 0 0 1 {x1:.1f},{y1 - r:.1f} Z" fill="none" '
                   'stroke="#d97706" stroke-width="1.5"/>')
    out.append(f'<rect x="{X(-cx / 2):.1f}" y="{Y(cy / 2):.1f}" width="{cx * s:.1f}" '
               f'height="{cy * s:.1f}" fill="#6b7280"/>')
    out.append(f'<circle cx="{X(ex):.1f}" cy="{Y(ey):.1f}" r="3" fill="#111"/>')
    out.append(f'<text x="{X(0):.1f}" y="{Y(-By / 2) + 16:.1f}" class="t" '
               f'text-anchor="middle">Bx = {Bx:.2f} m</text>')
    out.append(f'<text x="{X(Bx / 2) + 6:.1f}" y="{Y(0):.1f}" class="t">By = {By:.2f} m</text>')
    out.append(f'<text x="10" y="{H - 22:.1f}" class="t" fill="#2e8b57">▭ {escape(t_eff)} '
               f'{Bp:.2f} × {Lp:.2f} m</text>')
    out.append(f'<text x="10" y="{H - 8:.1f}" class="t" fill="#d97706">◯ {escape(t_punch)}'
               f'</text>')
    out.append("</svg>")
    return "\n".join(out)


def slope_section(sm, rd: dict, rs: dict | None, grid: list, tr=lambda s, **k: s) -> str:
    """Slope section with critical circles, slices and the centre grid heat map (mm in)."""
    from .scene3d import heat_color

    k = 1e-3
    H, Ls = sm.H * k, sm.Ls * k
    xl, xr, ymin = sm.x_left * k, sm.x_right * k, sm.y_min * k
    ytop = max([H] + [g[1] * k for g in grid] + [rd["yc"] * k]) + 1.0
    W = 720.0
    s = (W - 40) / (xr - xl)
    Hpx = (ytop - (ymin - 1)) * s + 30
    X = lambda x: 20 + (x - xl) * s  # noqa: E731
    Y = lambda y: 10 + (ytop - y) * s  # noqa: E731
    pts = lambda P: " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in P)  # noqa: E731
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {Hpx:.0f}" '
           'class="diagram" role="img"><style>.t{font:11px sans-serif;fill:#223}'
           '.tb{font:600 12px sans-serif;paint-order:stroke;stroke:#fff;stroke-width:3px}'
           '</style>']
    ground = [(xl, ymin - 1), (xr, ymin - 1), (xr, 0), (Ls, 0), (0, H), (xl, H)]
    out.append(f'<polygon points="{pts(ground)}" fill="#e9d8b8" stroke="#8a6d3b"/>')
    out.append(f'<line x1="{X(xl):.1f}" y1="{Y(ymin):.1f}" x2="{X(xr):.1f}" y2="{Y(ymin):.1f}" '
               'stroke="#6b5a3a" stroke-dasharray="6 4"/>'
               f'<text x="{X(xr) - 4:.1f}" y="{Y(ymin) - 4:.1f}" class="t" text-anchor="end">'
               f'{escape(tr("firm stratum"))}</text>')
    if sm.q > 0 and sm.q_w > 0:
        x1, x2 = -(sm.q_off + sm.q_w) * k, -sm.q_off * k
        out.append(f'<rect x="{X(x1):.1f}" y="{Y(H) - 8:.1f}" width="{(x2 - x1) * s:.1f}" '
                   'height="8" fill="#8e6cc4" fill-opacity="0.6"/>')
    if grid:
        fmin = min(g[2] for g in grid)
        for xc, yc, f in grid:
            t = min((f - fmin) / max(fmin, 1e-6), 1.0)
            out.append(f'<circle cx="{X(xc * k):.1f}" cy="{Y(yc * k):.1f}" r="4" '
                       f'fill="{heat_color(1 - t)}" fill-opacity="0.8"/>')

    def circle(r, col, dashed, slices):
        xs = np.linspace(r["x1"], r["x2"], 80)
        ys = r["yc"] - np.sqrt(np.maximum(r["R"] ** 2 - (xs - r["xc"]) ** 2, 0))
        arc = [(x * k, y * k) for x, y in zip(xs, ys)]
        top = [(x * k, float(sm.ground(x)) * k) for x in xs[::-1]]
        out.append(f'<polygon points="{pts(arc + top)}" fill="{col}" fill-opacity="0.18" '
                   f'stroke="{col}" stroke-width="2" {"stroke-dasharray=\"6 4\"" if dashed else ""}/>')
        if slices:
            for e in r["edges"][1:-1]:
                yb = r["yc"] - math.sqrt(max(r["R"] ** 2 - (e - r["xc"]) ** 2, 0))
                out.append(f'<line x1="{X(e * k):.1f}" y1="{Y(yb * k):.1f}" x2="{X(e * k):.1f}" '
                           f'y2="{Y(float(sm.ground(e)) * k):.1f}" stroke="{col}" '
                           'stroke-opacity="0.45"/>')
        cx, cy = r["xc"] * k, r["yc"] * k
        out.append(f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="4" fill="{col}"/>'
                   f'<line x1="{X(cx):.1f}" y1="{Y(cy):.1f}" x2="{X(arc[len(arc) // 2][0]):.1f}" '
                   f'y2="{Y(arc[len(arc) // 2][1]):.1f}" stroke="{col}" stroke-dasharray="3 3"/>')
        return cx, cy

    cx, cy = circle(rd, "#e03b3b", False, True)
    out.append(f'<text x="{X(cx) + 8:.1f}" y="{Y(cy) - 6:.1f}" class="tb" fill="#e03b3b">'
               f'F_d = {rd["F"]:.2f}</text>')
    if rs:
        cx2, cy2 = circle(rs, "#8e6cc4", True, False)
        out.append(f'<text x="{X(cx2) + 8:.1f}" y="{Y(cy2) + 14:.1f}" class="tb" '
                   f'fill="#8e6cc4">F_d,E = {rs["F"]:.2f}</text>')
    out.append(f'<text x="{X(Ls) + 6:.1f}" y="{Y(H / 2):.1f}" class="t">H = {H:.1f} m</text>')
    out.append("</svg>")
    return "\n".join(out)


def vertical_diagrams(z: np.ndarray, H: float, t: float, series: list, z_anchor=None) -> str:
    """Side-by-side vertical diagrams along a pile (depth in metres, downwards)."""
    n = len(series)
    W, top, Hpx = 720.0, 34.0, 420.0
    zmax = max(float(z[-1]), H + t)
    pw = (W - 70) / n
    Y = lambda d: top + d / zmax * (Hpx - top - 20)  # noqa: E731
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {Hpx:.0f}" '
           'class="diagram" role="img"><style>.t{font:11px sans-serif;fill:#223}'
           '.tb{font:600 11px sans-serif;fill:#334}.ax{stroke:#99a}</style>']
    for d in np.arange(0, zmax + 1e-9, 1.0):
        out.append(f'<text x="8" y="{Y(d) + 4:.1f}" class="t">{d:.0f}</text>')
    out.append(f'<text x="8" y="16" class="t">z [m]</text>')
    for i, (title, vals, col) in enumerate(series):
        x0 = 50 + i * pw
        cx = x0 + pw / 2
        vals = np.asarray(vals, dtype=float)
        vmax = float(np.max(np.abs(vals))) or 1.0
        s = (pw / 2 - 12) / vmax
        out.append(f'<text x="{cx:.1f}" y="16" class="tb" text-anchor="middle">{escape(title)}'
                   '</text>')
        out.append(f'<line x1="{cx:.1f}" y1="{Y(0):.1f}" x2="{cx:.1f}" y2="{Y(zmax):.1f}" '
                   'class="ax"/>')
        out.append(f'<line x1="{x0 + 4:.1f}" y1="{Y(H):.1f}" x2="{x0 + pw - 4:.1f}" '
                   f'y2="{Y(H):.1f}" stroke="#8a6d3b" stroke-dasharray="4 3"/>')
        if z_anchor is not None:
            out.append(f'<circle cx="{cx:.1f}" cy="{Y(z_anchor):.1f}" r="3" fill="#111"/>')
        pts = [(cx, Y(0))] + [(cx + v * s, Y(d)) for v, d in zip(vals, z)] + [(cx, Y(z[-1]))]
        out.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) +
                   f'" fill="{col}" fill-opacity="0.2" stroke="{col}" stroke-width="1.4"/>')
        k = int(np.argmax(np.abs(vals)))
        out.append(f'<text x="{cx + vals[k] * s + (4 if vals[k] >= 0 else -4):.1f}" '
                   f'y="{Y(z[k]) + 4:.1f}" class="t" text-anchor="{"start" if vals[k] >= 0 else "end"}"'
                   f' fill="{col}">{vals[k]:.1f}</text>')
    out.append(f'<text x="{W - 6:.1f}" y="{Y(H) - 4:.1f}" class="t" text-anchor="end">'
               '▽ H</text>')
    out.append("</svg>")
    return "\n".join(out)
