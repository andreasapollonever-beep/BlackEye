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


def rc_section(b: float, h: float, cover: float, link: float, dia: float, n: int) -> str:
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
    for cx in (ox + inner, ox + wb - inner):  # hanger bars
        parts.append(f'<circle cx="{cx:.1f}" cy="{oy + inner:.1f}" r="{max(r * 0.6, 2):.1f}" '
                     'fill="#777"/>')
    parts.append(f'<text x="{ox + wb / 2:.1f}" y="{oy + hb + 18:.1f}" class="dim" '
                 f'text-anchor="middle">b = {b:g} mm</text>')
    parts.append(f'<text x="{ox + wb + 10:.1f}" y="{oy + hb / 2:.1f}" class="dim">'
                 f'h = {h:g} mm</text>')
    parts.append("</svg>")
    return "\n".join(parts)


__all__ = ["beam_diagrams", "rc_section", "math"]
