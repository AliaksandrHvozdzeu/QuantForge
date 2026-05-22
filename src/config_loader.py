"""
Load QuantForge YAML configuration (legacy import path).
"""

from __future__ import annotations

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from quantforge.config import (  # noqa: E402
    config_to_json,
)

config_as_json = config_to_json
