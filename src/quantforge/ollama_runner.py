"""Ollama integration checks."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from .config import PROJECT_ROOT, load_config
from .inference import IM_END

IM_START = "<|im_start|>"


def modelfile_path(config: dict) -> Path:
    ollama = config.get("ollama", {})
    rel = ollama.get("modelfile", "ollama/Modelfile")
    return PROJECT_ROOT / rel


def validate_modelfile(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Modelfile not found: {path}"]

    text = path.read_text(encoding="utf-8")
    if "TEMPLATE" not in text:
        errors.append("Modelfile missing TEMPLATE block")
    if IM_START not in text:
        errors.append(f"Modelfile missing {IM_START}")
    if IM_END not in text:
        errors.append(f"Modelfile missing {IM_END}")
    if "redacted_im_end" in text or "redacted" in text.lower():
        errors.append("Modelfile contains invalid placeholder tokens (redacted_im_end)")
    if "FROM " not in text:
        errors.append("Modelfile missing FROM (GGUF path)")
    return errors


def ollama_available() -> bool:
    return shutil.which("ollama") is not None


def ollama_model_exists(name: str) -> bool:
    if not ollama_available():
        return False
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode != 0:
            return False
        pattern = re.compile(rf"^\s*{re.escape(name)}\s", re.MULTILINE)
        return bool(pattern.search(result.stdout))
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def run_ollama_verify(
    profile: str | None = None,
    *,
    require_model: bool = False,
    require_gguf: bool = False,
) -> int:
    config = load_config(profile)
    model_name = config.get("ollama", {}).get("model_name", "")
    mf = modelfile_path(config)
    gguf = PROJECT_ROOT / config.get("paths", {}).get("models", "models")
    gguf = gguf / config.get("model", {}).get("gguf_output", "")

    print("Ollama verification")
    print("=" * 50)
    errors: list[str] = []

    mf_errors = validate_modelfile(mf)
    errors.extend(mf_errors)
    if mf_errors:
        for e in mf_errors:
            print(f"  FAIL: {e}")
    else:
        print(f"  OK: Modelfile ({mf.name})")

    if gguf.exists():
        print(f"  OK: GGUF ({gguf.name})")
    else:
        msg = f"GGUF not found: {gguf}"
        if require_gguf:
            errors.append(msg)
            print(f"  FAIL: {msg}")
        else:
            print(f"  WARN: {msg}")

    if not ollama_available():
        print("  WARN: ollama CLI not in PATH")
        if require_model:
            errors.append("ollama CLI not found")
    else:
        print("  OK: ollama CLI")
        if model_name:
            if ollama_model_exists(model_name):
                print(f"  OK: model '{model_name}' registered")
            else:
                msg = f"Ollama model '{model_name}' not found (run setup_ollama.ps1)"
                if require_model:
                    errors.append(msg)
                print(f"  WARN: {msg}")

    print()
    if errors:
        print("Verification FAILED")
        return 1
    print("Verification passed.")
    return 0
