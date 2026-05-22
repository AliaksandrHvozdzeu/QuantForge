#!/usr/bin/env python3
"""CLI entry for config loading (used by PowerShell)."""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_src = _root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from quantforge.config import apply_env, config_to_json, load_config  # noqa: E402

config_as_json = config_to_json


def main():
    profile = None
    apply = "--apply-env" in sys.argv
    print_json = "--print-json" in sys.argv
    for i, arg in enumerate(sys.argv):
        if arg == "--profile" and i + 1 < len(sys.argv):
            profile = sys.argv[i + 1]

    cfg = load_config(profile)
    if apply:
        apply_env(cfg)
    if print_json or not apply:
        print(config_as_json(cfg))


if __name__ == "__main__":
    main()
