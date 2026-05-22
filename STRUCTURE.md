# Project Structure

## Model

- **HF:** `Qwen/Qwen2.5-Coder-7B-Instruct`
- **Quantization:** `Q5_K_M` (5-bit)
- **Output:** `models/Qwen2.5-Coder-7B-Q5_K_M.gguf`

## Key Files

| File | Role |
|------|------|
| `config.ps1` | Model repo, paths, quant type |
| `run_optimization.ps1` | Full pipeline |
| `quantize_only.ps1` | Convert + quantize only |
| `scripts/quantize.sh` | Docker: download, convert, quantize, bench |
| `src/benchmark.py` | Python CPU/GPU benchmark |
| `src/model_config.py` | Shared paths |
| `test_models.ps1` | Run benchmark |

## Switching Model

Edit `config.ps1` and re-run `run_optimization.ps1` or `quantize_only.ps1`.
