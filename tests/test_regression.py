"""Benchmark regression logic tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.metrics_export import check_regression  # noqa: E402


def test_regression_within_tolerance():
    baseline = {
        "results": [
            {"backend": "cpu", "avg_tokens_per_sec": 10.0},
            {"backend": "gpu", "avg_tokens_per_sec": 50.0},
        ]
    }
    current = {
        "results": [
            {"backend": "cpu", "avg_tokens_per_sec": 11.0},
            {"backend": "gpu", "avg_tokens_per_sec": 48.0},
        ]
    }
    assert check_regression(current, baseline, tolerance=0.2) == []


def test_regression_fails_when_outside_tolerance():
    baseline = {
        "results": [{"backend": "gpu", "avg_tokens_per_sec": 50.0}],
    }
    current = {
        "results": [{"backend": "gpu", "avg_tokens_per_sec": 30.0}],
    }
    failures = check_regression(current, baseline, tolerance=0.2)
    assert len(failures) == 1
    assert "gpu" in failures[0]
