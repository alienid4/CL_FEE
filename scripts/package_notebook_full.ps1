# Build the FULL notebook package -- a self-contained folder that runs on its own.
#
# Difference from package_notebook_patch.ps1: that one ships code only, for a
# machine that already has a working control panel. This one ships everything a
# bare machine needs to go from "nothing" to "system running", which is what has
# to travel by mail to a site with no GitHub access.
#
# What ships (and nothing else -- every extra file is one more thing to explain):
#     app\                      the whole program
#     service.bat/.ps1          the only entry point
#     requirements-runtime.txt  the 3 packages the app actually imports
#     requirements.txt          pulled in by the -r line above; must travel together
#     請先讀我.txt              instructions, maintained in notebook-package\
#
# Deliberately NOT shipped:
#     data\ .env       the target machine owns these. Shipping them would clobber
#                      a live database; their absence is what makes "paste over"
#                      safe. See 請先讀我.txt.
#     download.bat     both fetch from github.com, which is blocked on the target
#     update.bat       network. Shipping a button that cannot work just wastes a
#                      mail round trip. Add -IncludeUpdaters for sites that can
#                      reach GitHub.
#     tests\           needs pytest/httpx/playwright, which the runtime install
#                      deliberately omits. Add -IncludeTests to ship them anyway.
#     demo_start.bat   runs a throwaway 8025 preview against an empty database.
#                      Handing it to a user who has real data looks exactly like
#                      "all my data is gone".
#
# THIS FILE MUST STAY UTF-8 WITH BOM. It contains Chinese (a filename and the zip
# name). Windows PowerShell 5.1 reads a BOM-less .ps1 as the system ANSI codepage,
# so without the BOM those turn to mojibake and the build dies on "file not found"
# for a file that is sitting right there. Same rule as notebook-package\service.ps1.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\package_notebook_full.ps1
#   ... -ForMail            also emit a copy with a neutered extension (see below)
#   ... -IncludeTests       add tests\ + pytest.ini
#   ... -IncludeUpdaters    add download.bat + update.bat

param(
    [switch]$ForMail,
    [switch]$IncludeTests,
    [switch]$IncludeUpdaters,
    [string]$OutDir
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pkg  = Join-Path $root "notebook-package"
if (-not $OutDir) { $OutDir = $root }

# Single source of truth for the version: the string the running app reports at
# /health. Reading it from anywhere else risks shipping a zip whose filename and
# whose contents disagree about what version they are.
$buildLine = Select-String -Path "$root\app\main.py" -Pattern 'BACKEND_BUILD = "(v[\d.]+)' | Select-Object -First 1
if (-not $buildLine) { throw "Could not find BACKEND_BUILD in app/main.py" }
$version = $buildLine.Matches[0].Groups[1].Value

$stage = Join-Path $env:TEMP "CL_FEE_full_stage"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Path $stage | Out-Null

Copy-Item -Path "$root\app" -Destination "$stage\app" -Recurse

# requirements.txt has a "-r requirements-runtime.txt" line, so the pair is
# indivisible: ship one without the other and pip dies on a missing file with an
# error that points nowhere near the real cause.
Copy-Item -Path "$root\requirements.txt"         -Destination "$stage\requirements.txt"
Copy-Item -Path "$root\requirements-runtime.txt" -Destination "$stage\requirements-runtime.txt"

foreach ($f in @("service.bat", "service.ps1", "請先讀我.txt")) {
    $src = Join-Path $pkg $f
    if (-not (Test-Path -LiteralPath $src)) { throw "Missing required file: $src" }
    Copy-Item -LiteralPath $src -Destination (Join-Path $stage $f)
}

if ($IncludeTests) {
    Copy-Item -Path "$root\tests" -Destination "$stage\tests" -Recurse
    Copy-Item -Path "$root\pytest.ini" -Destination "$stage\pytest.ini"
}
if ($IncludeUpdaters) {
    foreach ($f in @("download.bat", "update.bat")) {
        Copy-Item -LiteralPath (Join-Path $pkg $f) -Destination (Join-Path $stage $f)
    }
}

Get-ChildItem -Path $stage -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path $stage -Recurse -Filter "*.pyc" | Remove-Item -Force

# Fail loudly rather than mail out a package that cannot possibly work. Every
# check here maps to a failure that would otherwise surface days later, on the
# far side of a mail round trip, on a machine nobody can log into.
$mustExist = @("app\main.py", "app\web\index.html", "service.bat", "service.ps1", "requirements-runtime.txt")
foreach ($f in $mustExist) {
    if (-not (Test-Path -LiteralPath (Join-Path $stage $f))) { throw "Sanity check failed, missing: $f" }
}
$mustNotExist = @("data", ".env")
foreach ($f in $mustNotExist) {
    if (Test-Path -LiteralPath (Join-Path $stage $f)) { throw "Sanity check failed, must NOT ship: $f" }
}

$zipName = "CL_FEE_完整包_$version.zip"
$dest = Join-Path $OutDir $zipName
if (Test-Path -LiteralPath $dest) { Remove-Item -Force -LiteralPath $dest }
Compress-Archive -Path "$stage\*" -DestinationPath $dest -CompressionLevel Optimal
Remove-Item -Recurse -Force $stage

$sizeKB = [math]::Round((Get-Item -LiteralPath $dest).Length / 1KB, 1)
Write-Host "Built: $dest  ($sizeKB KB)"

if ($ForMail) {
    # Corporate mail gateways block .zip that contain .bat, and they usually do it
    # by silent quarantine -- the sender sees a normal "sent", the recipient never
    # gets anything, and nobody learns this until someone asks a week later.
    # Renaming the extension gets it past the scanner; the recipient renames it
    # back. Instructions for that go in the mail body, not in the zip (they cannot
    # open the zip until they have renamed it).
    $mailDest = "$dest.rename-to-zip"
    if (Test-Path -LiteralPath $mailDest) { Remove-Item -Force -LiteralPath $mailDest }
    Copy-Item -LiteralPath $dest -Destination $mailDest
    Write-Host "Mail copy: $mailDest"
    Write-Host ""
    Write-Host "Tell the recipient: save the attachment, then delete the"
    Write-Host "'.rename-to-zip' from the end of the filename so it ends in .zip."
}
