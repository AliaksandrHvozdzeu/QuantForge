"""models/manifest.json management."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def file_sha256(path: Path, chunk_mb: int = 8) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_mb * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"models": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"models": []}


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

    manifest = read_manifest(manifest_path)
    models_list = [
        m for m in manifest.get("models", []) if m.get("gguf_file") != entry["gguf_file"]
    ]
    models_list.append(entry)
    manifest["models"] = models_list
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path
