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
from ..design import sitezones
from ..design.annex import ANNEXES
from ..i18n import LANGS, tr
from .. import license as lic
from ..manual import build_manual
from ..drawings import make as make_dxf, supported as dxf_supported
from ..optimize import optimise, spec
from ..project import project_report, run_project
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


@app.get("/api/annexes")
def list_annexes(lang: str = "en") -> list[dict[str, Any]]:
    lang = _lang(lang)
    return [{"code": a.code, "label": tr(a.label, lang), "reference": a.reference,
             "zones": [{"label": tr(z, lang), "ag": ag} for z, ag in a.zones],
             "notes": [tr(n, lang) for n in a.notes],
             "map": "/static/maps/cy_zones.png" if sitezones.has_map(a.code) else None}
            for a in ANNEXES.values()]


@app.get("/api/site/places")
def site_places(annex: str = "CY") -> list[dict[str, Any]]:
    return sitezones.places(annex)


@app.get("/api/site/zone")
def site_zone(annex: str = "CY", lat: float | None = None, lon: float | None = None,
              x: float | None = None, y: float | None = None) -> dict[str, Any]:
    if not sitezones.has_map(annex):
        raise HTTPException(404, "No zonation map for this National Annex")
    if (lat is None or lon is None) and (x is None or y is None):
        raise HTTPException(422, "Give lat/lon or x/y")
    return sitezones.zone_at(annex, lat, lon, x, y)


@app.get("/api/modules/{module_id}")
def module_schema(module_id: str, lang: str = "en") -> dict[str, Any]:
    return {**_module(module_id).schema(_lang(lang)), "has_dxf": dxf_supported(module_id)}


@app.post("/api/modules/{module_id}/dxf")
def module_dxf(module_id: str, req: RunRequest):
    """DXF drawing (plan / section, reinforcement, dimensions) for CAD."""
    from fastapi.responses import Response
    mod = _module(module_id)
    _check_license(_lang(req.lang))
    if not dxf_supported(module_id):
        raise HTTPException(404, "No drawing for this calculation")
    try:
        calc = mod.calculate(req.inputs, req.project, _lang(req.lang))
        text = make_dxf(calc, mod.parse_inputs(req.inputs, _lang(req.lang)))
    except InputError as exc:
        raise HTTPException(422, {"message": str(exc), "field": exc.field}) from exc
    return Response(text, media_type="application/dxf",
                    headers={"Content-Disposition": f'attachment; filename="{module_id}.dxf"'})


class LicenseRequest(BaseModel):
    key: str = ""
    lang: str = "en"


@app.get("/api/license")
def license_status() -> dict[str, Any]:
    return lic.status()


@app.post("/api/license")
def license_activate(req: LicenseRequest) -> dict[str, Any]:
    try:
        lic.activate(req.key)
    except lic.LicenseError as exc:
        raise HTTPException(400, tr(exc.template, _lang(req.lang), **exc.params)) from exc
    return lic.status()


def _check_license(lang: str) -> None:
    if not lic.allowed():
        raise HTTPException(402, {"message": tr("The 30-day trial has ended — enter your licence "
                                                "key (Licence button at the top).", lang),
                                  "field": None, "license": True})


@app.post("/api/modules/{module_id}/run")
def run_module(module_id: str, req: RunRequest) -> dict[str, Any]:
    mod = _module(module_id)
    _check_license(_lang(req.lang))
    try:
        calc = mod.calculate(req.inputs, req.project, _lang(req.lang))
    except InputError as exc:
        raise HTTPException(422, {"message": str(exc), "field": exc.field}) from exc
    return _json_safe({"summary": calc.summary(), "html": render_html(calc),
                       "model3d": calc.model3d, "quantities": calc.quantities,
                       "structure": getattr(calc, "structure", None)})


@app.post("/api/structure/autosize")
def structure_autosize(req: RunRequest) -> dict[str, Any]:
    """Erisma Structure: enlarge members / switch options until every check passes."""
    from ..structure.autosize import autosize

    _check_license(_lang(req.lang))
    return _json_safe(autosize(req.inputs, req.project, _lang(req.lang)))


class OptimiseRequest(RunRequest):
    variables: list[dict[str, Any]] = Field(default_factory=list)


class ReserveRequest(RunRequest):
    mode: str = "loads"            # "loads" (reserve factor λ) or "field" (inverse solution)
    groups: list[str] = Field(default_factory=list)
    field: str = ""


@app.get("/api/modules/{module_id}/reserve")
def reserve_spec(module_id: str, lang: str = "en") -> dict[str, Any]:
    """Load groups that can be scaled and inputs that can be solved for."""
    from ..reserve import spec as rspec
    _module(module_id)
    sp = rspec(module_id)
    L = _lang(lang)
    sp["group_labels"] = {g: tr(t, L) for g, t in sp["group_labels"].items()}
    for f in sp["fields"]:
        f["label"] = tr(f["label"], L)
    return sp


@app.post("/api/modules/{module_id}/reserve")
def reserve_run(module_id: str, req: ReserveRequest) -> dict[str, Any]:
    """Reserve factor on the loads, or the range of an input for which all checks pass."""
    from ..reserve import inverse, reserve
    _module(module_id)
    L = _lang(req.lang)
    _check_license(L)
    try:
        if req.mode == "field":
            res = inverse(module_id, req.inputs, req.project, req.field, L)
            if res.get("message"):
                res["message"] = tr(res["message"], L)
        else:
            res = reserve(module_id, req.inputs, req.project, req.groups or ["G", "Q", "E", "A"], L)
    except ValueError as exc:
        raise HTTPException(422, {"message": tr(str(exc), L), "field": None}) from exc
    return _json_safe(res)


@app.get("/api/modules/{module_id}/optimise")
def optimise_spec(module_id: str, lang: str = "en") -> list[dict[str, Any]]:
    _module(module_id)
    return [{**v, "label": tr(v["label"], _lang(lang))} for v in spec(module_id)]


@app.post("/api/modules/{module_id}/optimise")
def optimise_run(module_id: str, req: OptimiseRequest) -> dict[str, Any]:
    """Cheapest design that passes every check, varying the chosen design variables."""
    _module(module_id)
    _check_license(_lang(req.lang))
    return _json_safe(optimise(module_id, req.inputs, req.project, req.variables,
                               _lang(req.lang)))


@app.post("/api/modules/{module_id}/report", response_class=HTMLResponse)
def module_report(module_id: str, req: RunRequest) -> HTMLResponse:
    return HTMLResponse(run_module(module_id, req)["html"])


class ProjectRequest(BaseModel):
    doc: dict[str, Any] = Field(default_factory=dict)
    lang: str = "en"


@app.post("/api/project/run")
def project_run(req: ProjectRequest) -> dict[str, Any]:
    """Run all calculations of a project (links resolved in dependency order)."""
    from ..core.units import DIMENSIONS
    _check_license(_lang(req.lang))
    return _json_safe({**run_project(req.doc, _lang(req.lang)), "dims": DIMENSIONS})


@app.post("/api/project/report", response_class=HTMLResponse)
def project_report_html(req: ProjectRequest) -> HTMLResponse:
    """The whole project as one printable document (cover, contents, all calculations)."""
    _check_license(_lang(req.lang))
    return HTMLResponse(project_report(req.doc, _lang(req.lang)))


@app.get("/manual", response_class=HTMLResponse, include_in_schema=False)
def manual(lang: str = "el") -> HTMLResponse:
    """Bilingual user manual, generated from the modules (inputs, checks) and chapters."""
    return HTMLResponse(build_manual(_lang(lang)))


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
