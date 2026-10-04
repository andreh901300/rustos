@echo off
title RustOS setup (run once)
echo === RustOS setup ===
echo Needs about 20 GB free disk space.
echo.

wsl -d archlinux -u root -e true >nul 2>&1
if %errorlevel% equ 0 goto :tools

echo Arch Linux for WSL is not installed. Installing it now...
wsl --update
wsl --install -d archlinux --no-launch

wsl -d archlinux -u root -e true >nul 2>&1
if %errorlevel% neq 0 goto :notready

:tools
echo.
echo Installing archiso inside Arch (a few minutes)...
wsl -d archlinux -u root bash -c "if grep -qi microsoft /proc/version && ! grep -q '^DisableSandbox' /etc/pacman.conf; then sed -i '/^\[options\]/a DisableSandbox' /etc/pacman.conf; fi; pacman-key --init && pacman-key --populate archlinux && pacman -Syu --noconfirm archiso rsync" || goto :fail

echo.
echo Setup done. Now run build.bat
pause
exit /b 0

:notready
echo.
echo Arch for WSL is still not ready.
echo 1. Restart your PC and run setup.bat again.
echo 2. If it still fails, open PowerShell and run:  wsl --list --online
echo    and tell me the exact name shown for Arch Linux.
pause
exit /b 1

:fail
echo.
echo Something failed. Scroll up for the error.
pause
exit /b 1
