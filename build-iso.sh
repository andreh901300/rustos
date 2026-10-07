#!/usr/bin/env bash
# Builds the RustOS ISO. Must run as root on Arch Linux with the "archiso" package installed.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Run as root."; exit 1; }
[ -d /usr/share/archiso/configs/releng ] || { echo "Install archiso: pacman -S archiso"; exit 1; }

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK=/var/tmp/rustos-build
PROFILE="$WORK/profile"
AIR="$PROFILE/airootfs"
strip_list() { grep -v '^\s*#' "$1" | sed '/^\s*$/d'; }

rm -rf "$PROFILE" "$WORK/work"
mkdir -p "$WORK"
cp -r /usr/share/archiso/configs/releng "$PROFILE"

# --- ISO branding ---
sed -i \
  -e 's|^iso_name=.*|iso_name="rustos"|' \
  -e 's|^iso_label=.*|iso_label="RUSTOS_$(date +%Y%m)"|' \
  -e 's|^iso_publisher=.*|iso_publisher="RustOS"|' \
  -e 's|^iso_application=.*|iso_application="RustOS Live/Install ISO"|' \
  "$PROFILE/profiledef.sh"
grep -rIl "Arch Linux" "$PROFILE/syslinux" "$PROFILE/efiboot" "$PROFILE/grub" 2>/dev/null \
  | xargs -r sed -i 's/Arch Linux/RustOS/g' || true

# --- packages: remove bloat, add ours ---
strip_list "$HERE/packages-remove.txt" > "$WORK/remove.txt"
grep -vxFf "$WORK/remove.txt" "$PROFILE/packages.x86_64" > "$WORK/pk.txt" || true
strip_list "$HERE/packages-extra.txt" >> "$WORK/pk.txt"
# things the installer needs - make sure they are there whatever the upstream profile does
for p in base linux linux-firmware mkinitcpio-archiso arch-install-scripts gptfdisk dosfstools e2fsprogs \
         grub efibootmgr os-prober openssl parted; do
  grep -qx "$p" "$WORK/pk.txt" || echo "$p" >> "$WORK/pk.txt"
done
awk '!seen[$0]++' "$WORK/pk.txt" > "$PROFILE/packages.x86_64"
echo "ISO will contain $(wc -l < "$PROFILE/packages.x86_64") packages."

# --- pacman.conf ---
sed -i -e 's/^#Color/Color/' -e 's/^#ParallelDownloads.*/ParallelDownloads = 5/' "$PROFILE/pacman.conf"
if grep -qi microsoft /proc/version; then   # WSL kernels lack landlock
  grep -q '^DisableSandbox' "$PROFILE/pacman.conf" || sed -i '/^\[options\]/a DisableSandbox' "$PROFILE/pacman.conf"
fi

# --- networking: NetworkManager instead of systemd-networkd; no sshd/cloud-init on a desktop ---
find "$AIR/etc/systemd" \( -name 'systemd-networkd*' -o -name 'systemd-resolved*' \) -delete 2>/dev/null || true
rm -rf "$AIR/etc/systemd/network" "$AIR/etc/systemd/resolved.conf.d" "$AIR/etc/resolv.conf"
find "$AIR/etc/systemd/system" \( -name 'sshd*' -o -name 'cloud-*' -o -name 'iwd*' -o -name 'ModemManager*' \) -delete 2>/dev/null || true

# --- our files ---
# NOTE: archiso copies the overlay BEFORE pacman installs packages, so the overlay must not contain
# files owned by a package (e.g. /usr/lib/os-release). Those are applied by the rustos-branding pacman hook.
cp -a "$HERE/overlay/airootfs/." "$AIR/"
mkdir -p "$AIR/usr/share/rustos" "$AIR/usr/share/pixmaps" "$AIR/usr/share/icons/hicolor/scalable/apps"
cp "$HERE"/branding/*.png "$HERE"/branding/logo.svg "$AIR/usr/share/rustos/"
cp "$HERE/packages-extra.txt" "$AIR/usr/share/rustos/packages-installed.txt"
cp "$HERE/CHANGELOG.txt" "$AIR/usr/share/rustos/CHANGELOG.txt"
# RustOS update channel (optional): written by repo-setup.bat into rustos.conf
if [ -f "$HERE/rustos.conf" ] && [ -f "$HERE/repo/rustos-pub.gpg" ]; then
  grep -E '^(REPO_URL|REPO_FPR)=' "$HERE/rustos.conf" > "$AIR/usr/share/rustos/repo.conf"
  cp "$HERE/repo/rustos-pub.gpg" "$AIR/usr/share/rustos/rustos-pub.gpg"
  echo "Update channel: $(grep ^REPO_URL= "$HERE/rustos.conf")"
else
  echo "No update channel configured (run repo-setup.bat to enable RustOS updates)."
fi
cp "$HERE/branding/logo-256.png" "$AIR/usr/share/pixmaps/rustos.png"
cp "$HERE/branding/logo.svg" "$AIR/usr/share/icons/hicolor/scalable/apps/rustos.svg"

# --- enable services ---
S="$AIR/etc/systemd/system"
mkdir -p "$S/multi-user.target.wants" "$S/network-online.target.wants" "$S/bluetooth.target.wants"
ln -sf /usr/lib/systemd/system/sddm.service            "$S/display-manager.service"
ln -sf /usr/lib/systemd/system/NetworkManager.service  "$S/multi-user.target.wants/NetworkManager.service"
ln -sf /usr/lib/systemd/system/NetworkManager-wait-online.service "$S/network-online.target.wants/NetworkManager-wait-online.service"
ln -sf /usr/lib/systemd/system/bluetooth.service       "$S/bluetooth.target.wants/bluetooth.service"
ln -sf /etc/systemd/system/rustos-live-user.service    "$S/multi-user.target.wants/rustos-live-user.service"

# --- file permissions (mkarchiso does not keep modes from the overlay) ---
cat >> "$PROFILE/profiledef.sh" <<'EOF'

file_permissions+=(
  ["/usr/local/bin/rustos-install"]="0:0:755"
  ["/usr/local/bin/rustos-install-run"]="0:0:755"
  ["/usr/local/bin/rustos-welcome"]="0:0:755"
  ["/usr/local/bin/rustos-live-setup"]="0:0:755"
  ["/usr/local/bin/rustos-first-login"]="0:0:755"
  ["/usr/local/bin/rustos-branding"]="0:0:755"
  ["/usr/local/bin/neofetch"]="0:0:755"
  ["/usr/local/bin/rustos-update"]="0:0:755"
  ["/usr/local/bin/rustos-autoupdate"]="0:0:755"
  ["/usr/local/bin/rustos-bootloader-update"]="0:0:755"
  ["/usr/local/bin/rustos-update-event"]="0:0:755"
  ["/usr/local/bin/rustos-update-notify"]="0:0:755"
  ["/usr/local/bin/rustos-update-center"]="0:0:755"
  ["/usr/local/bin/rustos-gaming"]="0:0:755"
  ["/usr/local/bin/rustos-restorepoint"]="0:0:755"
  ["/usr/local/bin/rustos-rollback"]="0:0:755"
  ["/usr/local/bin/rustos-run-exe"]="0:0:755"
  ["/usr/local/bin/rustos-apps"]="0:0:755"
  ["/usr/local/bin/rustos-switch"]="0:0:755"
  ["/usr/local/bin/rustos-education"]="0:0:755"
  ["/usr/share/kio/servicemenus/rustos-run-game.desktop"]="0:0:755"
  ["/etc/sudoers.d/10-wheel"]="0:0:440"
  ["/etc/skel/Desktop/install-rustos.desktop"]="0:0:755"
)
EOF

# --- build ---
mkdir -p "$HERE/out"
mkarchiso -v -w "$WORK/work" -o "$HERE/out" "$PROFILE"
echo
echo "DONE: $(ls "$HERE"/out/*.iso)"
