param(
    [string] $BaseUrl = "http://localhost",
    [string] $FrontendUrl = "http://localhost:3000",
    [string] $CoreUrl = "http://localhost:8080",
    [switch] $ThroughNginx
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-Endpoint {
    param(
        [string] $Name,
        [string] $Url
    )

    Write-Host "==> $Name $Url"
    $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15
    if ($Response.StatusCode -lt 200 -or $Response.StatusCode -ge 300) {
        throw "$Name returned HTTP $($Response.StatusCode)"
    }
}

if ($ThroughNginx) {
    Test-Endpoint "Nginx health" "$BaseUrl/nginx-health"
    Test-Endpoint "Spring health through Nginx" "$BaseUrl/api/health"
    Test-Endpoint "Frontend through Nginx" "$BaseUrl/"
}
else {
    Test-Endpoint "Frontend health" "$FrontendUrl/api/health"
    Test-Endpoint "Spring health" "$CoreUrl/api/health"
}

Write-Host "Smoke test completed successfully."
