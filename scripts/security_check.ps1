param(
    [switch]$IncludePytestCollect,
    [switch]$FailOnWarnings
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Warnings = New-Object System.Collections.Generic.List[string]

function Add-Warning {
    param([string]$Message)
    $Warnings.Add($Message) | Out-Null
    Write-Warning $Message
}

Write-Host "Security check: workspace hygiene"
git status --short
if ($LASTEXITCODE -ne 0) {
    Add-Warning "git status failed."
}

git diff --check
if ($LASTEXITCODE -ne 0) {
    Add-Warning "git diff --check reported issues."
}

Write-Host "Security check: .gitignore coverage"
$GitIgnore = Get-Content -Raw -Encoding UTF8 ".gitignore"
$RequiredIgnorePatterns = @(".env", "data/*.db", "*.pdf", "*.xlsx", "*.xls", "*.csv", "*.tsv", "logs/")
foreach ($Pattern in $RequiredIgnorePatterns) {
    if ($GitIgnore -notmatch [regex]::Escape($Pattern)) {
        Add-Warning ".gitignore may be missing pattern: $Pattern"
    }
}

Write-Host "Security check: high-confidence secret patterns"
$ScanRoots = @("app", "tests", "scripts", ".github", "requirements.txt")
$CandidateFiles = @()
foreach ($ScanRoot in $ScanRoots) {
    if (Test-Path -LiteralPath $ScanRoot) {
        $Item = Get-Item -LiteralPath $ScanRoot
        if ($Item.PSIsContainer) {
            $CandidateFiles += Get-ChildItem -LiteralPath $ScanRoot -Recurse -File
        } else {
            $CandidateFiles += $Item
        }
    }
}

$SecretPattern = '(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*["'']?[^"''\s]{8,}|BEGIN (RSA|OPENSSH|PRIVATE) KEY'
$SecretMatches = @()
foreach ($File in $CandidateFiles) {
    $RelativePath = Resolve-Path -LiteralPath $File.FullName -Relative
    $RelativePath = $RelativePath.TrimStart(".", "\", "/")
    if ($RelativePath -eq "scripts\security_check.ps1") {
        continue
    }
    $Matches = Select-String -LiteralPath $File.FullName -Pattern $SecretPattern -AllMatches -ErrorAction SilentlyContinue
    foreach ($Match in $Matches) {
        $SecretMatches += "${RelativePath}:$($Match.LineNumber)"
    }
}

if ($SecretMatches.Count -gt 0) {
    Add-Warning "Potential high-confidence secret match(es): $($SecretMatches -join ', ')"
} else {
    Write-Host "PASS: no high-confidence secret patterns found in app/tests/scripts/.github/requirements."
}

Write-Host "Security check: archive misuse in runtime paths"
$ArchivePattern = "old_api_local_web|archive/old_api|archive\\old_api"
$RuntimePaths = @("app", "tests", "scripts")
$ArchiveMatches = @()
foreach ($RuntimePath in $RuntimePaths) {
    if (Test-Path -LiteralPath $RuntimePath) {
        $RuntimeFiles = Get-ChildItem -LiteralPath $RuntimePath -Recurse -File
        $Matches = foreach ($RuntimeFile in $RuntimeFiles) {
            $RelativeRuntimePath = Resolve-Path -LiteralPath $RuntimeFile.FullName -Relative
            $RelativeRuntimePath = $RelativeRuntimePath.TrimStart(".", "\", "/")
            if ($RelativeRuntimePath -eq "scripts\security_check.ps1") {
                continue
            }
            Select-String -LiteralPath $RuntimeFile.FullName -Pattern $ArchivePattern -ErrorAction SilentlyContinue
        }
        foreach ($Match in $Matches) {
            $ArchiveMatches += "$($Match.Path):$($Match.LineNumber)"
        }
    }
}

if ($ArchiveMatches.Count -gt 0) {
    Add-Warning "Archive reference found in runtime path(s): $($ArchiveMatches -join ', ')"
} else {
    Write-Host "PASS: no archive references found in app/tests/scripts."
}

if ($IncludePytestCollect) {
    Write-Host "Security check: pytest collection excludes archive"
    $CollectOutput = & python -m pytest --collect-only -q 2>&1
    $CollectExit = $LASTEXITCODE
    $CollectText = ($CollectOutput | Out-String)
    if ($CollectExit -ne 0) {
        Add-Warning "pytest --collect-only failed."
    } elseif ($CollectText -match "archive[/\\]") {
        Add-Warning "pytest collection includes archive tests."
    } else {
        Write-Host "PASS: pytest collection does not include archive paths."
    }
}

python -m pip check
if ($LASTEXITCODE -ne 0) {
    Add-Warning "pip check reported dependency issues."
} else {
    Write-Host "PASS: pip check passed."
}

if ($Warnings.Count -gt 0) {
    Write-Host "Security check completed with warning(s): $($Warnings.Count)"
    if ($FailOnWarnings) {
        exit 10
    }
} else {
    Write-Host "PASS: security check completed without warnings."
}
