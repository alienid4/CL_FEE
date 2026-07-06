param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8888,
    [string]$SqlitePath = "data/fee_control.db",
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if ($Install) {
    python -m pip install -r requirements.txt
}

$env:APP_HOST = $HostAddress
$env:APP_PORT = [string]$Port
$env:SQLITE_PATH = $SqlitePath

python -m uvicorn app.main:app --host $HostAddress --port $Port --reload

