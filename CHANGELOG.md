# Changelog

All notable changes to QuantForge are documented here.

## [0.3.0] - 2026-05-22

### Added (P3)
- OpenAI-compatible API: `quantforge serve`, `docker-compose.yml`, `start_api.ps1`
- Documentation: [docs/api.md](docs/api.md)

### Added (P2)
- Multi-stage `Dockerfile` with pinned `llama.cpp` (b9193)
- GitHub Actions CI: ruff, pytest, Docker build
- Pinned `requirements.txt`, `docker/requirements.txt`
- `scripts/ci.ps1` for local lint/tests

### Added (P1)
- Python package `quantforge` with CLI
- Commands: `config`, `validate`, `benchmark`, `chat`, `inventory`, `metrics`
- Benchmark history JSONL and `metrics compare`

### Added (P0)
- YAML configuration and profiles
- GGUF validation and `models/manifest.json`
- [docs/troubleshooting.md](docs/troubleshooting.md)

## [0.6.0] - 2026-05-22

### Added (P6)
- Web dashboard: `quantforge web` / `start_web.ps1`
- Profile picker, pipeline modes, live log (SSE), GGUF download
- REST API under `/api/*`
- [docs/web.md](docs/web.md)

## [0.5.0] - 2026-05-22

### Added (P5)
- `quantforge ollama verify` — Modelfile + GGUF + optional Ollama model check
- `quantforge metrics export` — CSV export of benchmark history
- `quantforge metrics regression` — compare latest run vs baseline (±20%)
- Dependabot (pip + GitHub Actions)
- CI: shellcheck, pip-audit, Modelfile validation
- Unit tests: config, inference, ollama, regression
- [docs/void.md](docs/void.md), [LICENSE](LICENSE)
- Fixed `ollama/Modelfile` ChatML `im_end` tokens

## [0.4.0] - 2026-05-22

### Added (P4)
- Unified entry point: `quantforge.ps1` / `quantforge.bat`
- `quantforge clean` — remove inactive GGUF, base weights, old logs
- `quantforge report` — Markdown benchmark report
- Pipeline lock (`logs/.pipeline.lock`)
- Env flags: `SKIP_BENCHMARK`, `FORCE_QUANTIZE` (skip quantize if valid GGUF exists)
- [docs/architecture.md](docs/architecture.md), [docs/models.md](docs/models.md)
