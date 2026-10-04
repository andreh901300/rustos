# Makes room for RustOS next to Windows by shrinking C: (nothing is deleted, no partition is created).
# The RustOS installer then uses the free space ("Install next to Windows").
$ErrorActionPreference = 'Stop'
function Say($t, $c = 'White') { Write-Host $t -ForegroundColor $c }

Say '=== RustOS dual boot: make room next to Windows ===' Cyan
Say ''

# --- checks ---------------------------------------------------------------
$fw = (Get-ItemProperty 'HKLM:\System\CurrentControlSet\Control' -Name PEFirmwareType -ErrorAction SilentlyContinue).PEFirmwareType
if ($fw -ne 2) { Say 'This PC starts Windows in old BIOS mode. RustOS dual boot needs UEFI.' Red; exit 1 }

$part = Get-Partition -DriveLetter C
$disk = Get-Disk -Number $part.DiskNumber
if ($disk.PartitionStyle -ne 'GPT') { Say "Disk $($disk.Number) is not GPT. RustOS dual boot needs a GPT disk." Red; exit 1 }

$sup      = Get-PartitionSupportedSize -DriveLetter C
$canGB    = [int][Math]::Floor(($part.Size - $sup.SizeMin) / 1GB) - 5     # keep a safety margin
$totalGB  = [int][Math]::Floor($part.Size / 1GB)
Say ("Disk {0}: {1} ({2} GB total)" -f $disk.Number, $disk.FriendlyName, [int]($disk.Size / 1GB))
Say ("Windows (C:) is {0} GB. Windows can give up to about {1} GB." -f $totalGB, $canGB)
if ($canGB -lt 25) {
  Say 'Not enough room to shrink C: (RustOS needs at least 25 GB).' Red
  Say 'Free some space on C: (and run Disk Cleanup), restart, then try again.' Yellow
  exit 1
}

# BitLocker
$bl = $null
try { $bl = Get-BitLockerVolume -MountPoint 'C:' -ErrorAction Stop } catch { }
if ($bl -and $bl.ProtectionStatus -eq 'On') {
  Say ''
  Say 'BitLocker is ON for C:. Windows may ask for your recovery key after the install.' Yellow
  Say 'Make sure you have the recovery key: https://aka.ms/myrecoverykey' Yellow
  $a = Read-Host 'Pause BitLocker for the next 2 restarts so Windows boots normally afterwards? (y/n)'
  if ($a -match '^[yY]') { Suspend-BitLocker -MountPoint 'C:' -RebootCount 2 | Out-Null; Say 'BitLocker paused for 2 restarts.' Green }
}

# --- ask how much ---------------------------------------------------------
$def = [Math]::Min(80, $canGB)
Say ''
Say 'RustOS needs at least 25 GB. 60-100 GB is comfortable for daily use.'
$in = Read-Host ("How many GB should RustOS get? ({0}-{1}, Enter = {2})" -f 25, $canGB, $def)
if ([string]::IsNullOrWhiteSpace($in)) { $gb = $def } else { $gb = [int]$in }
if ($gb -lt 25 -or $gb -gt $canGB) { Say "Please choose between 25 and $canGB." Red; exit 1 }

Say ''
Say "This will shrink C: by $gb GB. Your Windows files are kept, but BACK UP anything important first." Yellow
$ok = Read-Host 'Type SHRINK to continue'
if ($ok -cne 'SHRINK') { Say 'Cancelled. Nothing was changed.'; exit 0 }

# --- do it ----------------------------------------------------------------
Say 'Turning off Fast Startup / hibernation (Linux cannot use a hibernated Windows disk safely)...'
powercfg /h off | Out-Null

$newSize = $part.Size - ([int64]$gb * 1GB)
if ($newSize -lt ($sup.SizeMin + 1GB)) { $newSize = $sup.SizeMin + 1GB }
Say "Shrinking C: to $([int]($newSize / 1GB)) GB (this can take a few minutes)..."
Resize-Partition -DriveLetter C -Size $newSize

Say ''
Say 'Done! There is now unallocated space on the disk for RustOS.' Green
Say 'Do NOT create a partition in it from Windows.' Green
Say ''
Say 'Next:' Cyan
Say '  1. Put the RustOS ISO on a USB stick (Rufus or Ventoy), keep Secure Boot OFF in the BIOS.'
Say '  2. Boot the USB, click "Install RustOS", pick this disk, then choose "Install next to Windows".'
Say '  3. Restart. The boot menu shows RustOS and Windows.'
