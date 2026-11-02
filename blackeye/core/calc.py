"""The calculation record.

A :class:`Calculation` is the heart of BlackEye.  Design modules do not just
return numbers: they *write* a calculation, step by step, exactly as an
engineer would on a calc sheet - headings, inputs, formulas with substituted
values, code references and pass/fail checks.  The record is renderer-agnostic
and is turned into HTML/PDF reports or JSON by :mod:`blackeye.report`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .units import from_base


@dataclass
class ProjectInfo:
    project: str = ""
    job_no: str = ""
    client: str = ""
    section: str = ""
    calc_by: str = ""
    checked_by: str = ""
    date: str = field(default_factory=lambda: date.today().isoformat())
    company: str = "BlackEye Engineering"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ProjectInfo":
        data = data or {}
        known = {k: str(v) for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class Item:
    kind: str
    data: dict[str, Any]


@dataclass
class Check:
    description: str
    demand: float
    capacity: float
    unit: str
    ref: str | None = None
    utilisation: float = 0.0
    passed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "demand": from_base(self.demand, self.unit),
            "capacity": from_base(self.capacity, self.unit),
            "unit": self.unit,
            "ref": self.ref,
            "utilisation": self.utilisation,
            "passed": self.passed,
        }


class Calculation:
    """A step-by-step, auditable engineering calculation."""

    def __init__(self, title: str, module_id: str = "", standard: str = "",
                 project: ProjectInfo | None = None) -> None:
        self.title = title
        self.module_id = module_id
        self.standard = standard
        self.project = project or ProjectInfo()
        self.items: list[Item] = []
        self.checks: list[Check] = []
        self.values: dict[str, float] = {}
        self.warnings: list[str] = []
        self.model3d: dict[str, Any] | None = None  # optional 3D scene for viewers

    # ------------------------------------------------------------------ text
    def heading(self, text: str, level: int = 1) -> None:
        self.items.append(Item("heading", {"text": text, "level": level}))

    def text(self, text: str) -> None:
        self.items.append(Item("text", {"text": text}))

    def note(self, text: str) -> None:
        self.items.append(Item("note", {"text": text}))

    def warn(self, text: str) -> None:
        self.warnings.append(text)
        self.items.append(Item("warning", {"text": text}))

    # ---------------------------------------------------------------- values
    def input(self, symbol: str, value: float, unit: str = "", description: str = "",
              dp: int | None = None) -> float:
        """Record a design input (value is in base units)."""
        self.values[symbol] = value
        self.items.append(Item("input", {
            "symbol": symbol, "value": from_base(value, unit), "unit": unit,
            "description": description, "dp": dp,
        }))
        return value

    def label(self, symbol: str, value: str, description: str = "") -> str:
        """Record a non-numeric input such as a section or material name."""
        self.items.append(Item("label", {"symbol": symbol, "value": value,
                                         "description": description}))
        return value

    def formula(self, symbol: str, expression: str, value: float, unit: str = "",
                description: str = "", ref: str | None = None,
                dp: int | None = None) -> float:
        """Record a derived quantity: ``symbol = expression = value unit``."""
        self.values[symbol] = value
        self.items.append(Item("formula", {
            "symbol": symbol, "expression": expression,
            "value": from_base(value, unit), "unit": unit,
            "description": description, "ref": ref, "dp": dp,
        }))
        return value

    def table(self, headers: list[str], rows: list[list[Any]], caption: str = "") -> None:
        self.items.append(Item("table", {"headers": headers, "rows": rows,
                                         "caption": caption}))

    def figure(self, svg: str, caption: str = "") -> None:
        self.items.append(Item("figure", {"svg": svg, "caption": caption}))

    # ---------------------------------------------------------------- checks
    def check(self, description: str, demand: float, capacity: float, unit: str = "",
              ref: str | None = None) -> Check:
        """Record a design check ``demand <= capacity`` (base units)."""
        demand, capacity = float(demand), float(capacity)
        if capacity > 0:
            util = abs(demand) / capacity
        else:
            util = float("inf") if abs(demand) > 0 else 0.0
        chk = Check(description, abs(demand), capacity, unit, ref, util, util <= 1.0 + 1e-9)
        self.checks.append(chk)
        self.items.append(Item("check", {"check": chk}))
        return chk

    def check_limit(self, description: str, value: float, limit: float, unit: str = "",
                    ref: str | None = None) -> Check:
        """Alias of :meth:`check` for geometric/detailing limits."""
        return self.check(description, value, limit, unit, ref)

    def check_min(self, description: str, provided: float, required: float, unit: str = "",
                  ref: str | None = None) -> Check:
        """Record a check ``provided >= required`` (e.g. minimum reinforcement)."""
        provided, required = float(provided), float(required)
        util = required / provided if provided > 0 else float("inf")
        chk = Check(description, required, provided, unit, ref, util, util <= 1.0 + 1e-9)
        self.checks.append(chk)
        self.items.append(Item("check", {"check": chk, "min": True}))
        return chk

    # --------------------------------------------------------------- summary
    @property
    def max_utilisation(self) -> float:
        return max((c.utilisation for c in self.checks), default=0.0)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def summary(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "module": self.module_id,
            "standard": self.standard,
            "passed": self.passed,
            "max_utilisation": self.max_utilisation,
            "checks": [c.to_dict() for c in self.checks],
            "warnings": list(self.warnings),
        }
