"""Safe I/O path validation tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.safe_io import resolve_under_root, write_json, write_utf8  # noqa: E402


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
