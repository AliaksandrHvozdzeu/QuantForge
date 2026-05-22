#!/usr/bin/env python3
"""Benchmark wrapper (delegates to quantforge package)."""

from __future__ import annotations

import sys

from quantforge.benchmark_runner import run_benchmark


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark GGUF model")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--cpu-only", action="store_true")
    parser.add_argument("--gpu-only", action="store_true")
    parser.add_argument("--force-gpu", action="store_true")
    args = parser.parse_args()
    return run_benchmark(
        args.profile,
        cpu_only=args.cpu_only,
        gpu_only=args.gpu_only,
        force_gpu=args.force_gpu,
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
