"""Tests for disk cleanup planner."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.clean_runner import collect_clean_items  # noqa: E402
from quantforge.config import load_config  # noqa: E402


@pytest.fixture
def fake_models(tmp_path: Path):
    models = tmp_path / "models"
    models.mkdir()
    (models / "Active-Q5.gguf").write_bytes(b"x" * 100)
    (models / "Old-Q4.gguf").write_bytes(b"x" * 200)
    active_base = models / "active-base"
    active_base.mkdir()
    (active_base / "w.bin").write_bytes(b"x" * 50)
    old_base = models / "old-base"
    old_base.mkdir()
    (old_base / "w.bin").write_bytes(b"x" * 500)
    return models


def test_collect_inactive_items(fake_models, monkeypatch):
    cfg = load_config("qwen2.5-coder-7b")
    cfg["model"]["gguf_output"] = "Active-Q5.gguf"
    cfg["model"]["base_dir"] = "active-base"
    cfg["paths"]["models"] = str(fake_models)

    monkeypatch.setattr(
        "quantforge.clean_runner.paths_from_config",
        lambda c: {
            "models": fake_models,
            "logs": fake_models.parent / "logs",
            "metrics": fake_models.parent / "metrics",
            "root": fake_models.parent,
            "gguf": fake_models / c["model"]["gguf_output"],
            "base_weights": fake_models / c["model"]["base_dir"],
        },
    )

    items = collect_clean_items(cfg)
    paths = {i.path.name for i in items}
    assert "Old-Q4.gguf" in paths
    assert "old-base" in paths
    assert "Active-Q5.gguf" not in paths
    assert "active-base" not in paths
