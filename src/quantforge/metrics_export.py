"""Metrics export and regression checks."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .metrics_store import load_history
from .safe_io import read_json, resolve_under_root


def export_history_csv(metrics_dir: Path, output: Path) -> Path:
    runs = load_history(metrics_dir)
    output = resolve_under_root(output, PROJECT_ROOT)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "profile",
                "model",
                "quantize",
                "backend",
                "avg_tokens_per_sec",
                "load_sec",
                "avg_generation_sec",
                "gpu_speedup",
            ]
        )
        for run in runs:
            speedup = run.get("summary", {}).get("gpu_speedup", "")
            for r in run.get("results", []):
                writer.writerow(
                    [
                        run.get("timestamp", ""),
                        run.get("profile", ""),
                        run.get("model", ""),
                        run.get("quantize", ""),
                        r.get("backend", ""),
                        r.get("avg_tokens_per_sec", ""),
                        r.get("load_sec", ""),
                        r.get("avg_generation_sec", ""),
                        speedup,
                    ]
                )
    return output


def load_baseline(path: Path) -> dict[str, Any]:
    data = read_json(path, root=PROJECT_ROOT, default={})
    return data if isinstance(data, dict) else {}


def check_regression(
    current: dict[str, Any],
    baseline: dict[str, Any],
    tolerance: float = 0.2,
) -> list[str]:
    """Return list of failures if any backend is outside tolerance."""
    failures: list[str] = []
    base_results = {r["backend"]: r for r in baseline.get("results", [])}
    cur_results = {r["backend"]: r for r in current.get("results", [])}

    for backend, base in base_results.items():
        cur = cur_results.get(backend)
        if not cur:
            failures.append(f"Missing backend in current run: {backend}")
            continue
        base_tps = float(base.get("avg_tokens_per_sec", 0))
        cur_tps = float(cur.get("avg_tokens_per_sec", 0))
        if base_tps <= 0:
            continue
        delta = abs(cur_tps - base_tps) / base_tps
        if delta > tolerance:
            failures.append(
                f"{backend}: {cur_tps:.2f} tok/s vs baseline {base_tps:.2f} "
                f"({delta * 100:.1f}% change, limit {tolerance * 100:.0f}%)"
            )
    return failures


def run_metrics_export(metrics_dir: Path, output: Path) -> int:
    if not load_history(metrics_dir):
        print(f"No history in {metrics_dir}")
        return 1
    path = export_history_csv(metrics_dir, output)
    print(f"Exported: {path}")
    return 0


def run_regression_check(
    metrics_dir: Path,
    baseline_path: Path,
    tolerance: float = 0.2,
) -> int:
    from .metrics_store import latest_path

    latest = latest_path(metrics_dir)
    if not latest.exists():
        print(f"No latest benchmark: {latest}", file=sys.stderr)
        return 1
    if not baseline_path.exists():
        print(f"Baseline not found: {baseline_path}", file=sys.stderr)
        return 1

    current = read_json(latest, root=PROJECT_ROOT)
    baseline = load_baseline(baseline_path)
    failures = check_regression(current, baseline, tolerance)

    print("Regression check")
    print(f"  Baseline: {baseline_path.name}")
    print(f"  Current:  {latest.name}")
    print(f"  Tolerance: {tolerance * 100:.0f}%")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nPASSED: all backends within tolerance.")
    return 0
