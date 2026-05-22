# Re-run conversion + quantization only
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$Profile = if ($env:QUANTFORGE_PROFILE) { $env:QUANTFORGE_PROFILE } else { "qwen2.5-coder-7b" }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Quantize Only" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "config.ps1") { . .\config.ps1 }
. (Join-Path $PSScriptRoot "scripts\Load-Config.ps1") -Profile $Profile

if (-not (Test-Path $env:QF_LOGS_DIR)) { New-Item -ItemType Directory -Path $env:QF_LOGS_DIR -Force | Out-Null }
. (Join-Path $PSScriptRoot "scripts\Pipeline-Lock.ps1") -LogsDir $env:QF_LOGS_DIR

try {
$baseDir = Join-Path $env:QF_MODELS_DIR $env:MODEL_BASE_DIR
$indexFile = Join-Path $baseDir "model.safetensors.index.json"
if (-not (Test-Path $indexFile) -and -not (Test-Path (Join-Path $baseDir "model.safetensors"))) {
    Write-Host "ERROR: Base weights not found at $baseDir" -ForegroundColor Red
    Write-Host "Run .\run_optimization.ps1 first" -ForegroundColor Yellow
    exit 1
}

docker info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker not running" -ForegroundColor Red
    exit 1
}

if (-not (docker images -q llama-quantizer:latest)) {
    $llamaRef = if ($env:LLAMA_CPP_REF) { $env:LLAMA_CPP_REF } else { "b9193" }
    docker build -t llama-quantizer:latest --build-arg "LLAMA_CPP_REF=$llamaRef" .
}

$modelsPath = (Resolve-Path $env:QF_MODELS_DIR).Path
$metricsPath = (Resolve-Path $env:QF_METRICS_DIR).Path
$scriptsPath = (Resolve-Path "scripts").Path

$dockerEnvArgs = @(
    "-e", "SKIP_DOWNLOAD=1",
    "-e", "KEEP_BASE=$env:KEEP_BASE",
    "-e", "MODEL_REPO=$env:MODEL_REPO",
    "-e", "MODEL_BASE_DIR=$env:MODEL_BASE_DIR",
    "-e", "GGUF_OUTPUT=$env:GGUF_OUTPUT",
    "-e", "QUANT_TYPE=$env:QUANT_TYPE"
)

docker run --rm `
    -v "${modelsPath}:/models" `
    -v "${metricsPath}:/metrics" `
    -v "${scriptsPath}:/scripts:ro" `
    @dockerEnvArgs `
    llama-quantizer:latest `
    /bin/bash /scripts/quantize.sh

if ($LASTEXITCODE -ne 0) { exit 1 }

$python = if (Test-Path "venv\Scripts\python.exe") { ".\venv\Scripts\python.exe" } else { "python" }
& $python -m pip install -q -e ".[inference]" 2>$null
& $python -m quantforge validate --profile $Profile --smoke-test

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS: models\$env:GGUF_OUTPUT" -ForegroundColor Green
} else {
    exit 1
}
} finally {
    . (Join-Path $PSScriptRoot "scripts\Pipeline-Lock.ps1") -LogsDir $env:QF_LOGS_DIR -Release
}
