param(
    [string]$LogPath = "logs\agent_loop_audit.jsonl",
    [string]$OutputPath = "logs\agent_loop_audit_summary.md"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$LogFullPath = Join-Path $Root $LogPath
if (-not (Test-Path -LiteralPath $LogFullPath -PathType Leaf)) {
    Write-Error "FAIL: audit log not found: $LogPath"
    exit 1
}

$Entries = @()
$LineNumber = 0
foreach ($Line in Get-Content -LiteralPath $LogFullPath -Encoding UTF8) {
    $LineNumber += 1
    if ([string]::IsNullOrWhiteSpace($Line)) {
        continue
    }
    try {
        $Entries += ($Line | ConvertFrom-Json)
    } catch {
        Write-Error "FAIL: audit log line $LineNumber is not valid JSON."
        exit 2
    }
}

if ($Entries.Count -eq 0) {
    Write-Error "FAIL: audit log has no entries."
    exit 3
}

$OutputFullPath = Join-Path $Root $OutputPath
$OutputDir = Split-Path -Parent $OutputFullPath
if (-not (Test-Path -LiteralPath $OutputDir -PathType Container)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$Latest = $Entries[-1]
$PassCount = @($Entries | Where-Object { $_.audit_result -match "pass|completed|ok|not applicable" }).Count
$RiskCount = @($Entries | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.remaining_gap) }).Count

$Lines = New-Object System.Collections.Generic.List[string]
$GeneratedAt = (Get-Date).ToString("o")
$Lines.Add("# Agent Loop Audit Summary") | Out-Null
$Lines.Add("") | Out-Null
$Lines.Add("- Generated: $GeneratedAt") | Out-Null
$Lines.Add("- Log path: $LogPath") | Out-Null
$Lines.Add("- Total entries: $($Entries.Count)") | Out-Null
$Lines.Add("- Completed/pass-like entries: $PassCount") | Out-Null
$Lines.Add("- Entries with remaining gap: $RiskCount") | Out-Null
$Lines.Add("") | Out-Null
$Lines.Add("## Latest Entry") | Out-Null
$Lines.Add("") | Out-Null
$Lines.Add("- Timestamp: $($Latest.timestamp)") | Out-Null
$Lines.Add("- Goal: $($Latest.goal)") | Out-Null
$Lines.Add("- Classification: $($Latest.classification)") | Out-Null
$Lines.Add("- Audit result: $($Latest.audit_result)") | Out-Null
$Lines.Add("- Remaining gap: $($Latest.remaining_gap)") | Out-Null
$Lines.Add("- Next loop: $($Latest.next_loop)") | Out-Null
$Lines.Add("") | Out-Null
$Lines.Add("## Recent Entries") | Out-Null
$Lines.Add("") | Out-Null
$Lines.Add("| Timestamp | Classification | Goal | Audit | Next |") | Out-Null
$Lines.Add("| --- | --- | --- | --- | --- |") | Out-Null

$Recent = @($Entries | Select-Object -Last 10)
foreach ($Entry in $Recent) {
    $Goal = ([string]$Entry.goal).Replace("|", "/")
    $Next = ([string]$Entry.next_loop).Replace("|", "/")
    $Lines.Add("| $($Entry.timestamp) | $($Entry.classification) | $Goal | $($Entry.audit_result) | $Next |") | Out-Null
}

Set-Content -LiteralPath $OutputFullPath -Value $Lines -Encoding UTF8
Write-Host "PASS: wrote audit summary to $OutputPath"
