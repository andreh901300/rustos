#!/usr/bin/env bash
# Builds the signed RustOS package repository into out/site/ .
# Runs on Arch Linux: automatically in GitHub Actions, or by hand in your WSL Arch for a test.
#   --stage-only   only prepare the package sources (no signing/building), for debugging
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OV=overlay/airootfs
OUT="$ROOT/out/site"
WORK=/tmp/rustos-pkg
STAGE_ONLY=0; [ "${1:-}" = "--stage-only" ] && STAGE_ONLY=1

[ -f rustos.conf ] && . ./rustos.conf
id builder >/dev/null 2>&1 || useradd -m builder

rm -rf "$WORK" && mkdir -p "$WORK/payload"
P="$WORK/payload"

# ---------------------------------------------------------------- what goes into the package
put() { # put <mode> <source> <destination-in-package>
  install -Dm"$1" "$2" "$P/$3"
}
for f in neofetch rustos-branding rustos-first-login rustos-update rustos-autoupdate rustos-bootloader-update \
         rustos-update-event rustos-update-notify rustos-update-center rustos-gaming \
         rustos-restorepoint rustos-rollback rustos-run-exe rustos-apps rustos-switch rustos-education rustos-antivirus rustos-exe-center rustos-ipad-mode; do
  put 755 "$OV/usr/local/bin/$f" "usr/local/bin/$f"
done
put 644 "$OV/etc/systemd/system/rustos-update.service" etc/systemd/system/rustos-update.service
put 644 "$OV/etc/systemd/system/rustos-update.timer"   etc/systemd/system/rustos-update.timer
put 644 "$OV/etc/pacman.d/hooks/rustos-branding.hook"   etc/pacman.d/hooks/rustos-branding.hook
put 644 "$OV/etc/pacman.d/hooks/rustos-bootloader.hook" etc/pacman.d/hooks/rustos-bootloader.hook
put 644 "$OV/etc/pacman.d/hooks/rustos-update-event.hook" etc/pacman.d/hooks/rustos-update-event.hook
put 644 "$OV/etc/systemd/user/rustos-update-notify.path"    etc/systemd/user/rustos-update-notify.path
put 644 "$OV/etc/systemd/user/rustos-update-notify.service" etc/systemd/user/rustos-update-notify.service
put 644 "$OV/usr/share/applications/rustos-update-center.desktop" usr/share/applications/rustos-update-center.desktop
put 644 "$OV/usr/share/applications/rustos-gaming.desktop"        usr/share/applications/rustos-gaming.desktop
put 644 "$OV/etc/sysctl.d/99-rustos.conf"                         etc/sysctl.d/99-rustos.conf
put 644 "$OV/etc/udev/rules.d/60-rustos-ioschedulers.rules"       etc/udev/rules.d/60-rustos-ioschedulers.rules
put 644 "$OV/etc/systemd/journald.conf.d/rustos.conf"             etc/systemd/journald.conf.d/rustos.conf
put 644 "$OV/etc/systemd/system.conf.d/rustos.conf"               etc/systemd/system.conf.d/rustos.conf
put 644 "$OV/etc/skel/.config/baloofilerc"                        etc/skel/.config/baloofilerc
put 644 CHANGELOG.txt                                             usr/share/rustos/CHANGELOG.txt
put 644 "$OV/etc/pacman.d/hooks/rustos-restorepoint.hook"         etc/pacman.d/hooks/rustos-restorepoint.hook
put 644 "$OV/usr/share/applications/rustos-exe.desktop"           usr/share/applications/rustos-exe.desktop
put 644 "$OV/usr/share/applications/rustos-apps.desktop"          usr/share/applications/rustos-apps.desktop
put 644 "$OV/usr/share/applications/rustos-switch.desktop"        usr/share/applications/rustos-switch.desktop
put 644 "$OV/usr/share/applications/rustos-education.desktop"     usr/share/applications/rustos-education.desktop
put 644 "$OV/usr/share/applications/rustos-antivirus.desktop"     usr/share/applications/rustos-antivirus.desktop
put 644 "$OV/usr/share/applications/rustos-exe-center.desktop"       usr/share/applications/rustos-exe-center.desktop
put 644 "$OV/usr/share/applications/rustos-ipad-mode.desktop"       usr/share/applications/rustos-ipad-mode.desktop
put 644 "$OV/usr/share/applications/rustos-ipad-keyboard.desktop"   usr/share/applications/rustos-ipad-keyboard.desktop
put 644 "$OV/etc/sddm.conf.d/rustos-touch.conf"                   etc/sddm.conf.d/rustos-touch.conf
put 644 "$OV/usr/share/rustos/apps.catalog"                         usr/share/rustos/apps.catalog
put 644 "$OV/usr/share/rustos/wallpapers/ipad.svg"                  usr/share/rustos/wallpapers/ipad.svg
put 755 "$OV/usr/share/kio/servicemenus/rustos-scan-virus.desktop" usr/share/kio/servicemenus/rustos-scan-virus.desktop
put 755 "$OV/usr/share/kio/servicemenus/rustos-run-game.desktop"  usr/share/kio/servicemenus/rustos-run-game.desktop
put 644 "$OV/etc/xdg/mimeapps.list"                               etc/xdg/mimeapps.list
put 644 "$OV/usr/share/rustos/windows-equivalents.txt"            usr/share/rustos/windows-equivalents.txt
# start the update popup helper in every user session (same as "systemctl --global enable")
mkdir -p "$P/etc/systemd/user/default.target.wants"
ln -s ../rustos-update-notify.path    "$P/etc/systemd/user/default.target.wants/rustos-update-notify.path"
ln -s ../rustos-update-notify.service "$P/etc/systemd/user/default.target.wants/rustos-update-notify.service"
install -dm755 "$P/var/lib/rustos"
put 644 "$OV/etc/xdg/fastfetch/config.jsonc"            etc/xdg/fastfetch/config.jsonc
put 644 "$OV/etc/skel/.config/fastfetch/config.jsonc"   etc/skel/.config/fastfetch/config.jsonc
put 644 "$OV/etc/xdg/autostart/rustos-first-login.desktop" etc/xdg/autostart/rustos-first-login.desktop
put 644 "$OV/usr/share/rustos/os-release"               usr/share/rustos/os-release
put 644 "$OV/usr/share/rustos/fastfetch-logo.txt"       usr/share/rustos/fastfetch-logo.txt
for f in branding/logo-*.png branding/wallpaper.png branding/logo.svg; do
  put 644 "$f" "usr/share/rustos/$(basename "$f")"
done
put 644 branding/logo-256.png usr/share/pixmaps/rustos.png
put 644 branding/logo.svg     usr/share/icons/hicolor/scalable/apps/rustos.svg
# Windows line endings would break the scripts
find "$P" -type f \( -path '*/usr/local/bin/*' -o -name '*.hook' -o -name '*.service' -o -name '*.timer' \
  -o -name '*.desktop' -o -name '*.jsonc' -o -name 'os-release' -o -name '*.path' -o -name '*.rules' \
  -o -name '*.conf' -o -name 'baloofilerc' -o -name 'CHANGELOG.txt' -o -name 'mimeapps.list' -o -name 'windows-equivalents.txt' -o -name 'apps.catalog' \) -exec sed -i 's/\r$//' {} +

# ---------------------------------------------------------------- PKGBUILD
BASEV="$(tr -d ' \r\n' < VERSION)"
case "$BASEV" in
  ''|*[!0-9.]*) echo "WARNING: VERSION must look like 1.2 (numbers and dots) - using 1.0 for now."; BASEV=1.0 ;;
esac
PKGVER="${BASEV}.$(date -u +%Y%m%d%H%M)"          # the timestamp always increases, but the version number must never go DOWN (publish.sh checks that)
# Safety net: a package name that does not exist (typo, renamed, removed from Arch) must NEVER end up in the
# dependency list, or "pacman -Syu" would fail on everyone's PC. On Arch we check every name; missing ones are left out.
x86_depends() {
  local name out="" dropped="" check=0
  if command -v pacman >/dev/null 2>&1 && pacman -Sp base >/dev/null 2>&1; then check=1; fi
  while read -r name; do
    if [ "$check" = 1 ] && ! pacman -Sp "$name" >/dev/null 2>&1; then dropped="$dropped $name"; continue; fi
    out="$out '$name'"
  done < <(grep -v '^\s*#' packages-extra.txt | sed '/^\s*$/d' | awk '{print $1}')
  if [ "$check" = 1 ]; then echo "x86: left out (not in the Arch repositories):${dropped:- nothing}" >&2
  else echo "x86: package names were not checked (not running on Arch)" >&2; fi
  printf '%s' "$out"
}
DEPENDS="$(x86_depends)"
URL="${REPO_URL:-https://archlinux.org}"

# ---- ARM (aarch64): the same package, but its dependency list only has what Arch Linux ARM actually provides
ARM_MIRROR="${ARM_MIRROR:-http://mirror.archlinuxarm.org/aarch64}"
arm_available() { # prints every package name in the Arch Linux ARM repositories (empty if they cannot be reached)
  local r
  for r in core extra alarm aur; do
    curl -fsSL --retry 3 --max-time 120 "$ARM_MIRROR/$r/$r.db" 2>/dev/null | tar -tz 2>/dev/null \
      | grep '/$' | sed -E 's/-[^-]+-[^-]+\/$//' || true
  done
}
arm_depends() {
  local avail=/tmp/arm-available.txt name out="" dropped=""
  arm_available | sort -u > "$avail"
  # always left out on ARM (a virtual machine has no Bluetooth, battery or disks to partition)
  grep -v '^\s*#' packages-arm-remove.txt | sed '/^\s*$/d' | awk '{print $1}' > /tmp/arm-remove.txt
  if [ -s "$avail" ]; then
    echo "ARM: checked $(wc -l < "$avail") packages from Arch Linux ARM" >&2
  else
    echo "ARM: could not read the Arch Linux ARM package lists - only packages-arm-remove.txt is used" >&2
  fi
  while read -r name; do
    grep -qxF "$name" /tmp/arm-remove.txt && { dropped="$dropped $name"; continue; }
    if [ -s "$avail" ]; then grep -qxF "$name" "$avail" || { dropped="$dropped $name"; continue; }; fi
    out="$out '$name'"
  done < <(grep -v '^\s*#' packages-extra.txt | sed '/^\s*$/d' | awk '{print $1}')
  echo "ARM: left out (not available for ARM):${dropped:- nothing}" >&2
  printf '%s' "$out"
}

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
backup=('etc/xdg/fastfetch/config.jsonc' 'etc/skel/.config/fastfetch/config.jsonc')

package() {
  cp -a "$startdir/payload/." "$pkgdir/"
  chmod 755 "$pkgdir"/usr/local/bin/*
}
EOF
sed -i "s|@PKGVER@|$PKGVER|; s|@URL@|$URL|; s|@DEPENDS@|$DEPENDS|" "$WORK/PKGBUILD"

cat > "$WORK/rustos-base.install" <<'EOF'
post_install() {
  systemctl daemon-reload 2>/dev/null || true
  systemctl enable power-profiles-daemon.service 2>/dev/null || true
  /usr/local/bin/rustos-branding || true
}
post_upgrade() {
  systemctl daemon-reload 2>/dev/null || true
  systemctl enable power-profiles-daemon.service 2>/dev/null || true
  /usr/local/bin/rustos-branding || true
}
EOF
chown -R builder "$WORK"
echo "Package rustos-base $PKGVER staged in $WORK"
if [ "$STAGE_ONLY" = 1 ]; then arm_depends >/dev/null; exit 0; fi

# ---------------------------------------------------------------- signing key
KEYSRC=/tmp/rustos-private.asc
trap 'rm -f "$KEYSRC"' EXIT
if [ -n "${GPG_PRIVATE_KEY:-}" ]; then
  printf '%s\n' "$GPG_PRIVATE_KEY" > "$KEYSRC"
elif [ -f "$ROOT/.secrets/private.asc" ]; then
  cp "$ROOT/.secrets/private.asc" "$KEYSRC"
else
  echo "ERROR: no signing key. In GitHub add the secret GPG_PRIVATE_KEY (see GITHUB-SETUP.md)."; exit 1
fi
chown builder "$KEYSRC"; chmod 600 "$KEYSRC"
as_builder() { su builder -s /bin/bash -c "$1"; }
as_builder "gpg --batch --import $KEYSRC"
FPR="$(as_builder 'gpg --list-secret-keys --with-colons' | awk -F: '/^fpr:/{print $10; exit}')"
[ -n "$FPR" ] || { echo "ERROR: could not read the signing key."; exit 1; }
if [ -n "${REPO_FPR:-}" ] && [ "$REPO_FPR" != "$FPR" ]; then
  echo "ERROR: the signing key ($FPR) is not the one the ISO trusts ($REPO_FPR from rustos.conf)."; exit 1
fi
echo "Signing with key $FPR"

# ---------------------------------------------------------------- build + repo database
# --nodeps on purpose: rustos-base is a meta-package; its dependencies get installed on the user's PC, not here.
as_builder "cd $WORK && makepkg -f --nodeps --noconfirm --sign --key $FPR"
as_builder "cd $WORK && repo-add --sign --key $FPR rustos.db.tar.zst rustos-base-*.pkg.tar.zst"

rm -rf "$OUT" && mkdir -p "$OUT/x86_64"
cp "$WORK"/rustos-base-*.pkg.tar.zst "$WORK"/rustos-base-*.pkg.tar.zst.sig "$OUT/x86_64/"
for n in db files; do
  cp -L "$WORK/rustos.$n.tar.zst"     "$OUT/x86_64/rustos.$n.tar.zst"
  cp -L "$WORK/rustos.$n.tar.zst.sig" "$OUT/x86_64/rustos.$n.tar.zst.sig"
  cp -L "$WORK/rustos.$n.tar.zst"     "$OUT/x86_64/rustos.$n"        # pacman asks for "rustos.db"
  cp -L "$WORK/rustos.$n.tar.zst.sig" "$OUT/x86_64/rustos.$n.sig"
done

# ---------------------------------------------------------------- ARM repository (same package, ARM dependency list)
echo "== Building the ARM (aarch64) repository"
ARMW=/tmp/rustos-pkg-arm
rm -rf "$ARMW" && cp -a "$WORK" "$ARMW"
rm -f "$ARMW"/rustos-base-*.pkg.tar.zst* "$ARMW"/rustos.db* "$ARMW"/rustos.files*
ARMDEPS="$(arm_depends)"
sed -i "s|^depends=.*|depends=(${ARMDEPS} )|" "$ARMW/PKGBUILD"
chown -R builder "$ARMW"
as_builder "cd $ARMW && makepkg -f --nodeps --noconfirm --sign --key $FPR"
as_builder "cd $ARMW && repo-add --sign --key $FPR rustos.db.tar.zst rustos-base-*.pkg.tar.zst"
mkdir -p "$OUT/aarch64"
cp "$ARMW"/rustos-base-*.pkg.tar.zst "$ARMW"/rustos-base-*.pkg.tar.zst.sig "$OUT/aarch64/"
for n in db files; do
  cp -L "$ARMW/rustos.$n.tar.zst"     "$OUT/aarch64/rustos.$n.tar.zst"
  cp -L "$ARMW/rustos.$n.tar.zst.sig" "$OUT/aarch64/rustos.$n.tar.zst.sig"
  cp -L "$ARMW/rustos.$n.tar.zst"     "$OUT/aarch64/rustos.$n"
  cp -L "$ARMW/rustos.$n.tar.zst.sig" "$OUT/aarch64/rustos.$n.sig"
done

[ -f repo/rustos-pub.gpg ] && cp repo/rustos-pub.gpg "$OUT/rustos-pub.gpg"
touch "$OUT/.nojekyll"
cat > "$OUT/index.html" <<EOF
<!doctype html><meta charset=utf-8><title>RustOS package repository</title>
<h1>RustOS package repository</h1><p>Latest: <code>rustos-base $PKGVER</code></p>
<p>This is a pacman repository for RustOS. It is used automatically by installed systems.</p>
EOF
echo "DONE: repository for rustos-base $PKGVER is in $OUT"
