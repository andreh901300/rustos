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
  echo This folder is not connected to GitHub yet. Connecting it to your RustOS repository now...
  git init >nul 2>&1
  git remote add origin https://github.com/andreh901300/rustos.git
  git fetch origin main || (
    echo.
    echo Could not reach GitHub. Check your internet and GitHub login, then run publish.bat again.
    rmdir /s /q ".git"
    pause
    exit /b 1
  )
  git symbolic-ref HEAD refs/heads/main
  git reset origin/main >nul
  rem keep any file that exists on GitHub but is missing from this folder
  for /f "delims=" %%f in ('git ls-files --deleted') do git checkout -- "%%f"
  echo Connected. Your files will be compared with what is already on GitHub.
  echo.
)
set "DIRTY="
for /f "delims=" %%i in ('git status --porcelain') do set "DIRTY=1"
if not defined DIRTY (
  echo Nothing changed since the last publish.
  pause
  exit /b 0
)
set "MSG="
set /p MSG=One line for the What's new list (or just press Enter to skip): 
set "COMMITMSG=%MSG%"
if "%COMMITMSG%"=="" set "COMMITMSG=update"
set "NEWVER="
set /p NEWVER=New version number? (like 1.2, or just press Enter to keep the same version): 
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0add-changelog.ps1"
git add -A
git diff --cached --quiet && (
  echo Nothing changed since the last publish.
  pause
  exit /b 0
)
git commit -m "%COMMITMSG%"
git pull --no-rebase --no-edit -X ours origin main >nul 2>&1
git push origin main || (
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
