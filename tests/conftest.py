"""Test isolation: licence state in a temporary profile directory."""

import pytest


@pytest.fixture(autouse=True)
def _erisma_home(tmp_path, monkeypatch):
    monkeypatch.setenv("ERISMA_HOME", str(tmp_path / "erisma-home"))
