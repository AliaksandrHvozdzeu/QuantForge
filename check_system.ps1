# ============================================================================
# System Readiness Check for Quantization
# ============================================================================

# Set UTF-8 encoding for proper text display
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  QuantForge System Diagnostics" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# ============================================================================
# 1. Check Windows version
# ============================================================================
Write-Host "[1/7] Checking operating system..." -ForegroundColor Yellow
try {
    $osInfo = Get-CimInstance Win32_OperatingSystem
    $osName = $osInfo.Caption
    $osVersion = $osInfo.Version
    
    Write-Host "  OS: $osName" -ForegroundColor White
    Write-Host "  Version: $osVersion" -ForegroundColor White
    
    if ($osInfo.OSArchitecture -ne "64-bit") {
        Write-Host "  64-bit Windows required" -ForegroundColor Red
        $allGood = $false
    } else {
        Write-Host "  64-bit system OK" -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not determine OS version" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# 2. Check RAM
# ============================================================================
Write-Host "[2/7] Checking RAM..." -ForegroundColor Yellow
try {
    $ram = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    Write-Host "  Installed: $([math]::Round($ram, 2)) GB" -ForegroundColor White
    
    if ($ram -lt 16) {
        Write-Host "  Minimum 16 GB RAM recommended" -ForegroundColor Yellow
        Write-Host "    Quantization may be slow or fail" -ForegroundColor Yellow
        $allGood = $false
    } elseif ($ram -lt 32) {
        Write-Host "  Sufficient for quantization (32 GB recommended)" -ForegroundColor Green
    } else {
        Write-Host "  Excellent! More than 32 GB" -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not determine RAM amount" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# 3. Check free disk space
# ============================================================================
Write-Host "[3/7] Checking free disk space..." -ForegroundColor Yellow
try {
    $drive = (Get-Location).Drive.Name
    $disk = Get-PSDrive -Name $drive
    $freeSpaceGB = $disk.Free / 1GB
    
    Write-Host "  Drive: $drive`:\" -ForegroundColor White
    Write-Host "  Free: $([math]::Round($freeSpaceGB, 2)) GB" -ForegroundColor White
    
    if ($freeSpaceGB -lt 30) {
        Write-Host "  Insufficient space! Minimum 30 GB required" -ForegroundColor Red
        $allGood = $false
    } elseif ($freeSpaceGB -lt 50) {
        Write-Host "  Sufficient space (50+ GB recommended)" -ForegroundColor Green
    } else {
        Write-Host "  Excellent! More than 50 GB free" -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not determine free space" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# 4. Check Docker Desktop
# ============================================================================
Write-Host "[4/7] Checking Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Version: $dockerVersion" -ForegroundColor White
        
        # Check if Docker is running
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Docker Desktop is running" -ForegroundColor Green
            
            # Check Docker resources
            $dockerMemory = docker info --format '{{.MemTotal}}' 2>&1
            if ($dockerMemory -and $dockerMemory -match '^\d+$') {
                $dockerMemGB = [math]::Round([int64]$dockerMemory / 1GB, 2)
                Write-Host "  Docker memory: $dockerMemGB GB" -ForegroundColor White
                
                if ($dockerMemGB -lt 8) {
                    Write-Host "  Recommend allocating at least 8 GB RAM to Docker" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "  Docker installed but not running!" -ForegroundColor Red
            Write-Host "    Start Docker Desktop from Start menu" -ForegroundColor Yellow
            $allGood = $false
        }
    } else {
        Write-Host "  Docker not installed!" -ForegroundColor Red
        Write-Host "    Download: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        $allGood = $false
    }
} catch {
    Write-Host "  Docker not found" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# ============================================================================
# 5. Check Python (optional)
# ============================================================================
Write-Host "[5/7] Checking Python (optional)..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Version: $pythonVersion" -ForegroundColor White
        
        # Check Python version
        if ($pythonVersion -match 'Python (\d+\.\d+)') {
            $version = [version]$matches[1]
            if ($version -lt [version]"3.8") {
                Write-Host "  Python 3.8 or newer recommended" -ForegroundColor Yellow
            } else {
                Write-Host "  Python version OK" -ForegroundColor Green
            }
        }
        
        # Check pip
        $pipVersion = python -m pip --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  pip installed" -ForegroundColor Green
        }
    } else {
        Write-Host "  Python not found" -ForegroundColor Yellow
        Write-Host "    Not critical - models will be quantized without Python tests" -ForegroundColor White
        Write-Host "    Install Python 3.8+ for full testing" -ForegroundColor White
    }
} catch {
    Write-Host "  Python not installed (optional)" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# 6. Check internet connection
# ============================================================================
Write-Host "[6/7] Checking internet connection..." -ForegroundColor Yellow
try {
    $pingResult = Test-Connection -ComputerName huggingface.co -Count 1 -Quiet -ErrorAction SilentlyContinue
    if ($pingResult) {
        Write-Host "  Connection to Hugging Face OK" -ForegroundColor Green
    } else {
        Write-Host "  Could not connect to huggingface.co" -ForegroundColor Yellow
        Write-Host "    Check internet connection" -ForegroundColor White
    }
} catch {
    Write-Host "  Could not check internet" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# 7. Check project files
# ============================================================================
Write-Host "[7/7] Checking project files..." -ForegroundColor Yellow
$requiredFiles = @(
    "run_optimization.ps1",
    "quantize_only.ps1",
    "Dockerfile",
    "config\default.yaml",
    "config\profiles\qwen2.5-coder-7b.yaml",
    "config.ps1.example",
    "scripts\quantize.sh",
    "scripts\Load-Config.ps1",
    "src\quantforge\cli.py",
    "pyproject.toml",
    "docker\versions.env",
    ".github\workflows\ci.yml",
    "scripts\ci.ps1",
    "docker-compose.yml",
    "docs\api.md",
    "start_api.ps1",
    "quantforge.ps1",
    "docs\architecture.md",
    "docs\models.md",
    "CHANGELOG.md",
    "ARTICLE.md",
    "LICENSE",
    "docs\void.md",
    "scripts\verify_ollama.ps1",
    "start_web.ps1",
    "docs\web.md",
    "src\benchmark.py",
    "src\validate_gguf.py"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  OK: $file" -ForegroundColor Green
    } else {
        Write-Host "  Missing: $file" -ForegroundColor Red
        $missingFiles += $file
        $allGood = $false
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "  Missing files:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "    - $file" -ForegroundColor Yellow
    }
}
Write-Host ""

# ============================================================================
# Final report
# ============================================================================
Write-Host "============================================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  READY TO GO!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "System is ready for model quantization." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step:" -ForegroundColor Cyan
    Write-Host "  .\run_optimization.ps1" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "  ISSUES DETECTED" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please fix the issues above before running." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Main requirements:" -ForegroundColor Cyan
    Write-Host "  - Windows 10/11 64-bit" -ForegroundColor White
    Write-Host "  - 16+ GB RAM (32 GB recommended)" -ForegroundColor White
    Write-Host "  - 30+ GB free disk space" -ForegroundColor White
    Write-Host "  - Docker Desktop (running)" -ForegroundColor White
    Write-Host ""
    Write-Host "Detailed instructions: README.md" -ForegroundColor Cyan
    Write-Host ""
}

# Pause to read results
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
