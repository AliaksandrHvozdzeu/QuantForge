# Local CI checks (lint + config) — mirrors GitHub Actions lint/test-package jobs
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot

try {
    $python = if (Test-Path "venv\Scripts\python.exe") { ".\venv\Scripts\python.exe" } else { "python" }

    Write-Host "Installing dev dependencies..." -ForegroundColor Yellow
    & $python -m pip install -q -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

    Write-Host "Ruff check..." -ForegroundColor Yellow
    & $python -m ruff check src/
    if ($LASTEXITCODE -ne 0) { throw "ruff check failed" }

    Write-Host "Ruff format..." -ForegroundColor Yellow
    & $python -m ruff format --check src/
    if ($LASTEXITCODE -ne 0) { throw "ruff format failed" }

    Write-Host "Config smoke..." -ForegroundColor Yellow
    & $python -m quantforge config --json --profile qwen2.5-coder-7b | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "config load failed" }

    Write-Host "Unit tests..." -ForegroundColor Yellow
    & $python -m pytest tests/ -q
    if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

    Write-Host ""
    Write-Host "CI checks passed." -ForegroundColor Green
}
finally {
    Pop-Location
}
