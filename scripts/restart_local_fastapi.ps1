param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8888,
    [string]$SqlitePath = "data/fee_control.db",
    [int]$StartupTimeoutSec = 30
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$AppMain = Join-Path $Root "app\main.py"

if (-not (Test-Path -LiteralPath $AppMain)) {
    Write-Error "FAIL: app\main.py was not found under $Root"
    exit 2
}

function Get-LocalPortOwners {
    param([int]$TargetPort)

    $ownerIds = New-Object System.Collections.Generic.HashSet[int]

    $connections = @(Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue)
    foreach ($connection in $connections) {
        [void]$ownerIds.Add([int]$connection.OwningProcess)
    }

    $netstatLines = @(netstat -ano | Select-String (":$TargetPort\s+.*LISTENING\s+\d+"))
    foreach ($line in $netstatLines) {
        if ($line.Line -match "LISTENING\s+(\d+)\s*$") {
            [void]$ownerIds.Add([int]$Matches[1])
        }
    }

    foreach ($ownerId in $ownerIds) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ownerId" -ErrorAction SilentlyContinue
        if ($null -eq $process) {
            [PSCustomObject]@{
                ProcessId = [int]$ownerId
                CommandLine = ""
                ExecutablePath = ""
                IsInspectable = $false
            }
        } else {
            [PSCustomObject]@{
                ProcessId = [int]$process.ProcessId
                CommandLine = [string]$process.CommandLine
                ExecutablePath = [string]$process.ExecutablePath
                IsInspectable = $true
            }
        }
    }
}

function Test-IsAiFeeUvicorn {
    param([string]$CommandLine)

    if ([string]::IsNullOrWhiteSpace($CommandLine)) {
        return $false
    }

    return ($CommandLine -match "uvicorn") -and ($CommandLine -match "app\.main:app")
}

Write-Host "Restarting AI_FEE FastAPI runtime on ${HostAddress}:${Port}"

$owners = @(Get-LocalPortOwners -TargetPort $Port)
foreach ($owner in $owners) {
    if (-not $owner.IsInspectable) {
        Write-Error "FAIL: port $Port is owned by PID $($owner.ProcessId), but Windows did not expose process metadata. Refusing to stop an uninspectable process."
        exit 3
    }

    if (Test-IsAiFeeUvicorn -CommandLine $owner.CommandLine) {
        Write-Host "Stopping existing AI_FEE uvicorn process PID $($owner.ProcessId)."
        Stop-Process -Id $owner.ProcessId -Force -ErrorAction SilentlyContinue
    } else {
        Write-Error "FAIL: port $Port is owned by non-AI_FEE process PID $($owner.ProcessId): $($owner.CommandLine)"
        exit 3
    }
}

Start-Sleep -Milliseconds 800

$remainingOwners = @(Get-LocalPortOwners -TargetPort $Port)
if ($remainingOwners.Count -gt 0) {
    Write-Error "FAIL: port $Port is still occupied after cleanup."
    exit 4
}

$env:APP_HOST = $HostAddress
$env:APP_PORT = [string]$Port
$env:SQLITE_PATH = $SqlitePath

$process = Start-Process `
    -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", $HostAddress, "--port", [string]$Port) `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Started AI_FEE FastAPI process PID $($process.Id)."

$healthUrl = "http://${HostAddress}:${Port}/health"
$openApiUrl = "http://${HostAddress}:${Port}/openapi.json"
$deadline = (Get-Date).AddSeconds($StartupTimeoutSec)

while ((Get-Date) -lt $deadline) {
    try {
        $health = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3
        if ($health.StatusCode -eq 200) {
            $openapi = Invoke-RestMethod -Uri $openApiUrl -TimeoutSec 5
            $paths = @($openapi.paths.PSObject.Properties.Name)
            if ("/api/import-batches/{batch_id}/confirm-preflight" -notin $paths) {
                Write-Error "FAIL: runtime started but confirm-preflight endpoint is missing."
                exit 5
            }

            Write-Host "PASS: runtime is fresh at $healthUrl"
            Write-Host "PASS: OpenAPI includes /api/import-batches/{batch_id}/confirm-preflight"
            exit 0
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

Write-Error "FAIL: runtime did not become healthy within $StartupTimeoutSec seconds."
exit 6
