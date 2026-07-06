param(
    [string]$LogPath = "logs\agent_loop_audit.jsonl",
    [switch]$RequireLog,
    [switch]$SkipUiTextCheck
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$PromptPack = Get-ChildItem -LiteralPath (Join-Path $Root "docs") -Directory | Where-Object { $_.Name -like "*v2.2" } | Select-Object -First 1
if ($null -eq $PromptPack) {
    $PromptPack = Get-ChildItem -LiteralPath (Join-Path $Root "docs") -Directory | Where-Object { $_.Name -like "*v2.1" } | Select-Object -First 1
}
if ($null -eq $PromptPack) {
    $PromptPack = Get-ChildItem -LiteralPath (Join-Path $Root "docs") -Directory | Where-Object { $_.Name -like "*v2.0" } | Select-Object -First 1
}
if ($null -eq $PromptPack) {
    Write-Error "FAIL: audit gate could not find prompt pack directory."
    exit 1
}

$RequiredGateDocs = @("CURRENT_STATUS.md", "START_NEXT.md", "GATE_CATALOG.md", "AGENT_AUDIT_RULES.md")
foreach ($Doc in $RequiredGateDocs) {
    $Path = Join-Path $PromptPack.FullName $Doc
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Write-Error "FAIL: audit gate missing required gate document: $Doc"
        exit 1
    }
}

$StartNextContent = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $PromptPack.FullName "START_NEXT.md")
if ($StartNextContent -notmatch "pytest") {
    Write-Error "FAIL: START_NEXT.md must include at least one pytest verification command."
    exit 1
}

$LogFullPath = Join-Path $Root $LogPath

if (-not (Test-Path -LiteralPath $LogFullPath -PathType Leaf)) {
    if ($RequireLog) {
        Write-Error "FAIL: audit gate requires a log file, but it was not found: $LogPath"
        exit 1
    }
    Write-Host "SKIP: audit log not found. Use -RequireLog when a completed loop must have audit evidence."
    exit 0
}

$Lines = @(Get-Content -LiteralPath $LogFullPath -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($Lines.Count -eq 0) {
    Write-Error "FAIL: audit log exists but has no entries: $LogPath"
    exit 2
}

$LastLine = $Lines[-1]
try {
    $Entry = $LastLine | ConvertFrom-Json
} catch {
    Write-Error "FAIL: last audit log line is not valid JSON."
    exit 3
}

$RequiredFields = @("timestamp", "goal", "classification", "changed_files", "verification", "audit_result", "remaining_gap", "next_loop")
$Missing = @()
foreach ($Field in $RequiredFields) {
    if (-not ($Entry.PSObject.Properties.Name -contains $Field)) {
        $Missing += $Field
    }
}

if ($Missing.Count -gt 0) {
    Write-Error "FAIL: last audit log entry missing field(s): $($Missing -join ', ')"
    exit 4
}

if ([string]::IsNullOrWhiteSpace([string]$Entry.goal)) {
    Write-Error "FAIL: last audit log entry has empty goal."
    exit 5
}

if ([string]::IsNullOrWhiteSpace([string]$Entry.audit_result)) {
    Write-Error "FAIL: last audit log entry has empty audit_result."
    exit 6
}

if ($Entry.audit_result -notmatch "pass|completed|ok|not applicable") {
    Write-Error "FAIL: last audit_result does not look like a completed audit result: $($Entry.audit_result)"
    exit 7
}

if ($Entry.audit_result -match "pass|completed|ok") {
    if ($null -eq $Entry.verification -or $Entry.verification.Count -eq 0) {
        Write-Error "FAIL: completed audit entry must include verification evidence."
        exit 8
    }
    if ([string]::IsNullOrWhiteSpace([string]$Entry.next_loop)) {
        Write-Error "FAIL: completed audit entry must include next_loop."
        exit 9
    }
}

if (-not $SkipUiTextCheck) {
    $UiPath = Join-Path $Root "app\web"
    if (Test-Path -LiteralPath $UiPath -PathType Container) {
        $UiFiles = Get-ChildItem -LiteralPath $UiPath -Recurse -File -Include *.html,*.js,*.css
        $BlockedUiPattern = '(?i)(TODO|FIXME|HACK|Prompt|Agent|debug|test-only|internal note|under construction|lorem ipsum)'
        $UiMatches = @()
        foreach ($UiFile in $UiFiles) {
            $Matches = Select-String -LiteralPath $UiFile.FullName -Pattern $BlockedUiPattern -ErrorAction SilentlyContinue
            foreach ($Match in $Matches) {
                $RelativePath = Resolve-Path -LiteralPath $Match.Path -Relative
                $RelativePath = $RelativePath.TrimStart(".", "\", "/")
                $UiMatches += "${RelativePath}:$($Match.LineNumber):$($Match.Line.Trim())"
            }
        }

        if ($UiMatches.Count -gt 0) {
            Write-Error "FAIL: UI text gate found internal/commentary marker(s) that may be visible or shipped: $($UiMatches -join ' | ')"
            exit 10
        }
        Write-Host "PASS: UI text gate found no blocked internal markers in app/web."

        $IndexPath = Join-Path $UiPath "index.html"
        if (Test-Path -LiteralPath $IndexPath -PathType Leaf) {
            $IndexContent = Get-Content -Raw -Encoding UTF8 -LiteralPath $IndexPath
            if ($IndexContent -notmatch 'name="viewport"\s+content="width=1500') {
                Write-Error "FAIL: UI product gate requires desktop viewport width=1500; mobile-first viewport is not allowed for this product."
                exit 11
            }
            $ForbiddenProductUiText = @(
                "檢視角色",
                "使用者：",
                "DEMO",
                "Demo",
                "demo",
                "Contract code",
                "Contract name",
                "Vendor",
                "Amount",
                "Dashboard",
                "Project",
                "Budget_ID",
                "formal confirm",
                "commit",
                ">alert<",
                "File name",
                ">Draft<",
                ">Reviewing<",
                ">Disabled<",
                ">Active<",
                ">Pending<"
            )
            $ProductUiHits = @()
            foreach ($Forbidden in $ForbiddenProductUiText) {
                if ($IndexContent.Contains($Forbidden)) {
                    $ProductUiHits += $Forbidden
                }
            }
            if ($ProductUiHits.Count -gt 0) {
                Write-Error "FAIL: UI product gate found demo role switch or English operator wording in index.html: $($ProductUiHits -join ', ')"
                exit 12
            }
            Write-Host "PASS: UI product gate confirms desktop viewport, no demo role switch, and Chinese static UI labels."

            $RequiredModuleIds = @(
                'id="cases-module"',
                'id="budget"',
                'id="projects"',
                'id="signoff"',
                'id="contracts-module"',
                'id="purchases"',
                'id="payments-module"',
                'id="data-review"'
            )
            $MissingModuleIds = @()
            foreach ($RequiredModuleId in $RequiredModuleIds) {
                if (-not $IndexContent.Contains($RequiredModuleId)) {
                    $MissingModuleIds += $RequiredModuleId
                }
            }
            if ($MissingModuleIds.Count -gt 0) {
                Write-Error "FAIL: UI product gate missing required module checkpoint id(s): $($MissingModuleIds -join ', ')"
                exit 13
            }
            Write-Host "PASS: UI product gate confirms required module checkpoint ids."
        }
    }
}

Write-Host "PASS: audit gate found a valid latest audit log entry."
Write-Host "Latest audit goal: $($Entry.goal)"
