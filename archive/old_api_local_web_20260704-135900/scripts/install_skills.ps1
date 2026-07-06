param(
  [string]$CodexSkillsDir = "$env:USERPROFILE\.codex\skills",
  [switch]$IncludeAddons
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$skills = Join-Path $root "skills"
$addonPacks = Join-Path $root "addon-packs"

New-Item -ItemType Directory -Force -Path $CodexSkillsDir | Out-Null

function Install-SkillDir {
  param([Parameter(Mandatory=$true)][System.IO.DirectoryInfo]$SkillDir)
  $dest = Join-Path $CodexSkillsDir $SkillDir.Name
  if (Test-Path $dest) {
    Remove-Item -LiteralPath $dest -Recurse -Force
  }
  Copy-Item -LiteralPath $SkillDir.FullName -Destination $dest -Recurse
  Write-Output "installed $($SkillDir.Name) -> $dest"
}

Get-ChildItem -LiteralPath $skills -Directory | ForEach-Object {
  Install-SkillDir -SkillDir $_
}

if ($IncludeAddons -and (Test-Path $addonPacks)) {
  Get-ChildItem -LiteralPath $addonPacks -Directory | ForEach-Object {
    $packSkills = Join-Path $_.FullName "skills"
    if (Test-Path $packSkills) {
      Get-ChildItem -LiteralPath $packSkills -Directory | ForEach-Object {
        Install-SkillDir -SkillDir $_
      }
    }
  }
}

Write-Output "done"
