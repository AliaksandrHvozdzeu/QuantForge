"""GGUF validation."""

from __future__ import annotations

from pathlib import Path

from .config import load_config, paths_from_config
from .inference import chat_completion, extract_reply, llama_kwargs, system_prompt
from .manifest import file_sha256, write_manifest_entry


def validate_file(gguf_path: Path, min_size_mb: float) -> list[str]:
    errors = []
    if not gguf_path.exists():
        errors.append(f"File not found: {gguf_path}")
        return errors
    size_mb = gguf_path.stat().st_size / (1024 * 1024)
    if size_mb < min_size_mb:
        errors.append(f"Too small: {size_mb:.1f} MB (min {min_size_mb} MB)")
    return errors


def run_smoke_test(gguf_path: Path, config: dict, max_tokens: int) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    try:
        from llama_cpp import Llama

        from . import llama_env  # noqa: F401
    except ImportError as exc:
        warnings.append(f"Smoke test skipped: {exc}")
        return errors, warnings

    try:
        llm = Llama(
            model_path=str(gguf_path),
            n_ctx=512,
            n_gpu_layers=0,
            n_threads=4,
            verbose=False,
            **llama_kwargs(),
        )
        resp = chat_completion(
            llm,
            "Reply with exactly: OK",
            system=system_prompt(config),
            max_tokens=max_tokens,
            temperature=0.1,
        )
        text = extract_reply(resp)
        del llm
        if not text:
            errors.append("Smoke test: empty response")
        elif "<|im_start|>" in text or text.count("im_start") > 3:
            errors.append(f"Smoke test: bad ChatML output: {text[:60]!r}")
    except Exception as exc:
        errors.append(f"Smoke test failed: {exc}")
    return errors, warnings


def run_validate(
    profile: str | None = None,
    *,
    smoke_test: bool = False,
    require_smoke: bool = False,
    write_manifest: bool = True,
) -> int:
    config = load_config(profile)
    paths = paths_from_config(config)
    gguf_path = paths["gguf"]
    min_mb = float(config.get("validation", {}).get("min_gguf_size_mb", 4000))
    do_smoke = smoke_test or config.get("validation", {}).get("smoke_test", False)
    smoke_tokens = int(config.get("validation", {}).get("smoke_test_tokens", 24))

    print(f"Validating: {gguf_path}")
    print(f"Profile:    {config.get('profile')}")

    errors = validate_file(gguf_path, min_mb)
    warnings: list[str] = []

    if not errors and do_smoke:
        print("Smoke test (ChatML)...")
        se, sw = run_smoke_test(gguf_path, config, smoke_tokens)
        errors.extend(se)
        warnings.extend(sw)
        if require_smoke and sw:
            errors.extend(sw)

    for w in warnings:
        print(f"WARNING: {w}")

    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {gguf_path.stat().st_size / (1024**2):.2f} MB")
    if write_manifest:
        print("SHA256...")
        root = paths["root"]
        digest = file_sha256(gguf_path, root=root)
        mp = write_manifest_entry(config, gguf_path, digest, root)
        print(f"Manifest: {mp}")
    print("Validation passed.")
    return 0
