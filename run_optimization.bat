@echo off
chcp 65001 > nul
REM ============================================================================
REM Wrapper for launching PowerShell optimization script
REM ============================================================================

echo.
echo ============================================================
echo   Qwen2.5-Coder-7B Q5_K_M Quantization
echo ============================================================
echo.

REM Check for PowerShell
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell not found!
    echo Install PowerShell or use Windows 7+
    pause
    exit /b 1
)

REM Run PowerShell script with execution rights and UTF-8 encoding
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & '%~dp0run_optimization.ps1'"

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo   Error detected during execution
    echo ============================================================
    pause
    exit /b %errorlevel%
)

echo.
echo Press any key to exit...
pause > nul
