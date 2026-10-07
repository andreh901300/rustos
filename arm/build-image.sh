#!/usr/bin/env bash
# Builds the RustOS ARM (aarch64) disk image for UTM on iPad (and Apple Silicon Macs, Raspberry-class ARM VMs).
# Runs on an ARM Linux machine as root: normally GitHub Actions ("Build RustOS ARM image"), runner ubuntu-24.04-arm.
# Result: out/arm/RustOS-arm64-<version>.qcow2  (UEFI disk image; first boot asks for a user name and password)
#
# It starts from the official Arch Linux ARM root filesystem, adds the RustOS package repository (aarch64 folder,
# built by repo/build-repo.sh) and installs rustos-base, which brings the whole RustOS desktop.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ "$(uname -m)" = aarch64 ] || { echo "ERROR: this must run on an ARM (aarch64) machine."; exit 1; }
[ "$(id -u)" = 0 ] || exec sudo -E bash "$0" "$@"

SIZE_GB="${IMG_SIZE_GB:-16}"
VER="$(tr -d ' \r\n' < VERSION)"
OUT="$ROOT/out/arm"
ALARM_URL="${ALARM_URL:-http://os.archlinuxarm.org/os/ArchLinuxARM-aarch64-latest.tar.gz}"

# ---- where the update repository is, and which key signs it
REPO_URL=""; REPO_FPR=""
[ -f rustos.conf ] && . ./rustos.conf
if [ -z "$REPO_URL" ] && [ -n "${GITHUB_REPOSITORY:-}" ]; then
  REPO_URL="https://${GITHUB_REPOSITORY%%/*}.github.io/${GITHUB_REPOSITORY##*/}"
  REPO_URL="$(printf '%s' "$REPO_URL" | tr 'A-Z' 'a-z')"
fi
[ -f repo/rustos-pub.gpg ] || { echo "ERROR: repo/rustos-pub.gpg is missing (run repo-setup first)."; exit 1; }
if [ -z "$REPO_FPR" ]; then
  REPO_FPR="$(gpg --show-keys --with-colons repo/rustos-pub.gpg | awk -F: '/^fpr:/{print $10; exit}')"
fi
[ -n "$REPO_URL" ] && [ -n "$REPO_FPR" ] || { echo "ERROR: could not work out the repository address or key."; exit 1; }
echo "RustOS repository: $REPO_URL (key $REPO_FPR)"
echo "Checking that the ARM repository is published..."
curl -fsSL --retry 3 -o /dev/null "$REPO_URL/aarch64/rustos.db" \
  || { echo "ERROR: $REPO_URL/aarch64/rustos.db not found. Run the normal publish first and wait for its green check."; exit 1; }

# ---- work in the folder with the most free space
free_gb() { df --output=avail -BG "$1" 2>/dev/null | tail -n 1 | tr -dc '0-9'; }
WORKD=/tmp/rustos-arm
if [ -d /mnt ] && [ -w /mnt ] && [ "$(free_gb /mnt || echo 0)" -gt "$(free_gb /tmp || echo 0)" ]; then WORKD=/mnt/rustos-arm; fi
rm -rf "$WORKD"; mkdir -p "$WORKD/mnt" "$WORKD/cache" "$OUT"
IMG="$WORKD/rustos-arm64.raw"
MNT="$WORKD/mnt"
LOOP=""
echo "Working in $WORKD ($(free_gb "$WORKD") GB free)"

cleanup() {
  set +e
  sync
  umount -R "$MNT" 2>/dev/null
  [ -n "$LOOP" ] && losetup -d "$LOOP" 2>/dev/null
}
trap cleanup EXIT

# ---- 1. the Arch Linux ARM root filesystem
TAR="$WORKD/alarm.tar.gz"
echo "== Downloading Arch Linux ARM"
curl -fL --retry 5 -o "$TAR" "$ALARM_URL"
if curl -fsSL --retry 3 -o "$WORKD/alarm.md5" "$ALARM_URL.md5"; then
  echo "$(awk '{print $1}' "$WORKD/alarm.md5")  $TAR" | md5sum -c - || { echo "ERROR: the download is damaged."; exit 1; }
else
  echo "(no checksum file found - continuing without the check)"
fi

# ---- 2. the empty disk: 1 GB boot partition (UEFI) + the rest for the system
echo "== Making the disk"
truncate -s "${SIZE_GB}G" "$IMG"
parted -s "$IMG" mklabel gpt mkpart ESP fat32 1MiB 1025MiB set 1 esp on mkpart root ext4 1025MiB 100%
LOOP="$(losetup -fP --show "$IMG")"
mkfs.vfat -F 32 -n RUSTOSESP "${LOOP}p1" >/dev/null
mkfs.ext4 -F -q -L rustos-root "${LOOP}p2"
mount "${LOOP}p2" "$MNT"
echo "== Unpacking Arch Linux ARM"
bsdtar -xpf "$TAR" -C "$MNT"
rm -f "$TAR"
mkdir -p "$MNT/boot"
mount "${LOOP}p1" "$MNT/boot"                      # the kernel lives on the boot partition

# ---- 3. get ready to work inside it
mount -t proc proc "$MNT/proc"
mount -t sysfs sys "$MNT/sys"
mount --rbind /dev "$MNT/dev"
mount --make-rslave "$MNT/dev"
mount -t tmpfs tmpfs "$MNT/run"
mkdir -p "$MNT/var/cache/pacman/hostcache"
mount --bind "$WORKD/cache" "$MNT/var/cache/pacman/hostcache"
rm -f "$MNT/etc/resolv.conf"
printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' > "$MNT/etc/resolv.conf"
install -Dm644 repo/rustos-pub.gpg "$MNT/usr/share/rustos/rustos-pub.gpg"
printf 'REPO_URL=%s\nREPO_FPR=%s\n' "$REPO_URL" "$REPO_FPR" > "$MNT/usr/share/rustos/repo.conf"
install -Dm755 arm/rustos-firstboot "$MNT/usr/local/bin/rustos-firstboot"
install -Dm644 arm/rustos-firstboot.service "$MNT/etc/systemd/system/rustos-firstboot.service"
# lighter desktop in an emulated machine: no window animations, no file indexer
install -Dm644 /dev/stdin "$MNT/etc/skel/.config/kdeglobals" <<'KDE'
[KDE]
AnimationDurationFactor=0
KDE

cat > "$MNT/root/setup.sh" <<'CHROOT'
#!/bin/bash
set -euo pipefail
export LANG=C
inst() { # install what exists, say what was skipped
  local ok=() p
  for p in "$@"; do
    if pacman -Si "$p" >/dev/null 2>&1; then ok+=("$p"); else echo "  (skipping $p - not in the ARM repositories)"; fi
  done
  if [ "${#ok[@]}" -gt 0 ]; then pacman -S --noconfirm --needed --cachedir /var/cache/pacman/hostcache "${ok[@]}"; fi
}

echo "== Package keys"
pacman-key --init
pacman-key --populate archlinuxarm
pacman-key --add /usr/share/rustos/rustos-pub.gpg
pacman-key --lsign-key "$REPO_FPR"
sed -i 's/^CheckSpace/#CheckSpace/' /etc/pacman.conf
grep -q '^\[rustos\]' /etc/pacman.conf || printf '\n[rustos]\nSigLevel = Required DatabaseRequired\nServer = %s/$arch\n' "$REPO_URL" >> /etc/pacman.conf

# the disk is not the machine that builds it: do not trim the initramfs to this builder's hardware
sed -i 's/ autodetect//' /etc/mkinitcpio.conf
sed -i 's/^MODULES=.*/MODULES=(virtio_pci virtio_blk virtio_scsi virtio_net virtio_gpu ext4 vfat nls_cp437 nls_iso8859_1)/' /etc/mkinitcpio.conf

echo "== Updating the base system"
pacman -Syu --noconfirm --cachedir /var/cache/pacman/hostcache
echo "== Kernel (reinstalled so it lands on the boot partition)"
pacman -S --noconfirm --cachedir /var/cache/pacman/hostcache linux-aarch64 mkinitcpio
echo "== Tools for a virtual machine"
inst sudo networkmanager qemu-guest-agent spice-vdagent cloud-guest-utils parted e2fsprogs dosfstools
echo "== The RustOS desktop (rustos-base)"
pacman -S --noconfirm --needed --cachedir /var/cache/pacman/hostcache rustos-base

echo "== Settings"
echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen
locale-gen
echo 'LANG=en_US.UTF-8' > /etc/locale.conf
echo rustos > /etc/hostname
ln -sf /usr/share/zoneinfo/UTC /etc/localtime
echo '%wheel ALL=(ALL:ALL) ALL' > /etc/sudoers.d/10-wheel
chmod 440 /etc/sudoers.d/10-wheel
# Arch Linux ARM ships a default user ("alarm") and a known root password: remove both
userdel -r alarm 2>/dev/null || true
passwd -l root
systemctl disable sshd 2>/dev/null || true
for u in NetworkManager sddm systemd-timesyncd qemu-guest-agent spice-vdagentd \
         rustos-update.timer paccache.timer rustos-firstboot.service; do
  systemctl enable "$u" 2>/dev/null || echo "  (could not enable $u)"
done
systemctl disable reflector.timer 2>/dev/null || true        # reflector picks Arch mirrors: wrong for ARM
systemctl set-default graphical.target
sed -i 's/^#CheckSpace/CheckSpace/' /etc/pacman.conf

echo "== Same settings as the PC edition"
# (the journal, sysctl and scheduler settings come from the rustos-base package, exactly like on a PC)
printf '[zram0]\nzram-size = min(ram / 2, 8192)\ncompression-algorithm = zstd\n' > /etc/systemd/zram-generator.conf
for u in bluetooth.service power-profiles-daemon.service fstrim.timer; do
  systemctl enable "$u" 2>/dev/null || echo "  (could not enable $u)"
done

echo "== Cleaning up"
gpgconf --homedir /etc/pacman.d/gnupg --kill all 2>/dev/null || true
pkill gpg-agent 2>/dev/null || true
pkill dirmngr 2>/dev/null || true
rm -rf /etc/pacman.d/gnupg                                     # made again on the first boot
rm -rf /var/cache/pacman/pkg/* /var/lib/pacman/sync/*.db.sig
rm -f /root/setup.sh
CHROOT

echo "== Installing inside the image (this is the long part)"
chroot "$MNT" env REPO_URL="$REPO_URL" REPO_FPR="$REPO_FPR" /bin/bash /root/setup.sh

# ---- 4. boot loader (systemd-boot, UEFI, started from the removable-media path)
echo "== Boot loader"
BOOTEFI="$MNT/usr/lib/systemd/boot/efi/systemd-bootaa64.efi"
[ -f "$BOOTEFI" ] || { echo "ERROR: systemd-boot for ARM was not found in the image."; exit 1; }
install -Dm644 "$BOOTEFI" "$MNT/boot/EFI/BOOT/BOOTAA64.EFI"
bootfile() { find "$MNT/boot" -maxdepth 1 -type f "$@" -printf '%f\n' | sort | head -n 1; }
KERN="$(bootfile \( -name Image -o -name 'vmlinuz*' \))"
INITRD="$(bootfile -name 'initramfs-*.img' ! -name '*fallback*')"
FALLBACK="$(bootfile -name 'initramfs-*fallback.img')"
[ -n "$KERN" ] && [ -n "$INITRD" ] || { echo "ERROR: no kernel or initramfs on the boot partition:"; ls -la "$MNT/boot"; exit 1; }
echo "Kernel: $KERN   initramfs: $INITRD   fallback: ${FALLBACK:-none}"
mkdir -p "$MNT/boot/loader/entries"
printf 'timeout 2\ndefault rustos.conf\nconsole-mode keep\n' > "$MNT/boot/loader/loader.conf"
printf 'title   RustOS\nlinux   /%s\ninitrd  /%s\noptions root=LABEL=rustos-root rw console=tty0 quiet loglevel=3\n' \
  "$KERN" "$INITRD" > "$MNT/boot/loader/entries/rustos.conf"
if [ -n "$FALLBACK" ]; then
  printf 'title   RustOS (fallback)\nlinux   /%s\ninitrd  /%s\noptions root=LABEL=rustos-root rw console=tty0\n' \
    "$KERN" "$FALLBACK" > "$MNT/boot/loader/entries/rustos-fallback.conf"
fi
printf 'LABEL=rustos-root  /      ext4  rw,noatime  0 1\nLABEL=RUSTOSESP    /boot  vfat  rw,umask=0077  0 2\n' > "$MNT/etc/fstab"

# ---- 5. tidy up and shrink
echo "== Tidying"
rm -f "$MNT/etc/resolv.conf"
: > "$MNT/etc/machine-id"
rm -rf "$MNT/var/log/journal"/* "$MNT/root/.bash_history"
fuser -km "$MNT" >/dev/null 2>&1 || true
umount "$MNT/var/cache/pacman/hostcache"
rm -rf "$WORKD/cache"
fstrim -v "$MNT" || true
fstrim -v "$MNT/boot" || true
umount -R "$MNT"
losetup -d "$LOOP"; LOOP=""

echo "== Making the final disk file (compressed)"
QCOW="$OUT/RustOS-arm64-$VER.qcow2"
qemu-img convert -p -f raw -O qcow2 -c "$IMG" "$QCOW"
rm -f "$IMG"
( cd "$OUT" && sha256sum "$(basename "$QCOW")" > "$(basename "$QCOW").sha256" )
ls -lh "$OUT"
echo "DONE: $QCOW"
