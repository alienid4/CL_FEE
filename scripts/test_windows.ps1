param(
    [string]$PytestTarget = "tests",
    [switch]$IncludeUiLifecycle,
    [switch]$IncludeUiDocuments,
    [switch]$CheckNonLocalGuard,
    [switch]$IncludeRuntimeFreshness,
    [string]$RuntimeBaseUrl = "http://127.0.0.1:8888"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

python -m pytest $PytestTarget -q
$PytestExitCode = $LASTEXITCODE
if ($PytestExitCode -ne 0) {
    exit $PytestExitCode
}

if ($IncludeUiLifecycle -or $IncludeUiDocuments) {
    $UiArgs = @("-ExecutionPolicy", "Bypass", "-File", "scripts\test_ui_documents.ps1")
    if ($CheckNonLocalGuard) {
        $UiArgs += "-CheckNonLocalGuard"
    }
    powershell @UiArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($IncludeRuntimeFreshness) {
    powershell -ExecutionPolicy Bypass -File "scripts\check_runtime_freshness.ps1" -BaseUrl $RuntimeBaseUrl
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
