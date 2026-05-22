"""
ChatML helpers for Qwen2.5-Instruct (legacy import path).
Re-exports quantforge.inference.
"""

from quantforge.inference import (  # noqa: F401
    CHAT_FORMAT,
    DEFAULT_SYSTEM,
    IM_END,
    STOP_TOKENS,
    chat_completion,
    extract_reply,
    llama_kwargs,
    system_prompt,
)

SYSTEM_PROMPT = DEFAULT_SYSTEM
