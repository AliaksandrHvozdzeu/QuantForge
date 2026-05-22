# Install CPU-only llama-cpp-python (no CUDA dependencies)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$venvPip = Join-Path $ProjectRoot "venv\Scripts\pip.exe"
$venvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

Write-Host "Installing CPU-only llama-cpp-python..." -ForegroundColor Yellow
& $venvPip uninstall -y llama-cpp-python 2>$null
& $venvPip install llama-cpp-python --force-reinstall

$testScript = @"
import sys
sys.path.insert(0, r'$ProjectRoot\src')
import llama_env
from llama_cpp import Llama
print('OK')
"@
& $venvPython -c $testScript
if ($LASTEXITCODE -eq 0) {
    Write-Host "CPU build ready." -ForegroundColor Green
} else {
    Write-Host "Install failed." -ForegroundColor Red
    exit 1
}
