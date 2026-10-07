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

## RustOS EXE Center (.exe)

Linux cannot run `.exe` files by itself, and there is no native way to do it. RustOS runs them through **Wine** (and
Steam's **Proton** for Steam games). Wine is the engine; the **RustOS EXE Center** is the front door. Double-click an
`.exe`, `.msi` or `.lnk` and `rustos-run-exe` runs it; the first time it offers to install Wine
(`rustos-gaming --install wine`). Right-click an `.exe` -> **Run as game** (GameMode + MangoHud) or **Add to RustOS EXE Center**.

Menu -> **RustOS EXE Center** (`rustos-exe-center`) has a folder, `~/EXE-Center`, where you put your files:

- `Setups`: installers like `cs1.6 setup.exe` or `game-setup.msi` -> **Install a setup**
- `Runtimes`: .NET, Visual C++ and DirectX installers -> **Install .NET / Visual C++ / DirectX from my files**
- `DLLs`: extra `.dll` files -> **Install a DLL** (system-wide or next to one program; 32/64-bit is detected from the file;
  it is registered and Wine is told to prefer it). Double-clicking a `.dll` offers the same.
- `Programs`: portable programs and games, even whole folders -> **Run a program** / **Run a program as a game**

**Add files** copies what you pick into the right folder by its name; you can also drop files in the folder yourself.
Other items: download .NET / Visual C++ / DirectX / fonts / DXVK automatically (winetricks), look a program up in the WineHQ
database, uninstall programs, Wine settings, reset the Windows environment (old one kept as `~/.wine.old-DATE`), and
**Remove Windows support** (uninstalls Wine; your EXE-Center files stay).

RustOS warns before it runs things known to be troublesome (anti-cheat games, Microsoft Office, Adobe). Honest limits: many
programs and games work (older games such as Counter-Strike 1.6 usually do), some don't. Games with kernel anti-cheat
usually won't run, and Office / Adobe apps are poor under Wine. It does not exist on the ARM edition (it needs an
Intel/AMD PC). Wine package names and winetricks downloads are unverified on a real install.

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

At first login RustOS offers **RustOS Apps** (also in the menu). It lists 50+ apps in groups (office and study, internet and
chat, music and video, pictures and design, programming, games, Windows programs, tools). Open a group, tick what you want,
go back, open another group, then press **Install** at the bottom. Nothing is installed by default, so RustOS stays light.
The list is a plain text file, `overlay/airootfs/usr/share/rustos/apps.catalog`, one app per line
(`category|id|label|pacman packages|flatpak ids|services|flags`). To add an app, add a line and publish. Package names that
do not exist are skipped at install time, so a wrong name cannot break anything. Apps that only exist for PCs (flag `x86`)
are hidden on the ARM edition.
**Switching from Windows** (menu) opens your Windows drives and files, runs an `.exe`, and lists replacement apps
(`usr/share/rustos/windows-equivalents.txt`).

## iPad mode and touchscreens

Menu -> **iPad Mode** (also a button on the desktop and in the taskbar, in the Update Center, and **Meta+Ctrl+T**).
It works with a mouse and keyboard, so you can try it on any PC without a touchscreen.

- **iPad mode** swaps the panel for a floating dock at the bottom (grid icon = all apps, then pinned apps, a **Touch Keyboard**
  button and an **iPad Mode** button), a thin bar with clock and status icons on top, Papirus icons, a soft wallpaper, and
  windows that open maximized. The dock's **iPad Mode** button opens a window with **Turn off**.
- **Touch only** keeps your normal desktop and adds just the touch keyboard and gestures.
- The touch keyboard is the Wayland on-screen keyboard (Maliit). It shows by itself when you tap a text box; the dock's
  **Touch Keyboard** button shows or hides it with a mouse click. It needs the Wayland session (the default). The login screen
  uses the Qt virtual keyboard.
- Swipe up from the bottom edge of the screen = open windows overview; the top-left corner does the same with the mouse.
- Turning it off restores your saved panel layout and settings (`~/.config/rustos-ipad`), nothing is deleted.
- On a touchscreen PC, first login asks if you want it. The ARM edition asks during its first start.
- `rustos-ipad-mode status | on | touch | off | keyboard` work from a terminal.

**Not tested on real hardware yet**: the dock layout is built by a Plasma script and the gestures use KWin settings, so the
first run may need small fixes depending on the exact Plasma version. It is an iPad-style desktop, not iPadOS.

## iPad and other ARM devices (experimental, UTM)

An iPad cannot run another system at full speed (iPadOS has no hardware virtualization for apps), so **UTM** emulates the
hardware: expect it to feel slow. Without JIT (the App Store "UTM SE") it is very slow; the full UTM with JIT is much better.
Good for the browser, documents and trying RustOS. Not for games. Windows `.exe` support and Steam are switched off on ARM
(they need an Intel or AMD PC) and say so. Everything else is the same as the PC edition: same package list (only names that
do not exist for ARM are left out, see `packages-arm-remove.txt`), same language and keyboard questions at first start, same
settings, plus the iPad mode question.

How it is made (all on GitHub, nothing to run on your PC):
1. `repo/build-repo.sh` now also builds an **aarch64** update repository next to the normal one. Its dependency list is
   `packages-extra.txt` minus whatever Arch Linux ARM does not have (it checks the real ARM package lists while building;
   `packages-arm-remove.txt` is the fallback list).
2. After the normal publish is green: GitHub -> **Actions** -> **Build RustOS ARM image** -> **Run workflow**. It takes a
   while. `arm/build-image.sh` starts from the Arch Linux ARM root filesystem, adds the RustOS repository, installs
   `rustos-base`, sets up UEFI boot (systemd-boot) and writes `RustOS-arm64-VERSION.qcow2`.
3. Download that file from the finished run (the **Artifacts** section), upload it to Mega, and paste the link into
   `arm_download_url` in the website's `inc/config.php`.
4. First boot asks for a computer name, time zone, language, keyboard, user name, password and whether to use iPad mode (`arm/rustos-firstboot`). There is no default
   password: the Arch Linux ARM `alarm` user is removed and root is locked.

Steps for the iPad owner are in the website's install guide (section "iPad and ARM"). **Nothing in this ARM pipeline has been
run yet**: expect to fix a few things from the Actions log the first time (package names, boot loader, file sizes).
If the artifact is too big for GitHub, tell me and the image can be made smaller.

## Lightweight

- No indexer (Baloo is off), no bloat apps, no sshd/cloud-init, a lean Plasma package list.
- Compressed-RAM swap (zram) with matching memory settings, the right disk scheduler per disk type
  (NVMe / SSD / hard disk), logs capped at 200 MB, and 15-second shutdown timeout.
- `power-profiles-daemon` gives a Performance / Balanced / Power saver switch in the battery menu.
- Check it yourself after a boot: `fastfetch` shows RAM used. Numbers differ per PC, so I have not promised any.
