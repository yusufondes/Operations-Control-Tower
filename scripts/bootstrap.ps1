param(
    [string]$Database = "operations_control_tower",
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot

try {
    if (-not (Test-Path -LiteralPath ".env")) {
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
        throw "A local .env file was created. Replace its placeholder password, then run bootstrap again."
    }

    $resolved = docker compose config --format json | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw "Compose configuration validation failed." }
    $databaseUser = $resolved.services.db.environment.POSTGRES_USER
    $databasePassword = $resolved.services.db.environment.POSTGRES_PASSWORD
    if ($Port -le 0) {
        $Port = [int]$resolved.services.odoo.ports[0].published
    }

    docker compose up -d db
    if ($LASTEXITCODE -ne 0) { throw "Unable to start PostgreSQL." }

    docker compose run --rm -T odoo odoo `
        --database=$Database `
        --init=operations_control_tower `
        --stop-after-init `
        --db_host=db `
        --db_port=5432 `
        --db_user=$databaseUser `
        --db_password=$databasePassword `
        --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
    if ($LASTEXITCODE -ne 0) { throw "Database initialization failed." }

    $securePassword = Read-Host "Choose the initial Odoo administrator password" -AsSecureString
    $secureConfirmation = Read-Host "Confirm the Odoo administrator password" -AsSecureString
    $adminPassword = [System.Net.NetworkCredential]::new(
        "admin", $securePassword
    ).Password
    $adminPasswordConfirmation = [System.Net.NetworkCredential]::new(
        "admin", $secureConfirmation
    ).Password
    if ($adminPassword.Length -lt 12) {
        throw "The Odoo administrator password must contain at least 12 characters."
    }
    if ($adminPassword -cne $adminPasswordConfirmation) {
        throw "The Odoo administrator passwords do not match."
    }

    $env:OCT_BOOTSTRAP_ADMIN_PASSWORD = $adminPassword
    try {
        $passwordUpdate = @'
import os

administrator = env.ref("base.user_admin")
administrator.write({"password": os.environ["OCT_BOOTSTRAP_ADMIN_PASSWORD"]})
env.cr.commit()
'@
        $passwordUpdate | docker compose run --rm -T `
            -e OCT_BOOTSTRAP_ADMIN_PASSWORD `
            odoo odoo shell `
            --database=$Database `
            --db_host=db `
            --db_port=5432 `
            --db_user=$databaseUser `
            --db_password=$databasePassword `
            --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons `
            --no-http
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to set the initial Odoo administrator password."
        }
    }
    finally {
        Remove-Item Env:OCT_BOOTSTRAP_ADMIN_PASSWORD -ErrorAction SilentlyContinue
        $adminPassword = $null
        $adminPasswordConfirmation = $null
    }

    docker compose up -d odoo
    if ($LASTEXITCODE -ne 0) { throw "Unable to start Odoo." }

    $healthUri = "http://localhost:$Port/web/health"
    $healthy = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri $healthUri -TimeoutSec 3
            if ($health.status -eq "pass") {
                $healthy = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }
    if (-not $healthy) { throw "Odoo did not become healthy at $healthUri." }

    Write-Host "Operations Control Tower is ready at http://localhost:$Port." -ForegroundColor Green
    Write-Host "Sign in with the admin account and the password you just chose."
}
finally {
    Pop-Location
}
