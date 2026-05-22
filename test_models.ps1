# ============================================================================
# Quick testing of already quantized models
# ============================================================================

# Set UTF-8 encoding for proper text display
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Qwen2.5-Coder-7B Model Testing" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$Profile = if ($env:QUANTFORGE_PROFILE) { $env:QUANTFORGE_PROFILE } else { "qwen2.5-coder-7b" }
if (Test-Path "config.ps1") { . .\config.ps1 }
. (Join-Path $PSScriptRoot "scripts\Load-Config.ps1") -Profile $Profile

$modelPath = Join-Path $env:QF_MODELS_DIR $env:GGUF_OUTPUT

if (-not (Test-Path $modelPath)) {
    Write-Host "Model not found:" -ForegroundColor Red
    Write-Host "  -> $modelPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run .\run_optimization.ps1 or .\quantize_only.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found model: $modelPath" -ForegroundColor Green
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found in PATH" -ForegroundColor Red
    Write-Host "Install Python 3.8+ from python.org" -ForegroundColor Yellow
    exit 1
}

# Check/create venv
if (-not (Test-Path "venv")) {
    Write-Host ""
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error creating venv" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created" -ForegroundColor Green
}

# Activate and install dependencies
$venvPython = ".\venv\Scripts\python.exe"
$venvPip = ".\venv\Scripts\pip.exe"

Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow

# Check if llama-cpp-python is installed
$installed = & $venvPip list 2>&1 | Select-String "llama-cpp-python"
$hasNvidiaGpu = $false

try {
    $null = Get-Command nvidia-smi -ErrorAction Stop
    $gpuName = & nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1
    if ($gpuName) {
        $hasNvidiaGpu = $true
        Write-Host "NVIDIA GPU: $gpuName" -ForegroundColor Green
    }
} catch {
    Write-Host "No NVIDIA GPU detected - CPU benchmark only" -ForegroundColor Yellow
}

if (-not $installed) {
    Write-Host "Installing llama-cpp-python (CPU build)..." -ForegroundColor Yellow
    & $venvPip install --upgrade pip | Out-Null
    & $venvPip install llama-cpp-python
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error installing llama-cpp-python" -ForegroundColor Red
        Write-Host "https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Cyan
        exit 1
    }
    Write-Host "llama-cpp-python installed (CPU)" -ForegroundColor Green
} else {
    Write-Host "llama-cpp-python already installed" -ForegroundColor Green
}

# Offer CUDA build for GPU benchmarks
if ($hasNvidiaGpu) {
    Write-Host ""
    Write-Host "GPU detected. For GPU benchmarks install CUDA build:" -ForegroundColor Cyan
    Write-Host "  .\scripts\install_llama_gpu.ps1" -ForegroundColor White
    Write-Host ""
    
    $installGpu = Read-Host "Install CUDA build now? (y/N)"
    if ($installGpu -eq "y" -or $installGpu -eq "Y") {
        & "$PSScriptRoot\scripts\install_llama_gpu.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "CUDA install failed - continuing with CPU-only tests" -ForegroundColor Yellow
        }
    }
}

# Run benchmark
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Running model tests..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Installing QuantForge package..." -ForegroundColor Yellow
& $venvPip install -q -e ".[inference]" -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install -e . failed" -ForegroundColor Red
    exit 1
}

# Verify llama_cpp loads (fix missing CUDA DLLs on Windows)
Write-Host "Verifying llama-cpp-python..." -ForegroundColor Yellow
$verifyScript = "from quantforge import llama_env; from llama_cpp import Llama; print('OK')"
& $venvPython -c $verifyScript 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "llama.dll load failed - running repair..." -ForegroundColor Yellow
    & "$PSScriptRoot\scripts\repair_llama.ps1"
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

& $venvPython -m quantforge benchmark --profile $Profile

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  Testing completed successfully!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Results saved to:" -ForegroundColor Cyan
    Write-Host "  -> metrics\python_benchmark_results.txt" -ForegroundColor White
    Write-Host "  -> metrics\benchmark_results.json" -ForegroundColor White
    Write-Host "  -> metrics\benchmark_history.jsonl" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  CPU only:  .\venv\Scripts\python.exe -m quantforge benchmark --cpu-only" -ForegroundColor White
    Write-Host "  GPU only:  .\venv\Scripts\python.exe -m quantforge benchmark --gpu-only" -ForegroundColor White
    Write-Host "  Compare:   .\venv\Scripts\python.exe -m quantforge metrics compare" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Error running benchmark" -ForegroundColor Red
    exit 1
}
