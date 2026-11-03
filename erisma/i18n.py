"""Translations. English is the source language; Greek strings live in ``i18n_el``.

Lookup is by exact English text, so modules stay readable.  Templates use
``str.format`` placeholders (``"{name} sliding"``).  Untranslated strings are
collected in :data:`MISSING` (used by the tests to list work to do).
"""

from __future__ import annotations

from typing import Any

LANGS = ("en", "el")
MISSING: set[str] = set()
_TABLES: dict[str, dict[str, str]] = {}
_PRODUCED: set[str] = set()  # outputs of formatted templates (already translated)


def _table(lang: str) -> dict[str, str]:
    if lang not in _TABLES:
        if lang == "el":
            from .i18n_el import EL
            _TABLES[lang] = EL
        else:
            _TABLES[lang] = {}
    return _TABLES[lang]


def tr(text: Any, lang: str = "en", quiet: bool = False, **kw: Any) -> Any:
    """Translate ``text``. ``quiet`` = do not report it as missing (maths, codes)."""
    if not isinstance(text, str) or not text:
        return text
    out = text
    if lang != "en":
        table = _table(lang)
        if text in table:
            out = table[text]
        elif not quiet and text not in _PRODUCED and any(ch.isalpha() for ch in text):
            MISSING.add(text)
    if kw:
        try:
            out = out.format(**kw)
        except (KeyError, IndexError, ValueError):
            out = text.format(**kw)
        if len(_PRODUCED) < 50000:
            _PRODUCED.add(out)
    return out
