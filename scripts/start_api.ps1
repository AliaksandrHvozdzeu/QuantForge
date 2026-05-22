# Start OpenAI-compatible API server (llama-cpp-python)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot

$Profile = if ($env:QUANTFORGE_PROFILE) { $env:QUANTFORGE_PROFILE } else { "qwen2.5-coder-7b" }

try {
    if (Test-Path "config.ps1") { . .\config.ps1 }
    . (Join-Path $PSScriptRoot "Load-Config.ps1") -Profile $Profile

    $ggufPath = Join-Path $env:QF_MODELS_DIR $env:GGUF_OUTPUT
    if (-not (Test-Path $ggufPath)) {
        Write-Host "Model not found: $ggufPath" -ForegroundColor Red
        Write-Host "Run .\run_optimization.ps1 first." -ForegroundColor Yellow
        exit 1
    }

    $python = if (Test-Path "venv\Scripts\python.exe") { ".\venv\Scripts\python.exe" } else { "python" }
    $pip = if (Test-Path "venv\Scripts\pip.exe") { ".\venv\Scripts\pip.exe" } else { "pip" }

    if (-not (Test-Path "venv")) {
        Write-Host "Creating venv..." -ForegroundColor Yellow
        python -m venv venv
        $python = ".\venv\Scripts\python.exe"
        $pip = ".\venv\Scripts\pip.exe"
    }

    Write-Host "Installing API dependencies..." -ForegroundColor Yellow
    & $pip install -q -e ".[api]" -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

    $port = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
    Write-Host ""
    Write-Host "Starting QuantForge API on http://127.0.0.1:${port}/v1" -ForegroundColor Cyan
    Write-Host "Void / IDE model name: qwen2.5-coder-q5" -ForegroundColor Gray
    Write-Host "Docs: http://127.0.0.1:${port}/docs" -ForegroundColor Gray
    Write-Host ""

    & $python -m quantforge serve --profile $Profile --host 127.0.0.1 --port $port
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
