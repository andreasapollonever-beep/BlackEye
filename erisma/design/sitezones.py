"""Seismic zone of a site from the official zonation map (Cyprus).

The grid is built by ``tools/build_cy_zones.py`` from the map in the NA to
CYS EN 1998-1. A query returns the zone at the point and — to stay on the safe
side near a boundary — the highest zone within ``radius_km``.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

# Towns and villages (WGS84, approximate centre). The pin is shown on the map so the
# user can move it to the exact site.
CY_PLACES: list[tuple[str, str, float, float]] = [
    ("Λευκωσία", "Nicosia", 35.1725, 33.3650),
    ("Λεμεσός", "Limassol", 34.6841, 33.0379),
    ("Λάρνακα", "Larnaca", 34.9229, 33.6233),
    ("Πάφος", "Paphos", 34.7754, 32.4245),
    ("Αμμόχωστος", "Famagusta", 35.1250, 33.9417),
    ("Κερύνεια", "Kyrenia", 35.3400, 33.3190),
    ("Παραλίμνι", "Paralimni", 35.0378, 33.9817),
    ("Αγία Νάπα", "Ayia Napa", 34.9823, 33.9999),
    ("Πόλη Χρυσοχούς", "Polis", 35.0353, 32.4253),
    ("Μόρφου", "Morphou", 35.1986, 32.9933),
    ("Στρόβολος", "Strovolos", 35.1430, 33.3400),
    ("Λακατάμια", "Lakatamia", 35.1167, 33.3167),
    ("Λατσιά", "Latsia", 35.1000, 33.3667),
    ("Αγλαντζιά", "Aglantzia", 35.1500, 33.3833),
    ("Έγκωμη", "Engomi", 35.1667, 33.3333),
    ("Δάλι", "Dali", 35.0222, 33.4206),
    ("Τσέρι", "Tseri", 35.0700, 33.3200),
    ("Κοκκινοτριμιθιά", "Kokkinotrimithia", 35.1517, 33.2017),
    ("Πέρα Χωριό", "Pera Chorio", 35.0167, 33.3833),
    ("Γερμασόγεια", "Germasogeia", 34.7167, 33.0833),
    ("Ύψωνας", "Ypsonas", 34.6833, 32.9500),
    ("Μέσα Γειτονιά", "Mesa Geitonia", 34.7000, 33.0500),
    ("Πισσούρι", "Pissouri", 34.6667, 32.7000),
    ("Αυδήμου", "Avdimou", 34.6833, 32.7667),
    ("Πάνω Πλάτρες", "Pano Platres", 34.8890, 32.8640),
    ("Τρόοδος", "Troodos", 34.9200, 32.8800),
    ("Κακοπετριά", "Kakopetria", 34.9900, 32.9000),
    ("Πεδουλάς", "Pedoulas", 34.9670, 32.8300),
    ("Αγρός", "Agros", 34.9170, 33.0170),
    ("Παλαιχώρι", "Palaichori", 34.9230, 33.0950),
    ("Κλήρου", "Klirou", 35.0170, 33.1830),
    ("Ξυλιάτος", "Xyliatos", 35.0140, 33.0410),
    ("Ευρύχου", "Evrychou", 35.0390, 32.9010),
    ("Κοφίνου", "Kofinou", 34.8170, 33.3830),
    ("Λευκαρα", "Lefkara", 34.8670, 33.3000),
    ("Αραδίππου", "Aradippou", 34.9500, 33.5833),
    ("Ξυλοφάγου", "Xylofagou", 34.9670, 33.8500),
    ("Ορμήδεια", "Ormideia", 34.9930, 33.7800),
    ("Δερύνεια", "Deryneia", 35.0600, 33.9600),
    ("Σωτήρα", "Sotira", 35.0230, 33.9510),
    ("Πύλα", "Pyla", 35.0170, 33.7000),
    ("Κίτι", "Kiti", 34.8500, 33.5667),
    ("Πέγεια", "Peyia", 34.8830, 32.3830),
    ("Γεροσκήπου", "Geroskipou", 34.7470, 32.4500),
    ("Κισσόνεργα", "Chlorakas/Kissonerga", 34.8170, 32.4000),
    ("Τσάδα", "Tsada", 34.8370, 32.4770),
    ("Κούκλια", "Kouklia", 34.7010, 32.5730),
    ("Πάνω Παναγιά", "Pano Panagia", 34.9200, 32.6300),
    ("Λύσος", "Lysos", 35.0170, 32.5330),
    ("Αεροδρόμιο Λάρνακας", "Larnaca Airport", 34.8751, 33.6249),
    ("Αεροδρόμιο Πάφου", "Paphos Airport", 34.7180, 32.4857),
]


@lru_cache(maxsize=4)
def _grid(code: str) -> dict:
    if code != "CY":
        raise KeyError(code)
    d = json.loads((DATA / "cy_zones.json").read_text())
    rows = []
    for r in d["rle"]:
        row = []
        for v, n in zip(r[0::2], r[1::2]):
            row.extend([v] * n)
        rows.append(row)
    d["grid"] = rows
    return d


def has_map(code: str) -> bool:
    return code == "CY"


def xy_to_latlon(code: str, x: float, y: float) -> tuple[float, float]:
    g = _grid(code)["georef"]
    t = (y - g["y_frame"][0]) / (g["y_frame"][1] - g["y_frame"][0])
    x33 = g["x33"][0] + (g["x33"][1] - g["x33"][0]) * t
    x34 = g["x34"][0] + (g["x34"][1] - g["x34"][0]) * t
    lon = 33.0 + (x - x33) / (x34 - x33)
    s = (x - g["x_frame"][0]) / (g["x_frame"][1] - g["x_frame"][0])
    y35 = g["y35"][0] + (g["y35"][1] - g["y35"][0]) * s
    lat = 35.0 - (y - y35) / g["px_per_deg_lat"]
    return lat, lon


def latlon_to_xy(code: str, lat: float, lon: float) -> tuple[float, float]:
    x, y = 400.0, 300.0
    for _ in range(30):  # fixed-point inversion of the (nearly affine) map
        la, lo = xy_to_latlon(code, x, y)
        gx = _grid(code)["georef"]
        x += (lon - lo) * (gx["x34"][0] - gx["x33"][0])
        y -= (lat - la) * gx["px_per_deg_lat"]
    return x, y


def zone_at(code: str, lat: float | None = None, lon: float | None = None,
            x: float | None = None, y: float | None = None, radius_km: float = 1.0) -> dict:
    """Zone at a point; ``zone`` is the highest zone within ``radius_km`` (conservative)."""
    d = _grid(code)
    if x is None or y is None:
        x, y = latlon_to_xy(code, lat, lon)
    else:
        lat, lon = xy_to_latlon(code, x, y)
    W, H, grid = d["width"], d["height"], d["grid"]
    km_px = 111.32 * math.cos(math.radians(35)) / (d["georef"]["x34"][0] - d["georef"]["x33"][0])
    r = max(1, int(round(radius_km / km_px)))
    xi, yi = int(round(x)), int(round(y))
    inside = 0 <= xi < W and 0 <= yi < H
    here = grid[yi][xi] if inside else 0
    near = set()
    for yy in range(yi - r, yi + r + 1):
        for xx in range(xi - r, xi + r + 1):
            if 0 <= yy < H and 0 <= xx < W and (xx - xi) ** 2 + (yy - yi) ** 2 <= r * r:
                if grid[yy][xx]:
                    near.add(grid[yy][xx])
    zone = max(near) if near else here
    ag = d["zones"].get(str(zone)) if zone else None
    return {"lat": round(lat, 5), "lon": round(lon, 5), "x": round(x, 1), "y": round(y, 1),
            "zone": zone or None, "zone_here": here or None, "ag": ag,
            "near_boundary": len(near) > 1, "on_map": bool(near),
            "width": W, "height": H}


@lru_cache(maxsize=2)
def _wind(code: str) -> dict:
    if code != "CY":
        raise KeyError(code)
    d = json.loads((DATA / "cy_wind.json").read_text())
    rows = []
    for r in d["rle"]:
        row = []
        for v, n in zip(r[0::2], r[1::2]):
            row.extend([v] * n)
        rows.append(row)
    d["grid"] = rows
    return d


def wind_at(code: str, lat: float, lon: float, radius_km: float = 1.0) -> dict:
    """Fundamental basic wind velocity v_b,0 [m/s] at a site (highest within radius_km)."""
    d = _wind(code)
    xs, ys = latlon_to_xy(code, lat, lon)
    sx, sy, r, tx, ty = d["affine_to_seismic"]
    u, v = (xs - tx) / sx, (ys - ty) / sy
    c, s = math.cos(r), math.sin(r)
    x, y = c * u + s * v, -s * u + c * v
    W, H, grid = d["width"], d["height"], d["grid"]
    rp = max(1, int(round(radius_km / (0.301 * sx))))
    xi, yi = int(round(x)), int(round(y))
    vals = set()
    for yy in range(yi - rp, yi + rp + 1):
        for xx in range(xi - rp, xi + rp + 1):
            if 0 <= yy < H and 0 <= xx < W and (xx - xi) ** 2 + (yy - yi) ** 2 <= rp * rp:
                if grid[yy][xx]:
                    vals.add(grid[yy][xx])
    special = d["special"] in vals
    numeric = {v for v in vals if v != d["special"]}
    return {"vb0": max(numeric) if numeric and not special else None, "special": special,
            "near_boundary": len(vals) > 1, "on_map": bool(vals)}


def places(code: str) -> list[dict]:
    if code != "CY":
        return []
    out = []
    for el, en, lat, lon in CY_PLACES:
        z = zone_at(code, lat, lon)
        out.append({"name_el": el, "name_en": en, "lat": lat, "lon": lon, "zone": z["zone"]})
    return out
