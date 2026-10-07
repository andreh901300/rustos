#!/usr/bin/env bash
# RustOS publish for Linux (use this on RustOS; publish.bat is the Windows version).
# Run it from the project folder:   bash publish.sh
# It connects the folder to your GitHub repository by itself the first time, adds your one-line message to
# CHANGELOG.txt, commits, and pushes. GitHub then builds the update for every installed RustOS.
REMOTE="${RUSTOS_REMOTE:-https://github.com/andreh901300/rustos.git}"
cd "$(dirname "$(readlink -f "$0")")" || exit 1

pause() { echo; read -r -p "Press Enter to close. " _ || true; }
die()   { echo; echo "$1"; pause; exit 1; }

command -v git >/dev/null 2>&1 || die "Git is not installed. Run:  sudo pacman -S git   then run this again."

if [ ! -d .git ]; then
  echo "This folder is not connected to GitHub yet. Connecting it to your RustOS repository now..."
  git init -q
  git remote add origin "$REMOTE"
  if ! git fetch -q origin main; then
    rm -rf .git
    die "Could not reach GitHub. Check your internet, then run publish.sh again."
  fi
  git symbolic-ref HEAD refs/heads/main
  git reset -q origin/main
  # keep any file that exists on GitHub but is missing from this folder
  git ls-files --deleted -z | xargs -0 -r git checkout --
  echo "Connected. Your files will be compared with what is already on GitHub."
  echo
fi

# git needs a name for the commit (one time)
if [ -z "$(git config user.name)" ]; then
  read -r -p "Your name for the commit (anything, like your GitHub name): " gname
  git config user.name "${gname:-RustOS}"
fi
if [ -z "$(git config user.email)" ]; then
  read -r -p "Your email for the commit (your GitHub email): " gmail
  git config user.email "${gmail:-rustos@users.noreply.github.com}"
fi

if [ -z "$(git status --porcelain)" ]; then
  echo "Nothing changed since the last publish."
  pause; exit 0
fi

read -r -p "One line for the What's new list (or just press Enter to skip): " MSG
MSG=$(printf '%s' "$MSG" | tr '\r\n' '  ' | sed 's/^ *//; s/ *$//' | cut -c1-120)
read -r -p "New version number? (like 2.3, or just press Enter to keep the same version): " NEWVER
NEWVER=$(printf '%s' "$NEWVER" | tr -d ' \r\n')
if [ -n "$NEWVER" ] && ! printf '%s' "$NEWVER" | grep -Eq '^[0-9]+(\.[0-9]+){0,2}$'; then
  echo "Version '$NEWVER' is not like 1.2 - keeping the old version number."
  NEWVER=""
fi
COMMITMSG=${MSG:-update}

# add the line (and the new version) to CHANGELOG.txt
if [ -n "$MSG" ] || [ -n "$NEWVER" ]; then
  [ -f CHANGELOG.txt ] || : > CHANGELOG.txt
  [ -n "$NEWVER" ] && printf '%s\n' "$NEWVER" > VERSION
  MSG="$MSG" NEWVER="$NEWVER" awk '
    function line_msg() { if (ENVIRON["MSG"] != "") print "- " ENVIRON["MSG"] }
    !seen && /^== / {
      seen = 1
      if (ENVIRON["NEWVER"] != "") { print "== RustOS " ENVIRON["NEWVER"] " =="; line_msg(); print ""; print; next }
      print; line_msg(); next
    }
    { print }
    END {
      if (!seen) {
        print ""
        if (ENVIRON["NEWVER"] != "") print "== RustOS " ENVIRON["NEWVER"] " =="; else print "== RustOS =="
        line_msg()
      }
    }' CHANGELOG.txt > CHANGELOG.txt.new && mv CHANGELOG.txt.new CHANGELOG.txt
fi

git add -A
if git diff --cached --quiet; then
  echo "Nothing changed since the last publish."
  pause; exit 0
fi
git commit -q -m "$COMMITMSG" || die "The commit failed."
git pull -q --no-rebase --no-edit -X ours origin main >/dev/null 2>&1

push() { GIT_TERMINAL_PROMPT=0 git push -q origin main; }
if ! push; then
  echo
  echo "GitHub needs you to sign in (one time). A browser window will open."
  if ! command -v gh >/dev/null 2>&1; then
    echo "Installing the GitHub sign-in tool (needs your password)..."
    sudo pacman -S --needed --noconfirm github-cli || die "Could not install github-cli. Run:  sudo pacman -S github-cli"
  fi
  gh auth login -h github.com -p https -w || die "Sign-in did not finish. Run publish.sh again to retry."
  gh auth setup-git
  push || die "Push failed. Check your internet / GitHub login and try again."
fi
echo
echo "Pushed! GitHub is now building the update (about 2-3 minutes)."
echo "Watch it on your repository's \"Actions\" tab."
echo "Installed RustOS systems pick it up within a day, or right away with:  sudo rustos-autoupdate now"
pause
