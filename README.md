# QuantForge - Qwen2.5-Coder-7B Quantization for Windows

Automated download, **Q5_K_M** quantization, and benchmarking of **Qwen2.5-Coder-7B-Instruct** using Docker on Windows.

**Full system guide:** [ARTICLE.md](ARTICLE.md) — architecture, pipeline steps, diagrams, and all components.

## CLI (P1)

Install the package in your venv (done automatically by `run_optimization.ps1` / `test_models.ps1`):

```powershell
.\venv\Scripts\pip.exe install -e ".[inference]"
```

Commands:

| Command | Purpose |
|---------|---------|
| `quantforge config --json` | Print merged YAML config |
| `quantforge validate` | Check GGUF size + manifest |
| `quantforge validate --smoke-test` | ChatML smoke test (CPU) |
| `quantforge benchmark` | CPU + GPU benchmark |
| `quantforge chat` | Interactive ChatML chat |
| `quantforge inventory` | List GGUF files and disk usage |
| `quantforge metrics list` | Benchmark history |
| `quantforge metrics compare` | Compare last two runs |
| `quantforge serve` | OpenAI-compatible API for IDEs |
| `quantforge clean` | Free disk (inactive models/logs) |
| `quantforge report` | Markdown benchmark report |
| `quantforge ollama verify` | Check Modelfile + Ollama setup |
| `quantforge metrics export` | Export benchmark history to CSV |
| `quantforge metrics regression` | Compare run vs baseline |

Examples:

```powershell
.\venv\Scripts\python.exe -m quantforge benchmark -p qwen2.5-coder-7b
.\venv\Scripts\python.exe -m quantforge validate -p qwen2.5-coder-7b --smoke-test
.\venv\Scripts\python.exe -m quantforge metrics compare
.\venv\Scripts\python.exe -m quantforge chat --cpu
```

Legacy scripts (`src\benchmark.py`, `src\validate_gguf.py`) still work and delegate to the same package.

## Web dashboard (P6)

Browser UI: pick a profile, start quantization, watch live logs, download GGUF.

```powershell
.\start_web.ps1
```

Opens **http://127.0.0.1:8787/** (local only). Details: [docs/web.md](docs/web.md)

| Mode | Action |
|------|--------|
| Full | Download + quantize + validate + benchmark |
| Quantize only | Re-run Docker quantize |
| Benchmark / Validate | Test existing GGUF |

Requires **Docker Desktop** for quantize modes.

## Quality & integrations (P5)

| Feature | Command |
|---------|---------|
| Ollama check | `quantforge ollama verify` |
| CSV export | `quantforge metrics export` |
| Regression | `quantforge metrics regression --tolerance 0.2` |
| Void IDE guide | [docs/void.md](docs/void.md) |

```powershell
.\scripts\verify_ollama.ps1
.\venv\Scripts\python.exe -m quantforge metrics export -o metrics\history.csv
```

CI also runs **shellcheck**, **pip-audit**, and **Dependabot** (see `.github/`).

## Unified launcher & disk tools (P4)

Interactive menu or direct commands:

```powershell
.\quantforge.ps1
.\quantforge.ps1 run
.\quantforge.ps1 clean
```

| Command | Purpose |
|---------|---------|
| `quantforge clean --dry-run` | Preview removable files (old GGUF, base weights) |
| `quantforge clean -y` | Delete inactive artifacts |
| `quantforge report` | Generate `metrics/report.md` |

Pipeline flags (`config.ps1` or env):

| Variable | Effect |
|----------|--------|
| `SKIP_DOCKER_BUILD=1` | Reuse Docker image |
| `SKIP_BENCHMARK=1` | Skip benchmark step |
| `FORCE_QUANTIZE=1` | Re-run quantize even if GGUF exists |
| `KEEP_BASE=0` | Delete HF weights after quant |

Docs: [docs/architecture.md](docs/architecture.md) · [docs/models.md](docs/models.md) · [CHANGELOG.md](CHANGELOG.md)

## OpenAI API for IDE (P3)

Expose the GGUF as an OpenAI-compatible server for **Void**, **Continue**, Cline, etc.

```powershell
.\start_api.ps1
# or: docker compose --profile api up --build
```

| Setting | Value |
|---------|--------|
| Base URL | `http://127.0.0.1:8000/v1` |
| Model | `qwen2.5-coder-q5` |

Details: [docs/api.md](docs/api.md) · Ollama alternative: [ollama/VOID_IDE.md](ollama/VOID_IDE.md)

```powershell
.\venv\Scripts\python.exe -m quantforge serve
.\scripts\test_api.ps1
```

## CI & reproducible builds (P2)

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | GitHub Actions: ruff, config tests, Docker build |
| `docker/versions.env` | Pinned `llama.cpp` tag (`b9193`) and base image |
| `docker/requirements.txt` | Pinned Python deps inside Docker |
| `requirements.txt` | Pinned venv deps (`llama-cpp-python`, `pyyaml`) |
| `scripts/ci.ps1` | Run lint + config checks locally |

Local checks:

```powershell
.\scripts\ci.ps1
```

Docker image uses a **multi-stage** build (compile llama.cpp, then slim runtime). Override the llama.cpp tag:

```powershell
$env:LLAMA_CPP_REF = "b9193"
docker build -t llama-quantizer:latest --build-arg LLAMA_CPP_REF=$env:LLAMA_CPP_REF .
```

## Configuration (P0)

| File | Purpose |
|------|---------|
| `config/default.yaml` | Base settings |
| `config/profiles/qwen2.5-coder-7b.yaml` | Active model profile |
| `config.ps1.example` | Copy to `config.ps1` for secrets (HF token) |

```powershell
copy config.ps1.example config.ps1
$env:QUANTFORGE_PROFILE = "qwen2.5-coder-7b"   # optional
```

## Quick Start

### 1. Check System
```
check_system.bat
```

### 2. Run Full Pipeline
```
run_optimization.bat
```

Wait ~25-40 minutes (download + convert + quantize).

### 3. Test (CPU + GPU)
```
test_models.ps1
```

## Output

```
models/
  Qwen2.5-Coder-7B-Q5_K_M.gguf
  manifest.json                   (checksums, metadata)

metrics/
  bench_results.txt
  python_benchmark_results.txt
  benchmark_results.json          (structured benchmark)
  report.md                       (Markdown summary)

logs/
  .pipeline.lock                  (while pipeline runs)
  run-YYYY-MM-DD_HH-mm-ss.log
```

## Configuration

Edit `config.ps1`:

```powershell
$env:MODEL_REPO = "Qwen/Qwen2.5-Coder-7B-Instruct"
$env:GGUF_OUTPUT = "Qwen2.5-Coder-7B-Q5_K_M.gguf"
$env:QUANT_TYPE = "Q5_K_M"
```

## Commands

| Script | Purpose |
|--------|---------|
| `start_web.ps1` | Web dashboard (browser UI) |
| `run_optimization.ps1` | Download + quantize + test |
| `quantize_only.ps1` | Quantize only (weights already downloaded) |
| `test_models.ps1` | Run Python benchmark |
| `scripts/install_llama_gpu.ps1` | CUDA build for GPU tests |
| `scripts/repair_llama.ps1` | Fix llama.dll load errors |

## Python Usage

Qwen2.5-Instruct **requires ChatML format**. Do not call `llm("raw text")` — you will get repeated `<|im_start|>` tokens.

```python
import sys
sys.path.insert(0, "src")
import llama_env
from llama_cpp import Llama
from qwen_chat import chat_completion, extract_reply, llama_kwargs

llm = Llama(
    model_path="models/Qwen2.5-Coder-7B-Q5_K_M.gguf",
    n_ctx=8192,
    n_gpu_layers=-1,
    n_threads=8,
    **llama_kwargs(),  # chat_format="chatml"
)

resp = chat_completion(llm, "Write a Python quicksort function.", max_tokens=256)
print(extract_reply(resp))
```

Interactive chat:
```powershell
.\venv\Scripts\python.exe -m quantforge chat
```

## Requirements

- Windows 10/11 (64-bit)
- Docker Desktop (running)
- 16+ GB RAM, 30+ GB disk
- Python 3.8+ (optional, for testing)
- NVIDIA GPU + CUDA wheel (optional, for GPU benchmark)

## GPU Setup

```powershell
.\scripts\install_llama_gpu.ps1
.\venv\Scripts\python.exe -m quantforge benchmark
```

If `llama.dll` fails to load:
```powershell
.\scripts\repair_llama.ps1
```

## Re-quantize After Config Change

```powershell
.\quantize_only.ps1
```

## Ollama + Void IDE

If Ollama returns `<|im_start|>` repeatedly, the GGUF was imported **without ChatML template**.

```powershell
.\setup_ollama.ps1
```

Or: `cd ollama` then `.\setup_ollama.ps1`

In Void IDE select model: **`qwen2.5-coder-q5`** (not the raw `.gguf` path).

Details: [ollama/VOID_IDE.md](ollama/VOID_IDE.md)

## Validation

After quantization:

```powershell
.\venv\Scripts\python.exe -m quantforge validate -p qwen2.5-coder-7b --smoke-test
```

Checks: file size, optional ChatML smoke test, updates `models/manifest.json`.

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md)

## Links

- Model: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
- llama.cpp: https://github.com/ggerganov/llama.cpp
- Ollama + Qwen: https://qwen.readthedocs.io/en/v2.5/run_locally/ollama.html
