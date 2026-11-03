"""DXF drawings are valid R12 files in the Greek code page."""

from fastapi.testclient import TestClient

from erisma.core import get_module
from erisma.drawings import _FN, make
from erisma.web.app import app


def test_every_drawing_is_well_formed():
    for mid in _FN:
        m = get_module(mid)
        data = make(m.calculate({}, {"project": "Οικία"}, "el"), m.parse_inputs({}))
        text = data.decode("cp1253")
        assert text.startswith("0\r\nSECTION") and text.rstrip().endswith("EOF")
        assert "ANSI_1253" in text and "ENTITIES" in text
        assert "Οικία" in text


def test_dxf_endpoint():
    r = TestClient(app).post("/api/modules/ec7_pad_footing/dxf", json={"inputs": {}, "lang": "el"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/dxf")
    assert TestClient(app).post("/api/modules/ec7_slope_stability/dxf", json={}).status_code == 404
