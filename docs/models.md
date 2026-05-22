# Supported Models

QuantForge uses **YAML profiles** under `config/profiles/`. Each profile defines HuggingFace repo, output GGUF name, and quant type.

## Active profile: Qwen2.5 Coder 7B

| Setting | Value |
|---------|--------|
| Profile | `qwen2.5-coder-7b` |
| HuggingFace | `Qwen/Qwen2.5-Coder-7B-Instruct` |
| Quantization | `Q5_K_M` |
| Output GGUF | `Qwen2.5-Coder-7B-Q5_K_M.gguf` |
| Size (approx.) | ~5.2 GB |
| Chat format | ChatML |
| Ollama name | `qwen2.5-coder-q5` |
| API model alias | `qwen2.5-coder-q5` |

```powershell
$env:QUANTFORGE_PROFILE = "qwen2.5-coder-7b"
.\run_optimization.ps1
```

## Quantization types

| Type | Use case | VRAM (7B, approx.) |
|------|----------|---------------------|
| Q4_K_M | Smallest, fastest on GPU | ~4–5 GB |
| Q5_K_M | **Default** — quality/size balance | ~5–6 GB |
| Q8_0 | Highest quality | ~8+ GB (often memory-bound on 8 GB GPUs) |

Set in profile: `quantize_type: Q5_K_M`

## Adding a new model

1. Create `config/profiles/my-model.yaml`:

```yaml
profile: my-model
model:
  repo: org/My-Model-Instruct
  base_dir: my-model-base
  gguf_output: My-Model-Q5_K_M.gguf
  display_name: My Model
quantize_type: Q5_K_M
chat:
  format: chatml   # or llama-3, mistral — must match model family
validation:
  min_gguf_size_mb: 3000
```

2. Run with profile:

```powershell
$env:QUANTFORGE_PROFILE = "my-model"
.\run_optimization.ps1
```

3. Update `ollama/Modelfile` or create a model-specific Modelfile if chat template differs.

## Legacy artifacts

Older runs may leave files on disk:

| Path | Notes |
|------|--------|
| `models/llama-3-8b-instruct-base/` | Old Llama 3 download (~15 GB) |
| `models/Llama-3-8B-*.gguf` | Old quantizations |

Remove safely:

```powershell
.\venv\Scripts\python.exe -m quantforge clean --dry-run
.\venv\Scripts\python.exe -m quantforge clean -y
```

## Licenses

- QuantForge scripts: MIT (see repository).
- Model weights: follow each model’s HuggingFace license (e.g. Qwen license in `models/*/LICENSE`).
