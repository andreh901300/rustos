#!/usr/bin/env bash
# One-time setup: creates the signing key and writes rustos.conf. Called by repo-setup.bat.
# Usage: make-signing-key.sh <github-user> <github-repo>
set -euo pipefail
GH_USER="$(printf '%s' "${1:?github user}" | tr 'A-Z' 'a-z')"
GH_REPO="${2:?github repo}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p .secrets

if [ -f .secrets/private.asc ] && [ -f repo/rustos-pub.gpg ]; then
  echo "A signing key already exists - keeping it (delete .secrets and repo/rustos-pub.gpg to start over)."
  H="$(mktemp -d)"; chmod 700 "$H"
  GNUPGHOME="$H" gpg --batch --import .secrets/private.asc >/dev/null 2>&1
  FPR="$(GNUPGHOME="$H" gpg --list-secret-keys --with-colons 2>/dev/null | awk -F: '/^fpr:/{print $10; exit}')"
  rm -rf "$H"
else
  H="$(mktemp -d)"; chmod 700 "$H"
  export GNUPGHOME="$H"
  cat > "$H/key.batch" <<EOF
%no-protection
Key-Type: eddsa
Key-Curve: ed25519
Key-Usage: sign
Name-Real: RustOS Repository
Name-Email: repo@rustos.invalid
Expire-Date: 0
%commit
EOF
  gpg --batch --gen-key "$H/key.batch" 2>/dev/null
  FPR="$(gpg --list-keys --with-colons | awk -F: '/^fpr:/{print $10; exit}')"
  gpg --armor --export "$FPR" > repo/rustos-pub.gpg
  gpg --armor --export-secret-keys "$FPR" > .secrets/private.asc
  unset GNUPGHOME
  rm -rf "$H"
fi

if ! printf '%s' "$FPR" | grep -qE '^[0-9A-F]{40}$'; then
  echo "ERROR: could not read the key fingerprint (got: $FPR)"; exit 1
fi
cat > rustos.conf <<EOF
REPO_URL=https://${GH_USER}.github.io/${GH_REPO}
REPO_FPR=${FPR}
EOF
echo "Key fingerprint: $FPR"
echo "Update repository URL: https://${GH_USER}.github.io/${GH_REPO}"
