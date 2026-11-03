"""Shared 3D helpers for line members (beams): supports, loads, deflection, moment ribbon.

All inputs in metres / kN / kNm; the beam axis is x, y is up, z across.
"""

from __future__ import annotations

import numpy as np

from .scene3d import PALETTE, Scene3D, heat_color


def supports(sc: Scene3D, layer: str, items, h: float, w: float) -> None:
    """items: [(x, kind)] with kind pinned | fixed."""
    s = max(0.18, 0.6 * h)
    for x, kind in items:
        if kind == "fixed":
            sc.box(layer, (x, h / 2, 0), (0.08, h + 2 * s, w + 0.4), "#7d8794")
        else:
            sc.prism(layer, [(x, 0), (x - s * 0.6, -s), (x + s * 0.6, -s)], w + 0.2, "#7d8794")
            sc.box(layer, (x, -s - 0.03, 0), (s * 1.6, 0.06, w + 0.3), "#5a6b7d")


def udl_arrows(sc: Scene3D, layer: str, x1: float, x2: float, w: float, top: float,
               wmax: float, label: str | None = None) -> None:
    if abs(w) < 1e-9 or x2 <= x1:
        return
    ln = 0.25 + 0.6 * abs(w) / max(wmax, 1e-9)
    n = max(int((x2 - x1) / 0.5), 2)
    sgn = 1 if w > 0 else -1
    for i in range(n + 1):
        x = x1 + (x2 - x1) * i / n
        o = (x, top + ln, 0) if sgn > 0 else (x, top, 0)
        sc.arrow(layer, o, (0, -sgn, 0), ln, PALETTE["load"], 0.08)
    sc.line(layer, [(x1, top + ln, 0), (x2, top + ln, 0)], PALETTE["load"])
    if label:
        sc.label(layer, label, ((x1 + x2) / 2, top + ln + 0.2, 0), "force")


def point_arrow(sc: Scene3D, layer: str, x: float, P: float, top: float, Pmax: float,
                label: str) -> None:
    if abs(P) < 1e-9:
        return
    ln = 0.5 + 0.8 * abs(P) / max(Pmax, 1e-9)
    sgn = 1 if P > 0 else -1
    o = (x, top + ln, 0) if sgn > 0 else (x, top, 0)
    sc.arrow(layer, o, (0, -sgn, 0), ln, "#e03b3b", 0.16)
    sc.label(layer, label, (x, top + ln + 0.2, 0), "force")


def deflected(sc: Scene3D, layer: str, xs, ys, scale: float, z: float, y0: float = 0.0) -> None:
    pts = [(float(x), y0 - float(y) * scale, z) for x, y in zip(xs, ys)]
    sc.line(layer, pts, "#e03b3b", dashed=True)


def moment_ribbon(sc: Scene3D, layer: str, xs, Ms, z: float, height: float) -> None:
    """Vertical heat-coloured ribbon behind the beam: sagging below, hogging above."""
    xs, Ms = np.asarray(xs, float), np.asarray(Ms, float)
    mmax = float(np.abs(Ms).max()) or 1.0
    verts, cols, faces = [], [], []
    for x, M in zip(xs, Ms):
        verts += [(float(x), 0.0, z), (float(x), -M / mmax * height, z)]
        c = heat_color(abs(M) / mmax)
        cols += [c, c]
    for i in range(len(xs) - 1):
        a = 2 * i
        faces += [(a, a + 1, a + 3), (a, a + 3, a + 2)]
    sc.mesh(layer, verts, faces, opacity=0.75, colors=cols)
    k = int(np.argmax(np.abs(Ms)))
    sc.label(layer, f"M = {Ms[k]:.1f} kNm", (float(xs[k]), -Ms[k] / mmax * height * 1.1, z),
             "result")
