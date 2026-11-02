"""Render a :class:`Calculation` as a print-ready HTML calculation sheet."""

from __future__ import annotations

import math
import re
from html import escape

from ..core.calc import Calculation, Check

_SUB = re.compile(r"([A-Za-zΑ-Ωα-ωλ̄]+)_([A-Za-z0-9,.Ͱ-Ͽ]+)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def sym(text: str) -> str:
    """Escape and typeset subscripts: ``f_ck`` → f<sub>ck</sub>."""
    return _SUB.sub(lambda m: f"{m.group(1)}<sub>{m.group(2)}</sub>", escape(text))


def rich(text: str) -> str:
    return _BOLD.sub(r"<strong>\1</strong>", sym(text))


def num(value: float, dp: int | None = None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "–"
    if math.isinf(value):
        return "∞"
    if dp is None:
        a = abs(value)
        dp = 0 if a >= 1000 else 1 if a >= 100 else 2 if a >= 1 else 3 if a >= 0.01 else 5
        if a == 0:
            dp = 0
    s = f"{value:,.{dp}f}".replace(",", " ")
    return s


def _unit(u: str) -> str:
    return f'<span class="u">{escape(u)}</span>' if u and u != "-" else ""


def _check_html(chk: Check, is_min: bool) -> str:
    ok = "pass" if chk.passed else "fail"
    word = "PASS" if chk.passed else "FAIL"
    op = "≥" if is_min else "≤"
    from ..core.units import from_base
    dem, cap = from_base(chk.demand, chk.unit), from_base(chk.capacity, chk.unit)
    left, right = (cap, dem) if is_min else (dem, cap)
    ref = f'<span class="ref">{escape(chk.ref)}</span>' if chk.ref else ""
    util = "∞" if math.isinf(chk.utilisation) else f"{chk.utilisation:.3f}"
    return (f'<div class="check {ok}"><div class="cdesc">{sym(chk.description)}{ref}</div>'
            f'<div class="cval">{num(left)} {_unit(chk.unit)} {op} {num(right)} '
            f'{_unit(chk.unit)}</div><div class="cutil">U = {util}</div>'
            f'<div class="badge {ok}">{word}</div></div>')


CSS = """
:root{--ink:#1d2433;--muted:#5d6678;--line:#d8dce4;--accent:#14365d;--pass:#1e7a46;
--fail:#b3261e;--paper:#fff}
*{box-sizing:border-box}
body{margin:0;background:#eef0f4;color:var(--ink);font:14px/1.45 "Segoe UI",Roboto,
"Helvetica Neue",Arial,sans-serif}
.sheet{max-width:860px;margin:24px auto;background:var(--paper);padding:28px 40px 40px;
box-shadow:0 2px 12px rgba(0,0,0,.08)}
header.tb{display:grid;grid-template-columns:1.3fr 1fr 1fr;border:1.5px solid var(--accent);
margin-bottom:18px}
header.tb>div{padding:6px 10px;border-left:1px solid var(--line)}
header.tb>div:first-child{border-left:0}
header.tb .k{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
header.tb .v{font-weight:600;min-height:1.2em}
header.tb .brand{grid-row:span 2;background:var(--accent);color:#fff}
header.tb .brand .v{font-size:18px}
header.tb .brand .k{color:#c5d3e6}
h1{font-size:20px;margin:6px 0 2px;color:var(--accent)}
.std{color:var(--muted);margin-bottom:12px}
h2{font-size:15px;margin:22px 0 8px;padding-bottom:3px;border-bottom:2px solid var(--accent);
color:var(--accent)}
.row{display:grid;grid-template-columns:minmax(160px,1.4fr) 2.2fr auto;gap:10px;
padding:3px 0;border-bottom:1px dotted var(--line);align-items:baseline}
.row .d{color:var(--muted)}
.row .e{font-family:"Cambria Math","STIX Two Math",Cambria,Georgia,serif}
.row .ref,.check .ref{color:var(--muted);font-size:11px;margin-left:8px;white-space:nowrap}
.row .r{text-align:right;white-space:nowrap;font-weight:600}
.u{color:var(--muted);font-weight:400;margin-left:2px}
p{margin:6px 0}
.note{color:var(--muted);font-style:italic}
.warning{background:#fff4e5;border-left:4px solid #e08a00;padding:6px 10px;margin:8px 0}
.check{display:grid;grid-template-columns:1fr auto auto 64px;gap:12px;align-items:center;
padding:7px 10px;margin:6px 0;border-radius:4px}
.check.pass{background:#eaf6ee}.check.fail{background:#fdeceb}
.check .cdesc{font-weight:600}
.check .cval{white-space:nowrap}
.check .cutil{color:var(--muted);white-space:nowrap}
.badge{font-weight:700;text-align:center;padding:2px 0;border-radius:3px;color:#fff}
.badge.pass{background:var(--pass)}.badge.fail{background:var(--fail)}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:12.5px}
th,td{border:1px solid var(--line);padding:4px 6px;text-align:center}
th{background:#f3f5f8}
caption{caption-side:bottom;color:var(--muted);font-size:11px;padding-top:3px}
figure{margin:10px 0;text-align:center}
figure svg{max-width:100%;height:auto}
figure svg.section{max-width:340px}
figcaption{color:var(--muted);font-size:11px}
.summary{margin-top:26px;border:1.5px solid var(--accent);padding:10px 14px}
.summary .big{font-size:16px;font-weight:700}
.summary .big.pass{color:var(--pass)}.summary .big.fail{color:var(--fail)}
footer{margin-top:20px;color:var(--muted);font-size:11px;text-align:center}
@media (max-width:640px){.sheet{padding:16px;margin:0}.row{grid-template-columns:1fr auto}
.row .e{grid-column:1/-1;order:3}.check{grid-template-columns:1fr auto}
header.tb{grid-template-columns:1fr 1fr}}
@media print{body{background:#fff}.sheet{box-shadow:none;margin:0;max-width:none;padding:0}
.check,figure,table{break-inside:avoid}h2{break-after:avoid}
@page{size:A4;margin:14mm 14mm 16mm}}
"""


def render_body(calc: Calculation) -> str:
    out: list[str] = []
    for item in calc.items:
        d = item.data
        k = item.kind
        if k == "heading":
            out.append(f"<h2>{escape(d['text'])}</h2>")
        elif k == "text":
            out.append(f"<p>{rich(d['text'])}</p>")
        elif k == "note":
            out.append(f'<p class="note">{rich(d["text"])}</p>')
        elif k == "warning":
            out.append(f'<div class="warning">⚠ {rich(d["text"])}</div>')
        elif k == "input":
            out.append(f'<div class="row"><div class="d">{escape(d["description"])}</div>'
                       f'<div class="e">{sym(d["symbol"])}</div>'
                       f'<div class="r">{num(d["value"], d["dp"])} {_unit(d["unit"])}</div></div>')
        elif k == "label":
            out.append(f'<div class="row"><div class="d">{escape(d["description"])}</div>'
                       f'<div class="e">{sym(d["symbol"])}</div>'
                       f'<div class="r">{escape(d["value"])}</div></div>')
        elif k == "formula":
            ref = f'<span class="ref">{escape(d["ref"])}</span>' if d.get("ref") else ""
            out.append(f'<div class="row"><div class="d">{escape(d["description"])}</div>'
                       f'<div class="e">{sym(d["symbol"])} = {sym(d["expression"])}{ref}</div>'
                       f'<div class="r">{num(d["value"], d["dp"])} {_unit(d["unit"])}</div></div>')
        elif k == "check":
            out.append(_check_html(d["check"], d.get("min", False)))
        elif k == "table":
            head = "".join(f"<th>{escape(str(h))}</th>" for h in d["headers"])
            body = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>"
                           for r in d["rows"])
            cap = f"<caption>{escape(d['caption'])}</caption>" if d["caption"] else ""
            out.append(f"<table>{cap}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
        elif k == "figure":
            cap = f"<figcaption>{escape(d['caption'])}</figcaption>" if d["caption"] else ""
            out.append(f"<figure>{d['svg']}{cap}</figure>")
    return "\n".join(out)


def render_summary(calc: Calculation) -> str:
    if not calc.checks:
        return ""
    ok = "pass" if calc.passed else "fail"
    word = "ALL CHECKS PASS" if calc.passed else "DESIGN FAILS"
    rows = "".join(
        f"<tr><td style='text-align:left'>{sym(c.description)}</td>"
        f"<td>{'∞' if math.isinf(c.utilisation) else f'{c.utilisation:.3f}'}</td>"
        f"<td style='color:var(--{'pass' if c.passed else 'fail'});font-weight:700'>"
        f"{'PASS' if c.passed else 'FAIL'}</td></tr>" for c in calc.checks)
    mu = "∞" if math.isinf(calc.max_utilisation) else f"{calc.max_utilisation:.3f}"
    return (f'<section class="summary"><div class="big {ok}">{word} — max utilisation '
            f'{mu}</div><table><thead><tr><th>Check</th><th>Utilisation</th>'
            f'<th>Result</th></tr></thead><tbody>{rows}</tbody></table></section>')


def render_html(calc: Calculation, standalone: bool = True) -> str:
    p = calc.project
    tb = (
        f'<header class="tb"><div class="brand"><div class="k">Company</div>'
        f'<div class="v">{escape(p.company)}</div><div class="k">Project</div>'
        f'<div class="v">{escape(p.project)}</div></div>'
        f'<div><div class="k">Job no.</div><div class="v">{escape(p.job_no)}</div></div>'
        f'<div><div class="k">Section / element</div><div class="v">{escape(p.section)}</div></div>'
        f'<div><div class="k">Calc. by / checked</div><div class="v">{escape(p.calc_by)}'
        f'{" / " + escape(p.checked_by) if p.checked_by else ""}</div></div>'
        f'<div><div class="k">Date</div><div class="v">{escape(p.date)}</div></div></header>'
    )
    content = (f'<div class="sheet">{tb}<h1>{escape(calc.title)}</h1>'
               f'<div class="std">In accordance with {escape(calc.standard)}'
               f'{" — client: " + escape(p.client) if p.client else ""}</div>'
               f'{render_body(calc)}{render_summary(calc)}'
               f'<footer>Generated by BlackEye · module {escape(calc.module_id)}</footer></div>')
    if not standalone:
        return content
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(calc.title)}</title><style>{CSS}</style></head>'
            f'<body>{content}</body></html>')
