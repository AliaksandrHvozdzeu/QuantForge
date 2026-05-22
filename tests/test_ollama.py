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


def test_ollama_verify_missing_gguf_warn_only(monkeypatch, capsys):
    """CI has no GGUF in repo; verify should pass on Modelfile alone."""
    from pathlib import Path

    from quantforge.ollama_runner import run_ollama_verify

    monkeypatch.setattr("quantforge.ollama_runner.ollama_available", lambda: False)
    real_exists = Path.exists

    def fake_exists(self: Path) -> bool:
        if self.suffix.lower() == ".gguf":
            return False
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)

    assert run_ollama_verify("qwen2.5-coder-7b", require_gguf=False) == 0
    assert "WARN: GGUF not found" in capsys.readouterr().out

    assert run_ollama_verify("qwen2.5-coder-7b", require_gguf=True) == 1
    assert "FAIL: GGUF not found" in capsys.readouterr().out
