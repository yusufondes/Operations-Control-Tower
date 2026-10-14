param(
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$testDatabase = "oct_test_$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())_$PID"
$databaseUser = $null
Push-Location $projectRoot

try {
    $resolved = docker compose config --format json | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw "Compose configuration validation failed." }
    $databaseUser = $resolved.services.db.environment.POSTGRES_USER
    $databasePassword = $resolved.services.db.environment.POSTGRES_PASSWORD
    if ($Port -le 0) {
        $Port = [int]$resolved.services.odoo.ports[0].published
    }

    python .\scripts\check_repository.py
    if ($LASTEXITCODE -ne 0) { throw "Repository checks failed." }

    python -m compileall -q .\addons\operations_control_tower
    if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }

    docker compose up -d db odoo
    if ($LASTEXITCODE -ne 0) { throw "Unable to start the Docker services." }

    docker compose run --rm -T odoo odoo `
        --database=$testDatabase `
        --init=operations_control_tower `
        --stop-after-init `
        --without-demo=true `
        --test-enable `
        --test-tags=/operations_control_tower `
        --db_host=db `
        --db_port=5432 `
        --db_user=$databaseUser `
        --db_password=$databasePassword `
        --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons `
        --log-level=test
    if ($LASTEXITCODE -ne 0) { throw "Odoo addon tests failed." }

    $health = Invoke-RestMethod -Uri "http://localhost:$Port/web/health" -TimeoutSec 5
    if ($health.status -ne "pass") { throw "Odoo health endpoint did not pass." }

}
finally {
    if ($databaseUser) {
        docker compose exec -T db dropdb -U $databaseUser --if-exists --force $testDatabase | Out-Null
    }
    if ($testDatabase -match '^oct_test_\d+_\d+$') {
        $filestoreCleanup = "import pathlib, re, shutil, sys; name = sys.argv[1]; assert re.fullmatch(r'oct_test_\d+_\d+', name); root = pathlib.Path('/var/lib/odoo/filestore').resolve(); target = (root / name).resolve(); assert target.parent == root; shutil.rmtree(target, ignore_errors=True)"
        docker compose exec -T odoo python3 -c $filestoreCleanup $testDatabase
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Unable to remove the disposable test filestore."
        }
    }
    Pop-Location
}

Write-Host "Operations Control Tower smoke tests passed." -ForegroundColor Green
