@echo off
cd /d "%~dp0"
title RustOS - dual boot with Windows
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Asking for administrator permission...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dualboot-prepare.ps1"
echo.
pause
