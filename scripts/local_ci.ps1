param(
    [switch]$IncludeUiDocuments,
    [switch]$IncludeUiImportPreview,
    [switch]$IncludeRuntimeFreshness,
    [switch]$IncludeAuditGate,
    [switch]$RequireAuditLog,
    [switch]$CheckNonLocalGuard,
    [switch]$FailOnSecurityWarnings,
    [string]$RuntimeBaseUrl = "http://127.0.0.1:8888"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "Local CI: prompt pack, automation foundation, tests, and security checks."

$ArgsList = @(
    "-ExecutionPolicy", "Bypass",
    "-File", "scripts\test_all.ps1",
    "-IncludePromptPack",
    "-IncludeAutomationFoundation",
    "-IncludeSecurity",
    "-RuntimeBaseUrl", $RuntimeBaseUrl
)

if ($IncludeUiDocuments) {
    $ArgsList += "-IncludeUiDocuments"
}
if ($IncludeUiImportPreview) {
    $ArgsList += "-IncludeUiImportPreview"
}
if ($IncludeRuntimeFreshness) {
    $ArgsList += "-IncludeRuntimeFreshness"
}
if ($IncludeAuditGate) {
    $ArgsList += "-IncludeAuditGate"
}
if ($RequireAuditLog) {
    $ArgsList += "-RequireAuditLog"
}
if ($CheckNonLocalGuard) {
    $ArgsList += "-CheckNonLocalGuard"
}
if ($FailOnSecurityWarnings) {
    $ArgsList += "-FailOnSecurityWarnings"
}

powershell @ArgsList
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "PASS: local CI completed."
