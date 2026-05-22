#!/usr/bin/env python3
"""Interactive chat (wrapper for quantforge CLI)."""

from __future__ import annotations

import sys

from quantforge.chat_runner import run_chat


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Interactive chat")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()
    layers = 0 if args.cpu else -1
    return run_chat(args.profile, n_gpu_layers=layers)


if __name__ == "__main__":
    sys.exit(main())
