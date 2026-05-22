# Fix llama.dll load errors on Windows (missing CUDA dependencies)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$venvPip = Join-Path $ProjectRoot "venv\Scripts\pip.exe"
$venvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $venvPip)) {
    Write-Host "ERROR: venv not found." -ForegroundColor Red
    exit 1
}

Write-Host "Repairing llama-cpp-python environment..." -ForegroundColor Cyan
Write-Host ""

# Check if CUDA build is installed
$libDir = Join-Path $ProjectRoot "venv\Lib\site-packages\llama_cpp\lib"
$hasCuda = Test-Path (Join-Path $libDir "ggml-cuda.dll")

if ($hasCuda) {
    Write-Host "CUDA build detected - installing NVIDIA runtime packages..." -ForegroundColor Yellow
    & $venvPip install nvidia-cuda-runtime-cu12 nvidia-cublas-cu12 nvidia-cuda-nvrtc-cu12
} else {
    Write-Host "CPU build detected - reinstalling..." -ForegroundColor Yellow
    & $venvPip uninstall -y llama-cpp-python 2>$null
    & $venvPip install llama-cpp-python --force-reinstall
}

Write-Host ""
Write-Host "Verifying import..." -ForegroundColor Yellow
$testScript = @"
import sys
sys.path.insert(0, r'$ProjectRoot\src')
import llama_env
from llama_cpp import Llama
print('OK')
"@

& $venvPython -c $testScript
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Fixed! Run: .\test_models.ps1" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Still failing. Try CPU-only reinstall:" -ForegroundColor Yellow
    Write-Host "  .\scripts\install_llama_cpu.ps1" -ForegroundColor White
    exit 1
}
