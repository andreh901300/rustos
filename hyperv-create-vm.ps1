# Creates (or reuses) a Hyper-V VM called "RustOS" that boots the newest ISO from the "out" folder.
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$name = 'RustOS'

$iso = Get-ChildItem (Join-Path $here 'out') -Filter 'rustos-*.iso' -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $iso) {
  Write-Host 'No ISO found in the "out" folder. Double-click build.bat first.' -ForegroundColor Red
  exit 1
}
if (-not (Get-Command New-VM -ErrorAction SilentlyContinue)) {
  Write-Host 'Hyper-V is not enabled on this PC.' -ForegroundColor Red
  Write-Host 'Run this in an admin PowerShell, then restart:'
  Write-Host '  Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All'
  Write-Host '(Windows Home does not include Hyper-V.)'
  exit 1
}

$vm = Get-VM -Name $name -ErrorAction SilentlyContinue
if ($vm) {
  Write-Host "A VM called '$name' already exists - putting the newest ISO in it and starting it."
  $dvd = Get-VMDvdDrive -VMName $name | Select-Object -First 1
  if ($dvd) { Set-VMDvdDrive -VMName $name -ControllerNumber $dvd.ControllerNumber -ControllerLocation $dvd.ControllerLocation -Path $iso.FullName }
  else      { Add-VMDvdDrive -VMName $name -Path $iso.FullName }
  if ($vm.State -ne 'Running') { Start-VM -Name $name }
  vmconnect.exe localhost $name
  exit 0
}

$vhd = Join-Path (Get-VMHost).VirtualHardDiskPath "$name.vhdx"
if (Test-Path $vhd) { $vhd = Join-Path (Get-VMHost).VirtualHardDiskPath ("$name-" + (Get-Date -Format 'yyyyMMddHHmm') + '.vhdx') }
Write-Host "Creating 64 GB virtual disk: $vhd"
New-VHD -Path $vhd -SizeBytes 64GB -Dynamic | Out-Null

# Pick the VM's RAM from what Windows really has free (Hyper-V refuses to start a VM that doesn't fit).
$freeMB = [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
$ramMB  = [Math]::Min(4096, [int]([Math]::Floor(($freeMB - 1024) / 256) * 256))
if ($ramMB -lt 2048) {
  Write-Host "Only $freeMB MB of RAM is free. RustOS needs at least 3 GB for the VM." -ForegroundColor Yellow
  Write-Host 'Close Chrome / games / other VMs and run hyperv.bat again.' -ForegroundColor Yellow
  $ramMB = 2048
}
Write-Host "VM memory: $ramMB MB (free on this PC: $freeMB MB)"
$params = @{ Name = $name; Generation = 2; MemoryStartupBytes = ([int64]$ramMB * 1MB); VHDPath = $vhd }
$switch = Get-VMSwitch -Name 'Default Switch' -ErrorAction SilentlyContinue
if (-not $switch) { $switch = Get-VMSwitch -ErrorAction SilentlyContinue | Select-Object -First 1 }
if ($switch) { $params.SwitchName = $switch.Name } else { Write-Host 'Note: no virtual switch found, the VM will have no internet (the installer needs it).' -ForegroundColor Yellow }

Write-Host 'Creating the VM...'
New-VM @params | Out-Null
$cpus = [Math]::Min(4, (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors)
Set-VM -Name $name -ProcessorCount $cpus -CheckpointType Disabled
Set-VMFirmware -VMName $name -EnableSecureBoot Off      # the Arch-based ISO is not Secure Boot signed
Add-VMDvdDrive -VMName $name -Path $iso.FullName
# Disk first: while it is empty the VM boots the ISO, after the install it boots RustOS from the disk.
Set-VMFirmware -VMName $name -BootOrder (Get-VMHardDiskDrive -VMName $name), (Get-VMDvdDrive -VMName $name)
try { Set-VMVideo -VMName $name -HorizontalResolution 1920 -VerticalResolution 1080 -ResolutionType Single } catch { }

Start-VM -Name $name
Write-Host ''
Write-Host 'Done! The VM window is opening. Click "Install RustOS" on the desktop.' -ForegroundColor Green
vmconnect.exe localhost $name
