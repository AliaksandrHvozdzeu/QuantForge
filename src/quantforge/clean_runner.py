"""Disk cleanup for models, GGUF files, and logs."""

from __future__ import annotations

import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .config import load_config, paths_from_config
from .utils import format_size


@dataclass
class CleanItem:
    path: Path
    size: int
    reason: str


def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def collect_clean_items(
    config: dict,
    *,
    remove_inactive_gguf: bool = True,
    remove_base_weights: bool = True,
    logs_keep_days: int = 14,
) -> list[CleanItem]:
    paths = paths_from_config(config)
    models_dir = paths["models"]
    logs_dir = paths["logs"]
    model_cfg = config.get("model", {})
    active_gguf = model_cfg.get("gguf_output", "")
    active_base = model_cfg.get("base_dir", "")
    items: list[CleanItem] = []

    if remove_inactive_gguf:
        for f in models_dir.glob("*.gguf"):
            if f.name != active_gguf:
                items.append(
                    CleanItem(f, f.stat().st_size, f"inactive GGUF (active: {active_gguf})")
                )

    if remove_base_weights:
        for d in models_dir.iterdir():
            if not d.is_dir() or d.name.startswith("."):
                continue
            if d.name != active_base:
                items.append(
                    CleanItem(d, _dir_size(d), f"base weights (active: {active_base})")
                )

    if logs_keep_days >= 0 and logs_dir.is_dir():
        cutoff = time.time() - logs_keep_days * 86400
        for f in logs_dir.glob("run-*.log"):
            if f.stat().st_mtime < cutoff:
                items.append(CleanItem(f, f.stat().st_size, f"log older than {logs_keep_days}d"))

    return items


def run_clean(
    profile: str | None = None,
    *,
    dry_run: bool = False,
    remove_inactive_gguf: bool = True,
    remove_base_weights: bool = True,
    logs_keep_days: int = 14,
    yes: bool = False,
) -> int:
    config = load_config(profile)
    items = collect_clean_items(
        config,
        remove_inactive_gguf=remove_inactive_gguf,
        remove_base_weights=remove_base_weights,
        logs_keep_days=logs_keep_days,
    )

    if not items:
        print("Nothing to clean.")
        return 0

    total = sum(i.size for i in items)
    print(f"\nClean plan (profile: {config.get('profile')})")
    print("=" * 60)
    for item in items:
        print(f"  {format_size(item.size):>10}  {item.path.name}")
        print(f"             {item.reason}")
    print(f"\nTotal reclaimable: {format_size(total)}")

    if dry_run:
        print("\nDry run — no files removed.")
        return 0

    if not yes:
        try:
            answer = input("\nDelete these items? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 130
        if answer not in ("y", "yes"):
            print("Cancelled.")
            return 0

    errors = []
    for item in items:
        try:
            if item.path.is_dir():
                shutil.rmtree(item.path)
            else:
                item.path.unlink()
            print(f"Removed: {item.path}")
        except OSError as exc:
            errors.append(f"{item.path}: {exc}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"\nFreed approximately {format_size(total)}.")
    return 0
