"""models/manifest.json management."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .safe_io import MANIFEST_PARTS, read_json_at, resolve_under_root, write_json_at


def manifest_path(root: Path) -> Path:
    """Canonical manifest location (fixed relative path under *root*)."""
    from .safe_io import path_from_root

    return path_from_root(root, *MANIFEST_PARTS)


def file_sha256(path: Path, *, root: Path, chunk_mb: int = 8) -> str:
    safe = resolve_under_root(path, root)
    digest = hashlib.sha256()
    with open(safe, "rb") as handle:
        while chunk := handle.read(chunk_mb * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(*, root: Path) -> dict[str, Any]:
    """Load ``models/manifest.json`` under *root*."""
    data = read_json_at(root, *MANIFEST_PARTS, default={"models": []})
    if not isinstance(data, dict):
        return {"models": []}
    if "models" not in data:
        data["models"] = []
    return data


def write_manifest_entry(
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
        "gguf_path": str(resolve_under_root(gguf_path, project_root).relative_to(project_root.resolve())),
        "quantize_type": config.get("quantize_type"),
        "size_bytes": gguf_path.stat().st_size,
        "sha256": sha256,
    }

    manifest = read_manifest(root=project_root)
    models_list = [
        m for m in manifest.get("models", []) if m.get("gguf_file") != entry["gguf_file"]
    ]
    models_list.append(entry)
    manifest["models"] = models_list
    return write_json_at(project_root, *MANIFEST_PARTS, data=manifest)
