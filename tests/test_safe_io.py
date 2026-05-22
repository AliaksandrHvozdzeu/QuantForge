"""Safe I/O path validation tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.manifest import read_manifest  # noqa: E402
from quantforge.safe_io import read_json, resolve_under_root, write_json, write_utf8  # noqa: E402


def test_resolve_under_root_allows_child(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    child = root / "metrics" / "report.md"
    assert resolve_under_root(child, root) == child.resolve()


def test_resolve_under_root_blocks_traversal(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "escape.txt"
    with pytest.raises(ValueError, match="outside project root"):
        resolve_under_root(outside, root)


def test_write_utf8_under_root(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    target = root / "out.txt"
    write_utf8(target, "hello", root=root)
    assert target.read_text(encoding="utf-8") == "hello"


def test_write_json_under_root(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    target = root / "data.json"
    write_json(target, {"a": 1}, root=root)
    assert '"a": 1' in target.read_text(encoding="utf-8")


def test_read_json_blocks_traversal(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "secret.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="outside project root"):
        read_json(outside, root=root)


def test_read_manifest_under_root(tmp_path: Path):
    root = tmp_path / "project"
    models = root / "models"
    models.mkdir(parents=True)
    manifest = models / "manifest.json"
    write_json(manifest, {"models": [{"gguf_file": "a.gguf"}]}, root=root)
    data = read_manifest(manifest, root=root)
    assert len(data["models"]) == 1
