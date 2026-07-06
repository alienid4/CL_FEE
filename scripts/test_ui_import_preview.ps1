param(
    [string]$BaseUrl = "http://127.0.0.1:8888",
    [switch]$InstallDeps,
    [switch]$InstallBrowsers,
    [switch]$AllowNonLocal,
    [switch]$Headed
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if ($InstallDeps) {
    python -m pip install -r requirements.txt
}

if ($InstallBrowsers) {
    python -m playwright install chromium
}

$ArgsList = @("tests/ui_import_preview_regression.py", "--base-url", $BaseUrl)
if ($AllowNonLocal) {
    $ArgsList += "--allow-non-local"
}
if ($Headed) {
    $ArgsList += "--headed"
}

python @ArgsList
