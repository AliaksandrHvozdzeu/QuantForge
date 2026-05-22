# QuantForge Troubleshooting

## Docker: `command not found` or `$'\r': command not found`

**Cause:** Windows CRLF line endings in `scripts/quantize.sh`.

**Fix:** Scripts use LF endings. Re-run from latest repo. Ensure `.gitattributes` has `*.sh text eol=lf`.

---

## Quantization says SUCCESS but no `.gguf` file

**Cause:** Docker bash failed silently (CRLF, wrong convert script name).

**Fix:**

1. Run `.\quantize_only.ps1`
2. After quantize, validation runs automatically in `run_optimization.ps1`
3. Manual check: `.\venv\Scripts\python.exe -m quantforge validate`

---

## Python: `Failed to load shared library llama.dll`

**Cause:** CUDA build of `llama-cpp-python` without NVIDIA runtime DLLs.

**Fix:**

```powershell
.\scripts\repair_llama.ps1
```

Or install GPU build:

```powershell
.\scripts\install_llama_gpu.ps1
```

---

## Model outputs `<|im_start|><|im_start|>...`

**Cause:** Qwen2.5-Instruct requires **ChatML** format. Raw prompts break inference.

### Python (llama-cpp-python)

Use `create_chat_completion`, not `llm("text")`:

```python
from qwen_chat import chat_completion, extract_reply, llama_kwargs
llm = Llama(model_path="...", **llama_kwargs())
resp = chat_completion(llm, "your prompt")
print(extract_reply(resp))
```

### Ollama / Void IDE

Do **not** import `.gguf` without a Modelfile TEMPLATE.

```powershell
.\setup_ollama.ps1
```

In Void IDE use Ollama model name: **`qwen2.5-coder-q5`** (not file path).

See [ollama/VOID_IDE.md](../ollama/VOID_IDE.md).

---

## `setup_ollama.ps1` not found

Run from project root:

```powershell
cd D:\AI\QuantForge
.\setup_ollama.ps1
```

Not from a subfolder unless you use `.\ollama\setup_ollama.ps1`.

---

## Config / profile errors

```powershell
# List profiles in config/profiles/
# Default profile: qwen2.5-coder-7b

$env:QUANTFORGE_PROFILE = "qwen2.5-coder-7b"
.\scripts\Load-Config.ps1 -Profile qwen2.5-coder-7b
```

Copy secrets only:

```powershell
copy config.ps1.example config.ps1
# edit HF_TOKEN if needed
```

---

## Out of disk space

Typical usage:

| Item | Size |
|------|------|
| HF weights (base) | ~15 GB |
| GGUF Q5_K_M | ~5 GB |
| Docker build cache | ~5–10 GB |

Set `quantize.keep_base: false` in YAML to delete weights after quantize.

---

## Slow GPU vs CPU on large quants (Q8 on 8GB VRAM)

8GB GPU + ~8GB model = memory bound. Use **Q5_K_M** or **Q4_K_M** for GPU speed.

---

## Validation failed: file too small

Re-run quantization:

```powershell
.\quantize_only.ps1
.\venv\Scripts\python.exe -m quantforge validate --smoke-test
```

Check Docker logs for convert/quantize errors.

---

## IDE: OpenAI API / Void (P3)

**Symptoms:** Connection refused, or `<|im_start|>` in responses.

**Fix:**

1. Start API: `.\start_api.ps1`
2. Health: `.\scripts\test_api.ps1`
3. In IDE use base URL `http://127.0.0.1:8000/v1` and model `qwen2.5-coder-q5` (not `.gguf` path)
4. Install deps: `pip install -e ".[api]"`

Full guide: [api.md](api.md)
