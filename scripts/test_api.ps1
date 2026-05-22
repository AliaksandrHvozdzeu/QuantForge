# Quick health check for QuantForge API
param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
$url = "$BaseUrl/v1/models"

Write-Host "GET $url" -ForegroundColor Cyan
try {
    $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
    Write-Host "OK" -ForegroundColor Green
    $resp | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "FAILED: $_" -ForegroundColor Red
    Write-Host "Start server: .\scripts\start_api.ps1" -ForegroundColor Yellow
    exit 1
}
