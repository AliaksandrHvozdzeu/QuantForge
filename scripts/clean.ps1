# Disk cleanup wrapper
param(
    [switch]$DryRun,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$python = if (Test-Path "$ProjectRoot\venv\Scripts\python.exe") {
    "$ProjectRoot\venv\Scripts\python.exe"
} else { "python" }

$args = @("clean")
if ($DryRun) { $args += "--dry-run" }
if ($Yes) { $args += "-y" }

Push-Location $ProjectRoot
try {
    & $python -m pip install -q -e . 2>$null
    & $python -m quantforge @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
