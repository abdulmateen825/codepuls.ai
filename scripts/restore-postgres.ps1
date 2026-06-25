param(
    [Parameter(Mandatory = $true)]
    [string] $BackupFile,
    [string] $ComposeFile = "docker-compose.prod.yml",
    [string] $Service = "postgres",
    [string] $Database = "codepulse",
    [string] $Username = "codepulse"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ResolvedBackup = Resolve-Path $BackupFile

Write-Host "This will restore $ResolvedBackup into database '$Database'."
Write-Host "Make sure you have stopped application traffic and have a fresh backup."
$Confirmation = Read-Host "Type RESTORE to continue"
if ($Confirmation -ne "RESTORE") {
    throw "Restore cancelled."
}

Push-Location $Root
try {
    Write-Host "==> Restoring PostgreSQL backup"
    Get-Content -Raw $ResolvedBackup | docker compose -f $ComposeFile exec -T $Service psql -U $Username $Database
}
finally {
    Pop-Location
}

Write-Host "Restore completed."
