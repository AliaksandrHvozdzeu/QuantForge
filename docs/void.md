# Void IDE Setup

QuantForge supports two ways to use **Qwen2.5-Coder-7B** in [Void IDE](https://voideditor.com/):

## Option A: Ollama (recommended for simplicity)

1. Install [Ollama](https://ollama.com) and keep it running.
2. Register the model with ChatML template:

```powershell
.\setup_ollama.ps1
```

3. Verify:

```powershell
.\venv\Scripts\python.exe -m quantforge ollama verify
```

4. In Void → **Ollama** provider:

| Setting | Value |
|---------|--------|
| Model | `qwen2.5-coder-q5` |
| Base URL | `http://localhost:11434` |

Do **not** select the `.gguf` file path directly.

More detail: [ollama/VOID_IDE.md](../ollama/VOID_IDE.md)

## Option B: OpenAI-compatible API

1. Start the local server:

```powershell
.\start_api.ps1
```

2. In Void → **OpenAI-compatible** provider:

| Setting | Value |
|---------|--------|
| Base URL | `http://127.0.0.1:8000/v1` |
| Model | `qwen2.5-coder-q5` |
| API key | empty (unless you set `api.api_key` in config) |

More detail: [api.md](api.md)

## Common mistake

Pointing Void at a raw **GGUF** path without a chat template causes repeated `<|im_start|>` tokens. Always use **Ollama model name** or **QuantForge API** with ChatML.

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) and run:

```powershell
.\venv\Scripts\python.exe -m quantforge ollama verify --require-model
```
