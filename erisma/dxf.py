"""Minimal DXF (R12, ASCII) writer — opens in AutoCAD, BricsCAD, DraftSight, LibreCAD.

Units are millimetres.  Only LINE, POLYLINE, CIRCLE and TEXT entities are used so the files
work with every CAD program.
"""

from __future__ import annotations

import math

# layer -> AutoCAD colour index
LAYERS = {"CONCRETE": 7, "REBAR": 1, "SOIL": 34, "DIM": 3, "TEXT": 2, "AXIS": 8, "STEEL": 5,
          "HATCH": 9}


CODEPAGE = ("ANSI_1253", "cp1253")  # Greek; AutoCAD reads it from $DWGCODEPAGE


def _enc(s: str) -> str:
    """AutoCAD control codes for symbols outside the code page (Ø, °, ±)."""
    return s.replace("Ø", "%%c").replace("ø", "%%c").replace("°", "%%d").replace("±", "%%p")


class Drawing:
    def __init__(self) -> None:
        self.ents: list[str] = []

    def _e(self, *pairs) -> None:
        self.ents.append("\n".join(f"{c}\n{v}" for c, v in pairs))

    def line(self, p1, p2, layer: str = "CONCRETE") -> None:
        self._e((0, "LINE"), (8, layer), (10, f"{p1[0]:.2f}"), (20, f"{p1[1]:.2f}"), (30, "0"),
                (11, f"{p2[0]:.2f}"), (21, f"{p2[1]:.2f}"), (31, "0"))

    def poly(self, pts, layer: str = "CONCRETE", closed: bool = True) -> None:
        pts = list(pts)
        out = [(0, "POLYLINE"), (8, layer), (66, "1"), (70, "1" if closed else "0")]
        for x, y in pts:
            out += [(0, "VERTEX"), (8, layer), (10, f"{x:.2f}"), (20, f"{y:.2f}"), (30, "0")]
        out += [(0, "SEQEND"), (8, layer)]
        self._e(*out)

    def rect(self, x, y, w, h, layer: str = "CONCRETE") -> None:
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer)

    def circle(self, c, r, layer: str = "REBAR") -> None:
        self._e((0, "CIRCLE"), (8, layer), (10, f"{c[0]:.2f}"), (20, f"{c[1]:.2f}"), (30, "0"),
                (40, f"{r:.2f}"))

    def text(self, p, s: str, h: float = 50, layer: str = "TEXT", rot: float = 0,
             center: bool = False) -> None:
        pairs = [(0, "TEXT"), (8, layer), (10, f"{p[0]:.2f}"), (20, f"{p[1]:.2f}"), (30, "0"),
                 (40, f"{h:.1f}"), (1, _enc(s)), (50, f"{rot:.1f}")]
        if center:
            pairs += [(72, "1"), (11, f"{p[0]:.2f}"), (21, f"{p[1]:.2f}"), (31, "0")]
        self._e(*pairs)

    def dim(self, p1, p2, off: float, label: str | None = None, h: float = 45) -> None:
        """Linear dimension drawn with lines and text (offset perpendicular to p1→p2)."""
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L * off, dx / L * off
        a, b = (p1[0] + nx, p1[1] + ny), (p2[0] + nx, p2[1] + ny)
        self.line(p1, a, "DIM")
        self.line(p2, b, "DIM")
        self.line(a, b, "DIM")
        t = 0.12 * abs(off) if off else 20
        for q in (a, b):  # ticks
            self.line((q[0] - t * 0.4, q[1] - t * 0.4), (q[0] + t * 0.4, q[1] + t * 0.4), "DIM")
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90 or ang < -90:
            ang += 180
        mid = ((a[0] + b[0]) / 2 + nx / max(abs(off), 1) * h * 0.4,
               (a[1] + b[1]) / 2 + ny / max(abs(off), 1) * h * 0.4)
        self.text(mid, label or f"{L:.0f}", h, "DIM", ang, center=True)

    def bar_line(self, p1, p2, label: str | None = None, h: float = 40) -> None:
        self.line(p1, p2, "REBAR")
        if label:
            self.text(((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + h * 0.6), label, h, "REBAR",
                      center=True)

    def title(self, x, y, lines: list[str], w: float = 2600) -> None:
        hgt = 90 * len(lines) + 60
        self.rect(x, y, w, hgt, "TEXT")
        for i, s in enumerate(lines):
            self.text((x + 40, y + hgt - 110 - i * 90), s, 60 if i else 80)

    def dumps(self) -> str:
        tables = ["0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", str(len(LAYERS))]
        for n, c in LAYERS.items():
            tables += ["0", "LAYER", "2", n, "70", "0", "62", str(c), "6", "CONTINUOUS"]
        tables += ["0", "ENDTAB", "0", "ENDSEC"]
        head = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9",
                "$DWGCODEPAGE", "3", CODEPAGE[0], "9", "$INSUNITS", "70", "4", "0", "ENDSEC"]
        body = ["0", "SECTION", "2", "ENTITIES"]
        return "\n".join(head + tables + body) + "\n" + "\n".join(self.ents) + \
            "\n0\nENDSEC\n0\nEOF\n"

    def dumps_bytes(self) -> bytes:
        return self.dumps().replace("\n", "\r\n").encode(CODEPAGE[1], errors="replace")
