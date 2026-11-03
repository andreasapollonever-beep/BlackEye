"""Projects: several calculations in one file, linked to each other, with one report.

A project document (``.erisma`` version 2)::

    {"format": "erisma", "version": 2, "project": {...ProjectInfo...},
     "calcs": [{"uid": "c1", "module": "ec7_pad_footing", "name": "Footing F1",
                "inputs": {...}, "links": {"NG": {"from": "c0", "symbol": "N_Ed"}}}]}

A link replaces an input by an output of another calculation of the same project (converted
to the unit of the input).  Calculations run in dependency order; a cycle is reported.
"""

from __future__ import annotations

from html import escape
from typing import Any

from .core import InputError, get_module
from .core.calc import ProjectInfo
from .core.units import compatible, convert
from .i18n import tr
from .report.html import CSS, render_html


class ProjectError(ValueError):
    pass


def _order(calcs: list[dict]) -> list[dict]:
    by = {c["uid"]: c for c in calcs}
    seen: dict[str, int] = {}
    out: list[dict] = []

    def visit(c: dict, stack: tuple = ()) -> None:
        uid = c["uid"]
        if seen.get(uid) == 2:
            return
        if seen.get(uid) == 1:
            names = " → ".join(by[u].get("name", u) for u in stack + (uid,))
            raise ProjectError(names)
        seen[uid] = 1
        for ln in (c.get("links") or {}).values():
            src = by.get(ln.get("from"))
            if src is not None:
                visit(src, stack + (uid,))
        seen[uid] = 2
        out.append(c)

    for c in calcs:
        visit(c)
    return out


def run_project(doc: dict, lang: str = "en", html: bool = False) -> dict[str, Any]:
    """Run every calculation; returns {uid: result} with resolved inputs and outputs."""
    project = ProjectInfo.from_dict(doc.get("project"))
    calcs = doc.get("calcs") or []
    results: dict[str, dict] = {}
    try:
        ordered = _order(calcs)
    except ProjectError as exc:
        return {"error": tr("Circular link between calculations: {names}", lang, names=str(exc)),
                "results": {}}
    for c in ordered:
        uid = c["uid"]
        try:
            mod = get_module(c["module"])
        except KeyError:
            results[uid] = {"error": f"Unknown calculation '{c['module']}'"}
            continue
        fields = {f.name: f for f in mod.fields}
        inputs = dict(c.get("inputs") or {})
        link_info = {}
        for name, ln in (c.get("links") or {}).items():
            src = results.get(ln.get("from"), {})
            out = (src.get("outputs") or {}).get(ln.get("symbol"))
            f = fields.get(name)
            if f is None or out is None:
                link_info[name] = {"ok": False}
                continue
            if not compatible(out["unit"], f.unit):
                link_info[name] = {"ok": False, "reason": "unit"}
                continue
            v = convert(out["value"], out["unit"], f.unit) * float(ln.get("factor", 1.0))
            inputs[name] = abs(v) if ln.get("abs") else v
            link_info[name] = {"ok": True, "value": inputs[name], "unit": f.unit,
                               "source": src.get("name", ""), "symbol": ln.get("symbol")}
        pi = ProjectInfo.from_dict({**project.__dict__, "section": c.get("name") or
                                    project.section})
        res: dict[str, Any] = {"name": c.get("name", ""), "module": c["module"],
                               "inputs": inputs, "links": link_info}
        try:
            calc = mod.calculate(inputs, pi, lang)
        except InputError as exc:
            res.update(error=str(exc), field=exc.field)
            results[uid] = res
            continue
        res.update(summary=calc.summary(), outputs=calc.outputs, title=calc.title)
        if html:
            res["html"] = render_html(calc, standalone=False)
        results[uid] = res
    return {"results": results}


COVER_CSS = """
.cover{min-height:250mm;display:flex;flex-direction:column}
.cover .logo{max-height:70px;max-width:220px;margin-bottom:24px}
.cover h1{font-size:30px;margin:60px 0 8px}
.cover .sub{font-size:16px;color:var(--muted);margin-bottom:40px}
.cover table.meta td{text-align:left;border:0;border-bottom:1px solid var(--line);padding:6px 4px}
.cover table.meta td:first-child{color:var(--muted);width:32%}
.toc td{text-align:left}.toc td.n,.toc td.u{text-align:right;width:70px}
.toc a{color:inherit;text-decoration:none}
.pb{break-before:page}
.ok{color:var(--pass);font-weight:700}.ko{color:var(--fail);font-weight:700}
@media print{.sheet{margin:0}}
"""


def project_report(doc: dict, lang: str = "en") -> str:
    """One printable document: cover page, contents with results, every calculation."""
    run = run_project(doc, lang, html=True)
    p = ProjectInfo.from_dict(doc.get("project"))
    t = lambda s: escape(tr(s, lang))  # noqa: E731
    calcs = doc.get("calcs") or []
    rows, sheets = [], []
    for i, c in enumerate(calcs, 1):
        r = run.get("results", {}).get(c["uid"], {})
        if "error" in r:
            status, util = f'<span class="ko">{t("Error")}</span>', "—"
        else:
            s = r["summary"]
            status = (f'<span class="ok">{t("PASS")}</span>' if s["passed"]
                      else f'<span class="ko">{t("FAIL")}</span>')
            util = f'{s["max_utilisation"]:.2f}' if s["max_utilisation"] < 1e6 else "∞"
        title = r.get("title") or c["module"]
        rows.append(f'<tr><td class="n">{i}</td><td><a href="#c{i}">{escape(c.get("name") or title)}'
                    f'</a><br><small>{escape(title)}</small></td><td class="u">{util}</td>'
                    f'<td>{status}</td></tr>')
        body = r.get("html") or (f'<div class="sheet"><h1>{escape(c.get("name") or title)}</h1>'
                                 f'<div class="warning">⚠ {escape(r.get("error", ""))}</div></div>')
        sheets.append(f'<section id="c{i}" class="pb">{body}</section>')
    logo = (f'<img class="logo" src="{escape(p.logo)}" alt="">'
            if p.logo.startswith("data:image/") else "")
    meta = "".join(f"<tr><td>{t(k)}</td><td>{escape(v)}</td></tr>" for k, v in (
        ("Company", p.company), ("Project", p.project), ("Client", p.client),
        ("Job no.", p.job_no), ("Calc. by / checked", " / ".join(x for x in (p.calc_by,
                                                                             p.checked_by) if x)),
        ("Date", p.date), ("Site", p.site)) if v)
    n_ok = sum(1 for r in run.get("results", {}).values()
               if "summary" in r and r["summary"]["passed"])
    cover = (f'<div class="sheet cover">{logo}<h1>{escape(p.project) or t("Structural calculations")}'
             f'</h1><div class="sub">{t("Structural calculations")} — {len(calcs)} '
             f'{t("calculations")}, {n_ok} {t("pass")}</div><table class="meta">{meta}</table>'
             f'<h2>{t("Contents")}</h2><table class="toc"><thead><tr><th>#</th>'
             f'<th>{t("Calculation")}</th><th>{t("Utilisation")}</th><th>{t("Result")}</th></tr>'
             f'</thead><tbody>{"".join(rows)}</tbody></table>'
             + (f'<div class="warning">⚠ {escape(run["error"])}</div>' if run.get("error") else "")
             + "</div>")
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<title>{escape(p.project or "Erisma")}</title><style>{CSS}{COVER_CSS}</style></head>'
            f'<body>{cover}{"".join(sheets)}</body></html>')
