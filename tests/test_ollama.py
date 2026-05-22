"""Ollama Modelfile validation tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.ollama_runner import validate_modelfile  # noqa: E402


def test_modelfile_valid():
    path = ROOT / "ollama" / "Modelfile"
    errors = validate_modelfile(path)
    assert errors == [], f"Modelfile errors: {errors}"
