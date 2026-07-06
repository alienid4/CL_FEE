param(
    [Parameter(Mandatory = $true)]
    [string]$Goal,

    [ValidateSet("small", "medium", "large", "high-risk")]
    [string]$Classification = "small",

    [string[]]$ChangedFiles = @(),
    [string[]]$Verification = @(),
    [string]$AuditResult = "",
    [string]$RemainingGap = "",
    [string]$NextLoop = "",
    [string]$LogPath = "logs\agent_loop_audit.jsonl"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$LogFullPath = Join-Path $Root $LogPath
$LogDir = Split-Path -Parent $LogFullPath
if (-not (Test-Path -LiteralPath $LogDir -PathType Container)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$SensitivePattern = '(?i)(password|passwd|secret|token|api[_-]?key|private key|BEGIN RSA|BEGIN OPENSSH|BEGIN PRIVATE)'
$FieldsToCheck = @($Goal, $AuditResult, $RemainingGap, $NextLoop) + $ChangedFiles + $Verification
foreach ($Field in $FieldsToCheck) {
    if ($null -ne $Field -and $Field -match $SensitivePattern) {
        Write-Error "Refusing to write audit log because input may contain sensitive text."
        exit 2
    }
}

$Entry = [ordered]@{
    timestamp = (Get-Date).ToString("o")
    goal = $Goal
    classification = $Classification
    changed_files = $ChangedFiles
    verification = $Verification
    audit_result = $AuditResult
    remaining_gap = $RemainingGap
    next_loop = $NextLoop
}

$Json = $Entry | ConvertTo-Json -Compress -Depth 5
Add-Content -LiteralPath $LogFullPath -Value $Json -Encoding UTF8
Write-Host "PASS: wrote audit log entry to $LogPath"
