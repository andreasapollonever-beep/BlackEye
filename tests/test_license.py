"""Licence keys: signature, tampering, expiry, trial and the API gate."""

import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from erisma import ed25519, license as lic
from erisma.web.app import app

SK = bytes(range(32))
PK = ed25519.public_key(SK)


def test_ed25519_rfc8032_vector():
    sk = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    assert ed25519.public_key(sk).hex() == \
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    assert ed25519.sign(sk, b"").hex().startswith("e5564300c360ac72")


def test_key_roundtrip_and_tampering():
    key = lic.make_key(SK, "Γραφείο Μελετών", "a@b.c")
    assert lic.parse_key(key, PK)["name"] == "Γραφείο Μελετών"
    body, sig = key.split(".")
    with pytest.raises(ValueError):
        lic.parse_key(body[:-2] + "AA." + sig, PK)
    with pytest.raises(ValueError):
        lic.parse_key("hello", PK)


def test_expired_key_rejected():
    key = lic.make_key(SK, "X", expires=(date.today() - timedelta(days=1)).isoformat())
    with pytest.raises(ValueError):
        lic.parse_key(key, PK)


def test_trial_counts_down_and_expires():
    s0 = lic.status()
    assert s0["state"] == "trial" and s0["days_left"] == 30
    assert lic.status(date.today() + timedelta(days=31))["state"] == "expired"


def test_api_blocks_after_trial(monkeypatch):
    c = TestClient(app)
    assert c.post("/api/modules/ec7_pad_footing/run", json={}).status_code == 200
    monkeypatch.setattr(lic, "allowed", lambda: False)
    r = c.post("/api/modules/ec7_pad_footing/run", json={})
    assert r.status_code == 402 and r.json()["detail"]["license"]
    assert c.post("/api/license", json={"key": "nonsense"}).status_code == 400


def test_every_paid_feature_is_blocked_after_trial(monkeypatch):
    c = TestClient(app)
    monkeypatch.setattr(lic, "allowed", lambda: False)
    doc = {"format": "erisma", "version": 2, "project": {},
           "calcs": [{"uid": "a", "module": "ec7_pad_footing", "name": "F1", "inputs": {}, "links": {}}]}
    for path, body in [("/api/modules/ec7_pad_footing/report", {}),
                       ("/api/modules/ec7_pad_footing/dxf", {}),
                       ("/api/modules/ec7_pad_footing/optimise", {"variables": []}),
                       ("/api/project/run", {"doc": doc}),
                       ("/api/project/report", {"doc": doc})]:
        assert c.post(path, json=body).status_code == 402, path
