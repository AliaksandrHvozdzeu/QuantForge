# Load QuantForge YAML config into environment variables
param(
    [string]$Profile = "qwen2.5-coder-7b"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Loader = Join-Path $ProjectRoot "scripts\load_config.py"

function Ensure-PyYaml {
    param([string]$PythonExe)
    $check = & $PythonExe -c "import yaml" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing PyYAML..." -ForegroundColor Yellow
        & $PythonExe -m pip install pyyaml -q
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install PyYAML. Run: pip install pyyaml"
        }
    }
}

# Prefer venv python if present
$python = "python"
$venvPy = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (Test-Path $venvPy) { $python = $venvPy }

Ensure-PyYaml -PythonExe $python

Push-Location $ProjectRoot
try {
    & $python $Loader --profile $Profile --apply-env
    if ($LASTEXITCODE -ne 0) { throw "Config load failed" }

    Write-Host "Config profile: $Profile" -ForegroundColor Green
    Write-Host "  MODEL_REPO:     $env:MODEL_REPO" -ForegroundColor Gray
    Write-Host "  GGUF_OUTPUT:    $env:GGUF_OUTPUT" -ForegroundColor Gray
    Write-Host "  QUANT_TYPE:     $env:QUANT_TYPE" -ForegroundColor Gray
}
finally {
    Pop-Location
}
