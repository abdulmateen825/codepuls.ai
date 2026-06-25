param(
    [string] $OutputDirectory = "backups",
    [string] $ComposeFile = "docker-compose.prod.yml",
    [string] $Service = "postgres",
    [string] $Database = "codepulse",
    [string] $Username = "codepulse"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackupDirectory = Join-Path $Root $OutputDirectory
New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$OutputFile = Join-Path $BackupDirectory "codepulse-postgres-$Timestamp.sql"

Push-Location $Root
try {
    Write-Host "==> Creating PostgreSQL backup at $OutputFile"
    docker compose -f $ComposeFile exec -T $Service pg_dump -U $Username $Database | Out-File -FilePath $OutputFile -Encoding utf8
}
finally {
    Pop-Location
}

Write-Host "Backup completed: $OutputFile"
