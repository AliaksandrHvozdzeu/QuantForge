#!/usr/bin/env python3
"""Validate GGUF output (wrapper for quantforge CLI)."""

from __future__ import annotations

import sys

from quantforge.validate_runner import run_validate


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate GGUF output")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--require-smoke", action="store_true")
    parser.add_argument("--no-manifest", action="store_true")
    args = parser.parse_args()
    return run_validate(
        args.profile,
        smoke_test=args.smoke_test,
        require_smoke=args.require_smoke,
        write_manifest=not args.no_manifest,
    )


if __name__ == "__main__":
    sys.exit(main())
