$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath ".env")) {
        throw "Missing .env. Copy .env.example to .env and replace the placeholder password."
    }
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw "Unable to start the Docker services." }
    docker compose ps
}
finally {
    Pop-Location
}
