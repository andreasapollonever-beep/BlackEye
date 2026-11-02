"""Command line interface: ``blackeye list | run | serve``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import InputError, all_modules, get_module
from .report import render_html


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="blackeye", description="BlackEye structural calculations")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list available calculation modules")
    r = sub.add_parser("run", help="run a module and write an HTML report")
    r.add_argument("module", help="module id, or a .bkeye project file")
    r.add_argument("-i", "--inputs", help="JSON file with inputs (defaults used if omitted)")
    r.add_argument("-o", "--out", help="output HTML file (default: <module>.html)")
    r.add_argument("--json", action="store_true", help="print the result summary as JSON")
    s = sub.add_parser("serve", help="start the web application")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for m in all_modules():
            print(f"{m.id:<20} {m.category:<10} {m.title}  [{m.standard}]")
        return 0

    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("blackeye.web.app:app", host=args.host, port=args.port)
        return 0

    project: dict = {}
    inputs: dict = {}
    module_id = args.module
    if module_id.endswith((".bkeye", ".json")) and Path(module_id).exists():
        doc = json.loads(Path(module_id).read_text(encoding="utf-8"))
        module_id, project, inputs = doc["module"], doc.get("project", {}), doc.get("inputs", {})
    if args.inputs:
        inputs.update(json.loads(Path(args.inputs).read_text(encoding="utf-8")))
    try:
        calc = get_module(module_id).calculate(inputs, project)
    except (KeyError, InputError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out = Path(args.out or f"{module_id}.html")
    out.write_text(render_html(calc), encoding="utf-8")
    if args.json:
        print(json.dumps(calc.summary(), indent=2, ensure_ascii=False))
    else:
        status = "PASS" if calc.passed else "FAIL"
        print(f"{calc.title}: {status} (max utilisation {calc.max_utilisation:.3f}) -> {out}")
    return 0 if calc.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
