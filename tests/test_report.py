"""Tests for Markdown report generation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.report_runner import render_report_markdown  # noqa: E402


def test_render_report_markdown():
    run = {
        "timestamp": "2026-05-22T12:00:00+00:00",
        "profile": "qwen2.5-coder-7b",
        "model": "Qwen2.5-Coder-7B Q5_K_M",
        "quantize": "Q5_K_M",
        "gguf_file": "Qwen2.5-Coder-7B-Q5_K_M.gguf",
        "gguf_size_bytes": 5_000_000_000,
        "results": [
            {
                "backend": "cpu",
                "backend_label": "CPU",
                "avg_tokens_per_sec": 10.5,
                "load_sec": 2.1,
                "avg_generation_sec": 1.2,
            },
            {
                "backend": "gpu",
                "backend_label": "GPU",
                "avg_tokens_per_sec": 49.0,
                "load_sec": 2.0,
                "avg_generation_sec": 0.3,
            },
        ],
        "summary": {"gpu_speedup": 4.67},
    }
    md = render_report_markdown(run, [run])
    assert "# QuantForge Benchmark Report" in md
    assert "Q5_K_M" in md
    assert "4.67" in md
    assert "CPU" in md and "GPU" in md
