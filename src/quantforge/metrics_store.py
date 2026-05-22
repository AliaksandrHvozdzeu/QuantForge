"""Benchmark history and comparison."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .safe_io import append_jsonl_line, write_json


def history_path(metrics_dir: Path) -> Path:
    return metrics_dir / "benchmark_history.jsonl"


def latest_path(metrics_dir: Path) -> Path:
    return metrics_dir / "benchmark_results.json"


def append_run(metrics_dir: Path, payload: dict[str, Any]) -> Path:
    metrics_dir.mkdir(parents=True, exist_ok=True)
    hp = history_path(metrics_dir)
    return append_jsonl_line(hp, payload, root=PROJECT_ROOT)


def save_latest(metrics_dir: Path, payload: dict[str, Any]) -> Path:
    metrics_dir.mkdir(parents=True, exist_ok=True)
    lp = latest_path(metrics_dir)
    return write_json(lp, payload, root=PROJECT_ROOT)


def load_history(metrics_dir: Path, limit: int | None = None) -> list[dict[str, Any]]:
    hp = history_path(metrics_dir)
    if not hp.exists():
        return []
    runs = []
    for line in hp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            runs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if limit:
        return runs[-limit:]
    return runs


def build_benchmark_payload(
    config: dict,
    gguf_path: Path,
    results: list[dict],
) -> dict[str, Any]:
    from .config import model_display_name

    cpu = next((r for r in results if r.get("backend") == "cpu"), None)
    gpu = next((r for r in results if r.get("backend") == "gpu"), None)
    summary: dict[str, Any] = {}
    if cpu and gpu and cpu.get("avg_tps", 0) > 0:
        summary["gpu_speedup"] = round(gpu["avg_tps"] / cpu["avg_tps"], 2)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "profile": config.get("profile"),
        "model": model_display_name(config),
        "quantize": config.get("quantize_type"),
        "gguf_file": gguf_path.name,
        "gguf_size_bytes": gguf_path.stat().st_size if gguf_path.exists() else None,
        "results": [
            {
                "backend": r["backend"],
                "backend_label": r["backend_label"],
                "avg_tokens_per_sec": round(r["avg_tps"], 2),
                "avg_generation_sec": round(r["avg_time"], 3),
                "load_sec": round(r["load_time"], 3),
            }
            for r in results
        ],
        "summary": summary,
    }


def print_comparison_table(runs: list[dict[str, Any]]) -> None:
    if not runs:
        print("No benchmark history found.")
        return

    print(f"\n{'Timestamp':<28} {'Profile':<20} {'Backend':<6} {'tok/s':<10} {'GPU x':<8}")
    print("-" * 80)
    for run in runs:
        ts = run.get("timestamp", "")[:19].replace("T", " ")
        profile = str(run.get("profile", ""))[:18]
        speedup = run.get("summary", {}).get("gpu_speedup", "-")
        for r in run.get("results", []):
            print(
                f"{ts:<28} {profile:<20} {r.get('backend_label', '?'):<6} "
                f"{r.get('avg_tokens_per_sec', 0):<10} {speedup!s:<8}"
            )


def compare_last_two(metrics_dir: Path) -> None:
    runs = load_history(metrics_dir, limit=2)
    if len(runs) < 2:
        print("Need at least 2 runs in history to compare.")
        print(f"History file: {history_path(metrics_dir)}")
        return

    old, new = runs[0], runs[1]
    print("\nBenchmark comparison (older -> newer)")
    print("=" * 60)
    print(f"Older: {old.get('timestamp')}")
    print(f"Newer: {new.get('timestamp')}")

    for backend in ("cpu", "gpu"):
        o = next((r for r in old.get("results", []) if r.get("backend") == backend), None)
        n = next((r for r in new.get("results", []) if r.get("backend") == backend), None)
        if not o or not n:
            continue
        delta = n["avg_tokens_per_sec"] - o["avg_tokens_per_sec"]
        pct = (delta / o["avg_tokens_per_sec"] * 100) if o["avg_tokens_per_sec"] else 0
        print(f"\n{backend.upper()}:")
        print(
            f"  {o['avg_tokens_per_sec']:.2f} -> {n['avg_tokens_per_sec']:.2f} tok/s ({pct:+.1f}%)"
        )
