Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Validating Docker Compose files"
Push-Location $Root
try {
    docker compose config --quiet
    docker compose --profile app config --quiet
    docker compose --env-file .env.example -f docker-compose.prod.yml config --quiet
}
finally {
    Pop-Location
}

Write-Host "==> Running FastAPI tests"
Push-Location (Join-Path $Root "backend-ai")
try {
    $Python = Join-Path (Get-Location) "venv\Scripts\python.exe"
    if (-not (Test-Path $Python)) {
        $Python = "python"
    }
    & $Python -m unittest discover -s app\tests
}
finally {
    Pop-Location
}

Write-Host "==> Running Spring Boot tests"
Push-Location (Join-Path $Root "backend-core")
try {
    mvn test
}
finally {
    Pop-Location
}

Write-Host "==> Running frontend lint and build"
Push-Location (Join-Path $Root "frontend")
try {
    npm run lint
    npm run build
}
finally {
    Pop-Location
}

Write-Host "All checks completed successfully."
