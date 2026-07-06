param(
    [Parameter(Mandatory = $true)]
    [string]$Goal,
    [ValidateSet("fast", "standard", "release")]
    [string]$Lane = "fast"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path -LiteralPath "logs" -PathType Container)) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

$StartedAt = Get-Date
$StatePath = "logs\agent_runtime_state.json"
$Status = "started"
$Verification = ""
$Classification = "small"
if ($Lane -eq "standard") {
    $Classification = "medium"
} elseif ($Lane -eq "release") {
    $Classification = "large"
}

function Write-State {
    param([string]$CurrentStatus)
    $State = [ordered]@{
        goal = $Goal
        lane = $Lane
        status = $CurrentStatus
        started_at = $StartedAt.ToString("s")
        updated_at = (Get-Date).ToString("s")
        state_file = $StatePath
    }
    $State | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $StatePath -Encoding UTF8
}

Write-State -CurrentStatus "detecting_profile"
powershell -ExecutionPolicy Bypass -File "scripts\detect_project_profile.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-State -CurrentStatus "profile_failed"
    exit $LASTEXITCODE
}

Write-State -CurrentStatus "running_$Lane"
if ($Lane -eq "fast") {
    powershell -ExecutionPolicy Bypass -File "scripts\fast_ci.ps1" -IncludePromptPack
    $Verification = "fast_ci with prompt pack"
} elseif ($Lane -eq "standard") {
    powershell -ExecutionPolicy Bypass -File "scripts\local_ci.ps1"
    $Verification = "local_ci"
} else {
    powershell -ExecutionPolicy Bypass -File "scripts\test_all.ps1" -IncludePromptPack -IncludeAutomationFoundation -IncludeSecurity
    $Verification = "test_all prompt/foundation/security"
}

if ($LASTEXITCODE -ne 0) {
    Write-State -CurrentStatus "verification_failed"
    exit $LASTEXITCODE
}

Write-State -CurrentStatus "writing_audit"
powershell -ExecutionPolicy Bypass -File "scripts\write_agent_audit_log.ps1" -Goal $Goal -Classification $Classification -Verification $Verification -AuditResult "pass" -RemainingGap "Runtime executes verification and audit; code edits still occur in the active Codex loop." -NextLoop "Continue the next safe backlog item using the selected speed lane."
if ($LASTEXITCODE -ne 0) {
    Write-State -CurrentStatus "audit_write_failed"
    exit $LASTEXITCODE
}

powershell -ExecutionPolicy Bypass -File "scripts\check_audit_gate.ps1" -RequireLog
if ($LASTEXITCODE -ne 0) {
    Write-State -CurrentStatus "audit_gate_failed"
    exit $LASTEXITCODE
}

Write-State -CurrentStatus "completed"
Write-Host "PASS: agent runtime completed one verified loop."
Write-Host "State: $StatePath"
