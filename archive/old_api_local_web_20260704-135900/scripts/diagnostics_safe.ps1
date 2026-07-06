param(
  [string]$Target = ".",
  [string]$OutputDir = $env:TEMP
)

$ErrorActionPreference = "Stop"
$targetPath = Resolve-Path -LiteralPath $Target
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$out = Join-Path $OutputDir "project_diagnostics_safe_$stamp.json"

function Get-HashShort([string]$value) {
  if ([string]::IsNullOrWhiteSpace($value)) { return "" }
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($value)
  $hash = $sha.ComputeHash($bytes)
  -join ($hash[0..5] | ForEach-Object { $_.ToString("x2") })
}

$files = Get-ChildItem -LiteralPath $targetPath -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch "\\.git\\|\\node_modules\\|\\venv\\|\\.venv\\|__pycache__" }

$summary = [ordered]@{
  generated_at = (Get-Date).ToString("s")
  target_hash = Get-HashShort $targetPath.Path
  computer_hash = Get-HashShort $env:COMPUTERNAME
  user_hash = Get-HashShort $env:USERNAME
  file_count = @($files).Count
  top_extensions = @{}
  markers = [ordered]@{
    has_git = Test-Path (Join-Path $targetPath ".git")
    has_agents = Test-Path (Join-Path $targetPath "AGENTS.md")
    has_memory = Test-Path (Join-Path $targetPath "Memory.md")
    has_tests = Test-Path (Join-Path $targetPath "tests")
    has_package_json = Test-Path (Join-Path $targetPath "package.json")
    has_requirements = Test-Path (Join-Path $targetPath "requirements.txt")
    has_env_example = Test-Path (Join-Path $targetPath ".env.example")
  }
}

$extGroups = $files | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 15
foreach ($g in $extGroups) {
  $name = if ([string]::IsNullOrWhiteSpace($g.Name)) { "<no_ext>" } else { $g.Name }
  $summary.top_extensions[$name] = $g.Count
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Output "output=$out"

