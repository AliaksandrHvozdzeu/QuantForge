"""models/manifest.json management."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .safe_io import read_json, resolve_under_root, write_json


def file_sha256(path: Path, chunk_mb: int = 8) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_mb * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(path: Path, *, root: Path) -> dict[str, Any]:
    """Load manifest JSON; *path* must resolve under *root* (blocks path injection)."""
    data = read_json(path, root=root, default={"models": []})
    if not isinstance(data, dict):
        return {"models": []}
    if "models" not in data:
        data["models"] = []
    return data


def write_manifest_entry(
    manifest_path: Path,
    config: dict,
    gguf_path: Path,
    sha256: str,
    project_root: Path,
) -> Path:
    model = config.get("model", {})
    entry = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "profile": config.get("profile"),
        "model_repo": model.get("repo"),
        "gguf_file": gguf_path.name,
        "gguf_path": str(gguf_path.relative_to(project_root)),
        "quantize_type": config.get("quantize_type"),
        "size_bytes": gguf_path.stat().st_size,
        "sha256": sha256,
    }

    safe_manifest = resolve_under_root(manifest_path, project_root)
    manifest = read_manifest(safe_manifest, root=project_root)
    models_list = [
        m for m in manifest.get("models", []) if m.get("gguf_file") != entry["gguf_file"]
    ]
    models_list.append(entry)
    manifest["models"] = models_list
    write_json(safe_manifest, manifest, root=project_root)
    return safe_manifest
