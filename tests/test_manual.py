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


def test_manual_documents_every_feature():
    """Each program feature has its chapter, and every card states its tools truthfully."""
    import re

    from erisma import drawings, optimize
    from erisma.manual import CHAPTERS, build_manual
    ids = {c[0] for c in CHAPTERS}
    assert {"start", "project", "chain", "preport", "cost", "optimise", "compare", "dxf",
            "licence"} <= ids
    for lang, word_dxf, word_opt in (("en", "DXF drawing", "automatic design"),
                                     ("el", "σχέδιο DXF", "αυτόματη διαστασιολόγηση")):
        html = build_manual(lang)
        for m in all_modules():
            card = html.split(f'<div class="card" id="{m.id}">', 1)[1].split('<div class="card"', 1)[0]
            tools = re.search(r"<p class='std'><b>[^<]+:</b>(.*?)</p>", card).group(1)
            assert (word_dxf in tools) == drawings.supported(m.id), (lang, m.id)
            assert (word_opt in tools) == bool(optimize.spec(m.id)), (lang, m.id)
        assert re.findall(r'<h2 id="[^"]+">(\d+)\.', html) == [str(i) for i in range(1, len(CHAPTERS) + 4)]
