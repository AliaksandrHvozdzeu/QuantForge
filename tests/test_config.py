"""Configuration loading tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.config import deep_merge, list_profiles, load_config, paths_from_config  # noqa: E402


def test_list_profiles_contains_qwen():
    profiles = list_profiles()
    assert "qwen2.5-coder-7b" in profiles


def test_load_qwen_profile():
    cfg = load_config("qwen2.5-coder-7b")
    assert cfg["quantize_type"] == "Q5_K_M"
    assert cfg["model"]["repo"] == "Qwen/Qwen2.5-Coder-7B-Instruct"
    assert cfg["chat"]["format"] == "chatml"


def test_deep_merge_nested():
    base = {"a": {"b": 1, "c": 2}}
    override = {"a": {"c": 3, "d": 4}}
    merged = deep_merge(base, override)
    assert merged == {"a": {"b": 1, "c": 3, "d": 4}}


def test_paths_from_config():
    cfg = load_config("qwen2.5-coder-7b")
    paths = paths_from_config(cfg)
    assert paths["gguf"].name == "Qwen2.5-Coder-7B-Q5_K_M.gguf"
    assert paths["models"].name == "models"


def test_unknown_profile_raises():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent-profile-xyz")
