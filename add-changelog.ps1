# Called by publish.bat. Adds your "what changed" line to CHANGELOG.txt (and starts a new version if asked).
# Input comes from environment variables MSG and NEWVER, so quotes in your text cannot break anything.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cl   = Join-Path $root 'CHANGELOG.txt'
$ver  = Join-Path $root 'VERSION'
$msg  = $env:MSG
$new  = $env:NEWVER
$utf8 = New-Object System.Text.UTF8Encoding($false)

$lines = New-Object System.Collections.Generic.List[string]
if (Test-Path $cl) { $lines.AddRange([string[]][System.IO.File]::ReadAllLines($cl)) }

$first = -1
for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -like '== *') { $first = $i; break } }

if ($new) {
  [System.IO.File]::WriteAllText($ver, $new + "`n", $utf8)
  $header = "== RustOS $new =="
  if ($first -lt 0) { $lines.Add(''); $lines.Add($header); $first = $lines.Count - 1 }
  else { $lines.Insert($first, ''); $lines.Insert($first, $header); }
}
if ($first -lt 0) { $lines.Add(''); $lines.Add('== RustOS =='); $first = $lines.Count - 1 }

if ($msg) { $lines.Insert($first + 1, "- $msg") }
[System.IO.File]::WriteAllLines($cl, $lines, $utf8)
