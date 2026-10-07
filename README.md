# RustOS (Arch-based, KDE Plasma)

A lean daily-driver distro: Arch Linux base (so you get **pacman** and all Arch packages),
**KDE Plasma** desktop, RustOS logo/wallpaper, `fastfetch` that shows RustOS, and a
point-and-click installer. Built with archiso into a bootable ISO.

## Windows + Hyper-V: four double-clicks

1. **setup.bat**: once. Installs Arch for WSL + archiso. (Restart the PC if it asks.)
2. **build.bat**: builds `out\rustos-*.iso` (15-40 min, ~3 GB download).
3. **hyperv.bat**: creates a Hyper-V VM called "RustOS" (Gen 2, 4 GB RAM, 4 CPUs, 64 GB disk,
   Secure Boot off) and boots the ISO. It asks for admin rights.
4. In the VM, a welcome window asks "Install RustOS?". Click it and follow the 3 steps.

Running `hyperv.bat` again reuses the VM and loads the newest ISO into it.

## The installer

Normal windows, no terminal questions: pick the disk -> type your name -> choose a password -> done.
After you pick the disk, it asks how to install:

- **Erase the whole disk** (simplest).
- **Install next to Windows (dual boot)**: keeps Windows and your files, uses free space on the disk.
- **Advanced**: you choose the partition for RustOS (it is formatted) and the EFI partition (reused, not
  formatted), plus file system (ext4 / btrfs / xfs) and the computer name. A button opens Partition Manager.
It needs internet, because it downloads the packages fresh. The time zone is looked up from your IP
address (ipapi.co); if that fails it uses UTC. Log: `/var/log/rustos-install.log`.

## After installing

```
sudo pacman -Syu          # update everything
sudo pacman -S <package>  # install
sudo pacman -Ss <word>    # search
fastfetch                 # the RustOS banner (neofetch is an alias for it)
```
Software centre: Discover (also installs Flatpak apps). Games: open **RustOS Gaming Setup** (see below).

## What is (not) in it

`packages-extra.txt` is the full list for both the ISO and the installed system.
`packages-remove.txt` lists what is stripped out of the stock Arch ISO (clonezilla, nmap, VPN tools, ...).

## Customising

- `packages-extra.txt`, `packages-remove.txt`: add/remove packages.
- `branding/`: `logo.svg`, wallpaper (`python make_pngs.py`), fastfetch logo (`python make_ascii.py`).
- `overlay/airootfs/`: files copied into the system (installer scripts are in `usr/local/bin`).

## Known limits

- Not test-built by me: the first real build may need a small fix. Send me the first error line.
- If the mouse or screen misbehaves in Hyper-V, send me what you see.
- Secure Boot must be off.

## Hyper-V says "Not enough memory" (0x8007000E)

Windows doesn't have enough free RAM for the VM. `hyperv.bat` now runs `wsl --shutdown` (WSL keeps
GBs of RAM after a build) and sizes the VM to your free RAM. If you made the VM by hand: Hyper-V
Manager -> VM -> Settings -> Memory -> set Startup RAM to 3072 MB, and close Chrome/games first.
To stop WSL from hogging RAM during builds, create `C:\Users\<you>\.wslconfig` with:
```
[wsl2]
memory=6GB
```

## Boot loader choice

The installer asks which boot loader to use: **GRUB** (default, finds Windows), **systemd-boot** and
**rEFInd** (UEFI only), or **Limine**. GRUB is always installed as a safety net: if the loader you pick
fails to set up, the installer falls back to GRUB so the PC still boots. The non-GRUB loaders are the
least tested part; if one misbehaves, reinstall and pick GRUB.

## Dual boot with Windows

1. In Windows, double-click **dualboot.bat**. It checks UEFI/GPT/BitLocker, asks how many GB to give RustOS,
   shrinks C: (nothing is deleted), and turns off Fast Startup. Back up your files first.
2. Put the ISO on a USB stick (Rufus or Ventoy), Secure Boot off, boot it.
3. Click **Install RustOS**, pick the disk that has Windows, choose **Install next to Windows**.
4. GRUB is used for dual boot (it adds Windows to the boot menu and fits Windows' small EFI partition).
   It never overwrites Windows' boot files.

Needs UEFI + GPT (every Windows 10/11 PC from the last ~8 years). Old BIOS/MBR PCs: use a separate disk.

## Automatic updates (installed systems)

Installed RustOS updates itself, so you never reinstall or re-flash:

- **Daily** (first run 10 min after boot): all packages (`pacman -Syu`) + Flatpak apps, only when online and
  plugged in. If the kernel changed you get a "restart when you can" notification.
- **Weekly**: fastest mirrors are re-picked (reflector); old package cache is cleaned (paccache).
- **Boot loader**: when GRUB / Limine / rEFInd are upgraded, a hook refreshes them on disk automatically.

```
rustos-autoupdate status    # on/off + next run
rustos-autoupdate off|on    # switch it
rustos-autoupdate now       # update right now
rustos-autoupdate log       # last log lines  (full log: /var/log/rustos-update.log)
```
Discover still works for manual updates too.

What it does NOT update: your RustOS *ISO* (a new ISO is only needed for new installs) and RustOS-specific
tweaks you make in this project (branding, installer, package list). Those need a package repository that
installed systems can pull from, which needs somewhere to host files (GitHub Pages or any web host).
Arch is rolling: very rarely an update needs manual steps (see archlinux.org/news).

## Publishing from RustOS (no Windows needed)

First time only: `git clone https://github.com/andreh901300/rustos ~/rustos-arch`, then copy your changed files in.
After that, in the project folder: `bash publish.sh`. It asks for a one-line message and a version number, pushes to GitHub,
and signs you in to GitHub in the browser the first time (it installs `github-cli` for that). `publish.bat` is the same thing for Windows.

## Updates when YOU make a new version

`rustos-base` (branding, tools, auto-updater, app list) is published as a signed package repository on
GitHub Pages. Installed systems pull it with their daily update, so a new RustOS version reaches everyone
without reinstalling. One-time setup: **GITHUB-SETUP.md**. Then each release is just **publish.bat**.

## What users see when you release a new version

After any update (the daily one, Discover, or a manual `pacman -Syu`) a popup appears:
**"RustOS updated to 2.4"** with the top 3 lines of your change list, a **What's new** button and, if the
kernel changed, a **Restart now** button. If the PC was off or the user logged out, the popup shows at the
next login. It only shows once per update.

Where the text comes from: `CHANGELOG.txt`. **publish.bat asks for a one-line message (optional: press Enter to skip) and adds
that line for you.** It also asks for a new version number: type one (like `2.3`) for a big release, or press Enter.

The **RustOS Update Center** (app menu) shows the current version, checks for updates, installs them in a
terminal window you can watch, shows What's new and the update history, and turns automatic updates on/off.

What a release can change on everyone's PC: all RustOS scripts, branding, settings, the app list (new
packages in `packages-extra.txt` get installed everywhere), the Update Center, the Gaming Setup, tuning.
What it cannot change: files a user edited themselves, anything in their home folder that already exists,
and the ISO file (only needed for brand-new installs).

## Gaming

Menu -> **RustOS Gaming Setup** (RustOS also asks once at first login). Tick what you want:
Steam, GameMode + MangoHud + Gamescope, Lutris + Wine, Heroic, ProtonUp-Qt, Discord. It turns on 32-bit
support, picks the graphics driver (AMD and Intel use Mesa; NVIDIA RTX / GTX 16 and newer use `nvidia-open`;
older NVIDIA cards use the open Nouveau/NVK driver), and installs everything in one go. In Steam, set a
game's launch options to `gamemoderun mangohud %command%`. It is optional on purpose, so RustOS stays light.
Not useful inside Hyper-V (no real GPU there); it warns you.

## Windows App Support (.exe)

Linux cannot run `.exe` files by itself, so RustOS runs them through **Wine** (and Steam's **Proton** for Steam games),
the same idea as Windows App Support on Zorin OS. Double-click an `.exe`, `.msi` or `.lnk` and `rustos-run-exe` runs it;
the first time it offers to install Wine (`rustos-gaming --install wine`: Wine, Mono, Gecko, winetricks and the common
32-bit libraries). Right-click an `.exe` -> **Run as game** starts it with GameMode and the MangoHud overlay.

Menu -> **Windows App Support** (`rustos-windows`) is the control window: install a program from its setup file, list
the programs you installed, open the Windows C: drive, add fonts / Visual C++ / DirectX / DXVK / .NET (winetricks),
look a program up in the WineHQ database, uninstall programs, open Wine settings, or reset the Windows environment
(the old one is kept as `~/.wine.old-DATE`). Programs you install also appear in the normal menu.

RustOS warns before it runs things known to be troublesome (anti-cheat games, Microsoft Office, Adobe). You can still try them.
Honest limits: many programs and games work, some don't. Games with kernel anti-cheat usually won't run, and Office /
Adobe apps are poor under Wine. Use LibreOffice, GIMP, etc. instead (**Switching from Windows** shows replacements).
Bottles (Flatpak) is available in **RustOS Apps**. Wine package names and the winetricks downloads are unverified on a real install.

## Education Center

Menu -> **RustOS Education Center** (also offered in **RustOS Apps** and the Update Center). Tick what you want:
**PDF**: Okular (read and annotate), Xournal++ (write on and sign PDFs), PDF Arranger (merge, split, reorder).
**Website shortcuts**: Canva, Google Docs, Google Classroom, Microsoft 365 online, Khan Academy, Duolingo. These have no
Linux program, so RustOS adds a menu entry that opens the site in Firefox (needs internet and your own account).
**Study apps**: Calibre, Anki, Zotero, Obsidian, Scratch, GeoGebra, Stellarium, Zoom. Nothing is installed by default.
Flatpak IDs and some package names are unverified on a real install; missing ones are skipped with a message.

## Antivirus

Menu -> **RustOS Antivirus**, or right-click any file or folder -> **Scan for viruses (RustOS)**. It uses **ClamAV**,
installed the first time you open it (a few hundred MB for the virus database; the database then updates by itself).
Scans: quick (Downloads, Desktop, Documents), a folder / drive / file, the whole home folder, or the whole PC.
Infected files can be locked in a quarantine folder or deleted. It is **not** real-time protection (nothing runs in the
background, which keeps RustOS light), it misses brand-new malware, and a scan can use over 1 GB of memory.
Handy before you run a downloaded `.exe` or open a USB stick from someone else.

## Undo an update

Before every update RustOS saves a list of the installed packages (`/var/lib/rustos/restorepoints`, newest 10).
**Update Center -> Undo the last update** (or `rustos-rollback`) lists what would change and goes back to those
versions using the pacman cache or the Arch archive, then pauses automatic updates for 7 days
(`rustos-autoupdate resume` or **Update Center -> Resume** to end the pause). It restores programs, not your
files or settings, and it needs internet if the old packages are no longer cached.

## Installer choices

Besides the account, disk and boot loader the installer now asks for your **language** and **keyboard layout**,
and whether to install the **NVIDIA driver** (RTX / GTX 16 series or newer). Installer changes live on the ISO,
so run `build.bat` again to get them in a fresh install.

## Apps and switching from Windows

At first login RustOS offers **RustOS Apps** (also in the menu): Office (LibreOffice), VLC, Windows program support,
printing/scanning, GIMP, Thunderbird, OBS, Bottles and the gaming setup. Nothing is installed by default, so RustOS stays light.
**Switching from Windows** (menu) opens your Windows drives and files, runs an `.exe`, and lists replacement apps
(`usr/share/rustos/windows-equivalents.txt`).

## Lightweight

- No indexer (Baloo is off), no bloat apps, no sshd/cloud-init, a lean Plasma package list.
- Compressed-RAM swap (zram) with matching memory settings, the right disk scheduler per disk type
  (NVMe / SSD / hard disk), logs capped at 200 MB, and 15-second shutdown timeout.
- `power-profiles-daemon` gives a Performance / Balanced / Power saver switch in the battery menu.
- Check it yourself after a boot: `fastfetch` shows RAM used. Numbers differ per PC, so I have not promised any.
