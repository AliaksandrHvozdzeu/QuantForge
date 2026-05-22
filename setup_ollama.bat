@echo off
chcp 65001 > nul
cd /d "%~dp0ollama"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ollama\setup_ollama.ps1"
pause
