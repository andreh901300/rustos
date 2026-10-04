@echo off
cd /d "%~dp0"
title RustOS - Hyper-V
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Asking for administrator permission...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
echo Freeing the memory WSL is holding...
wsl --shutdown >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0hyperv-create-vm.ps1"
echo.
pause
