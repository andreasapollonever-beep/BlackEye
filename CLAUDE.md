# Erisma — project guide

Erisma is a commercial structural/geotechnical calculation suite (in the spirit of
Tekla Tedds, but doing more). Target users: practising engineers, first market Greece/Cyprus.

## Product principles (always apply)

1. **User-friendly first.** Every feature must be easy for a busy engineer:
   - sensible defaults that produce a passing, realistic design;
   - every input has a clear label, unit and (where useful) a help text;
   - invalid inputs point at the exact field and say how to fix it;
   - failing checks always come with a practical *hint* ("increase base width…");
   - results visible at a glance (status banner, utilisation bars, 3D view);
   - work is never lost (autosave, project files), keyboard shortcuts for common actions.
2. **Bilingual.** UI and reports in Greek (`el`) and English (`en`). New strings go through
   `calc.tr()` / `erisma/i18n.py`; run `tests/test_i18n.py` to find missing Greek strings.
3. **Auditable.** Calculations are written step by step (input → formula → value → clause →
   check). Never hide a number the engineer would need to verify by hand.
4. **Verified.** Every module has hand-calculation tests in `tests/`.
5. **Offline-capable.** No CDN at runtime; third-party JS is vendored under `web/static/vendor`.

## Conventions

- Internal units: N and mm (see `core/units.py`); convert only at inputs and output.
- A module = subclass of `DesignModule` registered with `@register` in `erisma/modules/`,
  imported from `erisma/modules/__init__.py`.
- Whole-building 3D analysis lives in its own package `erisma/structure/` (model, solver,
  modal/spectrum); it reuses units, materials, sections, annex data and i18n, and raises
  `StructureError` with a bilingual message and a `ref` to the node/member to fix.
  Hand-calculation tests in `tests/structure/`; every static result has `equilibrium_ok()`.
- 3D: modules may attach a generic scene (`erisma/report/scene3d.py`) as `calc.model3d`;
  `web/static/viewer3d.js` renders any scene (layers, prisms, boxes, meshes, arrows, labels).
- Partial factors / NDPs: never hard-code — read them from `erisma/design/annex.py`
  (`get_annex(calc.project.annex)`). Only enter annex values verified against the published
  document, and record the document in `Annex.reference`.

## Commands

```bash
pip install -e ".[dev]"
pytest -q
erisma serve   # http://127.0.0.1:8000
```

Do not `pkill -f erisma` from a shell whose command line contains that text (it kills the
shell); start test servers with `nohup … & echo $! > pidfile` and kill the pid.
