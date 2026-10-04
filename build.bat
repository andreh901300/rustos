@echo off
title RustOS ISO build
setlocal
cd /d "%~dp0"

wsl -d archlinux -u root -e true >nul 2>&1
if %errorlevel% neq 0 (
  echo Arch for WSL is not ready. Run setup.bat first.
  pause
  exit /b 1
)

for /f "delims=" %%i in ('wsl -d archlinux -u root wslpath -a "%CD%"') do set "SRC=%%i"
echo Project folder: %SRC%
echo This downloads about 3 GB of packages and takes 15-40 minutes.
echo.

wsl -d archlinux -u root bash -c "mkdir -p /root/rustos-arch && rsync -a --delete --exclude=out/ --exclude=.secrets/ --exclude=.git/ '%SRC%'/ /root/rustos-arch/ && find /root/rustos-arch -type f ! -name '*.png' ! -name '*.svg' -exec sed -i 's/\r$//' {} + && cd /root/rustos-arch && bash build-iso.sh && mkdir -p '%SRC%/out' && cp /root/rustos-arch/out/*.iso '%SRC%/out/'" || goto :fail

echo.
echo Done. Your ISO is in the "out" folder. Double-click hyperv.bat to try it in Hyper-V.
pause
exit /b 0

:fail
echo.
echo Build failed. Scroll up for the first error and send it to me.
pause
exit /b 1
