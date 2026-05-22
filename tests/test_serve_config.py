"""Tests for API server config generation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.config import load_config  # noqa: E402
from quantforge.serve_runner import build_server_config  # noqa: E402


def test_build_server_config_chatml():
    cfg = load_config("qwen2.5-coder-7b")
    doc = build_server_config(cfg)
    assert doc["port"] == 8000
    assert doc["models"][0]["chat_format"] == "chatml"
    assert doc["models"][0]["model_alias"] == "qwen2.5-coder-q5"
    assert doc["models"][0]["model"].endswith("Qwen2.5-Coder-7B-Q5_K_M.gguf")


def test_build_server_config_docker_paths():
    cfg = load_config("qwen2.5-coder-7b")
    doc = build_server_config(cfg, docker=True)
    assert doc["models"][0]["model"] == "/models/Qwen2.5-Coder-7B-Q5_K_M.gguf"


def test_build_server_config_cpu_override():
    cfg = load_config("qwen2.5-coder-7b")
    doc = build_server_config(cfg, n_gpu_layers=0)
    assert doc["models"][0]["n_gpu_layers"] == 0
