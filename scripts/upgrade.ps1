param(
    [string]$Database = "operations_control_tower"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$odooStopped = $false
Push-Location $projectRoot

try {
    $resolved = docker compose config --format json | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw "Compose configuration validation failed." }
    $databaseUser = $resolved.services.db.environment.POSTGRES_USER
    $databasePassword = $resolved.services.db.environment.POSTGRES_PASSWORD

    docker compose up -d db
    if ($LASTEXITCODE -ne 0) { throw "Unable to start PostgreSQL." }

    docker compose stop odoo
    if ($LASTEXITCODE -ne 0) { throw "Unable to stop Odoo before the upgrade." }
    $odooStopped = $true

    docker compose run --rm -T odoo odoo `
        --database=$Database `
        --update=operations_control_tower `
        --stop-after-init `
        --without-demo=true `
        --db_host=db `
        --db_port=5432 `
        --db_user=$databaseUser `
        --db_password=$databasePassword `
        --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
    if ($LASTEXITCODE -ne 0) { throw "Addon upgrade failed." }
}
finally {
    $restartFailed = $false
    if ($odooStopped) {
        docker compose up -d odoo
        $restartFailed = $LASTEXITCODE -ne 0
    }
    Pop-Location
    if ($restartFailed) { throw "Unable to start Odoo after the upgrade." }
}

Write-Host "Operations Control Tower was upgraded successfully." -ForegroundColor Green
