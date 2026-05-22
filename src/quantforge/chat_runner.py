"""Interactive chat."""

from __future__ import annotations

import sys

from . import llama_env  # noqa: F401
from .config import load_config, paths_from_config
from .inference import chat_completion, extract_reply, llama_kwargs, system_prompt


def run_chat(profile: str | None = None, n_gpu_layers: int = -1) -> int:
    from llama_cpp import Llama

    config = load_config(profile)
    paths = paths_from_config(config)
    gguf = paths["gguf"]

    if not gguf.exists():
        print(f"Model not found: {gguf}", file=sys.stderr)
        return 1

    print(f"Loading {gguf}...")
    llm = Llama(
        model_path=str(gguf),
        n_ctx=8192,
        n_gpu_layers=n_gpu_layers,
        n_threads=8,
        verbose=False,
        **llama_kwargs(),
    )
    sys_msg = system_prompt(config)
    print("Ready. Empty line or 'quit' to exit.\n")

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not user or user.lower() in ("quit", "exit", "q"):
            break
        resp = chat_completion(llm, user, system=sys_msg, max_tokens=512)
        print(f"\nAssistant:\n{extract_reply(resp)}\n")
    return 0
