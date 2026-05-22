"""Model paths from YAML config or environment."""

from __future__ import annotations

import os

from quantforge.config import PROJECT_ROOT, load_config, paths_from_config

try:
    profile = os.environ.get("QUANTFORGE_PROFILE")
    _cfg = load_config(profile)
    _paths = paths_from_config(_cfg)
    _model = _cfg.get("model", {})
    MODEL_REPO = _model.get("repo", "Qwen/Qwen2.5-Coder-7B-Instruct")
    MODEL_BASE_DIR = _model.get("base_dir", "qwen2.5-coder-7b-instruct-base")
    GGUF_OUTPUT = _model.get("gguf_output", "Qwen2.5-Coder-7B-Q5_K_M.gguf")
    QUANT_TYPE = _cfg.get("quantize_type", "Q5_K_M")
    MODEL_DISPLAY_NAME = f"{_model.get('display_name', 'Model')} {QUANT_TYPE}"
    MODELS_DIR = _paths["models"]
    GGUF_PATH = _paths["gguf"]
except Exception:
    MODEL_REPO = os.environ.get("MODEL_REPO", "Qwen/Qwen2.5-Coder-7B-Instruct")
    MODEL_BASE_DIR = os.environ.get("MODEL_BASE_DIR", "qwen2.5-coder-7b-instruct-base")
    GGUF_OUTPUT = os.environ.get("GGUF_OUTPUT", "Qwen2.5-Coder-7B-Q5_K_M.gguf")
    QUANT_TYPE = os.environ.get("QUANT_TYPE", "Q5_K_M")
    MODEL_DISPLAY_NAME = os.environ.get("MODEL_DISPLAY_NAME", f"Qwen2.5-Coder-7B {QUANT_TYPE}")
    MODELS_DIR = PROJECT_ROOT / os.environ.get("QF_MODELS_DIR", "models")
    GGUF_PATH = MODELS_DIR / GGUF_OUTPUT
