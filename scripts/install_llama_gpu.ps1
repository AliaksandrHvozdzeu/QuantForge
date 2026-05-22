# Install llama-cpp-python with CUDA support (Windows + NVIDIA GPU)
param(
    [string]$CudaIndex = "cu124"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$venvPip = Join-Path $ProjectRoot "venv\Scripts\pip.exe"
$venvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $venvPip)) {
    Write-Host "ERROR: venv not found. Run test_models.ps1 first." -ForegroundColor Red
    exit 1
}

$nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if (-not $nvidia) {
    Write-Host "ERROR: nvidia-smi not found. Install NVIDIA drivers first." -ForegroundColor Red
    exit 1
}

Write-Host "NVIDIA GPU detected:" -ForegroundColor Green
& nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

Write-Host ""
Write-Host "Step 1/3: Installing CUDA runtime libraries (pip)..." -ForegroundColor Yellow
& $venvPip install nvidia-cuda-runtime-cu12 nvidia-cublas-cu12 nvidia-cuda-nvrtc-cu12
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "Step 2/3: Installing llama-cpp-python with CUDA ($CudaIndex)..." -ForegroundColor Yellow
$indexUrl = "https://abetlen.github.io/llama-cpp-python/whl/$CudaIndex"

& $venvPip uninstall -y llama-cpp-python 2>$null
& $venvPip install llama-cpp-python --extra-index-url $indexUrl
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "CUDA $CudaIndex wheel failed. Try:" -ForegroundColor Yellow
    Write-Host "  .\scripts\install_llama_gpu.ps1 -CudaIndex cu121" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "Step 3/3: Verifying import..." -ForegroundColor Yellow
$testScript = @"
import sys
sys.path.insert(0, r'$ProjectRoot\src')
import llama_env
from llama_cpp import Llama
print('OK: llama_cpp loads correctly')
"@

& $venvPython -c $testScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Import verification failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "CUDA build ready. Run benchmark:" -ForegroundColor Green
Write-Host "  .\venv\Scripts\python.exe -m quantforge benchmark" -ForegroundColor White
