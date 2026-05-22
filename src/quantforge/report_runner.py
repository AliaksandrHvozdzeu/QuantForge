"""Markdown benchmark reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import load_config, paths_from_config
from .metrics_store import latest_path, load_history
from .utils import format_size


def _format_ts(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return ts[:19] if ts else "—"


def render_report_markdown(run: dict[str, Any], history: list[dict[str, Any]]) -> str:
    lines = [
        "# QuantForge Benchmark Report",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Latest run",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Timestamp | {_format_ts(run.get('timestamp', ''))} |",
        f"| Profile | {run.get('profile', '—')} |",
        f"| Model | {run.get('model', '—')} |",
        f"| Quantization | {run.get('quantize', '—')} |",
        f"| GGUF file | {run.get('gguf_file', '—')} |",
    ]
    size = run.get("gguf_size_bytes")
    if size:
        lines.append(f"| GGUF size | {format_size(int(size))} |")

    lines.extend(["", "## Results", "", "| Backend | tok/s | Load (s) | Gen (s) |", "|---------|-------|----------|---------|"])
    for r in run.get("results", []):
        lines.append(
            f"| {r.get('backend_label', '?')} "
            f"| {r.get('avg_tokens_per_sec', 0):.2f} "
            f"| {r.get('load_sec', 0):.3f} "
            f"| {r.get('avg_generation_sec', 0):.3f} |"
        )

    speedup = run.get("summary", {}).get("gpu_speedup")
    if speedup:
        lines.extend(["", f"**GPU speedup:** {speedup}x vs CPU", ""])

    if len(history) > 1:
        lines.extend(["", "## History (last runs)", "", "| Date | Profile | Backend | tok/s |", "|------|---------|---------|-------|"])
        for h in history[-5:]:
            ts = _format_ts(h.get("timestamp", ""))
            prof = h.get("profile", "")
            for r in h.get("results", []):
                lines.append(
                    f"| {ts} | {prof} | {r.get('backend_label', '?')} | {r.get('avg_tokens_per_sec', 0):.2f} |"
                )

    lines.append("")
    return "\n".join(lines)


def run_report(
    profile: str | None = None,
    *,
    output: Path | None = None,
) -> int:
    config = load_config(profile)
    metrics_dir = paths_from_config(config)["metrics"]
    latest = latest_path(metrics_dir)

    if not latest.exists():
        print(f"No benchmark data: {latest}")
        return 1

    run = json.loads(latest.read_text(encoding="utf-8"))
    history = load_history(metrics_dir)
    md = render_report_markdown(run, history)

    out = output or metrics_dir / "report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"Report: {out}")
    return 0
