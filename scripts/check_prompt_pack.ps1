param(
    [string]$PromptPackPath = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if ([string]::IsNullOrWhiteSpace($PromptPackPath)) {
    $Matches = @(Get-ChildItem -LiteralPath (Join-Path $Root "docs") -Directory | Where-Object { $_.Name -like "*v2.2" })
    if ($Matches.Count -eq 0) {
        $Matches = @(Get-ChildItem -LiteralPath (Join-Path $Root "docs") -Directory | Where-Object { $_.Name -like "*v2.1" })
    }
    if ($Matches.Count -eq 0) {
        $Matches = @(Get-ChildItem -LiteralPath (Join-Path $Root "docs") -Directory | Where-Object { $_.Name -like "*v2.0" })
    }
    if ($Matches.Count -ne 1) {
        Write-Error "FAIL: expected exactly one prompt pack directory matching v2.2/v2.1/v2.0 fallback, found $($Matches.Count)."
        exit 1
    }
    $Pack = $Matches[0].FullName
    $PromptPackPath = [System.IO.Path]::Combine("docs", $Matches[0].Name)
} else {
    $Pack = Join-Path $Root $PromptPackPath
}
if (-not (Test-Path -LiteralPath $Pack -PathType Container)) {
    Write-Error "FAIL: prompt pack directory not found: $PromptPackPath"
    exit 1
}

$RequiredFiles = @(
    "INDEX.md",
    "README.md",
    "ALL_IN_ONE_BUILD_PACK.md",
    "ONE_SHOT_DEV_PROMPT_v2.2_FINAL.md",
    "ONE_SHOT_DEV_PROMPT_v2.1_FINAL.md",
    "CURRENT_STATUS.md",
    "START_NEXT.md",
    "OPERATING_LOOP.md",
    "AUTO_DEV_LOOP.md",
    "AGENT_RUNTIME_RULES.md",
    "PROJECT_PROFILE_RULES.md",
    "SPEED_RULES.md",
    "DEVELOPMENT_RULES.md",
    "VERIFICATION_RULES.md",
    "MODULE_ROADMAP.md",
    "SECURITY_RULES.md",
    "SECURITY_SCAN_RULES.md",
    "SECURITY_COMMANDS.md",
    "AGENT_AUDIT_RULES.md",
    "UNIVERSAL_PROJECT_GUIDE.md",
    "CHANGELOG.md"
)

$Missing = @()
foreach ($File in $RequiredFiles) {
    $Path = Join-Path $Pack $File
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $Missing += $File
    }
}

if ($Missing.Count -gt 0) {
    Write-Error "FAIL: prompt pack missing required file(s): $($Missing -join ', ')"
    exit 2
}

$Checks = @(
    @{ File = "INDEX.md"; Pattern = "START_NEXT.md" },
    @{ File = "ALL_IN_ONE_BUILD_PACK.md"; Pattern = "CIO Build Mode" },
    @{ File = "ALL_IN_ONE_BUILD_PACK.md"; Pattern = "UI Mock Gate" },
    @{ File = "ALL_IN_ONE_BUILD_PACK.md"; Pattern = "HTML Mock" },
    @{ File = "ONE_SHOT_DEV_PROMPT_v2.1_FINAL.md"; Pattern = "CIO Build Mode" },
    @{ File = "ONE_SHOT_DEV_PROMPT_v2.1_FINAL.md"; Pattern = "UI Mock Gate" },
    @{ File = "ONE_SHOT_DEV_PROMPT_v2.1_FINAL.md"; Pattern = "HTML Mock Gate" },
    @{ File = "ONE_SHOT_DEV_PROMPT_v2.2_FINAL.md"; Pattern = "Data Model Gate" },
    @{ File = "ONE_SHOT_DEV_PROMPT_v2.2_FINAL.md"; Pattern = "Permission Matrix Gate" },
    @{ File = "ONE_SHOT_DEV_PROMPT_v2.2_FINAL.md"; Pattern = "Acceptance Case Gate" },
    @{ File = "ONE_SHOT_DEV_PROMPT_v2.2_FINAL.md"; Pattern = "Test Data Gate" },
    @{ File = "CURRENT_STATUS.md"; Pattern = "START_NEXT.md" },
    @{ File = "START_NEXT.md"; Pattern = "START_NEXT" },
    @{ File = "START_NEXT.md"; Pattern = "pytest" },
    @{ File = "OPERATING_LOOP.md"; Pattern = "LOOP" },
    @{ File = "AUTO_DEV_LOOP.md"; Pattern = "goal -> inspect -> plan -> change -> test -> audit -> update status -> next loop" },
    @{ File = "AGENT_RUNTIME_RULES.md"; Pattern = "agent_runtime_once.ps1" },
    @{ File = "PROJECT_PROFILE_RULES.md"; Pattern = "detect_project_profile.ps1" },
    @{ File = "SPEED_RULES.md"; Pattern = "Fast Lane" },
    @{ File = "SECURITY_COMMANDS.md"; Pattern = "rg -n" },
    @{ File = "AGENT_AUDIT_RULES.md"; Pattern = "pass/fail" },
    @{ File = "UNIVERSAL_PROJECT_GUIDE.md"; Pattern = "INDEX.md" },
    @{ File = "CHANGELOG.md"; Pattern = "v2.2" }
)

foreach ($Check in $Checks) {
    $Path = Join-Path $Pack $Check.File
    $Content = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
    if ($Content -notmatch [regex]::Escape($Check.Pattern)) {
        Write-Error "FAIL: $($Check.File) does not include required text: $($Check.Pattern)"
        exit 3
    }
}

Write-Host "PASS: prompt pack exists and includes all required files."
Write-Host "PASS: prompt pack key sections are present."
