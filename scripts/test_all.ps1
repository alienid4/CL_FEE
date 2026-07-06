param(
    [switch]$IncludeUiDocuments,
    [switch]$IncludeUiImportPreview,
    [switch]$IncludeRuntimeFreshness,
    [switch]$IncludePromptPack,
    [switch]$IncludeAutomationFoundation,
    [switch]$IncludeSecurity,
    [switch]$IncludeAuditGate,
    [switch]$RequireAuditLog,
    [switch]$CheckNonLocalGuard,
    [switch]$FailOnSecurityWarnings,
    [string]$RuntimeBaseUrl = "http://127.0.0.1:8888"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

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

python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($IncludeUiDocuments) {
    $ArgsList = @("-ExecutionPolicy", "Bypass", "-File", "scripts\test_ui_documents.ps1", "-BaseUrl", $RuntimeBaseUrl)
    if ($CheckNonLocalGuard) {
        $ArgsList += "-CheckNonLocalGuard"
    }
    powershell @ArgsList
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($IncludeUiImportPreview) {
    powershell -ExecutionPolicy Bypass -File "scripts\test_ui_import_preview.ps1" -BaseUrl $RuntimeBaseUrl
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($IncludeRuntimeFreshness) {
    powershell -ExecutionPolicy Bypass -File "scripts\check_runtime_freshness.ps1" -BaseUrl $RuntimeBaseUrl
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($IncludeSecurity) {
    $SecurityArgs = @("-ExecutionPolicy", "Bypass", "-File", "scripts\security_check.ps1", "-IncludePytestCollect")
    if ($FailOnSecurityWarnings) {
        $SecurityArgs += "-FailOnWarnings"
    }
    powershell @SecurityArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
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

Write-Host "PASS: test_all completed."
