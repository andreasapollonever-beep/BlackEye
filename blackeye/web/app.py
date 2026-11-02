"""FastAPI application: REST API + single-page web client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .. import __version__
from ..core import InputError, all_modules, get_module
from ..report import render_html

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="BlackEye", version=__version__,
              description="Structural engineering calculations API")


class RunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    project: dict[str, Any] = Field(default_factory=dict)


def _module(module_id: str):
    try:
        return get_module(module_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/api/modules")
def list_modules() -> list[dict[str, Any]]:
    return [{k: m.schema()[k] for k in ("id", "title", "category", "standard", "description")}
            for m in all_modules()]


@app.get("/api/modules/{module_id}")
def module_schema(module_id: str) -> dict[str, Any]:
    return _module(module_id).schema()


@app.post("/api/modules/{module_id}/run")
def run_module(module_id: str, req: RunRequest) -> dict[str, Any]:
    mod = _module(module_id)
    try:
        calc = mod.calculate(req.inputs, req.project)
    except InputError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"summary": calc.summary(), "html": render_html(calc)}


@app.post("/api/modules/{module_id}/report", response_class=HTMLResponse)
def module_report(module_id: str, req: RunRequest) -> HTMLResponse:
    return HTMLResponse(run_module(module_id, req)["html"])


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
