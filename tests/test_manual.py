"""The manual covers every module in both languages and is served by the web app."""

from fastapi.testclient import TestClient

from erisma.core import all_modules
from erisma.manual import CHAPTERS, NOTES, build_manual
from erisma.web.app import app


def test_every_module_has_method_notes_in_both_languages():
    for m in all_modules():
        assert m.id in NOTES, m.id
        assert NOTES[m.id]["en"] and NOTES[m.id]["el"], m.id


def test_chapters_bilingual():
    for cid, title, text in CHAPTERS:
        assert title["en"] and title["el"] and text["en"] and text["el"], cid


def test_manual_contains_every_module():
    for lang in ("el", "en"):
        html = build_manual(lang)
        for m in all_modules():
            assert f'id="{m.id}"' in html


def test_manual_route():
    r = TestClient(app).get("/manual?lang=el")
    assert r.status_code == 200 and "Εγχειρίδιο" in r.text
