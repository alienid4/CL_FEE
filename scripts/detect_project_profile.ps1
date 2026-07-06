param(
    [string]$OutputPath = "logs\project_profile.json"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path -LiteralPath "logs" -PathType Container)) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

$Languages = New-Object System.Collections.Generic.List[string]
$Frameworks = New-Object System.Collections.Generic.List[string]
$TestCommands = New-Object System.Collections.Generic.List[string]
$CiCommands = New-Object System.Collections.Generic.List[string]

if (Test-Path -LiteralPath "requirements.txt") {
    $Languages.Add("python") | Out-Null
    $Req = Get-Content -Raw -Encoding UTF8 -LiteralPath "requirements.txt"
    if ($Req -match "(?im)^fastapi") {
        $Frameworks.Add("fastapi") | Out-Null
    }
    if ($Req -match "(?im)^pytest") {
        $TestCommands.Add("python -m pytest tests -q") | Out-Null
        $TestCommands.Add("python -m pytest -q") | Out-Null
    }
}

if (Test-Path -LiteralPath "package.json") {
    $Languages.Add("node") | Out-Null
    $Package = Get-Content -Raw -Encoding UTF8 -LiteralPath "package.json"
    if ($Package -match '"test"\s*:') {
        $TestCommands.Add("npm test") | Out-Null
    }
}

if (Test-Path -LiteralPath "app\web" -PathType Container) {
    $Frameworks.Add("web-ui") | Out-Null
}

if (Test-Path -LiteralPath "scripts\fast_ci.ps1") {
    $CiCommands.Add("powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1") | Out-Null
}
if (Test-Path -LiteralPath "scripts\local_ci.ps1") {
    $CiCommands.Add("powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1") | Out-Null
}
if (Test-Path -LiteralPath "scripts\test_all.ps1") {
    $CiCommands.Add("powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludePromptPack -IncludeAutomationFoundation -IncludeSecurity") | Out-Null
}

$Profile = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    root = $Root.Path
    languages = @($Languages | Select-Object -Unique)
    frameworks = @($Frameworks | Select-Object -Unique)
    test_commands = @($TestCommands | Select-Object -Unique)
    ci_commands = @($CiCommands | Select-Object -Unique)
    risk_defaults = @(
        "Do not touch production data, credentials, deployment, irreversible migration, auth, or formal amount/status logic without user approval.",
        "Use Fast Lane only for low-risk locally verifiable fixes.",
        "Escalate DB, auth, import/export writeback, deployment, and security-sensitive work."
    )
}

$Json = $Profile | ConvertTo-Json -Depth 5
Set-Content -LiteralPath $OutputPath -Value $Json -Encoding UTF8
Write-Host "PASS: project profile written to $OutputPath"
Write-Host $Json
