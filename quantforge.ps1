# QuantForge — unified entry point (P4)
param(
    [Parameter(Position = 0)]
    [string]$Command = "",
    [string]$Profile = ""
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

if ($Profile) { $env:QUANTFORGE_PROFILE = $Profile }

function Show-Menu {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  QuantForge" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1  Check system" -ForegroundColor White
    Write-Host "  2  Full pipeline (download + quantize + benchmark)" -ForegroundColor White
    Write-Host "  3  Quantize only" -ForegroundColor White
    Write-Host "  4  Test / benchmark" -ForegroundColor White
    Write-Host "  5  Start API (Void / IDE)" -ForegroundColor White
    Write-Host "  W  Web dashboard" -ForegroundColor White
    Write-Host "  6  Setup Ollama" -ForegroundColor White
    Write-Host "  6v Verify Ollama" -ForegroundColor White
    Write-Host "  7  Inventory (disk usage)" -ForegroundColor White
    Write-Host "  8  Clean disk (inactive models)" -ForegroundColor White
    Write-Host "  9  CI checks (lint + tests)" -ForegroundColor White
    Write-Host "  0  Exit" -ForegroundColor White
    Write-Host ""
}

function Invoke-QuantforgePython {
    param([string[]]$Args)
    $python = if (Test-Path "$ProjectRoot\venv\Scripts\python.exe") {
        "$ProjectRoot\venv\Scripts\python.exe"
    } else { "python" }
    Push-Location $ProjectRoot
    try {
        & $python -m quantforge @Args
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }
}

Push-Location $ProjectRoot
try {
    if ($Command) {
        switch ($Command.ToLower()) {
            "check"      { & "$ProjectRoot\check_system.ps1"; break }
            "run"        { & "$ProjectRoot\run_optimization.ps1"; break }
            "quantize"   { & "$ProjectRoot\quantize_only.ps1"; break }
            "test"       { & "$ProjectRoot\test_models.ps1"; break }
            "api"        { & "$ProjectRoot\start_api.ps1"; break }
            "ollama"     { & "$ProjectRoot\setup_ollama.ps1"; break }
            "ollama-verify" { Invoke-QuantforgePython @("ollama", "verify"); break }
            "inventory"  { Invoke-QuantforgePython @("inventory"); break }
            "clean"      { Invoke-QuantforgePython @("clean", "--dry-run"); break }
            "ci"         { & "$ProjectRoot\scripts\ci.ps1"; break }
            "report"     { Invoke-QuantforgePython @("report"); break }
            "web"        { & "$ProjectRoot\start_web.ps1"; break }
            default {
                Write-Host "Unknown command: $Command" -ForegroundColor Red
                Write-Host "Usage: .\quantforge.ps1 [check|run|quantize|test|api|ollama|inventory|clean|ci|report]"
                exit 1
            }
        }
        exit 0
    }

    while ($true) {
        Show-Menu
        $choice = Read-Host "Select"
        switch ($choice) {
            "1" { & "$ProjectRoot\check_system.ps1" }
            "2" { & "$ProjectRoot\run_optimization.ps1" }
            "3" { & "$ProjectRoot\quantize_only.ps1" }
            "4" { & "$ProjectRoot\test_models.ps1" }
            "5" { & "$ProjectRoot\start_api.ps1" }
            "W" { & "$ProjectRoot\start_web.ps1" }
            "w" { & "$ProjectRoot\start_web.ps1" }
            "6" { & "$ProjectRoot\setup_ollama.ps1" }
            "6v" { Invoke-QuantforgePython @("ollama", "verify") }
            "7" { Invoke-QuantforgePython @("inventory") }
            "8" { Invoke-QuantforgePython @("clean") }
            "9" { & "$ProjectRoot\scripts\ci.ps1" }
            "0" { break }
            default { Write-Host "Invalid choice." -ForegroundColor Yellow }
        }
        if ($choice -eq "0") { break }
        Read-Host "Press Enter to continue"
    }
}
finally {
    Pop-Location
}
