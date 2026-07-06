param(
    [string]$VmHost = "192.168.187.51",
    [string]$VmUser = "root",
    [string]$RemotePath = "/opt/ai_fee",
    [string]$ServiceName = "ai-fee-api.service",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not $SkipTests) {
    & (Join-Path $PSScriptRoot "test_windows.ps1")
}

$Target = "$VmUser@$VmHost"
Write-Host "Deploying to ${Target}:$RemotePath"

ssh $Target "mkdir -p $RemotePath"
scp -r app docs tests scripts requirements.txt "${Target}:$RemotePath/"

ssh $Target "cd $RemotePath && .venv/bin/python -m pip install -r requirements.txt && .venv/bin/python -m pytest -q && systemctl restart $ServiceName && sleep 1 && systemctl is-active $ServiceName && curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8888/"
