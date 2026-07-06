param(
    [switch]$IncludeDast,
    [switch]$FailOnMissingTools,
    [string]$BaseUrl = "http://127.0.0.1:8888"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Warnings = New-Object System.Collections.Generic.List[string]

function Add-ScanWarning {
    param([string]$Message)
    $Warnings.Add($Message) | Out-Null
    Write-Warning $Message
}

function Invoke-OptionalCommand {
    param(
        [string]$Name,
        [string[]]$CommandLine
    )
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Add-ScanWarning "Optional security tool not installed: $Name"
        return
    }
    Write-Host "Security tool: $Name"
    & $CommandLine[0] @($CommandLine | Select-Object -Skip 1)
    if ($LASTEXITCODE -ne 0) {
        Add-ScanWarning "$Name reported findings or failed."
    }
}

Write-Host "Deep security check: baseline"
powershell -ExecutionPolicy Bypass -File "scripts\security_check.ps1" -IncludePytestCollect
if ($LASTEXITCODE -ne 0) {
    Add-ScanWarning "baseline security_check failed."
}

Write-Host "Deep security check: optional white-box tools"
Invoke-OptionalCommand -Name "bandit" -CommandLine @("bandit", "-r", "app", "-q")
Invoke-OptionalCommand -Name "pip-audit" -CommandLine @("pip-audit", "-r", "requirements.txt")
Invoke-OptionalCommand -Name "semgrep" -CommandLine @("semgrep", "scan", "--config", "auto", "app", "tests", "scripts")

if ($IncludeDast) {
    if ($BaseUrl -notmatch '^https?://(127\.0\.0\.1|localhost)(:\d+)?(/.*)?$') {
        Write-Error "FAIL: DAST is allowed only for localhost by default. Refusing BaseUrl: $BaseUrl"
        exit 20
    }
    Write-Host "Deep security check: local-only DAST smoke"
    try {
        $Response = Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 10
        if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500) {
            Write-Host "PASS: local DAST smoke reached $BaseUrl with status $($Response.StatusCode)."
        } else {
            Add-ScanWarning "local DAST smoke returned status $($Response.StatusCode)."
        }
    } catch {
        Add-ScanWarning "local DAST smoke failed: $($_.Exception.Message)"
    }
}

if ($Warnings.Count -gt 0) {
    Write-Host "Deep security check completed with warning(s): $($Warnings.Count)"
    if ($FailOnMissingTools) {
        exit 11
    }
} else {
    Write-Host "PASS: deep security check completed without warnings."
}
