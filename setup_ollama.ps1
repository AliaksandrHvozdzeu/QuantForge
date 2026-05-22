# Wrapper: register Qwen GGUF in Ollama (runs ollama/setup_ollama.ps1)
$ErrorActionPreference = "Stop"
$scriptDir = Join-Path $PSScriptRoot "ollama"
& (Join-Path $scriptDir "setup_ollama.ps1")
exit $LASTEXITCODE
