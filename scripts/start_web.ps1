# Start QuantForge web dashboard
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot

try {
    $python = if (Test-Path "venv\Scripts\python.exe") { ".\venv\Scripts\python.exe" } else { "python" }
    $pip = if (Test-Path "venv\Scripts\pip.exe") { ".\venv\Scripts\pip.exe" } else { "pip" }

    if (-not (Test-Path "venv")) {
        Write-Host "Creating venv..." -ForegroundColor Yellow
        python -m venv venv
        $python = ".\venv\Scripts\python.exe"
        $pip = ".\venv\Scripts\pip.exe"
    }

    Write-Host "Installing web dependencies..." -ForegroundColor Yellow
    & $pip install -q -e ".[web]"
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

    $port = if ($env:QF_WEB_PORT) { $env:QF_WEB_PORT } else { "8787" }
    Write-Host ""
    Write-Host "Dashboard: http://127.0.0.1:${port}/" -ForegroundColor Cyan
    Write-Host ""

    & $python -m quantforge web --port $port
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
