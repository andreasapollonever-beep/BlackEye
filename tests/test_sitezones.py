"""Seismic zone from the official Cyprus zonation map (NA to CYS EN 1998-1)."""

import pytest
from fastapi.testclient import TestClient

from erisma.core import get_module
from erisma.design.sitezones import latlon_to_xy, places, xy_to_latlon, zone_at
from erisma.web.app import app


def test_graticule_ticks_are_round_degrees():
    lat, lon = xy_to_latlon("CY", 241.0, 302.5)
    assert lat == pytest.approx(35.0, abs=0.01) and lon == pytest.approx(33.0, abs=0.01)
    lat, lon = xy_to_latlon("CY", 544.0, 300.0)
    assert lon == pytest.approx(34.0, abs=0.01)


def test_round_trip():
    x, y = latlon_to_xy("CY", 34.9, 33.2)
    assert xy_to_latlon("CY", x, y) == (pytest.approx(34.9, abs=1e-6), pytest.approx(33.2, abs=1e-6))


@pytest.mark.parametrize("lat,lon,zone", [
    (35.1725, 33.3650, 2),   # Nicosia
    (34.6841, 33.0379, 3),   # Limassol
    (34.9229, 33.6233, 3),   # Larnaca
    (34.7754, 32.4245, 3),   # Paphos
    (35.1250, 33.9417, 3),   # Famagusta
    (35.3400, 33.3190, 2),   # Kyrenia
    (34.9200, 32.8800, 1),   # Troodos
])
def test_town_zones_match_the_official_map(lat, lon, zone):
    assert zone_at("CY", lat, lon)["zone"] == zone


def test_sea_and_boundary():
    assert zone_at("CY", 34.3, 32.0)["zone"] is None            # in the sea
    # walk north from Limassol: the conservative zone never drops below the point zone
    for lat in (34.70, 34.75, 34.80, 34.85):
        z = zone_at("CY", lat, 33.04)
        assert z["zone"] >= z["zone_here"]


def test_places_have_zones():
    ps = places("CY")
    assert len(ps) > 30 and all(p["zone"] in (1, 2, 3) for p in ps)


def test_api_and_report_site_row():
    r = TestClient(app).get("/api/site/zone?annex=CY&lat=34.6841&lon=33.0379").json()
    assert r["zone"] == 3 and r["ag"] == 0.25
    c = get_module("ec7_slope_stability").calculate(
        {}, {"annex": "CY", "site": "Limassol", "lat": "34.6841", "lon": "33.0379"})
    rows = [i for i in c.items if i.kind == "table"][-1].data["rows"]
    assert any("Zone 3" in str(r[2]) for r in rows)
