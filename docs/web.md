# Web Dashboard

Local web UI to run quantization pipelines, watch live logs, view benchmark results, and download GGUF files.

**For local use only** (`127.0.0.1`). Do not expose to the internet without authentication.

## Start

```powershell
.\start_web.ps1
```

Or:

```powershell
.\venv\Scripts\pip.exe install -e ".[web]"
.\venv\Scripts\python.exe -m quantforge web
```

Opens: **http://127.0.0.1:8787/**

Options:

```powershell
quantforge web --port 8787 --no-browser
$env:QF_WEB_PORT = "8787"
```

## Features

| Mode | What it runs |
|------|----------------|
| Full | `run_optimization.ps1` — download, quantize, validate, benchmark |
| Quantize only | `quantize_only.ps1` |
| Benchmark only | `quantforge benchmark` |
| Validate | `quantforge validate --smoke-test` |

- Live log stream (SSE) while the job runs
- Docker status indicator
- Download ready `.gguf` from `models/`
- Benchmark table and `report.md` link when available

## Requirements

- **Docker Desktop** running (for Full / Quantize modes)
- **Python venv** recommended (created automatically by `start_web.ps1`)
- One job at a time (same as CLI pipeline lock in scripts)

## API (optional)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Docker + project info |
| `/api/profiles` | GET | List YAML profiles |
| `/api/jobs` | POST | Start job `{"profile","mode"}` |
| `/api/jobs/{id}/stream` | GET | SSE log stream |
| `/api/download/{file}.gguf` | GET | Download model |
| `/api/artifacts?profile=` | GET | GGUF + metrics JSON |

## Logs

Web job logs: `logs/web-job-<id>.log`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `503 Docker is not running` | Start Docker Desktop |
| `409 Another job is already running` | Wait or restart dashboard |
| Empty log | Check `logs/web-job-*.log` on disk |
| Download 404 | Run pipeline first; file must be under `models/` |

See [troubleshooting.md](troubleshooting.md).
