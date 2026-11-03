"""Design module framework and registry.

Every design calculation (an EC3 steel beam, an EC2 RC section, ...) is a
:class:`DesignModule`.  A module declares its inputs as :class:`Field` objects -
this declaration drives the web forms, the CLI, validation and the saved
project files - and implements :meth:`DesignModule.run` which writes a
:class:`~erisma.core.calc.Calculation`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar

from ..i18n import tr
from .calc import Calculation, ProjectInfo
from .units import to_base


class InputError(ValueError):
    """Raised when user inputs are invalid.

    ``field`` names the offending input so the UI can highlight it.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


@dataclass
class Field:
    name: str
    label: str
    unit: str = ""
    default: Any = None
    kind: str = "float"  # float | int | choice | bool | text | table
    choices: list[str] | None = None
    min: float | None = None
    max: float | None = None
    group: str = "General"
    help: str = ""
    columns: list["Field"] | None = None  # for kind == "table"

    def to_dict(self, lang: str = "en") -> dict[str, Any]:
        d = asdict(self)
        d["label"] = tr(self.label, lang)
        d["group"] = tr(self.group, lang)
        d["help"] = tr(self.help, lang)
        if self.choices:
            d["choice_labels"] = [tr(c, lang, quiet=True) for c in self.choices]
        if self.columns is not None:
            d["columns"] = [c.to_dict(lang) for c in self.columns]
        return d

    # ---------------------------------------------------------------- parse
    def parse(self, raw: Any, lang: str = "en") -> Any:
        """Validate ``raw`` and return the value (numbers in base units)."""
        L = tr(self.label, lang)

        def err(msg: str, **kw: Any) -> InputError:
            return InputError(tr(msg, lang, label=L, **kw), self.name)

        if raw is None or raw == "":
            raw = self.default
        if raw is None:
            raise err("'{label}' is required")
        if self.kind in ("float", "int"):
            try:
                num = float(raw)
            except (TypeError, ValueError) as exc:
                raise err("'{label}' must be a number") from exc
            if self.kind == "int":
                if num != int(num):
                    raise err("'{label}' must be a whole number")
                num = int(num)
            if self.min is not None and num < self.min:
                raise err("'{label}' must be ≥ {v} {unit}", v=f"{self.min:g}", unit=self.unit)
            if self.max is not None and num > self.max:
                raise err("'{label}' must be ≤ {v} {unit}", v=f"{self.max:g}", unit=self.unit)
            return to_base(num, self.unit) if self.kind == "float" else num
        if self.kind == "choice":
            if self.choices and str(raw) not in self.choices:
                raise err("'{label}' must be one of: {v}", v=", ".join(self.choices))
            return str(raw)
        if self.kind == "bool":
            if isinstance(raw, str):
                return raw.strip().lower() in ("1", "true", "yes", "on")
            return bool(raw)
        if self.kind == "table":
            if not isinstance(raw, list):
                raise err("'{label}' must be a list of rows")
            rows = []
            for i, row in enumerate(raw, 1):
                if not isinstance(row, dict):
                    raise err("'{label}' row {i} is invalid", i=i)
                parsed = {}
                for col in self.columns or []:
                    try:
                        parsed[col.name] = col.parse(row.get(col.name), lang)
                    except InputError as exc:
                        raise InputError(f"{L}, {tr('row', lang)} {i}: {exc}", self.name) from exc
                rows.append(parsed)
            return rows
        return str(raw)


class DesignModule:
    """Base class for all calculation modules."""

    id: ClassVar[str] = ""
    title: ClassVar[str] = ""
    category: ClassVar[str] = ""
    standard: ClassVar[str] = ""
    description: ClassVar[str] = ""
    fields: ClassVar[list[Field]] = []

    @classmethod
    def schema(cls, lang: str = "en") -> dict[str, Any]:
        return {
            "id": cls.id,
            "title": tr(cls.title, lang),
            "category": tr(cls.category, lang),
            "standard": tr(cls.standard, lang, quiet=True),
            "description": tr(cls.description, lang),
            "fields": [f.to_dict(lang) for f in cls.fields],
        }

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        return {f.name: f.default for f in cls.fields}

    @classmethod
    def parse_inputs(cls, raw: dict[str, Any] | None, lang: str = "en") -> dict[str, Any]:
        raw = raw or {}
        return {f.name: f.parse(raw.get(f.name), lang) for f in cls.fields}

    @classmethod
    def calculate(cls, raw_inputs: dict[str, Any] | None = None,
                  project: ProjectInfo | dict | None = None,
                  lang: str = "en") -> Calculation:
        if not isinstance(project, ProjectInfo):
            project = ProjectInfo.from_dict(project)
        inputs = cls.parse_inputs(raw_inputs, lang)
        calc = Calculation(cls.title, cls.id, cls.standard, project, lang=lang)
        try:
            cls.run(calc, inputs)
        except InputError as exc:
            raise InputError(tr(str(exc), lang), exc.field) from exc
        return calc

    @classmethod
    def run(cls, calc: Calculation, inp: dict[str, Any]) -> None:  # pragma: no cover
        raise NotImplementedError


_REGISTRY: dict[str, type[DesignModule]] = {}


def register(cls: type[DesignModule]) -> type[DesignModule]:
    if not cls.id:
        raise ValueError("Design modules need an id")
    if cls.id in _REGISTRY:
        raise ValueError(f"Duplicate module id '{cls.id}'")
    _REGISTRY[cls.id] = cls
    return cls


def get_module(module_id: str) -> type[DesignModule]:
    import erisma.modules  # noqa: F401  (ensure modules are registered)

    try:
        return _REGISTRY[module_id]
    except KeyError as exc:
        raise KeyError(f"Unknown module '{module_id}'") from exc


def all_modules() -> list[type[DesignModule]]:
    import erisma.modules  # noqa: F401

    return sorted(_REGISTRY.values(), key=lambda m: (m.category, m.title))


__all__ = ["Field", "DesignModule", "InputError", "register", "get_module",
           "all_modules", "field"]
