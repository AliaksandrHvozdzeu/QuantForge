"""OpenAI-compatible API server (llama-cpp-python)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from .config import PROJECT_ROOT, load_config, paths_from_config
from .safe_io import write_utf8


def build_server_config(
    config: dict[str, Any],
    *,
    host: str | None = None,
    port: int | None = None,
    n_gpu_layers: int | None = None,
    docker: bool = False,
) -> dict[str, Any]:
    """Build llama_cpp.server YAML config from QuantForge profile."""
    paths = paths_from_config(config)
    api = config.get("api", {})
    chat = config.get("chat", {})
    model = config.get("model", {})

    if docker:
        model_path = f"/models/{model.get('gguf_output', '')}"
    else:
        model_path = str(paths["gguf"].resolve())

    if n_gpu_layers is not None:
        layers = n_gpu_layers
    elif docker and os.environ.get("QF_API_N_GPU_LAYERS"):
        layers = int(os.environ["QF_API_N_GPU_LAYERS"])
    else:
        layers = int(api.get("n_gpu_layers", -1))

    return {
        "host": host or api.get("host", "127.0.0.1"),
        "port": port if port is not None else int(api.get("port", 8000)),
        "api_key": api.get("api_key"),
        "models": [
            {
                "model": model_path,
                "model_alias": api.get("model_alias", config.get("profile", "default")),
                "chat_format": chat.get("format", "chatml"),
                "n_ctx": int(api.get("n_ctx", 8192)),
                "n_gpu_layers": layers,
                "n_threads": int(api.get("n_threads", 8)),
                "verbose": bool(api.get("verbose", False)),
            }
        ],
    }


def write_server_config(config: dict[str, Any], path: Path) -> Path:
    text = yaml.safe_dump(config, sort_keys=False)
    return write_utf8(path, text, root=PROJECT_ROOT)


def run_serve(
    profile: str | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    cpu: bool = False,
    docker: bool = False,
    config_file: Path | None = None,
) -> int:
    from . import llama_env  # noqa: F401

    cfg = load_config(profile)
    paths = paths_from_config(cfg)
    gguf = paths["gguf"]

    if not docker and not gguf.exists():
        print(f"Model not found: {gguf}", file=sys.stderr)
        print("Run .\\run_optimization.ps1 first.", file=sys.stderr)
        return 1

    layers = 0 if cpu else None
    server_cfg = build_server_config(
        cfg,
        host=host,
        port=port,
        n_gpu_layers=layers,
        docker=docker,
    )

    if config_file:
        cfg_path = write_server_config(server_cfg, config_file)
    else:
        out_dir = paths["root"] / "config" / "generated"
        cfg_path = write_server_config(server_cfg, out_dir / "api-server.yaml")

    api = cfg.get("api", {})
    base_url = f"http://{server_cfg['host']}:{server_cfg['port']}"
    openai_base = f"{base_url.rstrip('/')}{api.get('openai_path', '/v1')}"

    print("QuantForge API server")
    print(f"  Profile:     {cfg.get('profile')}")
    print(f"  Model:       {server_cfg['models'][0]['model']}")
    print(f"  Chat format: {server_cfg['models'][0]['chat_format']}")
    print(f"  OpenAI URL:  {openai_base}")
    print(f"  Model name:  {server_cfg['models'][0]['model_alias']}")
    print(f"  Docs:        {base_url}/docs")
    print(f"  Config:      {cfg_path}")
    print()

    try:
        from llama_cpp.server.__main__ import main as server_main
    except ImportError as exc:
        print(
            'ERROR: API dependencies missing. Install with:\n  pip install -e ".[api]"',
            file=sys.stderr,
        )
        print(f"  ({exc})", file=sys.stderr)
        return 1

    argv = ["quantforge", "serve", "--config_file", str(cfg_path)]
    if host:
        argv.extend(["--host", host])
    if port is not None:
        argv.extend(["--port", str(port)])

    old_argv = sys.argv
    sys.argv = argv
    try:
        server_main()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        return 0
    finally:
        sys.argv = old_argv
    return 0


def config_preview(profile: str | None = None, docker: bool = False) -> str:
    cfg = load_config(profile)
    doc = build_server_config(cfg, docker=docker)
    return json.dumps(doc, indent=2, ensure_ascii=False)
