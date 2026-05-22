"""ChatML inference helper tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantforge.inference import CHAT_FORMAT, IM_END, STOP_TOKENS, system_prompt  # noqa: E402
from quantforge.config import load_config  # noqa: E402


def test_chat_format():
    assert CHAT_FORMAT == "chatml"


def test_stop_tokens_contain_im_end():
    assert IM_END in STOP_TOKENS
    assert IM_END == "<|" + "im_end" + "|>"


def test_system_prompt_from_config():
    cfg = load_config("qwen2.5-coder-7b")
    prompt = system_prompt(cfg)
    assert "Qwen" in prompt
