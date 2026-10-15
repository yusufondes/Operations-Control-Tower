param([switch]$WithPromise, [switch]$WithCampaign)

if ($WithCampaign) { $WithPromise = $true }

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$workingDatabase = "operations_control_tower"
$testDatabase = "oct_scenario_$([Guid]::NewGuid().ToString('N'))"
$ownsDatabase = $false
$databaseUser = $null
$before = $null
$failure = $null
$cleanupFailure = $null

function Assert-TestDatabase {
    param([string]$Name)
    if ($Name -cnotmatch '^oct_scenario_[0-9a-f]{32}$' -or $Name -eq $workingDatabase) {
        throw "Unsafe disposable database name."
    }
}

function Get-WorkingFingerprint {
    $query = @"
SELECT name || ':' || state || ':' || COALESCE(latest_version, '')
FROM ir_module_module
WHERE name IN ('operations_control_tower', 'sale_management', 'sale_stock',
               'stock', 'purchase_stock', 'purchase', 'mrp', 'sale_mrp',
               'operations_dispatch_promise', 'operations_campaign_automation') ORDER BY name;
SELECT COUNT(*)::text || ':' || md5(COALESCE(string_agg(row_to_json(t)::text, '' ORDER BY id), ''))
FROM operations_control_item t;
"@
    $lines = @($query | docker compose exec -T db psql -X -U $databaseUser `
        -d $workingDatabase -At -v ON_ERROR_STOP=1)
    if ($LASTEXITCODE -ne 0) { throw "Unable to read working database fingerprint." }
    return ($lines -join "`n")
}

Push-Location $projectRoot
try {
    Assert-TestDatabase $testDatabase
    # Resolve credentials in memory only. Never print the resolved Compose object.
    $configText = docker compose config --format json
    if ($LASTEXITCODE -ne 0) { throw "Compose validation failed." }
    $resolved = $configText | ConvertFrom-Json
    $databaseUser = $resolved.services.db.environment.POSTGRES_USER
    $databasePassword = $resolved.services.db.environment.POSTGRES_PASSWORD
    if (-not $databaseUser -or -not $databasePassword) { throw "Missing database configuration." }
    $before = Get-WorkingFingerprint
    Write-Host "Working database fingerprint before validation:"
    Write-Host $before

    $exists = docker compose exec -T db psql -X -U $databaseUser -d postgres -At `
        -v ON_ERROR_STOP=1 -c "SELECT 1 FROM pg_database WHERE datname = '$testDatabase';"
    if ($LASTEXITCODE -ne 0) { throw "Database existence check failed." }
    if ($exists -eq '1') { throw "Refusing to use an existing database." }
    docker compose exec -T db createdb -U $databaseUser -O $databaseUser -T template0 $testDatabase
    if ($LASTEXITCODE -ne 0) { throw "Disposable database creation failed." }
    $ownsDatabase = $true
    Write-Host "Disposable database: $testDatabase"

    $common = @(
        "--database=$testDatabase", "--db_host=db", "--db_port=5432",
        "--db_user=$databaseUser", "--db_password=$databasePassword",
        "--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons",
        "--data-dir=/tmp/oct_scenario_data", "--no-http", "--max-cron-threads=0", "--workers=0",
        "--http-interface=127.0.0.1"
    )
    # No service startup, image pull, live DB update, or shared filestore writes.
    $installModules = 'sale_management,sale_stock,purchase_stock,mrp,sale_mrp,operations_control_tower'
    $testTags = '/operations_control_tower'
    if ($WithPromise) {
        $installModules += ',operations_dispatch_promise'
        $testTags += ',/operations_dispatch_promise'
    }
    if ($WithCampaign) {
        $installModules += ',operations_campaign_automation'
        $testTags += ',/operations_campaign_automation'
    }
    docker compose run --no-deps --pull never --rm -T odoo odoo @common `
        --init=$installModules `
        --stop-after-init --without-demo=true --test-enable `
        --test-tags=$testTags --log-level=warn `
        --log-handler=odoo.tests.result:INFO --log-handler=odoo.tests.stats:INFO
    if ($LASTEXITCODE -ne 0) { throw "Fresh installation/addon compatibility tests failed." }

    $scenario = Get-Content -Raw (Join-Path $PSScriptRoot "validate_fulfilment.py")
    $scenarioOutput = @($scenario | docker compose run --no-deps --pull never --rm -T odoo `
        odoo shell @common --log-level=warn)
    $scenarioExit = $LASTEXITCODE
    $scenarioOutput | ForEach-Object { Write-Host $_ }
    if ($scenarioExit -ne 0) { throw "Standard fulfilment scenario failed." }
    $markers = @($scenarioOutput | Where-Object { $_ -like 'OCT_VALIDATION_RESULT=*' })
    if ($markers.Count -ne 1) { throw "Missing or ambiguous scenario result." }
    $result = $markers[0].Substring('OCT_VALIDATION_RESULT='.Length) | ConvertFrom-Json
    if ($result.database -ne $testDatabase -or $result.status -ne 'observed') {
        throw "Scenario result does not match the owned database."
    }
    if ($WithPromise) {
        $probe = Get-Content -Raw (Join-Path $PSScriptRoot "validate_dispatch_promise.py")
        $probeOutput = @($probe | docker compose run --no-deps --pull never --rm -T odoo `
            odoo shell @common --log-level=warn)
        $probeExit = $LASTEXITCODE
        $probeOutput | ForEach-Object { Write-Host $_ }
        if ($probeExit -ne 0) { throw "Dispatch promise concurrency/form probe failed." }
        $probeMarkers = @($probeOutput | Where-Object { $_ -like 'OCT_PROMISE_RESULT=*' })
        if ($probeMarkers.Count -ne 1) { throw "Missing or ambiguous promise probe result." }
        $probeResult = $probeMarkers[0].Substring('OCT_PROMISE_RESULT='.Length) | ConvertFrom-Json
        if ($probeResult.database -ne $testDatabase -or $probeResult.status -ne 'passed') {
            throw "Promise probe result does not match the owned database."
        }
    }
    if ($WithCampaign) {
        $campaign = Get-Content -Raw (Join-Path $PSScriptRoot "validate_campaign.py")
        $campaignOutput = @($campaign | docker compose run --no-deps --pull never --rm -T odoo `
            odoo shell @common --log-level=warn)
        $campaignExit = $LASTEXITCODE
        $campaignOutput | ForEach-Object { Write-Host $_ }
        if ($campaignExit -ne 0) { throw "Campaign end-to-end/concurrency probe failed." }
        $campaignMarkers = @($campaignOutput | Where-Object { $_ -like 'OCT_CAMPAIGN_RESULT=*' })
        if ($campaignMarkers.Count -ne 1) { throw "Missing or ambiguous campaign probe result." }
        $campaignResult = $campaignMarkers[0].Substring('OCT_CAMPAIGN_RESULT='.Length) | ConvertFrom-Json
        if ($campaignResult.database -ne $testDatabase -or $campaignResult.status -ne 'passed') {
            throw "Campaign probe result does not match the owned database."
        }
    }
}
catch {
    # Exception messages here are fixed strings, not resolved credentials.
    $failure = $_
}
finally {
    try {
        if ($ownsDatabase) {
            Assert-TestDatabase $testDatabase
            docker compose exec -T db dropdb -U $databaseUser --if-exists --force $testDatabase
            if ($LASTEXITCODE -ne 0) { throw "Disposable database cleanup failed." }
            $remaining = docker compose exec -T db psql -X -U $databaseUser -d postgres -At `
                -v ON_ERROR_STOP=1 -c "SELECT 1 FROM pg_database WHERE datname = '$testDatabase';"
            if ($LASTEXITCODE -ne 0 -or $remaining -eq '1') {
                throw "Disposable database removal could not be verified."
            }
            Write-Host "Disposable database removal verified."
        }
    }
    catch { $cleanupFailure = $_ }
    try {
        if ($null -ne $before) {
            $after = Get-WorkingFingerprint
            if ($after -cne $before) { throw "Working database fingerprint changed; investigate before continuing." }
            Write-Host "Working module states and control-item fingerprint unchanged."
        }
    }
    catch {
        if ($cleanupFailure) { $failure = "Cleanup and working fingerprint verification both failed." }
        $cleanupFailure = $_
    }
    finally {
        $databasePassword = $null
        $resolved = $null
        $configText = $null
        $common = $null
        Pop-Location
    }
}
if ($failure -or $cleanupFailure) {
    $messages = @()
    if ($failure) { $messages += [string]$failure }
    if ($cleanupFailure) { $messages += $cleanupFailure.Exception.Message }
    throw ($messages -join " | ")
}
Write-Host "Standard observations recorded. Reported business-rule gaps are NOT acceptance passes."
