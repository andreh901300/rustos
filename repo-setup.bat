@echo off
cd /d "%~dp0"
title RustOS - set up the update channel (one time)
wsl -d archlinux -u root -e true >nul 2>&1
if %errorlevel% neq 0 (
  echo Arch for WSL is not ready. Run setup.bat first.
  pause
  exit /b 1
)
echo === RustOS update channel setup (one time) ===
echo.
echo You need a free GitHub account and an EMPTY PUBLIC repository (see GITHUB-SETUP.md, step 1).
echo.
set /p GHUSER=Your GitHub username: 
set /p GHREPO=Name of the repository (for example rustos): 
if "%GHUSER%"=="" goto :bad
if "%GHREPO%"=="" goto :bad

for /f "delims=" %%i in ('wsl -d archlinux -u root wslpath -a "%CD%"') do set "SRC=%%i"
wsl -d archlinux -u root bash -c "bash '%SRC%/repo/make-signing-key.sh' '%GHUSER%' '%GHREPO%'" || goto :fail

echo.
echo ================================================================
echo  DONE. Now do step 3 of GITHUB-SETUP.md:
echo.
echo  Open this file in Notepad and copy ALL of its text:
echo      %CD%\.secrets\private.asc
echo  and paste it into a GitHub secret called  GPG_PRIVATE_KEY
echo.
echo  Keep that file private. Never upload it anywhere else.
echo ================================================================
start notepad "%CD%\.secrets\private.asc"
pause
exit /b 0

:bad
echo Please type both the username and the repository name.
pause
exit /b 1

:fail
echo.
echo Something failed. Scroll up for the error.
pause
exit /b 1
