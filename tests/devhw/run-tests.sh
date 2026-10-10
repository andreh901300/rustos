#!/usr/bin/env bash
# Tests for rustos-devhw. No hardware needed: every test builds a fake /sys, /proc, /usr/lib/modules and /etc
# and puts small stand-ins for lspci, modprobe, dkms, systemctl... first in PATH.
#   bash tests/devhw/run-tests.sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
TOOL=${TOOL:-$HERE/../../overlay/airootfs/usr/local/bin/rustos-devhw}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
PASS=0; FAIL=0; CUR=""
K=7.2.9-arch1-1

ok()   { PASS=$((PASS + 1)); }
bad()  { FAIL=$((FAIL + 1)); echo "  FAIL [$CUR] $*"; }
has()  { grep -qF -- "$2" <<<"$1" && ok || bad "expected: $2"; }
hasnt(){ grep -qF -- "$2" <<<"$1" && bad "did not expect: $2" || ok; }
eq()   { [ "$1" = "$2" ] && ok || bad "expected '$2', got '$1'"; }

# ---------------------------------------------------------------- the fake system
newroot() {   # newroot NAME  -> sets R, S (shims), LOG
  CUR=$1
  R=$TMP/$1; S=$TMP/$1.bin; LOG=$TMP/$1.log
  mkdir -p "$R"/{proc,etc/rustos,etc/default,dev,boot/loader/entries} "$R/sys/bus/pci/devices" "$R/sys/bus/pci/drivers" \
           "$R/sys/devices/pci0000:00" "$R/sys/kernel/iommu_groups" "$R/sys/class/iommu" "$R/sys/class/block" \
           "$R/sys/bus/usb/devices" "$R/sys/module" "$R/usr/lib/modules/$K/build" "$S"
  : > "$LOG"; : > "$R/sys/bus/pci/drivers_probe"
  echo "BOOT_IMAGE=/boot/vmlinuz-linux root=UUID=1234 rw quiet" > "$R/proc/cmdline"
  printf 'processor\t: 0\nvendor_id\t: GenuineIntel\n' > "$R/proc/cpuinfo"
  printf 'MemTotal:       16384000 kB\n' > "$R/proc/meminfo"
  : > "$R/proc/mounts"; printf 'Filename Type Size Used Priority\n' > "$R/proc/swaps"
  echo linux > "$R/usr/lib/modules/$K/pkgbase"
  printf 'kernel/drivers/vfio/vfio.ko.zst:\nkernel/drivers/vfio/pci/vfio-pci.ko.zst: kernel/drivers/vfio/vfio.ko.zst\nkernel/drivers/vfio/vfio_iommu_type1.ko.zst:\nkernel/drivers/usb/serial/ftdi_sio.ko.zst:\n' \
    > "$R/usr/lib/modules/$K/modules.dep"
  : > "$R/usr/lib/modules/$K/modules.builtin"
  kconfig 'CONFIG_IOMMU_SUPPORT=y' 'CONFIG_INTEL_IOMMU=y' '# CONFIG_INTEL_IOMMU_DEFAULT_ON is not set' 'CONFIG_AMD_IOMMU=y' \
          'CONFIG_VFIO=m' 'CONFIG_VFIO_PCI=m' 'CONFIG_VFIO_NOIOMMU=y' 'CONFIG_STRICT_DEVMEM=y' 'CONFIG_IO_STRICT_DEVMEM=y' \
          'CONFIG_USB_SERIAL_FTDI_SIO=m' 'CONFIG_USB_ACM=m' 'CONFIG_XILINX_XDMA=m' '# CONFIG_MODULE_SIG_FORCE is not set'
  : > "$TMP/$1.lspci"
  mkdir -p "$R/sys/module/vfio/parameters"; echo N > "$R/sys/module/vfio/parameters/enable_unsafe_noiommu_mode"
  # stand-ins
  printf '#!/bin/sh\ncat "%s"\n' "$TMP/$1.lspci" > "$S/lspci"
  for c in modprobe systemctl usermod groupadd gpasswd udevadm systemd-sysusers grub-mkconfig; do
    printf '#!/bin/sh\necho "%s $*" >> "%s"\n' "$c" "$LOG" > "$S/$c"
  done
  printf '#!/bin/sh\necho none\n' > "$S/systemd-detect-virt"
  printf '#!/bin/sh\ncase "$*" in "group uucp") echo "uucp:x:987:"; exit 0 ;; esac\nexit 2\n' > "$S/getent"
  chmod +x "$S"/*
}
kconfig() { printf '%s\n' "$@" | gzip > "$R/proc/config.gz"; }
iommu_on() { mkdir -p "$R/sys/class/iommu/dmar0"; }
# pcidev SLOT CLASS VENDOR DEVICE DRIVER GROUP [boot_vga]
pcidev() {
  local s=$1 d="$R/sys/devices/pci0000:00/$1"
  mkdir -p "$d"
  echo "0x$2" > "$d/class"; echo "0x$3" > "$d/vendor"; echo "0x$4" > "$d/device"; : > "$d/driver_override"
  [ -n "${7:-}" ] && echo "$7" > "$d/boot_vga"
  ln -sfn "../../../devices/pci0000:00/$s" "$R/sys/bus/pci/devices/$s"
  if [ -n "$5" ]; then mkdir -p "$R/sys/bus/pci/drivers/$5"; : > "$R/sys/bus/pci/drivers/$5/unbind"; ln -sfn "../../../bus/pci/drivers/$5" "$d/driver"; fi
  if [ -n "$6" ]; then
    mkdir -p "$R/sys/kernel/iommu_groups/$6/devices"; echo DMA-FQ > "$R/sys/kernel/iommu_groups/$6/type"
    ln -sfn "../../../kernel/iommu_groups/$6" "$d/iommu_group"
    ln -sfn "../../../../devices/pci0000:00/$s" "$R/sys/kernel/iommu_groups/$6/devices/$s"
  fi
}
lspci_add() { printf '%s\n' "$@" >> "$TMP/$CUR.lspci"; }
run() { PATH="$S:$PATH" NO_COLOR=1 RUSTOS_DEVHW_ROOT="$R" RUSTOS_DEVHW_KREL="${KREL_OVERRIDE:-$K}" RUSTOS_DEVHW_ARCH=x86_64 \
        RUSTOS_DEVHW_LSPCI="${LSPCI_OVERRIDE:-lspci}" bash "$TOOL" "$@" 2>&1; }

# a typical FPGA card: Xilinx 10ee:7024, no driver, alone in IOMMU group 14
fpga_card() {
  pcidev 0000:03:00.0 058000 10ee 7024 "" 14
  lspci_add '0000:03:00.0 Memory controller [0580]: Xilinx Corporation Device [10ee:7024]'
}

echo "rustos-devhw tests"

# ---------------------------------------------------------------- missing hardware
newroot no-hardware
out=$(run check); rc=$?
eq "$rc" 0
has "$out" "No PCIe devices are visible"
has "$out" "[untested]    PCIe devices"
has "$out" "No known FPGA/JTAG/debug adapter is plugged in"
out=$(run check --machine)
has "$out" $'SUMMARY\t'
hasnt "$out" "[supported]"

newroot no-lspci
out=$(LSPCI_OVERRIDE=/nonexistent/lspci run devices)
has "$out" "[unavailable] PCI listing              lspci is not installed"
has "$out" "sudo pacman -S pciutils"

# ---------------------------------------------------------------- missing kernel modules
newroot modules-gone
mkdir -p "$R/usr/lib/modules/7.2.10-arch1-1"
out=$(KREL_OVERRIDE=7.2.8-arch1-1 run check)
has "$out" "the modules of the running kernel (7.2.8-arch1-1) are gone"
has "$out" "Restart the PC"
has "$out" "module vfio_pci          cannot be checked"
has "$out" "no headers for 7.2.8-arch1-1"

newroot vfio-module-missing
iommu_on; fpga_card
printf 'kernel/drivers/usb/serial/ftdi_sio.ko.zst:\n' > "$R/usr/lib/modules/$K/modules.dep"
out=$(run check)
has "$out" "[unavailable] module vfio_pci          missing from kernel $K"
has "$out" "[unavailable] VFIO assignment          modules missing: vfio vfio_pci"
out=$(run vfio bind 03:00.0); rc=$?
eq "$rc" 1
has "$out" "the vfio-pci module is not available for kernel $K"
eq "$(cat "$R/sys/devices/pci0000:00/0000:03:00.0/driver_override")" ""

newroot builtin-module
iommu_on; fpga_card
printf 'kernel/drivers/vfio/vfio.ko\nkernel/drivers/vfio/pci/vfio-pci.ko\n' > "$R/usr/lib/modules/$K/modules.builtin"
: > "$R/usr/lib/modules/$K/modules.dep"
out=$(run check)
has "$out" "module vfio_pci          built into the kernel"

newroot no-headers
rmdir "$R/usr/lib/modules/$K/build"
out=$(run check)
has "$out" "[unavailable] kernel headers"
has "$out" "sudo pacman -S linux-headers"

# ---------------------------------------------------------------- inactive IOMMU
newroot iommu-inactive
pcidev 0000:03:00.0 058000 10ee 7024 "" ""
lspci_add '0000:03:00.0 Memory controller [0580]: Xilinx Corporation Device [10ee:7024]'
out=$(run check)
has "$out" "[unavailable] IOMMU                    not active"
has "$out" "Turn on VT-d"
has "$out" "sudo rustos-devhw iommu-on"
has "$out" "[unavailable] VFIO assignment          needs an active IOMMU"
out=$(run devices --machine)
has "$out" $'PCI\t0000:03:00.0\t10ee:7024\t0580\t-\t-\t-\tno\tthe IOMMU is not active'
out=$(run vfio bind 0000:03:00.0); rc=$?
eq "$rc" 1
has "$out" "RustOS will not give 0000:03:00.0 to VFIO"
has "$out" "the IOMMU is not active"
eq "$(cat "$R/sys/devices/pci0000:00/0000:03:00.0/driver_override")" ""
eq "$(cat "$R/sys/bus/pci/drivers_probe")" ""
hasnt "$(cat "$LOG")" "modprobe"

newroot iommu-inactive-amd
printf 'vendor_id\t: AuthenticAMD\n' > "$R/proc/cpuinfo"
out=$(run check)
has "$out" "Turn on IOMMU / AMD-Vi"

newroot iommu-off-cmdline
echo "root=UUID=1 rw quiet intel_iommu=off" > "$R/proc/cmdline"
out=$(run check)
has "$out" "turned off on the kernel command line (intel_iommu=off)"

newroot noiommu-mode
iommu_on; fpga_card
echo Y > "$R/sys/module/vfio/parameters/enable_unsafe_noiommu_mode"
out=$(run check)
has "$out" "[unavailable] VFIO no-IOMMU mode       ON"
has "$out" "VFIO assignment          off: no-IOMMU mode is on"
out=$(run vfio bind 0000:03:00.0); rc=$?
eq "$rc" 1
has "$out" "VFIO no-IOMMU (unsafe) mode is on"
eq "$(cat "$R/sys/devices/pci0000:00/0000:03:00.0/driver_override")" ""

newroot noiommu-modprobe
mkdir -p "$R/etc/modprobe.d"; echo 'options vfio enable_unsafe_noiommu_mode=1' > "$R/etc/modprobe.d/bad.conf"
out=$(run check)
has "$out" "turns VFIO no-IOMMU mode on"

# ---------------------------------------------------------------- unsupported devices and refusals
newroot unsupported
iommu_on; fpga_card
pcidev 0000:04:00.0 028000 8086 2725 "" 15
lspci_add '0000:04:00.0 Network controller [0280]: Intel Corporation Wi-Fi 6E [8086:2725]' $'\tKernel modules: iwlwifi'
out=$(run devices)
has "$out" "[unavailable] 0000:03:00.0             FPGA (AMD/Xilinx) Memory controller: Xilinx Corporation Device [10ee:7024] - no Linux driver"
has "$out" "VFIO: can be given to VFIO (IOMMU group 14)"
has "$out" "[untested]    0000:04:00.0"
has "$out" "has a driver (iwlwifi) but it is not loaded"
has "$out" "sudo modprobe iwlwifi"
out=$(run devices --machine)
has "$out" $'PCI\t0000:04:00.0\t8086:2725\t0280\t-\tiwlwifi\t15\tyes'

newroot refusals
iommu_on
pcidev 0000:00:01.0 060400 8086 a70d pcieport 2
lspci_add '0000:00:01.0 PCI bridge [0604]: Intel Corporation Bridge [8086:a70d]' $'\tKernel driver in use: pcieport'
pcidev 0000:00:02.0 030000 8086 a780 i915 0 1
lspci_add '0000:00:02.0 VGA compatible controller [0300]: Intel Corporation Graphics [8086:a780]' $'\tKernel driver in use: i915'
pcidev 0000:02:00.0 010802 144d a80a nvme 12
mkdir -p "$R/sys/devices/pci0000:00/0000:02:00.0/nvme/nvme0/nvme0n1/nvme0n1p2/holders"
ln -sfn "../../devices/pci0000:00/0000:02:00.0/nvme/nvme0/nvme0n1" "$R/sys/class/block/nvme0n1"
ln -sfn "../../devices/pci0000:00/0000:02:00.0/nvme/nvme0/nvme0n1/nvme0n1p2" "$R/sys/class/block/nvme0n1p2"
echo "/dev/nvme0n1p2 / ext4 rw 0 0" > "$R/proc/mounts"
lspci_add '0000:02:00.0 Non-Volatile memory controller [0108]: Samsung NVMe [144d:a80a]' $'\tKernel driver in use: nvme'
# two functions of one card in group 16: the audio part still has its driver
pcidev 0000:05:00.0 030000 10de 2484 "" 16
pcidev 0000:05:00.1 040300 10de 228b snd_hda_intel 16
lspci_add '0000:05:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [10de:2484]' '0000:05:00.1 Audio device [0403]: NVIDIA Corporation GA104 Audio [10de:228b]' $'\tKernel driver in use: snd_hda_intel'
out=$(run vfio bind 0000:00:01.0); has "$out" "PCI bridge or host bridge"
out=$(run vfio bind 0000:00:02.0); has "$out" "graphics card showing this screen"
out=$(run vfio bind 0000:02:00.0); has "$out" "holds disks that are in use: nvme0n1p2"
out=$(run vfio bind 0000:05:00.0); rc=$?
eq "$rc" 1
has "$out" "IOMMU group 16 also has 0000:05:00.1 (driver snd_hda_intel)"
for s in 0000:00:01.0 0000:00:02.0 0000:02:00.0 0000:05:00.0; do
  eq "$(cat "$R/sys/devices/pci0000:00/$s/driver_override")" ""
done
out=$(run vfio bind not-a-slot); has "$out" "give the PCI slot"
out=$(run vfio bind 0000:09:00.0); has "$out" "there is no PCI device 0000:09:00.0"
out=$(run devices)
has "$out" "bridge (never given away)"

# ---------------------------------------------------------------- binding an isolated device
newroot bind-isolated
iommu_on; fpga_card
out=$(run vfio bind 0000:03:00.0); rc=$?
has "$(cat "$LOG")" "modprobe vfio-pci"
has "$(cat "$R/sys/bus/pci/drivers_probe")" "0000:03:00.0"
# the fake kernel never really binds, so the tool must notice it and put the override back
eq "$rc" 1
has "$out" "vfio-pci did not take 0000:03:00.0"
eq "$(cat "$R/sys/devices/pci0000:00/0000:03:00.0/driver_override")" ""

newroot bind-unbinds-old-driver
iommu_on
pcidev 0000:06:00.0 020000 8086 125c igc 20
lspci_add '0000:06:00.0 Ethernet controller [0200]: Intel Corporation I226-V [8086:125c]' $'\tKernel driver in use: igc'
run vfio bind 0000:06:00.0 >/dev/null
eq "$(cat "$R/sys/bus/pci/drivers/igc/unbind")" "0000:06:00.0"

newroot already-bound
iommu_on
pcidev 0000:03:00.0 058000 10ee 7024 vfio-pci 14
lspci_add '0000:03:00.0 Memory controller [0580]: Xilinx Corporation Device [10ee:7024]' $'\tKernel driver in use: vfio-pci'
out=$(run vfio bind 03:00.0); rc=$?
eq "$rc" 0
has "$out" "already given to VFIO: /dev/vfio/14"
out=$(run vfio keep 0000:03:00.0)
eq "$(cat "$R/etc/rustos/vfio-devices.conf")" "0000:03:00.0 10ee:7024"
has "$(cat "$LOG")" "systemctl enable rustos-vfio.service"
out=$(run devices --machine)
has "$out" $'\tbound\t'
has "$out" $'\tyes'   # kept
out=$(run vfio list); has "$out" "0000:03:00.0 10ee:7024"
out=$(run vfio forget 0000:03:00.0)
eq "$(cat "$R/etc/rustos/vfio-devices.conf")" ""
has "$(cat "$LOG")" "systemctl disable rustos-vfio.service"

newroot apply-boot-changed-card
iommu_on; fpga_card
echo "0000:03:00.0 10ee:9038" > "$R/etc/rustos/vfio-devices.conf"
out=$(run vfio apply-boot); rc=$?
eq "$rc" 1
has "$out" "skipping 0000:03:00.0: the device there is now 10ee:7024, not 10ee:9038"
eq "$(cat "$R/sys/devices/pci0000:00/0000:03:00.0/driver_override")" ""

# ---------------------------------------------------------------- kernel configuration
newroot kconfig-unreadable
rm -f "$R/proc/config.gz"
out=$(run check)
has "$out" "[untested]    CONFIG_VFIO              unknown"
has "$out" "[untested]    module signatures"

newroot kconfig-no-vfio
kconfig 'CONFIG_IOMMU_SUPPORT=y' 'CONFIG_INTEL_IOMMU=y' '# CONFIG_VFIO is not set' '# CONFIG_VFIO_PCI is not set'
out=$(run check)
has "$out" "[unavailable] CONFIG_VFIO              not set: VFIO device assignment cannot work"
has "$out" "[info]        CONFIG_VFIO_NOIOMMU      not set"

newroot kconfig-full
out=$(run check)
has "$out" "[supported]   CONFIG_VFIO_PCI          m"
has "$out" "CONFIG_VFIO_NOIOMMU      y (the unsafe mode exists in the kernel; RustOS never turns it on)"
has "$out" "CONFIG_XILINX_XDMA       m (the mainline dmaengine driver"
has "$out" "/dev/mem                 restricted by the kernel"

# ---------------------------------------------------------------- iommu-on edits only the right options
newroot iommu-on-grub
echo "BOOTLOADER=grub" > "$R/etc/rustos/bootloader.conf"
printf 'GRUB_DEFAULT=0\nGRUB_CMDLINE_LINUX_DEFAULT="loglevel=3 quiet splash"\nGRUB_CMDLINE_LINUX=""\n' > "$R/etc/default/grub"
out=$(run iommu-on); run iommu-on >/dev/null
has "$(cat "$R/etc/default/grub")" 'GRUB_CMDLINE_LINUX_DEFAULT="loglevel=3 quiet splash intel_iommu=on"'
eq "$(grep -o 'intel_iommu=on' "$R/etc/default/grub" | wc -l)" 1
has "$(cat "$R/etc/default/grub")" 'GRUB_CMDLINE_LINUX=""'
hasnt "$(cat "$R/etc/default/grub")" "iommu=pt"
has "$out" "does not add iommu=pt"

newroot iommu-on-systemd-boot
echo "BOOTLOADER=systemd-boot" > "$R/etc/rustos/bootloader.conf"
printf 'title RustOS\nlinux /vmlinuz-linux\noptions root=UUID=1 rw quiet\n' > "$R/boot/loader/entries/rustos.conf"
run iommu-on >/dev/null; run iommu-on >/dev/null
eq "$(grep '^options' "$R/boot/loader/entries/rustos.conf")" "options root=UUID=1 rw quiet intel_iommu=on"

newroot iommu-on-refind
echo "BOOTLOADER=refind" > "$R/etc/rustos/bootloader.conf"
printf '"Boot RustOS" "root=UUID=1 rw quiet initrd=/initramfs-linux.img"\n' > "$R/boot/refind_linux.conf"
run iommu-on >/dev/null
eq "$(cat "$R/boot/refind_linux.conf")" '"Boot RustOS" "root=UUID=1 rw quiet initrd=/initramfs-linux.img intel_iommu=on"'

newroot iommu-on-amd
printf 'vendor_id\t: AuthenticAMD\n' > "$R/proc/cpuinfo"
echo "BOOTLOADER=grub" > "$R/etc/rustos/bootloader.conf"
printf 'GRUB_CMDLINE_LINUX_DEFAULT="quiet"\n' > "$R/etc/default/grub"
out=$(run iommu-on)
has "$out" "This is not an Intel PC"
eq "$(cat "$R/etc/default/grub")" 'GRUB_CMDLINE_LINUX_DEFAULT="quiet"'

newroot iommu-on-already
iommu_on; fpga_card
out=$(run iommu-on); has "$out" "already active"

# ---------------------------------------------------------------- DKMS
newroot dkms-missing-build
printf '#!/bin/sh\ncase "$1" in status) echo "xdma/2024.1, 7.2.0-arch1-1, x86_64: installed"; echo "xdma/2024.1, %s, x86_64: built" ;; esac\n' "$K" > "$S/dkms"
chmod +x "$S/dkms"
out=$(run dkms)
has "$out" "[unavailable] DKMS"
has "$out" "xdma/2024.1, $K, x86_64: built"
has "$out" "sudo rustos-devhw dkms build $K"
rmdir "$R/usr/lib/modules/$K/build"
out=$(run dkms build); rc=$?
eq "$rc" 1
has "$out" "the headers for $K are missing. Install them first: sudo pacman -S linux-headers"

newroot dkms-not-for-running
printf '#!/bin/sh\ncase "$1" in status) echo "mydrv/1.0, 7.2.0-arch1-1, x86_64: installed" ;; esac\n' > "$S/dkms"; chmod +x "$S/dkms"
out=$(run dkms)
has "$out" "DKMS mydrv/1.0           not built for the running kernel $K"

newroot dkms-absent
out=$(PATH="$S:/usr/bin:/bin" run dkms)
has "$out" "DKMS                     not installed"

# ---------------------------------------------------------------- USB boards and access
newroot usb
mkdir -p "$R/sys/bus/usb/devices/1-2"
echo 0403 > "$R/sys/bus/usb/devices/1-2/idVendor"; echo 6010 > "$R/sys/bus/usb/devices/1-2/idProduct"
echo 1 > "$R/sys/bus/usb/devices/1-2/busnum"; echo 5 > "$R/sys/bus/usb/devices/1-2/devnum"
mkdir -p "$R/sys/bus/usb/devices/1-3"; echo 046d > "$R/sys/bus/usb/devices/1-3/idVendor"; echo c52b > "$R/sys/bus/usb/devices/1-3/idProduct"
out=$(run usb --machine)
has "$out" $'USB\t0403:6010\tFTDI FT2232'
hasnt "$out" "046d"
out=$(run access root)
has "$(cat "$LOG")" "usermod -aG uucp root"
hasnt "$(cat "$LOG")" "rustos-vfio"
[ -e "$R/etc/security/limits.d/90-rustos-vfio.conf" ] && bad "limits written without --vfio" || ok
out=$(run access --vfio root)
has "$(cat "$LOG")" "usermod -aG rustos-vfio root"
has "$(cat "$R/etc/security/limits.d/90-rustos-vfio.conf")" "@rustos-vfio hard memlock 8192000"
out=$(run access --remove root)
has "$(cat "$LOG")" "gpasswd -d root uucp"
out=$(run access nosuchuser-xyz); has "$out" "there is no user nosuchuser-xyz"

# ---------------------------------------------------------------- safety: what the tool must never contain
CUR=static-safety
code=$(grep -v '^\s*#' "$TOOL")
hasnt "$code" "> /dev/mem"
hasnt "$code" "< /dev/mem"
hasnt "$code" "of=/dev/mem"
hasnt "$code" "if=/dev/mem"
hasnt "$code" "/dev/kmem"
grep -E 'enable_unsafe_noiommu_mode\s*=\s*(1|Y)' <<<"$code" | grep -qv 'grep\|has_arg\|-E' && bad "writes no-IOMMU mode" || ok
grep -E '(echo|printf).*(iommu=off|iommu=pt|intel_iommu=off|amd_iommu=off)' <<<"$code" | grep -qv 'never\|does not' && bad "adds an IOMMU-off option" || ok
grep -qE 'uio_pci_generic.*new_id|/new_id' <<<"$code" && bad "uses new_id/UIO binding" || ok

# ---------------------------------------------------------------- the udev rules: only known keys, uaccess, no MODE=0666
CUR=udev-rules
for f in "$HERE"/../../overlay/airootfs/etc/udev/rules.d/7[01]-rustos-*.rules; do
  while IFS= read -r l; do
    case "$l" in ""|\#*) continue ;; esac
    grep -qvE '^(ACTION|SUBSYSTEM|ENV\{DEVTYPE\}|ATTR\{idVendor\}|ATTR\{idProduct\}|KERNEL|LABEL|GOTO|TAG|GROUP|MODE|ENV\{ID_RUSTOS_FPGA\})' <<<"$(tr ',' '\n' <<<"$l" | sed 's/^ *//')" \
      && bad "unknown key in $f: $l" || ok
  done < "$f"
  hasnt "$(cat "$f")" '0666'
done
has "$(cat "$HERE/../../overlay/airootfs/etc/udev/rules.d/70-rustos-fpga.rules")" 'TAG+="uaccess"'

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]
