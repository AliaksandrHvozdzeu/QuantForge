@echo off
chcp 65001 > nul
REM ============================================================================
REM System readiness check
REM ============================================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & '%~dp0check_system.ps1'"

if %errorlevel% neq 0 (
    pause
    exit /b %errorlevel%
)
