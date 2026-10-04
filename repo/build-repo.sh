#!/usr/bin/env bash
# Builds the signed RustOS package repository into out/site.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OV="overlay/airootfs"
OUT="$ROOT/out/site"
WORK="/tmp/rustos-pkg"
STAGE_ONLY=0

[ "${1:-}" = "--stage-only" ] && STAGE_ONLY=1

[ -f rustos.conf ] && . ./rustos.conf

# ----------------------------------------------------------------
# Arch package database
# ----------------------------------------------------------------
echo "==> Updating Arch Linux package databases..."

pacman -Sy --noconfirm archlinux-keyring
pacman -Sy --noconfirm

# ----------------------------------------------------------------
# Builder user
# ----------------------------------------------------------------
id builder >/dev/null 2>&1 || useradd -m builder

rm -rf "$WORK"
mkdir -p "$WORK/payload"

P="$WORK/payload"

# ----------------------------------------------------------------
# Package contents
# ----------------------------------------------------------------
put() {
    install -Dm"$1" "$2" "$P/$3"
}

for f in \
    neofetch \
    rustos-branding \
    rustos-first-login \
    rustos-update \
    rustos-autoupdate \
    rustos-bootloader-update
do
    put 755 "$OV/usr/local/bin/$f" "usr/local/bin/$f"
done

put 644 "$OV/etc/systemd/system/rustos-update.service" \
    etc/systemd/system/rustos-update.service

put 644 "$OV/etc/systemd/system/rustos-update.timer" \
    etc/systemd/system/rustos-update.timer

put 644 "$OV/etc/pacman.d/hooks/rustos-branding.hook" \
    etc/pacman.d/hooks/rustos-branding.hook

put 644 "$OV/etc/pacman.d/hooks/rustos-bootloader.hook" \
    etc/pacman.d/hooks/rustos-bootloader.hook

put 644 "$OV/etc/xdg/fastfetch/config.jsonc" \
    etc/xdg/fastfetch/config.jsonc

put 644 "$OV/etc/skel/.config/fastfetch/config.jsonc" \
    etc/skel/.config/fastfetch/config.jsonc

put 644 "$OV/etc/xdg/autostart/rustos-first-login.desktop" \
    etc/xdg/autostart/rustos-first-login.desktop

put 644 "$OV/usr/share/rustos/os-release" \
    usr/share/rustos/os-release

put 644 "$OV/usr/share/rustos/fastfetch-logo.txt" \
    usr/share/rustos/fastfetch-logo.txt

for f in branding/logo-*.png branding/wallpaper.png branding/logo.svg; do
    put 644 "$f" "usr/share/rustos/$(basename "$f")"
done

put 644 branding/logo-256.png \
    usr/share/pixmaps/rustos.png

put 644 branding/logo.svg \
    usr/share/icons/hicolor/scalable/apps/rustos.svg

# Remove Windows CRLF line endings.
find "$P" -type f \
    \( -path '*/usr/local/bin/*' \
    -o -name '*.hook' \
    -o -name '*.service' \
    -o -name '*.timer' \
    -o -name '*.desktop' \
    -o -name '*.jsonc' \
    -o -name 'os-release' \) \
    -exec sed -i 's/\r$//' {} +

# ----------------------------------------------------------------
# Generate PKGBUILD
# ----------------------------------------------------------------
BASEV="$(tr -d ' \r\n' < VERSION)"
PKGVER="${BASEV}.$(date -u +%Y%m%d%H%M)"

DEPENDS="$(
    grep -v '^[[:space:]]*#' packages-extra.txt |
    sed '/^[[:space:]]*$/d' |
    awk '{printf "\047%s\047 ", $1}'
)"

URL="${REPO_URL:-https://archlinux.org}"

cat > "$WORK/PKGBUILD" <<'EOF'
pkgname=rustos-base
pkgver=@PKGVER@
pkgrel=1
pkgdesc="RustOS branding, tools, auto-updater and desktop meta-package"
arch=('any')
url="@URL@"
license=('custom')

depends=(@DEPENDS@)

install=rustos-base.install

backup=(
    'etc/xdg/fastfetch/config.jsonc'
    'etc/skel/.config/fastfetch/config.jsonc'
)

package() {
    cp -a "$startdir/payload/." "$pkgdir/"
    chmod 755 "$pkgdir"/usr/local/bin/*
}
EOF

sed -i \
    "s|@PKGVER@|$PKGVER|; s|@URL@|$URL|; s|@DEPENDS@|$DEPENDS|" \
    "$WORK/PKGBUILD"

cat > "$WORK/rustos-base.install" <<'EOF'
post_install() {
    systemctl daemon-reload 2>/dev/null || true
    /usr/local/bin/rustos-branding || true
}

post_upgrade() {
    systemctl daemon-reload 2>/dev/null || true
    /usr/local/bin/rustos-branding || true
}
EOF

chown -R builder "$WORK"

echo "Package rustos-base $PKGVER staged in $WORK"

[ "$STAGE_ONLY" = 1 ] && exit 0

# ----------------------------------------------------------------
# Signing key
# ----------------------------------------------------------------
KEYSRC="/tmp/rustos-private.asc"

trap 'rm -f "$KEYSRC"' EXIT

if [ -n "${GPG_PRIVATE_KEY:-}" ]; then
    printf '%s\n' "$GPG_PRIVATE_KEY" > "$KEYSRC"
elif [ -f "$ROOT/.secrets/private.asc" ]; then
    cp "$ROOT/.secrets/private.asc" "$KEYSRC"
else
    echo "ERROR: no signing key."
    echo "Add GPG_PRIVATE_KEY to GitHub Actions secrets."
    exit 1
fi

chown builder "$KEYSRC"
chmod 600 "$KEYSRC"

as_builder() {
    su builder -s /bin/bash -c "$1"
}

echo "==> Importing signing key..."

as_builder "gpg --batch --import '$KEYSRC'"

FPR="$(
    as_builder 'gpg --list-secret-keys --with-colons' |
    awk -F: '/^fpr:/{print $10; exit}'
)"

if [ -z "$FPR" ]; then
    echo "ERROR: could not read the signing key."
    exit 1
fi

if [ -n "${REPO_FPR:-}" ] && [ "$REPO_FPR" != "$FPR" ]; then
    echo "ERROR: signing key mismatch."
    echo "Expected: $REPO_FPR"
    echo "Found:    $FPR"
    exit 1
fi

echo "Signing with key $FPR"

# ----------------------------------------------------------------
# Build package
# ----------------------------------------------------------------
echo "==> Building rustos-base..."

as_builder "
    cd '$WORK' &&
    makepkg -f --noconfirm --sign --key '$FPR'
"

# ----------------------------------------------------------------
# Create repository database
# ----------------------------------------------------------------
echo "==> Creating repository database..."

as_builder "
    cd '$WORK' &&
    repo-add --sign --key '$FPR' \
        rustos.db.tar.zst \
        rustos-base-*.pkg.tar.zst
"

# ----------------------------------------------------------------
# Publish repository
# ----------------------------------------------------------------
echo "==> Publishing repository..."

rm -rf "$OUT"
mkdir -p "$OUT/x86_64"

cp "$WORK"/rustos-base-*.pkg.tar.zst \
   "$WORK"/rustos-base-*.pkg.tar.zst.sig \
   "$OUT/x86_64/"

for n in db files; do
    cp -L "$WORK/rustos.$n.tar.zst" \
        "$OUT/x86_64/rustos.$n.tar.zst"

    cp -L "$WORK/rustos.$n.tar.zst.sig" \
        "$OUT/x86_64/rustos.$n.tar.zst.sig"

    cp -L "$WORK/rustos.$n.tar.zst" \
        "$OUT/x86_64/rustos.$n"

    cp -L "$WORK/rustos.$n.tar.zst.sig" \
        "$OUT/x86_64/rustos.$n.sig"
done

if [ -f repo/rustos-pub.gpg ]; then
    cp repo/rustos-pub.gpg "$OUT/rustos-pub.gpg"
fi

touch "$OUT/.nojekyll"

cat > "$OUT/index.html" <<EOF
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>RustOS package repository</title>
</head>
<body>
<h1>RustOS package repository</h1>
<p>Latest: <code>rustos-base $PKGVER</code></p>
<p>This is a pacman repository for RustOS.</p>
</body>
</html>
EOF

echo ""
echo "=============================================="
echo " DONE"
echo " RustOS repository: $OUT"
echo " Package: rustos-base $PKGVER"
echo "=============================================="
