# Package a code-only patch zip for the Notebook copy (no git remote there).
# Deliberately excludes data/*.db and .env so extracting-over on the Notebook
# never clobbers its own test data or password config.
# Usage: pwsh scripts/package_notebook_patch.ps1
#   Output: CL_FEE_patch_<version>.zip in the repo root (version read from app/main.py BACKEND_BUILD)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$buildLine = Select-String -Path "$root\app\main.py" -Pattern 'BACKEND_BUILD = "(v[\d.]+)' | Select-Object -First 1
if (-not $buildLine) { throw "Could not find BACKEND_BUILD in app/main.py" }
$version = ($buildLine.Matches[0].Groups[1].Value) -replace '\.', '-'

$stage = "$env:TEMP\CL_FEE_patch_stage"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Path $stage | Out-Null

# Code + tests only. Do NOT include data/, .env, .claude -- Notebook keeps its own.
Copy-Item -Path "$root\app" -Destination "$stage\app" -Recurse
Copy-Item -Path "$root\tests" -Destination "$stage\tests" -Recurse
Copy-Item -Path "$root\requirements.txt" -Destination "$stage\requirements.txt"
# Must ship alongside requirements.txt, which pulls it in with a -r line.
Copy-Item -Path "$root\requirements-runtime.txt" -Destination "$stage\requirements-runtime.txt"
Copy-Item -Path "$root\pytest.ini" -Destination "$stage\pytest.ini"

Get-ChildItem -Path $stage -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path $stage -Recurse -Filter "*.pyc" | Remove-Item -Force

$dest = "$root\CL_FEE_patch_$version.zip"
if (Test-Path $dest) { Remove-Item -Force $dest }
Compress-Archive -Path "$stage\*" -DestinationPath $dest -CompressionLevel Optimal
Remove-Item -Recurse -Force $stage

Write-Host "Done: $dest"
Get-Item $dest | Select-Object Name, @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}}
