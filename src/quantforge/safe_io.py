"""Safe path resolution and file writes (Sonar / path-traversal hardening)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_utf8(path: Path, *, root: Path) -> str:
    """Read UTF-8 text only if *path* is under *root*."""
    safe = resolve_under_root(path, root)
    return safe.read_text(encoding="utf-8")


def read_json(path: Path, *, root: Path, default: Any | None = None) -> Any:
    """Read JSON only if *path* is under *root*."""
    safe = resolve_under_root(path, root)
    if not safe.exists():
        return {} if default is None else default
    try:
        return json.loads(safe.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {} if default is None else default


def resolve_under_root(path: Path, root: Path) -> Path:
    """Resolve *path* and ensure it stays under *root* (blocks ``../`` escapes)."""
    root_resolved = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        msg = f"Refusing path outside project root ({root_resolved}): {path}"
        raise ValueError(msg) from None
    return resolved


def write_utf8(path: Path, content: str, *, root: Path) -> Path:
    """Write UTF-8 text only if *path* is under *root*."""
    target = resolve_under_root(path, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def write_json(
    path: Path,
    data: Any,
    *,
    root: Path,
    indent: int | None = 2,
) -> Path:
    """Serialize JSON and write via :func:`write_utf8`."""
    text = json.dumps(data, indent=indent, ensure_ascii=False)
    return write_utf8(path, text, root=root)


def append_jsonl_line(path: Path, payload: dict[str, Any], *, root: Path) -> Path:
    """Append one JSONL record if *path* is under *root*."""
    target = resolve_under_root(path, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with open(target, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return target
