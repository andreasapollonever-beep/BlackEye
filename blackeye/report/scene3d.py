"""Generic 3D scene description rendered by ``web/static/viewer3d.js``.

Coordinates are metres in the three.js convention: x to the right, y up,
z towards the viewer.  Every object belongs to a *layer* that the user can
switch on and off.  Colours are CSS hex strings.
"""

from __future__ import annotations

from typing import Any, Iterable

Vec = tuple[float, float, float]

PALETTE = {
    "concrete": "#b4b8bf", "soil": "#d9bf8c", "soil2": "#e6d3ad", "rock": "#a89f91",
    "earth": "#c47a2c", "surcharge": "#8e6cc4", "water": "#2f8fd8", "seismic": "#e03b3b",
    "bearing": "#2e9b5f", "load": "#1d2433", "steel": "#5a6b7d", "slip": "#e03b3b",
    "result": "#111111", "punch": "#d97706",
}


def _r(v: float) -> float:
    return round(float(v), 4)


class Scene3D:
    def __init__(self, kind: str, tr=lambda s, **k: s.format(**k) if k else s) -> None:
        self.kind = kind
        self.tr = tr
        self.layers: list[dict[str, Any]] = []
        self.objects: list[dict[str, Any]] = []
        self.legend: list[dict[str, Any]] = []
        self.info: dict[str, Any] = {}
        self.views: dict[str, Any] = {}

    # ------------------------------------------------------------- layers
    def layer(self, key: str, label: str, visible: bool = True, toggle: bool = True) -> str:
        if not any(l["key"] == key for l in self.layers):
            self.layers.append({"key": key, "label": self.tr(label), "visible": visible,
                                "toggle": toggle})
        return key

    def legend_item(self, color: str, text: str) -> None:
        self.legend.append({"color": color, "text": text})

    # ------------------------------------------------------------ objects
    def prism(self, layer: str, pts: Iterable[tuple[float, float]], depth: float, color: str,
              opacity: float = 1.0, z: float = 0.0, edges: bool = True) -> None:
        """Polygon in the x-y plane extruded along z (centred on ``z``)."""
        self.objects.append({"t": "prism", "layer": layer,
                             "pts": [[_r(x), _r(y)] for x, y in pts], "depth": _r(depth),
                             "z": _r(z), "color": color, "opacity": opacity, "edges": edges})

    def box(self, layer: str, center: Vec, size: Vec, color: str, opacity: float = 1.0,
            edges: bool = True) -> None:
        self.objects.append({"t": "box", "layer": layer, "c": [_r(v) for v in center],
                             "s": [_r(v) for v in size], "color": color, "opacity": opacity,
                             "edges": edges})

    def mesh(self, layer: str, vertices: list[Vec], faces: list[tuple[int, int, int]],
             color: str = "#888888", opacity: float = 1.0,
             colors: list[str] | None = None) -> None:
        """Triangle mesh; optional per-vertex ``colors`` (heat maps)."""
        self.objects.append({"t": "mesh", "layer": layer,
                             "v": [[_r(a) for a in p] for p in vertices],
                             "f": [list(f) for f in faces], "color": color,
                             "opacity": opacity, "vc": colors})

    def line(self, layer: str, points: list[Vec], color: str, dashed: bool = False,
             closed: bool = False) -> None:
        self.objects.append({"t": "line", "layer": layer,
                             "p": [[_r(a) for a in p] for p in points], "color": color,
                             "dashed": dashed, "closed": closed})

    def cylinder(self, layer: str, p1: Vec, p2: Vec, radius: float, color: str,
                 opacity: float = 1.0) -> None:
        self.objects.append({"t": "cyl", "layer": layer, "a": [_r(v) for v in p1],
                             "b": [_r(v) for v in p2], "r": _r(radius), "color": color,
                             "opacity": opacity})

    def arrow(self, layer: str, origin: Vec, direction: Vec, length: float, color: str,
              head: float | None = None) -> None:
        if length <= 1e-6:
            return
        self.objects.append({"t": "arrow", "layer": layer, "o": [_r(v) for v in origin],
                             "d": [_r(v) for v in direction], "len": _r(length),
                             "color": color, "head": head})

    def label(self, layer: str, text: str, pos: Vec, style: str = "") -> None:
        self.objects.append({"t": "label", "layer": layer, "text": text,
                             "p": [_r(v) for v in pos], "style": style})

    # -------------------------------------------------------------- export
    def to_dict(self) -> dict[str, Any]:
        return {"version": 2, "kind": self.kind, "layers": self.layers,
                "objects": self.objects, "legend": self.legend, "info": self.info,
                "views": self.views}


def heat_color(t: float) -> str:
    """Blue → green → yellow → red for t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    stops = [(0.0, (47, 111, 216)), (0.35, (46, 155, 95)), (0.7, (240, 196, 40)),
             (1.0, (224, 59, 59))]
    for (t1, c1), (t2, c2) in zip(stops, stops[1:]):
        if t <= t2:
            k = (t - t1) / (t2 - t1)
            r, g, b = (int(a + (b_ - a) * k) for a, b_ in zip(c1, c2))
            return f"#{r:02x}{g:02x}{b:02x}"
    return "#e03b3b"
