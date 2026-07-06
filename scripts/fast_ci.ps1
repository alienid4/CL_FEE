param(
    [switch]$IncludePromptPack,
    [switch]$IncludeAutomationFoundation,
    [switch]$IncludeAuditGate,
    [switch]$RequireAuditLog
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$StartedAt = Get-Date
Write-Host "FAST CI: started at $($StartedAt.ToString('s'))"

if ($IncludePromptPack) {
    powershell -ExecutionPolicy Bypass -File "scripts\check_prompt_pack.ps1"
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($IncludeAutomationFoundation) {
    powershell -ExecutionPolicy Bypass -File "scripts\check_automation_foundation.ps1"
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($IncludeAuditGate) {
    $AuditArgs = @("-ExecutionPolicy", "Bypass", "-File", "scripts\check_audit_gate.ps1")
    if ($RequireAuditLog) {
        $AuditArgs += "-RequireLog"
    }
    powershell @AuditArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$EndedAt = Get-Date
$Duration = [int](New-TimeSpan -Start $StartedAt -End $EndedAt).TotalSeconds
Write-Host "PASS: fast_ci completed in ${Duration}s."
