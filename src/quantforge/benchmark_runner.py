"""Model benchmark (CPU + GPU)."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from . import llama_env  # noqa: F401
from .config import load_config, model_display_name, paths_from_config
from .inference import chat_completion, extract_reply, llama_kwargs, system_prompt
from .metrics_store import append_run, build_benchmark_payload, latest_path, save_latest
from .report_runner import run_report
from .utils import format_size, format_time

TEST_PROMPTS = [
    "Write a Python function to merge two sorted lists into one sorted list.",
    "Explain binary search and implement it in Python with O(log n) complexity.",
    "Refactor this code to use a context manager: f = open('data.txt'); data = f.read(); f.close()",
]


def nvidia_gpu_detected() -> str | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def resolve_backends(gguf_path: Path, cpu_only: bool, gpu_only: bool, force_gpu: bool):
    from llama_cpp import Llama

    backends = []
    if not gpu_only:
        backends.append({"id": "cpu", "label": "CPU", "n_gpu_layers": 0, "n_threads": 8})

    gpu_name = nvidia_gpu_detected()
    if gpu_only or force_gpu or (not cpu_only and gpu_name):

        def probe():
            try:
                llm = Llama(
                    model_path=str(gguf_path),
                    n_ctx=512,
                    n_gpu_layers=1,
                    verbose=False,
                    **llama_kwargs(),
                )
                del llm
                return True
            except Exception:
                return False

        if not gpu_name:
            if gpu_only or force_gpu:
                print("ERROR: No NVIDIA GPU (nvidia-smi)", file=sys.stderr)
                sys.exit(1)
        elif probe():
            print(f"NVIDIA GPU: {gpu_name}")
            backends.append({"id": "gpu", "label": "GPU", "n_gpu_layers": -1, "n_threads": 4})
        elif gpu_only or force_gpu:
            print("ERROR: CUDA offload failed. Run: scripts\\repair_llama.ps1", file=sys.stderr)
            sys.exit(1)
        else:
            print("WARNING: GPU found but CUDA unavailable. CPU-only.")

    if cpu_only and not backends:
        backends.append({"id": "cpu", "label": "CPU", "n_gpu_layers": 0, "n_threads": 8})
    return backends


def run_benchmark(
    profile: str | None = None,
    *,
    cpu_only: bool = False,
    gpu_only: bool = False,
    force_gpu: bool = False,
) -> int:
    from llama_cpp import Llama

    config = load_config(profile)
    paths = paths_from_config(config)
    gguf_path = paths["gguf"]
    display = model_display_name(config)
    quant = config.get("quantize_type", "")
    sys_msg = system_prompt(config)

    print("\n" + "=" * 70)
    print(f"  {display} Benchmark")
    print("=" * 70)

    if not gguf_path.exists():
        print(f"ERROR: Model not found: {gguf_path}", file=sys.stderr)
        return 1

    backends = resolve_backends(gguf_path, cpu_only, gpu_only, force_gpu)
    if not backends:
        print("ERROR: No backends available.", file=sys.stderr)
        return 1

    print(f"Backends: {', '.join(b['label'] for b in backends)}")
    all_results = []

    for backend in backends:
        label = backend["label"]
        print(f"\n{'=' * 70}\n  {display} [{label}]\n{'=' * 70}")
        print(f"File: {format_size(gguf_path.stat().st_size)} | Quant: {quant}")

        t0 = time.time()
        llm = Llama(
            model_path=str(gguf_path),
            n_ctx=8192,
            n_threads=backend["n_threads"],
            n_gpu_layers=backend["n_gpu_layers"],
            verbose=False,
            **llama_kwargs(),
        )
        load_time = time.time() - t0
        print(f"Loaded in {format_time(load_time)}")

        run_results = []
        for i, prompt in enumerate(TEST_PROMPTS, 1):
            print(f"\nTest {i}/{len(TEST_PROMPTS)}: {prompt[:55]}...")
            t1 = time.time()
            try:
                resp = chat_completion(llm, prompt, system=sys_msg, max_tokens=128)
                gen_time = time.time() - t1
                tokens = resp["usage"]["completion_tokens"]
                tps = tokens / gen_time if gen_time else 0
                preview = extract_reply(resp).replace("\n", " ")[:100]
                print(f"   {tokens} tokens | {tps:.2f} tok/s | {format_time(gen_time)}")
                if preview:
                    print(f"   Preview: {preview}...")
                run_results.append({"tokens": tokens, "time": gen_time, "tps": tps})
            except Exception as exc:
                print(f"   ERROR: {exc}")

        del llm
        if run_results:
            avg_tps = sum(r["tps"] for r in run_results) / len(run_results)
            avg_time = sum(r["time"] for r in run_results) / len(run_results)
            all_results.append(
                {
                    "model": display,
                    "backend": backend["id"],
                    "backend_label": label,
                    "file_size": gguf_path.stat().st_size,
                    "load_time": load_time,
                    "avg_tps": avg_tps,
                    "avg_time": avg_time,
                }
            )
            print(f"\nAverage: {avg_tps:.2f} tok/s")

    _print_summary(all_results)
    payload = build_benchmark_payload(config, gguf_path, all_results)
    metrics_dir = paths["metrics"]
    save_latest(metrics_dir, payload)
    hp = append_run(metrics_dir, payload)
    txt_path = metrics_dir / "python_benchmark_results.txt"
    _save_txt(all_results, txt_path, display, quant)

    print(f"\nLatest:  {latest_path(metrics_dir)}")
    print(f"History: {hp}")
    print(f"Text:    {txt_path}")
    run_report(profile)
    return 0


def _print_summary(results: list[dict]) -> None:
    if not results:
        return
    print(f"\n{'=' * 70}\n  SUMMARY\n{'=' * 70}")
    for r in results:
        print(f"{r['backend_label']:<6} {format_size(r['file_size']):<10} {r['avg_tps']:.2f} tok/s")
    cpu = next((r for r in results if r["backend"] == "cpu"), None)
    gpu = next((r for r in results if r["backend"] == "gpu"), None)
    if cpu and gpu and cpu["avg_tps"] > 0:
        print(f"GPU speedup: {gpu['avg_tps'] / cpu['avg_tps']:.2f}x")


def _save_txt(results: list[dict], path: Path, display: str, quant: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Benchmark - {display}\n{'=' * 70}\n\n")
        for r in results:
            f.write(
                f"{r['backend_label']}: {r['avg_tps']:.2f} tok/s, "
                f"load {format_time(r['load_time'])}, quant {quant}\n"
            )
