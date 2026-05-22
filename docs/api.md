# OpenAI-compatible API (P3)

QuantForge can expose your local GGUF as an **OpenAI-compatible HTTP API** via [llama-cpp-python](https://github.com/abetlen/llama-cpp-python). Use it with Void, Continue, Cline, or any client that supports a custom OpenAI base URL.

Chat format (`chatml` for Qwen2.5) is applied automatically — you should not see repeated `<|im_start|>` tokens when the IDE uses this endpoint.

## Quick start (Windows, native, GPU)

```powershell
.\scripts\start_api.ps1
```

First run installs `pip install -e ".[api]"` and starts the server.

Manual:

```powershell
.\venv\Scripts\pip.exe install -e ".[api]" -r requirements.txt
.\venv\Scripts\python.exe -m quantforge serve --profile qwen2.5-coder-7b
```

Endpoints:

| URL | Purpose |
|-----|---------|
| `http://127.0.0.1:8000/v1` | OpenAI-compatible base URL for IDEs |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/v1/models` | List loaded models |

Model name for clients: **`qwen2.5-coder-q5`** (see `api.model_alias` in config).

## Docker Compose (CPU in container)

```powershell
docker compose --profile api up --build
```

Uses `./models` mounted at `/models`. Good for testing or Linux hosts. For **GPU on Windows**, prefer the native script above after `.\scripts\install_llama_gpu.ps1`.

Environment:

```powershell
$env:QUANTFORGE_PROFILE = "qwen2.5-coder-7b"
$env:API_PORT = "8000"
docker compose --profile api up --build
```

## Void IDE

Two options:

### A) Ollama (simplest)

See [ollama/VOID_IDE.md](../ollama/VOID_IDE.md) — model `qwen2.5-coder-q5`, base URL `http://localhost:11434`.

### B) OpenAI-compatible (QuantForge API)

1. Start API: `.\scripts\start_api.ps1`
2. In Void → provider **OpenAI-compatible** (or OpenAI with custom base URL):

| Setting | Value |
|---------|--------|
| Base URL | `http://127.0.0.1:8000/v1` |
| Model | `qwen2.5-coder-q5` |
| API key | leave empty, or match `api.api_key` in config |

Do **not** point Void at the raw `.gguf` file path.

## Continue / Cline / other clients

```json
{
  "models": [
    {
      "title": "Qwen2.5 Coder Q5",
      "provider": "openai",
      "model": "qwen2.5-coder-q5",
      "apiBase": "http://127.0.0.1:8000/v1"
    }
  ]
}
```

## Configuration

`config/default.yaml` → section `api`:

```yaml
api:
  host: 127.0.0.1
  port: 8000
  openai_path: /v1
  model_alias: qwen2.5-coder-q5
  n_ctx: 8192
  n_gpu_layers: -1   # 0 for CPU-only
  n_threads: 8
```

Preview generated server config:

```powershell
.\venv\Scripts\python.exe -m quantforge serve --print-config
```

Optional API key (uncomment in YAML or set in `config.ps1`):

```powershell
# config.ps1
$env:QF_API_KEY = "my-secret"
```

Then in `config/default.yaml`: `api_key: ${QF_API_KEY}` — or set directly in YAML.

## CLI reference

```powershell
quantforge serve                          # start server
quantforge serve --cpu                    # force CPU
quantforge serve --host 0.0.0.0 --port 8080
quantforge serve --print-config           # show JSON config
quantforge serve --docker                 # paths for Docker (/models/...)
```

## Health check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/models
```

Or:

```powershell
.\scripts\test_api.ps1
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `No module named 'fastapi'` | `pip install -e ".[api]"` |
| `Model not found` | Run `.\run_optimization.ps1` or check `models\` path |
| Empty / token spam in IDE | Wrong base URL or model name; use `/v1` + `qwen2.5-coder-q5` |
| Slow in Docker | Use native `start_api.ps1` with GPU wheel |
| Port in use | `quantforge serve --port 8080` |

See also [troubleshooting.md](troubleshooting.md).
