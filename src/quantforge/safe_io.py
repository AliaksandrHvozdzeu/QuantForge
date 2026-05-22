"""Safe path resolution and file I/O (Sonar S2083 / path-traversal hardening)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Fixed relative locations (never built from user-controlled path strings)
MANIFEST_PARTS = ("models", "manifest.json")


def _reject_unsafe_segments(*parts: str) -> None:
    for part in parts:
        if not part or part in (".", ".."):
            raise ValueError(f"Unsafe path segment: {part!r}")
        if "/" in part or "\\" in part or os.sep in part:
            raise ValueError(f"Unsafe path segment: {part!r}")


def path_from_root(root: Path, *parts: str) -> Path:
    """Build an absolute path only from trusted *root* and literal *parts*."""
    _reject_unsafe_segments(*parts)
    return root.resolve().joinpath(*parts)


def resolve_under_root(path: Path, root: Path) -> Path:
    """Map *path* to a trusted location under *root* (rebuilt from root, not user path)."""
    base = root.resolve()
    absolute = path.resolve()
    if not absolute.is_relative_to(base):
        msg = f"Refusing path outside project root ({base}): {path}"
        raise ValueError(msg)
    relative = absolute.relative_to(base)
    if ".." in relative.parts:
        raise ValueError(f"Unsafe relative path: {relative}")
    return path_from_root(base, *relative.parts)


def read_utf8(path: Path, *, root: Path) -> str:
    """Read UTF-8 text only if *path* resolves under *root*."""
    trusted = resolve_under_root(path, root)
    with open(trusted, encoding="utf-8") as handle:
        return handle.read()


def read_json(path: Path, *, root: Path, default: Any | None = None) -> Any:
    """Read JSON only if *path* resolves under *root*."""
    trusted = resolve_under_root(path, root)
    if not trusted.exists():
        return {} if default is None else default
    try:
        with open(trusted, encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {} if default is None else default


def read_json_at(root: Path, *parts: str, default: Any | None = None) -> Any:
    """Read JSON at root / part1 / part2 / ... (literal segments only)."""
    return read_json(path_from_root(root, *parts), root=root, default=default)


def write_utf8(path: Path, content: str, *, root: Path) -> Path:
    """Write UTF-8 text only if *path* resolves under *root*."""
    trusted = resolve_under_root(path, root)
    trusted.parent.mkdir(parents=True, exist_ok=True)
    with open(trusted, "w", encoding="utf-8") as handle:
        handle.write(content)
    return trusted


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


def write_json_at(root: Path, *parts: str, data: Any, indent: int | None = 2) -> Path:
    """Write JSON at root / part1 / part2 / ... (literal segments only)."""
    return write_json(path_from_root(root, *parts), data, root=root, indent=indent)


def append_jsonl_line(path: Path, payload: dict[str, Any], *, root: Path) -> Path:
    """Append one JSONL record if *path* resolves under *root*."""
    trusted = resolve_under_root(path, root)
    trusted.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with open(trusted, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return trusted
