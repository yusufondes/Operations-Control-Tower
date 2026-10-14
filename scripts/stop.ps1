$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    docker compose stop
    if ($LASTEXITCODE -ne 0) { throw "Unable to stop the Docker services." }
}
finally {
    Pop-Location
}
