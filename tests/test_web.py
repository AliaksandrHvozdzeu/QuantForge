"""Web dashboard API tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from quantforge.web.app import app  # noqa: E402
from quantforge.web.jobs import safe_gguf_path  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert "docker" in r.json()


def test_profiles(client):
    r = client.get("/api/profiles")
    assert r.status_code == 200
    data = r.json()
    assert any(p["id"] == "qwen2.5-coder-7b" for p in data)


def test_index_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "QuantForge Dashboard" in r.text


def test_safe_gguf_path_rejects_traversal():
    assert safe_gguf_path("../secret.gguf") is None
    assert safe_gguf_path("foo.bin") is None
