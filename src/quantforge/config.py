"""YAML configuration loading."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG = CONFIG_DIR / "default.yaml"
PROFILES_DIR = CONFIG_DIR / "profiles"


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_yaml(path: Path) -> dict:
    if yaml is None:
        raise ImportError("PyYAML required: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid config: {path}")
    return data


def load_config(profile: str | None = None) -> dict[str, Any]:
    profile = profile or os.environ.get("QUANTFORGE_PROFILE", "qwen2.5-coder-7b")
    if not DEFAULT_CONFIG.exists():
        raise FileNotFoundError(f"Missing {DEFAULT_CONFIG}")

    config = load_yaml(DEFAULT_CONFIG)
    profile_path = PROFILES_DIR / f"{profile}.yaml"
    if profile_path.exists():
        config = deep_merge(config, load_yaml(profile_path))
    elif profile != "default":
        available = [p.stem for p in PROFILES_DIR.glob("*.yaml")]
        raise FileNotFoundError(
            f"Profile '{profile}' not found. Available: {', '.join(available) or 'none'}"
        )
    config["profile"] = profile
    return config


def apply_env(config: dict[str, Any]) -> None:
    model = config.get("model", {})
    os.environ["QUANTFORGE_PROFILE"] = str(config.get("profile", "default"))
    os.environ["MODEL_REPO"] = str(model.get("repo", ""))
    os.environ["MODEL_BASE_DIR"] = str(model.get("base_dir", ""))
    os.environ["GGUF_OUTPUT"] = str(model.get("gguf_output", ""))
    os.environ["MODEL_DISPLAY_NAME"] = str(model.get("display_name", "Model"))
    os.environ["QUANT_TYPE"] = str(config.get("quantize_type", "Q5_K_M"))
    os.environ["KEEP_BASE"] = "1" if config.get("quantize", {}).get("keep_base", True) else "0"

    paths = config.get("paths", {})
    os.environ["QF_MODELS_DIR"] = str(paths.get("models", "models"))
    os.environ["QF_METRICS_DIR"] = str(paths.get("metrics", "metrics"))
    os.environ["QF_LOGS_DIR"] = str(paths.get("logs", "logs"))

    val = config.get("validation", {})
    os.environ["QF_MIN_GGUF_MB"] = str(val.get("min_gguf_size_mb", 4000))
    os.environ["QF_SMOKE_TEST"] = "1" if val.get("smoke_test") else "0"

    ollama = config.get("ollama", {})
    os.environ["OLLAMA_MODEL_NAME"] = str(ollama.get("model_name", ""))


def paths_from_config(config: dict[str, Any]) -> dict[str, Path]:
    base = PROJECT_ROOT
    p = config.get("paths", {})
    models = base / p.get("models", "models")
    return {
        "root": base,
        "models": models,
        "metrics": base / p.get("metrics", "metrics"),
        "logs": base / p.get("logs", "logs"),
        "gguf": models / config.get("model", {}).get("gguf_output", ""),
        "base_weights": models / config.get("model", {}).get("base_dir", ""),
    }


def model_display_name(config: dict[str, Any]) -> str:
    model = config.get("model", {})
    return f"{model.get('display_name', 'Model')} {config.get('quantize_type', '')}".strip()


def list_profiles() -> list[str]:
    if not PROFILES_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILES_DIR.glob("*.yaml"))


def config_to_json(config: dict[str, Any]) -> str:
    return json.dumps(config, indent=2, ensure_ascii=False)
