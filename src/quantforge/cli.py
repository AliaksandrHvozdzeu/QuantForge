"""QuantForge CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .benchmark_runner import run_benchmark
from .chat_runner import run_chat
from .clean_runner import run_clean
from .config import apply_env, config_to_json, load_config
from .inventory import run_inventory
from .metrics_export import run_metrics_export, run_regression_check
from .metrics_store import compare_last_two, load_history, print_comparison_table
from .ollama_runner import run_ollama_verify
from .report_runner import run_report
from .serve_runner import config_preview, run_serve
from .validate_runner import run_validate
from .web_runner import run_web


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quantforge",
        description="QuantForge - local GGUF quantization toolkit",
    )
    parser.add_argument("--version", "-V", action="version", version=__version__)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--profile", "-p", default=None, help="Config profile name")

    sub = parser.add_subparsers(dest="command", required=True)

    # config
    p_cfg = sub.add_parser("config", parents=[common], help="Show configuration")
    p_cfg.add_argument("--json", action="store_true")
    p_cfg.add_argument("--apply-env", action="store_true", help="Export to environment")

    # validate
    p_val = sub.add_parser("validate", parents=[common], help="Validate GGUF file")
    p_val.add_argument("--smoke-test", action="store_true")
    p_val.add_argument("--require-smoke", action="store_true")
    p_val.add_argument("--no-manifest", action="store_true")

    # benchmark
    p_bench = sub.add_parser("benchmark", parents=[common], help="Run CPU/GPU benchmark")
    p_bench.add_argument("--cpu-only", action="store_true")
    p_bench.add_argument("--gpu-only", action="store_true")
    p_bench.add_argument("--force-gpu", action="store_true")

    # chat
    p_chat = sub.add_parser("chat", parents=[common], help="Interactive chat")
    p_chat.add_argument("--cpu", action="store_true", help="CPU only (n_gpu_layers=0)")

    # inventory
    sub.add_parser("inventory", parents=[common], help="List models and disk usage")

    # serve (OpenAI-compatible API)
    p_srv = sub.add_parser("serve", parents=[common], help="OpenAI-compatible API server")
    p_srv.add_argument("--host", default=None, help="Listen host (default from config)")
    p_srv.add_argument("--port", type=int, default=None, help="Listen port (default 8000)")
    p_srv.add_argument("--cpu", action="store_true", help="CPU only (n_gpu_layers=0)")
    p_srv.add_argument(
        "--docker",
        action="store_true",
        help="Use /models/<gguf> paths (for Docker Compose)",
    )
    p_srv.add_argument(
        "--print-config",
        action="store_true",
        help="Print server config JSON and exit",
    )

    # clean
    p_cln = sub.add_parser("clean", parents=[common], help="Free disk space")
    p_cln.add_argument("--dry-run", action="store_true", help="Show plan only")
    p_cln.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    p_cln.add_argument("--keep-logs", type=int, default=14, help="Keep logs newer than N days")
    p_cln.add_argument("--no-gguf", action="store_true", help="Do not remove inactive GGUF")
    p_cln.add_argument("--no-base", action="store_true", help="Do not remove base weights")

    # report
    p_rep = sub.add_parser("report", parents=[common], help="Generate Markdown benchmark report")
    p_rep.add_argument(
        "-o", "--output", default=None, help="Output path (default: metrics/report.md)"
    )

    # metrics
    p_met = sub.add_parser("metrics", parents=[common], help="Benchmark metrics")
    met_sub = p_met.add_subparsers(dest="metrics_cmd", required=True)
    p_list = met_sub.add_parser("list", parents=[common], help="List benchmark history")
    p_list.add_argument("--limit", type=int, default=None, help="Show last N runs")
    p_cmp = met_sub.add_parser("compare", parents=[common], help="Compare last two runs")
    p_cmp.add_argument("--last", type=int, default=2, help="Compare last N runs (default: 2)")
    p_exp = met_sub.add_parser("export", parents=[common], help="Export history to CSV")
    p_exp.add_argument(
        "-o",
        "--output",
        default=None,
        help="CSV path (default: metrics/benchmark_history.csv)",
    )
    p_reg = met_sub.add_parser("regression", parents=[common], help="Check vs baseline JSON")
    p_reg.add_argument(
        "--baseline",
        default="tests/fixtures/benchmark_baseline.json",
        help="Baseline benchmark JSON",
    )
    p_reg.add_argument(
        "--tolerance",
        type=float,
        default=0.2,
        help="Max relative change per backend (default: 0.2 = 20%%)",
    )

    # web dashboard
    p_web = sub.add_parser("web", help="Local web dashboard")
    p_web.add_argument("--host", default="127.0.0.1", help="Bind host (default: localhost)")
    p_web.add_argument("--port", type=int, default=8787, help="Port (default: 8787)")
    p_web.add_argument("--no-browser", action="store_true", help="Do not open browser")

    # ollama
    p_ollama = sub.add_parser("ollama", parents=[common], help="Ollama integration")
    oll_sub = p_ollama.add_subparsers(dest="ollama_cmd", required=True)
    p_oll_v = oll_sub.add_parser("verify", parents=[common], help="Verify Modelfile and setup")
    p_oll_v.add_argument(
        "--require-model",
        action="store_true",
        help="Fail if ollama model is not registered",
    )

    args = parser.parse_args(argv)
    profile = args.profile

    try:
        if args.command == "config":
            cfg = load_config(profile)
            if args.apply_env:
                apply_env(cfg)
            if args.json or not args.apply_env:
                print(config_to_json(cfg))
            else:
                print(f"Profile: {cfg.get('profile')}")
                print(f"  MODEL_REPO: {cfg.get('model', {}).get('repo')}")
                print(f"  GGUF:       {cfg.get('model', {}).get('gguf_output')}")
            return 0

        if args.command == "validate":
            return run_validate(
                profile,
                smoke_test=args.smoke_test,
                require_smoke=args.require_smoke,
                write_manifest=not args.no_manifest,
            )

        if args.command == "benchmark":
            return run_benchmark(
                profile,
                cpu_only=args.cpu_only,
                gpu_only=args.gpu_only,
                force_gpu=args.force_gpu,
            )

        if args.command == "chat":
            layers = 0 if args.cpu else -1
            return run_chat(profile, n_gpu_layers=layers)

        if args.command == "inventory":
            return run_inventory(profile)

        if args.command == "serve":
            if args.print_config:
                print(config_preview(profile, docker=args.docker))
                return 0
            return run_serve(
                profile,
                host=args.host,
                port=args.port,
                cpu=args.cpu,
                docker=args.docker,
            )

        if args.command == "clean":
            return run_clean(
                profile,
                dry_run=args.dry_run,
                remove_inactive_gguf=not args.no_gguf,
                remove_base_weights=not args.no_base,
                logs_keep_days=args.keep_logs,
                yes=args.yes,
            )

        if args.command == "report":
            out = Path(args.output) if args.output else None
            return run_report(profile, output=out)

        if args.command == "metrics":
            from .config import paths_from_config

            cfg = load_config(profile)
            metrics_dir = paths_from_config(cfg)["metrics"]
            if args.metrics_cmd == "list":
                print_comparison_table(load_history(metrics_dir, limit=args.limit))
                return 0
            if args.metrics_cmd == "compare":
                if args.last == 2:
                    compare_last_two(metrics_dir)
                else:
                    print_comparison_table(load_history(metrics_dir, limit=args.last))
                return 0
            if args.metrics_cmd == "export":
                out = Path(args.output) if args.output else metrics_dir / "benchmark_history.csv"
                return run_metrics_export(metrics_dir, out)
            if args.metrics_cmd == "regression":
                baseline = Path(args.baseline)
                if not baseline.is_absolute():
                    from .config import PROJECT_ROOT

                    baseline = PROJECT_ROOT / baseline
                return run_regression_check(metrics_dir, baseline, args.tolerance)

        if args.command == "web":
            return run_web(
                host=args.host,
                port=args.port,
                open_browser=not args.no_browser,
            )

        if args.command == "ollama":
            if args.ollama_cmd == "verify":
                return run_ollama_verify(profile, require_model=args.require_model)

    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
