# Pipeline lock — prevents concurrent run_optimization / quantize_only
param(
    [string]$LogsDir = "logs",
    [switch]$Release
)

$ErrorActionPreference = "Stop"
$lockPath = Join-Path $LogsDir ".pipeline.lock"

if ($Release) {
    if (Test-Path $lockPath) {
        Remove-Item $lockPath -Force
        Write-Host "Pipeline lock released." -ForegroundColor Gray
    }
    return
}

if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

if (Test-Path $lockPath) {
    $info = Get-Item $lockPath
    $age = (Get-Date) - $info.LastWriteTime
    if ($age.TotalHours -gt 6) {
        Write-Host "Stale lock (${age}) — removing." -ForegroundColor Yellow
        Remove-Item $lockPath -Force
    } else {
        $pid = Get-Content $lockPath -ErrorAction SilentlyContinue
        throw "Pipeline already running (lock: $lockPath, pid: $pid). Wait or delete the lock file."
    }
}

$procId = $PID
Set-Content -Path $lockPath -Value "$procId`n$(Get-Date -Format o)" -Encoding UTF8
Write-Host "Pipeline lock acquired (PID $procId)" -ForegroundColor Gray
