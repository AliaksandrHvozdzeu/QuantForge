# ============================================================================
# QuantForge - Model quantization pipeline (Windows + Docker)
# ============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$Profile = if ($env:QUANTFORGE_PROFILE) { $env:QUANTFORGE_PROFILE } else { "qwen2.5-coder-7b" }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  QuantForge - Model Quantization" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Load YAML config + optional config.ps1 secrets
if (Test-Path "config.ps1") { . .\config.ps1 }
. (Join-Path $PSScriptRoot "scripts\Load-Config.ps1") -Profile $Profile

Write-Host ""

# Folders
$folders = @($env:QF_MODELS_DIR, $env:QF_METRICS_DIR, $env:QF_LOGS_DIR, "src", "config")
foreach ($folder in $folders) {
    if ($folder -and -not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
    }
}

$logFile = Join-Path $env:QF_LOGS_DIR "run-$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').log"

. (Join-Path $PSScriptRoot "scripts\Pipeline-Lock.ps1") -LogsDir $env:QF_LOGS_DIR
Start-Transcript -Path $logFile -Append | Out-Null

try {
    # [1/7] Docker
    Write-Host "[1/7] Checking Docker Desktop..." -ForegroundColor Yellow
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker Desktop is not running!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Docker OK" -ForegroundColor Green
    Write-Host ""

    # [2/7] Dockerfile
    Write-Host "[2/7] Checking Dockerfile..." -ForegroundColor Yellow
    if (-not (Test-Path "Dockerfile")) {
        Write-Host "ERROR: Dockerfile not found!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Dockerfile OK" -ForegroundColor Green
    Write-Host ""

    # [3/7] Build image
    Write-Host "[3/7] Building Docker image..." -ForegroundColor Yellow
    if ($env:SKIP_DOCKER_BUILD -eq "1") {
        Write-Host "SKIP_DOCKER_BUILD=1, skipping build" -ForegroundColor Cyan
    } else {
        $llamaRef = if ($env:LLAMA_CPP_REF) { $env:LLAMA_CPP_REF } else { "b9193" }
        docker build -t llama-quantizer:latest --build-arg "LLAMA_CPP_REF=$llamaRef" .
        if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
        Write-Host "Docker image built" -ForegroundColor Green
    }
    Write-Host ""

    # [4/7] Quantize
    $ggufPath = Join-Path $env:QF_MODELS_DIR $env:GGUF_OUTPUT
    $skipQuant = $false
    if ($env:FORCE_QUANTIZE -ne "1" -and (Test-Path $ggufPath)) {
        $sizeMb = (Get-Item $ggufPath).Length / 1MB
        $minMb = if ($env:QF_MIN_GGUF_MB) { [double]$env:QF_MIN_GGUF_MB } else { 4000 }
        if ($sizeMb -ge $minMb) {
            Write-Host "[4/7] GGUF exists ($([math]::Round($sizeMb,0)) MB) — SKIP_QUANTIZE (set FORCE_QUANTIZE=1 to rebuild)" -ForegroundColor Cyan
            $skipQuant = $true
        }
    }

    if (-not $skipQuant) {
    Write-Host "[4/7] Quantizing model ($env:QUANT_TYPE)..." -ForegroundColor Yellow
    $modelsPath = (Resolve-Path $env:QF_MODELS_DIR).Path
    $metricsPath = (Resolve-Path $env:QF_METRICS_DIR).Path
    $scriptsPath = (Resolve-Path "scripts").Path

    if (-not (Test-Path "$scriptsPath\quantize.sh")) {
        throw "scripts\quantize.sh not found"
    }

    $keepBase = if ($env:KEEP_BASE -eq "0") { "0" } else { "1" }
    $dockerEnvArgs = @(
        "-e", "KEEP_BASE=$keepBase",
        "-e", "MODEL_REPO=$env:MODEL_REPO",
        "-e", "MODEL_BASE_DIR=$env:MODEL_BASE_DIR",
        "-e", "GGUF_OUTPUT=$env:GGUF_OUTPUT",
        "-e", "QUANT_TYPE=$env:QUANT_TYPE"
    )
    if ($env:HF_TOKEN) {
        $dockerEnvArgs += "-e", "HF_TOKEN=$env:HF_TOKEN"
    }

    docker run --rm `
        -v "${modelsPath}:/models" `
        -v "${metricsPath}:/metrics" `
        -v "${scriptsPath}:/scripts:ro" `
        @dockerEnvArgs `
        llama-quantizer:latest `
        /bin/bash /scripts/quantize.sh

    if ($LASTEXITCODE -ne 0) { throw "Docker quantization failed" }
    Write-Host ""
    }

    # [5/7] Validate GGUF
    Write-Host "[5/7] Validating GGUF output..." -ForegroundColor Yellow
    if (-not (Test-Path $ggufPath)) {
        throw "GGUF not created: $ggufPath"
    }

    $python = "python"
    if (Test-Path "venv\Scripts\python.exe") { $python = ".\venv\Scripts\python.exe" }

    & $python -m pip install -q -e . 2>$null
    & $python -m quantforge validate --profile $Profile
    if ($LASTEXITCODE -ne 0) { throw "GGUF validation failed" }
    Write-Host "Validation OK" -ForegroundColor Green
    Write-Host ""

    # [6/7] Python venv
    Write-Host "[6/7] Python environment..." -ForegroundColor Yellow
    try {
        python --version 2>&1 | Out-Null
    } catch {
        Write-Host "Python not found - skipping benchmark" -ForegroundColor Yellow
        Write-Host "Log: $logFile" -ForegroundColor Gray
        exit 0
    }

    if (-not (Test-Path "venv")) {
        python -m venv venv
    }

    $venvPython = ".\venv\Scripts\python.exe"
    $venvPip = ".\venv\Scripts\pip.exe"
    & $venvPip install -q -e ".[inference]" -r requirements.txt

    # [7/7] Benchmark
    if ($env:SKIP_BENCHMARK -eq "1") {
        Write-Host "[7/7] SKIP_BENCHMARK=1, skipping benchmark" -ForegroundColor Cyan
    } else {
        Write-Host "[7/7] Running benchmark..." -ForegroundColor Yellow
        & $venvPython -m quantforge validate --profile $Profile --smoke-test 2>$null
        & $venvPython -m quantforge benchmark --profile $Profile
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  ALL DONE" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Model:     $ggufPath" -ForegroundColor White
    Write-Host "Metrics:   metrics\benchmark_results.json" -ForegroundColor White
    Write-Host "Report:    metrics\report.md" -ForegroundColor White
    Write-Host "Manifest:  models\manifest.json" -ForegroundColor White
    Write-Host "Log:       $logFile" -ForegroundColor White
    Write-Host ""
    Write-Host "Ollama:    .\setup_ollama.ps1" -ForegroundColor Cyan
    Write-Host "Test:      .\test_models.ps1" -ForegroundColor Cyan

} catch {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host "Log: $logFile" -ForegroundColor Gray
    Write-Host "Help: docs\troubleshooting.md" -ForegroundColor Cyan
    exit 1
} finally {
    Stop-Transcript | Out-Null
    . (Join-Path $PSScriptRoot "scripts\Pipeline-Lock.ps1") -LogsDir $env:QF_LOGS_DIR -Release
}
