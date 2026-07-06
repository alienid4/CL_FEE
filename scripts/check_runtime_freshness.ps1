param(
    [string]$BaseUrl = "http://127.0.0.1:8888",
    [string[]]$RequiredEndpoints = @(
        "/api/audit-logs",
        "/api/import-batches",
        "/api/import-batches/{batch_id}/rows",
        "/api/import-mapping-draft",
        "/api/import-batches/{batch_id}/confirm",
        "/api/import-batches/{batch_id}/confirm-preflight"
    )
)

$ErrorActionPreference = "Stop"

function Join-ApiUrl {
    param(
        [string]$RootUrl,
        [string]$Path
    )

    return $RootUrl.TrimEnd("/") + "/" + $Path.TrimStart("/")
}

Write-Host "Runtime freshness check: $BaseUrl"

$healthUrl = Join-ApiUrl -RootUrl $BaseUrl -Path "/health"
try {
    $healthResponse = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
} catch {
    Write-Error "FAIL: /health request failed at ${healthUrl}: $($_.Exception.Message)"
    exit 2
}

if ($healthResponse.StatusCode -ne 200) {
    Write-Error "FAIL: /health returned HTTP $($healthResponse.StatusCode)."
    exit 2
}

Write-Host "PASS: /health returned HTTP 200."

$openApiUrl = Join-ApiUrl -RootUrl $BaseUrl -Path "/openapi.json"
try {
    $openApiResponse = Invoke-RestMethod -Uri $openApiUrl -TimeoutSec 10
} catch {
    Write-Error "FAIL: /openapi.json request failed at ${openApiUrl}: $($_.Exception.Message)"
    exit 3
}

if ($null -eq $openApiResponse.paths) {
    Write-Error "FAIL: /openapi.json did not include a paths object."
    exit 3
}

$availablePaths = @($openApiResponse.paths.PSObject.Properties.Name)
$missingEndpoints = @($RequiredEndpoints | Where-Object { $_ -notin $availablePaths })

if ($missingEndpoints.Count -gt 0) {
    Write-Error "FAIL: runtime is stale or incomplete. Missing OpenAPI endpoint(s): $($missingEndpoints -join ', ')"
    exit 4
}

Write-Host "PASS: /openapi.json includes required endpoint(s): $($RequiredEndpoints -join ', ')"
Write-Host "PASS: runtime freshness smoke completed."
