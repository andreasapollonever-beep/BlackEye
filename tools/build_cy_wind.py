"""Build the Cyprus basic wind velocity grid (v_b,0) from the official isotach map.

Source: NA to CYS EN 1991-1-4:2005, NA 2.4, Figure 1 "Cyprus wind velocity map —
fundamental basic wind velocity (m/s), annual risk of being exceeded 0.02".
Regions bounded by the isotachs are flood-filled from their printed labels
(24 / 30 / 40 m/s). The red area on the Troodos summit carries no value on the map:
it is marked as "special study" (no value is assumed).

The map has no graticule; it is registered onto the georeferenced seismic zoning map
(NA to CYS EN 1998-1) by an affine fit of the island outlines (IoU 0.98):
x_s = sx (cos r · x − sin r · y) + tx,  y_s = sy (sin r · x + cos r · y) + ty.

Run:  python tools/build_cy_wind.py   (writes erisma/data/cy_wind.json)
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "erisma/web/static/maps/cy_wind.png"
OUT = ROOT / "erisma/data/cy_wind.json"
AFFINE = [0.89736, 0.89286, -0.00075, -95.85755, -115.15625]  # wind px -> seismic map px
# label positions (x, y) on the wind map and their value; 99 = red area (special study)
SEEDS = [(530, 352, 30), (412, 400, 24), (362, 366, 30), (153, 485, 30), (211, 463, 24),
         (305, 532, 40), (270, 578, 30), (197, 565, 24), (533, 512, 24), (715, 462, 30),
         (365, 636, 30), (703, 303, 24), (328, 497, 99), (600, 420, 24), (820, 230, 24)]


def main() -> None:
    a = np.asarray(Image.open(IMG).convert("RGB")).astype(int)
    H, W, _ = a.shape
    white = a.min(axis=2) > 200
    red = (a[:, :, 0] > 200) & (a[:, :, 1] < 80) & (a[:, :, 2] < 80)
    sea = np.zeros((H, W), bool)
    q = deque([(20, x) for x in range(20, W - 20)] + [(H - 20, x) for x in range(20, W - 20)])
    while q:
        y, x = q.popleft()
        if 0 <= y < H and 0 <= x < W and white[y, x] and not sea[y, x]:
            sea[y, x] = True
            q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    z = np.zeros((H, W), np.uint8)
    for sx, sy, v in SEEDS:
        # start from the nearest white land pixel to the label
        cand = [(abs(dx) + abs(dy), sx + dx, sy + dy) for dx in range(-25, 26)
                for dy in range(-25, 26) if 0 <= sy + dy < H and 0 <= sx + dx < W
                and (white[sy + dy, sx + dx] or (v == 99 and red[sy + dy, sx + dx]))
                and not sea[sy + dy, sx + dx]]
        _, x0, y0 = min(cand)
        ok = red if v == 99 else (white & ~sea)
        q = deque([(y0, x0)])
        while q:
            y, x = q.popleft()
            if 0 <= y < H and 0 <= x < W and ok[y, x] and not z[y, x]:
                z[y, x] = v
                q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    land = ~sea
    land[:15, :] = land[-15:, :] = False
    land[:, :15] = land[:, -15:] = False
    for _ in range(15):  # lines and labels take the higher neighbouring value (safe side)
        holes = np.argwhere(land & (z == 0))
        if not len(holes):
            break
        zz = z.copy()
        for y, x in holes:
            win = z[max(y - 2, 0):y + 3, max(x - 2, 0):x + 3]
            vals = win[win > 0]
            if len(vals):
                zz[y, x] = vals.max()
        z = zz
    rows = []
    for y in range(H):
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
    OUT.write_text(json.dumps({"source": "NA to CYS EN 1991-1-4:2005, NA 2.4 Figure 1",
                               "width": W, "height": H, "affine_to_seismic": AFFINE,
                               "special": 99, "rle": rows}, separators=(",", ":")))
    print({int(k): int(v) for k, v in zip(*np.unique(z, return_counts=True))}, "->", OUT)


if __name__ == "__main__":
    main()
