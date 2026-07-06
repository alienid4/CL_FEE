param(
    [string]$BaseUrl = "http://127.0.0.1:8888",
    [switch]$InstallDeps,
    [switch]$InstallBrowsers,
    [switch]$CheckNonLocalGuard,
    [switch]$AllowNonLocal,
    [switch]$Headed
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if ($InstallDeps) {
    python -m pip install -r requirements.txt
}

if ($InstallBrowsers) {
    python -m playwright install chromium
}

$ArgsList = @("tests/ui_documents_regression.py", "--base-url", $BaseUrl)
if ($AllowNonLocal) {
    $ArgsList += "--allow-non-local"
}
if ($Headed) {
    $ArgsList += "--headed"
}

python @ArgsList
$MainExitCode = $LASTEXITCODE
if ($MainExitCode -ne 0) {
    exit $MainExitCode
}

if ($CheckNonLocalGuard) {
    $GuardArgs = @("tests/ui_documents_regression.py", "--base-url", "http://example.com")
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $GuardOutput = & python @GuardArgs 2>&1
        $GuardExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }
    if ($GuardExitCode -eq 0) {
        throw "Expected non-local base URL guard to fail for http://example.com, but it passed."
    }
    $GuardText = ($GuardOutput | Out-String).Trim()
    if ($GuardText -notmatch "is not local") {
        throw "Expected non-local base URL guard message was not found. Output: $GuardText"
    }
    $global:LASTEXITCODE = 0
    Write-Host "Non-local base URL guard passed: http://example.com was blocked as expected."
}
