"""Build the Cyprus seismic-zone grid from the official zonation map.

Source: NA to CYS EN 1998-1:2004, page 12, "Seismic zoning map of Cyprus"
(Zone 1 a_gR = 0.15 g, Zone 2 0.20 g, Zone 3 0.25 g). The map image embedded in the
PDF (745×512 px, stored upside down) is extracted with ``pdfimages``, flipped and saved
as ``erisma/web/static/maps/cy_zones.png``. Each pixel is classified by its colour; lines,
labels and town symbols on land take the most common zone around them.

Georeferencing from the graticule ticks on the map frame (12′ divisions):
33°00′E at x = 241 (top) / 240.5 (bottom), 34°00′E at x = 544 (top) / 548.5 (bottom),
35°00′N at y = 302.5 (left) / 299.5 (right); 1° latitude = 370.5 px.

Run:  python tools/build_cy_zones.py   (writes erisma/data/cy_zones.json)
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "erisma/web/static/maps/cy_zones.png"
OUT = ROOT / "erisma/data/cy_zones.json"

ZONE_RGB = {1: (245, 235, 85), 2: (240, 142, 53), 3: (158, 74, 72)}
SEA_RGB = (236, 244, 246)


def classify(a: np.ndarray) -> np.ndarray:
    z = np.zeros(a.shape[:2], dtype=np.uint8)
    for k, rgb in ZONE_RGB.items():
        d = np.abs(a - np.array(rgb)).sum(axis=2)
        z[d < 40] = k
    return z


def main() -> None:
    a = np.asarray(Image.open(IMG).convert("RGB")).astype(int)
    H, W, _ = a.shape
    z = classify(a)
    sea = np.abs(a - np.array(SEA_RGB)).sum(axis=2) < 25
    # keep only the island: the largest connected region of zone pixels + lines on land
    land = (z > 0) | (~sea & (a.sum(axis=2) < 600))
    land[:12, :] = land[-12:, :] = False
    land[:, :12] = land[:, -12:] = False
    seen = np.zeros_like(land)
    best = None
    for y0 in range(H):
        for x0 in range(W):
            if land[y0, x0] and not seen[y0, x0]:
                comp, q = [], deque([(y0, x0)])
                seen[y0, x0] = True
                while q:
                    y, x = q.popleft()
                    comp.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < H and 0 <= xx < W and land[yy, xx] and not seen[yy, xx]:
                            seen[yy, xx] = True
                            q.append((yy, xx))
                if best is None or len(comp) > len(best):
                    best = comp
    island = np.zeros_like(land)
    for y, x in best:
        island[y, x] = True
    z[~island] = 0
    # fill lines / labels / symbols on land with the dominant neighbouring zone
    for _ in range(12):
        holes = np.argwhere(island & (z == 0))
        if not len(holes):
            break
        zz = z.copy()
        for y, x in holes:
            win = z[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4]
            vals = win[win > 0]
            if len(vals):
                zz[y, x] = np.bincount(vals).argmax()
        z = zz
    rows = []
    for y in range(H):  # run-length encode each row: [value, count, value, count, ...]
        r, prev, n = [], int(z[y, 0]), 0
        for v in z[y]:
            v = int(v)
            if v == prev:
                n += 1
            else:
                r += [prev, n]
                prev, n = v, 1
        r += [prev, n]
        rows.append(r)
    OUT.write_text(json.dumps({
        "source": "NA to CYS EN 1998-1:2004, seismic zoning map (page 12)",
        "width": W, "height": H,
        "georef": {"x33": [241.0, 240.5], "x34": [544.0, 548.5], "y_frame": [4, 507],
                   "y35": [302.5, 299.5], "x_frame": [5, 740], "px_per_deg_lat": 370.5},
        "zones": {"1": 0.15, "2": 0.20, "3": 0.25},
        "rle": rows}, separators=(",", ":")))
    counts = np.bincount(z.ravel(), minlength=4)
    print("pixels per zone:", dict(enumerate(counts.tolist())), "->", OUT)


if __name__ == "__main__":
    main()
