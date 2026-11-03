# BlackEye — Structural Engineering Calculations

**BlackEye** is a professional structural calculation suite in the spirit of Tekla Tedds:
every design is written out step by step — inputs, formulas with substituted values, code
clause references and PASS/FAIL checks — and produced as a print-ready calculation sheet.

> **Ελληνικά:** Το BlackEye είναι λογισμικό στατικών υπολογισμών (τύπου Tedds) με
> Ευρωκώδικες. Κάθε υπολογισμός καταγράφεται αναλυτικά (δεδομένα → τύπος → τιμή →
> παραπομπή κανονισμού → έλεγχος) και εξάγεται ως επαγγελματικό τεύχος υπολογισμών (HTML/PDF).

## Features (v0.2)

| Module | Standard | Checks |
|---|---|---|
| Continuous beam analysis | Stiffness method | Any supports (pinned/fixed), UDLs, point loads, moments; reactions, V/M/δ diagrams |
| Steel beam design | EN 1993-1-1 | Classification, bending, shear, M+V interaction, LTB (Mcr, χLT), deflection |
| RC beam section design | EN 1992-1-1 | Flexure with **compression reinforcement**, strain-compatibility MRd, As,min/As,max, bar spacing, shear (VRd,c, VRd,s, VRd,max, variable θ) |
| Gravity retaining wall | EN 1997-1, EN 1998-5, EN 1992-1-1 §12 | Mass concrete / masonry with optional footing; stability as above plus plain-concrete body sections — **3D** |
| Pad footing | EN 1997-1, EN 1992-1-1, EN 1998-5 | Biaxial effective-area bearing (shape + inclination factors), sliding, eccentricity, bending, beam shear, punching (critical perimeter search, β), seismic combination — **3D pressure heat map** |
| Slope stability (Bishop) | EN 1997-1 §11, EN 1998-5 | Automatic critical-circle search, r_u, crest surcharge, pseudo-static seismic; verified against Taylor's chart — **3D** |
| Cantilever retaining wall | EN 1997-1, EN 1998-5, EN 1992-1-1 | Coulomb active pressure on virtual back, sloping backfill, surcharge, groundwater & uplift, Mononobe-Okabe seismic thrust (±kv), sliding, overturning (EQU), bearing (Annex D, inclination factors), eccentricity, EC2 design of stem/heel/toe — DA1/DA2/DA3 — **interactive 3D model** |

Platform:

* **Calculation engine** (`blackeye.core`) — auditable `Calculation` record, units, input schema.
* **Analysis engine** (`blackeye.analysis`) — FE beam solver, verified against closed-form results.
* **Section library** (`blackeye.sections`) — IPE / HEA / HEB, properties derived from dimensions.
* **Reports** (`blackeye.report`) — branded A4 calc sheets with title block, SVG diagrams, summary.
* **Web app** (`blackeye.web`) — schema-driven forms, live preview, save/open projects (`.bkeye`), print to PDF.
* **3D viewer** — Three.js (vendored, works offline): wall, soil, groundwater, cumulative pressure
  prisms with arrows (earth / surcharge / water / seismic), base pressure, resultant forces,
  layer toggles, live utilisation panel, PNG export.
* **Usability** — Greek / English UI and reports, hints on every failing check, the wrong input is
  highlighted, autosave, project files, module search, keyboard shortcuts (Ctrl+S/O/P/3).
* **REST API** — every module is available over HTTP (`/docs` for the OpenAPI UI).
* **CLI** — batch runs for automation.

## Quick start

```bash
pip install -e ".[dev]"
blackeye serve            # open http://127.0.0.1:8000
blackeye list
blackeye run ec3_steel_beam -o beam.html
pytest
```

## Adding a module

```python
from blackeye.core import DesignModule, Field, register

@register
class MyCheck(DesignModule):
    id = "my_check"; title = "My check"; category = "Steel"; standard = "EN 1993-1-8"
    fields = [Field("F", "Design force", "kN", 100.0, min=0)]

    @classmethod
    def run(cls, calc, inp):
        F = calc.input("F_Ed", inp["F"], "kN", "Design force")
        R = calc.formula("F_Rd", "A f_y / γ_M0", 2500 * 275 / 1.0, "kN", ref="6.2.3")
        calc.check("Tension: F_Ed ≤ F_Rd", F, R, "kN", "6.2.3(1)")
```

Import it in `blackeye/modules/__init__.py`; it then appears automatically in the web app,
API and CLI. All internal values are in **N and mm**; `Field`/`calc.*` units convert at the boundary.

## Roadmap — beyond Tedds

1. **More Eurocode modules:** EC2 columns (biaxial, 2nd order), slabs, punching, pad footings (EC7);
   EC3 columns, connections (EN 1993-1-8), EC5 timber, EC6 masonry, EC8 seismic (Greek NA).
2. **National Annexes** selectable per project (Greece, Cyprus, UK, Germany …) and Greek/English reports.
3. **Load generation:** EN 1990 combinations, EN 1991 wind/snow by location.
4. **Linked calculations:** results of one calc feed the next (beam → column → footing).
5. **Optimisation:** automatically find the lightest section / minimum reinforcement.
6. **Project workspace:** multi-calc projects, revisions, checker sign-off, PDF bundle with contents page.
7. **Integrations:** IFC/BIM import, Excel export, DXF reinforcement sketches.
8. **Commercial:** user accounts & licensing, cloud + desktop (packaged) editions, QA/verification document.

> ⚠ Engineering software must be verified before commercial release. Each module has hand-calc
> tests in `tests/`; extend these with independent benchmark examples before selling.
