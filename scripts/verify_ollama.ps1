# Verify Ollama Modelfile and optional registered model
param([switch]$RequireModel)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$python = if (Test-Path "$ProjectRoot\venv\Scripts\python.exe") {
    "$ProjectRoot\venv\Scripts\python.exe"
} else { "python" }

Push-Location $ProjectRoot
try {
    & $python -m pip install -q -e . 2>$null
    $args = @("ollama", "verify")
    if ($RequireModel) { $args += "--require-model" }
    & $python -m quantforge @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
