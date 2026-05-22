# Register Qwen2.5-Coder GGUF in Ollama with correct ChatML template
$ErrorActionPreference = "Stop"

$ollamaDir = $PSScriptRoot
$ggufPath = Join-Path $ollamaDir "..\models\Qwen2.5-Coder-7B-Q5_K_M.gguf"
$modelfile = Join-Path $ollamaDir "Modelfile"

if (-not (Test-Path $ggufPath)) {
    Write-Host "ERROR: GGUF not found: $ggufPath" -ForegroundColor Red
    Write-Host "Run quantization first: .\run_optimization.ps1" -ForegroundColor Yellow
    exit 1
}

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "ERROR: ollama not found. Install from https://ollama.com" -ForegroundColor Red
    exit 1
}

Write-Host "Creating Ollama model: qwen2.5-coder-q5" -ForegroundColor Cyan
Write-Host "GGUF: $ggufPath" -ForegroundColor Gray
Write-Host ""

Push-Location $ollamaDir
try {
    ollama create qwen2.5-coder-q5 -f Modelfile
    if ($LASTEXITCODE -ne 0) { exit 1 }

    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test in terminal:" -ForegroundColor Cyan
    Write-Host "  ollama run qwen2.5-coder-q5" -ForegroundColor White
    Write-Host ""
    Write-Host "In Void IDE use Ollama model name:" -ForegroundColor Cyan
    Write-Host "  qwen2.5-coder-q5" -ForegroundColor White
    Write-Host ""
    Write-Host "Do NOT point Void to raw .gguf file." -ForegroundColor Yellow
    Write-Host "Use the Ollama model name above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Verify:" -ForegroundColor Cyan
    Write-Host "  .\scripts\verify_ollama.ps1 -RequireModel" -ForegroundColor White
}
finally {
    Pop-Location
}
