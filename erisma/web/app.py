"""FastAPI application: REST API + single-page web client."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .. import __version__
from ..core import InputError, all_modules, get_module
from ..i18n import LANGS
from ..report import render_html

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Erisma", version=__version__,
              description="Structural engineering calculations API")


class RunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    project: dict[str, Any] = Field(default_factory=dict)
    lang: str = "en"


def _json_safe(obj: Any) -> Any:
    """Convert numpy scalars and non-finite floats into JSON-friendly values."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        obj = obj.item()
    if isinstance(obj, float) and not math.isfinite(obj):
        return 999.0 if obj > 0 else -999.0
    return obj


def _module(module_id: str):
    try:
        return get_module(module_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


def _lang(lang: str) -> str:
    return lang if lang in LANGS else "en"


@app.get("/api/modules")
def list_modules(lang: str = "en") -> list[dict[str, Any]]:
    lang = _lang(lang)
    return [{k: m.schema(lang)[k] for k in ("id", "title", "category", "standard",
                                            "description", "has_3d")} for m in all_modules()]


@app.get("/api/modules/{module_id}")
def module_schema(module_id: str, lang: str = "en") -> dict[str, Any]:
    return _module(module_id).schema(_lang(lang))


@app.post("/api/modules/{module_id}/run")
def run_module(module_id: str, req: RunRequest) -> dict[str, Any]:
    mod = _module(module_id)
    try:
        calc = mod.calculate(req.inputs, req.project, _lang(req.lang))
    except InputError as exc:
        raise HTTPException(422, {"message": str(exc), "field": exc.field}) from exc
    return _json_safe({"summary": calc.summary(), "html": render_html(calc),
                       "model3d": calc.model3d})


@app.post("/api/modules/{module_id}/report", response_class=HTMLResponse)
def module_report(module_id: str, req: RunRequest) -> HTMLResponse:
    return HTMLResponse(run_module(module_id, req)["html"])


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
