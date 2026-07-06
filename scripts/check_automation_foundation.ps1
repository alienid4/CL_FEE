param()

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$RequiredScripts = @(
    "scripts\check_prompt_pack.ps1",
    "scripts\security_check.ps1",
    "scripts\deep_security_check.ps1",
    "scripts\detect_project_profile.ps1",
    "scripts\agent_runtime_once.ps1",
    "scripts\fast_ci.ps1",
    "scripts\test_all.ps1",
    "scripts\local_ci.ps1",
    "scripts\write_agent_audit_log.ps1",
    "scripts\check_audit_gate.ps1",
    "scripts\summarize_agent_audit_log.ps1"
)

$MissingScripts = @()
foreach ($Script in $RequiredScripts) {
    if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) {
        $MissingScripts += $Script
    }
}

if ($MissingScripts.Count -gt 0) {
    Write-Error "FAIL: missing automation script(s): $($MissingScripts -join ', ')"
    exit 1
}

powershell -ExecutionPolicy Bypass -File "scripts\check_prompt_pack.ps1"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$AutoDevPath = Get-ChildItem -LiteralPath "docs" -Directory | Where-Object { $_.Name -like "*v2.2" } | Select-Object -First 1
if ($null -eq $AutoDevPath) {
    $AutoDevPath = Get-ChildItem -LiteralPath "docs" -Directory | Where-Object { $_.Name -like "*v2.1" } | Select-Object -First 1
}
if ($null -eq $AutoDevPath) {
    $AutoDevPath = Get-ChildItem -LiteralPath "docs" -Directory | Where-Object { $_.Name -like "*v2.0" } | Select-Object -First 1
}
if ($null -eq $AutoDevPath) {
    Write-Error "FAIL: prompt pack directory not found under docs."
    exit 2
}

$RequiredDocs = @("ALL_IN_ONE_BUILD_PACK.md", "AUTO_DEV_LOOP.md", "AGENT_AUDIT_RULES.md", "AGENT_RUNTIME_RULES.md", "GATE_CATALOG.md", "MVP_EVIDENCE_CHECKLIST.md", "PROJECT_PROFILE_RULES.md", "SECURITY_COMMANDS.md", "SPEED_RULES.md", "VERIFICATION_RULES.md")
foreach ($Doc in $RequiredDocs) {
    $Path = Join-Path $AutoDevPath.FullName $Doc
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Write-Error "FAIL: missing automation doc: $Doc"
        exit 3
    }
}

if (-not (Test-Path -LiteralPath ".github\workflows\local-ci.yml" -PathType Leaf)) {
    Write-Error "FAIL: missing platform CI workflow: .github\workflows\local-ci.yml"
    exit 4
}

Write-Host "PASS: automation foundation scripts and docs are present."
