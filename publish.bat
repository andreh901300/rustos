@echo off
cd /d "%~dp0"
title RustOS - publish a new version
where git >nul 2>&1
if %errorlevel% neq 0 (
  echo Git is not installed. Open a terminal and run:  winget install Git.Git
  echo Then close and reopen this window.
  pause
  exit /b 1
)
if not exist ".git" (
  echo This folder is not connected to GitHub yet. Follow GITHUB-SETUP.md, step 5.
  pause
  exit /b 1
)
set "MSG="
set /p MSG=What did you change? (a few words): 
if "%MSG%"=="" set "MSG=update"
git add -A
git diff --cached --quiet && (
  echo Nothing changed since the last publish.
  pause
  exit /b 0
)
git commit -m "%MSG%"
git push || (
  echo.
  echo Push failed. Check your internet / GitHub login and try again.
  pause
  exit /b 1
)
echo.
echo Pushed! GitHub is now building the update (about 2-3 minutes).
echo Watch it on your repository's "Actions" tab.
echo Installed RustOS systems pick it up within a day, or right away with:  sudo rustos-autoupdate now
pause
