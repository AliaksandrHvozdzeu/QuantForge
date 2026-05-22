# Qwen2.5-Coder in Ollama + Void IDE

> **Void setup guide:** [docs/void.md](../docs/void.md)  
> **Alternative:** OpenAI-compatible API — [docs/api.md](../docs/api.md) (`.\start_api.ps1`)

## Why you see `<|im_start|><|im_start|>...`

Qwen2.5-Instruct is a **chat model**. It needs the **ChatML** template:

```
<|im_start|>user
your prompt
<|im_start|>assistant
```

If you import only the `.gguf` file **without** a `Modelfile` (TEMPLATE + STOP), Ollama sends raw text. The model then outputs special tokens instead of an answer.

**The GGUF file is fine.** The Ollama configuration was wrong.

---

## Correct setup (one time)

### 1. Create Ollama model with template

From project root (`QuantForge`):

```powershell
.\setup_ollama.ps1
```

Or from `ollama` folder:

```powershell
cd ollama
.\setup_ollama.ps1
```

Or manually:

```powershell
cd ollama
ollama create qwen2.5-coder-q5 -f Modelfile
```

### 2. Test in terminal

```powershell
ollama run qwen2.5-coder-q5
```

Type: `Write a HelloWorld React component`

You should get normal code, not `<|im_start|>`.

### 3. Configure Void IDE

In Void settings (Ollama provider):

| Setting | Value |
|---------|--------|
| Model | `qwen2.5-coder-q5` |
| Base URL | `http://localhost:11434` (default) |

**Important:**

- Use model name **`qwen2.5-coder-q5`**, not the path to `.gguf`
- Do not import GGUF directly into Void
- Ollama must be running (`ollama serve` or Ollama app)

---

## If you already imported GGUF wrong

Remove old broken import (if any):

```powershell
ollama list
ollama rm your-old-model-name
```

Then run `.\setup_ollama.ps1` again.

---

## Recommended parameters for coding

Already set in `Modelfile`:

- `num_ctx 8192`
- `temperature 0.7`
- `stop` tokens: ``, `<|endoftext|>`, `<|im_start|>`

---

## Alternative: official Ollama model (no custom GGUF)

If custom GGUF keeps failing:

```powershell
ollama pull qwen2.5-coder:7b
```

Use in Void: `qwen2.5-coder:7b`

Your local Q5_K_M file is still useful for Python (`llama-cpp-python`) and offline use.
