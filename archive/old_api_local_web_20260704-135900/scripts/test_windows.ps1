param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Python = Join-Path $Root ".venv-win\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    python -m venv .venv-win
}

if ($Install) {
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r requirements.txt
}

& $Python -m pytest -q
