param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8888,
    [string]$SqlitePath = "data/dev.db",
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Python = Join-Path $Root ".venv-win\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    python -m venv .venv-win
}

if ($Install) {
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r requirements.txt
}

$env:APP_HOST = $HostAddress
$env:APP_PORT = [string]$Port
$env:SQLITE_PATH = $SqlitePath

Write-Host "Starting Fee Contract Control on http://$HostAddress`:$Port"
& $Python -m uvicorn app.main:app --host $HostAddress --port $Port --reload
