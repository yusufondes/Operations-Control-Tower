param(
    [ValidateSet('Start','Stop')][string]$Action = 'Start',
    [string]$Database,
    [string]$Container,
    [switch]$WithCampaign
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$workingDatabase = 'operations_control_tower'
$ownedDatabase = $false
$ownedContainer = $false
$containerAttempted = $false
$credentialPath = $null

function Assert-PreviewNames {
    if ($Database -cnotmatch '^oct_scenario_[0-9a-f]{32}$' -or
        $Container -cnotmatch '^oct-ui-[0-9a-f]{32}$' -or
        $Database.Substring(13) -cne $Container.Substring(7)) {
        throw 'Unsafe preview resource identity.'
    }
}

function Working-Fingerprint {
    $query = @"
SELECT name || ':' || state || ':' || COALESCE(latest_version, '') FROM ir_module_module
WHERE name IN ('operations_control_tower','operations_dispatch_promise','operations_campaign_automation','sale_management',
 'sale_stock','stock','purchase_stock','purchase','mrp','sale_mrp') ORDER BY name;
SELECT COUNT(*)::text || ':' || md5(COALESCE(string_agg(row_to_json(t)::text,'' ORDER BY id),''))
FROM operations_control_item t;
"@
    $value = @($query | docker compose exec -T db psql -X -U $databaseUser -d $workingDatabase -At -v ON_ERROR_STOP=1)
    if ($LASTEXITCODE -ne 0) { throw 'Working fingerprint read failed.' }
    return ($value -join "`n")
}

function Get-OwnedPreviewContainerId {
    Assert-PreviewNames
    $matchedContainers = @(docker container ls --all --filter "name=^/$Container`$" --format '{{.Names}}')
    if ($LASTEXITCODE -ne 0) { throw 'Preview container discovery failed.' }
    if ($matchedContainers.Count -eq 0) { return $null }
    if ($matchedContainers.Count -ne 1 -or $matchedContainers[0] -cne $Container) {
        throw 'Preview container identity could not be verified.'
    }
    # JSON avoids native-command quote loss in Windows PowerShell 5.1.
    $inspectionText = @(docker inspect --type container $Container)
    if ($LASTEXITCODE -ne 0) {
        throw 'Preview container ownership inspection failed.'
    }
    $inspections = ($inspectionText -join "`n") | ConvertFrom-Json
    if (@($inspections).Count -ne 1) { throw 'Ambiguous preview container inspection.' }
    $inspection = @($inspections)[0]
    if ($inspection.Id -cnotmatch '^[0-9a-f]{64}$' -or
        $inspection.Name -cne "/$Container" -or
        $inspection.Config.Labels.'oct.ui-preview' -cne $Database) {
        throw 'Preview ownership label mismatch.'
    }
    return $inspection.Id
}

function Test-PreviewModuleReady {
    # Before initialization commits there may be no module table. In PS5.1,
    # redirected native stderr can still terminate under ErrorAction Stop.
    try {
        $schemaReady = docker compose exec -T db psql -X -U $databaseUser -d $Database -At -v ON_ERROR_STOP=1 `
            -c "SELECT to_regclass('public.ir_module_module') IS NOT NULL;" 2>$null
        if ($LASTEXITCODE -ne 0 -or $schemaReady -ne 't') { return $false }
        $installed = docker compose exec -T db psql -X -U $databaseUser -d $Database -At -v ON_ERROR_STOP=1 `
            -c "SELECT count(*) FROM ir_module_module WHERE name='$previewModule' AND state='installed';" 2>$null
        return ($LASTEXITCODE -eq 0 -and $installed -eq '1')
    }
    catch { return $false }
}

function Remove-Preview {
    Assert-PreviewNames
    $cleanupErrors = [Collections.Generic.List[string]]::new()
    # Start proves DB ownership with successful createdb. A later Stop must
    # independently prove it from the exact existing container and its label.
    $databaseCanBeRemoved = $ownedDatabase
    if ($ownedContainer -or $containerAttempted -or $Action -eq 'Stop') {
        try {
            $previewContainerId = Get-OwnedPreviewContainerId
            if ($previewContainerId) {
                if ($Action -eq 'Stop') { $databaseCanBeRemoved = $true }
                docker rm --force $previewContainerId | Out-Null
                if ($LASTEXITCODE -ne 0) { throw 'Owned preview container removal failed.' }
                $remainingContainer = @(docker container ls --all --no-trunc `
                    --filter "id=$previewContainerId" --format '{{.ID}}')
                if ($LASTEXITCODE -ne 0 -or $remainingContainer.Count -ne 0) {
                    throw 'Owned preview container absence not verified.'
                }
            }
            elseif ($Action -eq 'Stop') {
                throw 'Preview container absent; DB ownership is unproven and its DB will not be dropped.'
            }
        }
        catch {
            $databaseCanBeRemoved = $false
            $cleanupErrors.Add($_.Exception.Message)
        }
    }
    if ($databaseCanBeRemoved) {
        try {
            $present = docker compose exec -T db psql -X -U $databaseUser -d postgres -At -v ON_ERROR_STOP=1 `
                -c "SELECT 1 FROM pg_database WHERE datname='$Database';"
            if ($LASTEXITCODE -ne 0) { throw 'Owned preview DB discovery failed.' }
            if ($present -eq '1') {
                docker compose exec -T db dropdb -U $databaseUser --force $Database
                if ($LASTEXITCODE -ne 0) { throw 'Owned preview DB removal failed.' }
            }
            $left = docker compose exec -T db psql -X -U $databaseUser -d postgres -At -v ON_ERROR_STOP=1 `
                -c "SELECT 1 FROM pg_database WHERE datname='$Database';"
            if ($LASTEXITCODE -ne 0 -or $left -eq '1') { throw 'Preview DB absence not verified.' }
        }
        catch { $cleanupErrors.Add($_.Exception.Message) }
    }
    try {
        if ($credentialPath -and (Test-Path -LiteralPath $credentialPath)) {
            $expectedPath = Join-Path ([IO.Path]::GetTempPath()) "$Container.json"
            if ([IO.Path]::GetFullPath($credentialPath) -cne [IO.Path]::GetFullPath($expectedPath) -or
                -not (Test-Path -LiteralPath $credentialPath -PathType Leaf)) {
                throw 'Unsafe preview credential path.'
            }
            Remove-Item -LiteralPath $credentialPath
            if (Test-Path -LiteralPath $credentialPath) {
                throw 'Preview credential file absence not verified.'
            }
        }
    }
    catch { $cleanupErrors.Add($_.Exception.Message) }
    if ($cleanupErrors.Count -gt 0) {
        throw ('Preview cleanup incomplete: ' + ($cleanupErrors -join ' '))
    }
}

Push-Location $projectRoot
try {
    $resolvedText = docker compose config --format json
    if ($LASTEXITCODE -ne 0) { throw 'Compose validation failed.' }
    $config = $resolvedText | ConvertFrom-Json
    $databaseUser = $config.services.db.environment.POSTGRES_USER
    $databasePassword = $config.services.db.environment.POSTGRES_PASSWORD
    $before = Working-Fingerprint
    if ($Action -eq 'Start') {
        if ($Database -or $Container) { throw 'Start always generates fresh resource names.' }
        $identity = [Guid]::NewGuid().ToString('N')
        $Database = "oct_scenario_$identity"
        $Container = "oct-ui-$identity"
        Assert-PreviewNames
        $existing = docker compose exec -T db psql -X -U $databaseUser -d postgres -At -v ON_ERROR_STOP=1 `
            -c "SELECT 1 FROM pg_database WHERE datname='$Database';"
        if ($LASTEXITCODE -ne 0 -or $existing -eq '1') { throw 'Existing or unverifiable DB; refusing preview.' }
        docker compose exec -T db createdb -U $databaseUser -O $databaseUser -T template0 $Database
        if ($LASTEXITCODE -ne 0) { throw 'Preview DB creation failed.' }
        $ownedDatabase = $true
        $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
        $listener.Start()
        $port = $listener.LocalEndpoint.Port
        $listener.Stop()
        $installModules = 'sale_management,operations_dispatch_promise'
        $previewModule = 'operations_dispatch_promise'
        $seedFile = 'seed_ui_preview.py'
        if ($WithCampaign) {
            $installModules += ',operations_campaign_automation'
            $previewModule = 'operations_campaign_automation'
            $seedFile = 'seed_campaign_preview.py'
        }
        # Compose can return nonzero after creating the named container.
        $containerAttempted = $true
        $containerId = docker compose run --no-deps --pull never --detach --name $Container `
            --label "oct.ui-preview=$Database" --publish "127.0.0.1:${port}:8069" odoo odoo `
            --database=$Database --init=$installModules --without-demo=true `
            --db_host=db --db_port=5432 --db_user=$databaseUser --db_password=$databasePassword `
            --db-filter="^$Database`$" --no-database-list --data-dir=/tmp/oct_ui_data `
            --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons `
            --http-interface=0.0.0.0 --max-cron-threads=0 --workers=0 --log-level=warn
        if ($LASTEXITCODE -ne 0) { throw 'Preview container startup failed.' }
        $ownedContainer = $true
        $ready = $false
        for ($attempt=0; $attempt -lt 120; $attempt++) {
            if (Test-PreviewModuleReady) { $ready=$true; break }
            Start-Sleep -Seconds 1
        }
        if (-not $ready) { throw 'Preview module initialization did not complete.' }
        $uiPassword = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
        $seed = "UI_PASSWORD = $($uiPassword | ConvertTo-Json -Compress)`n" +
            (Get-Content -Raw (Join-Path $PSScriptRoot $seedFile))
        $seedOutput = @($seed | docker exec -i $Container odoo shell --database=$Database `
            --db_host=db --db_port=5432 --db_user=$databaseUser --db_password=$databasePassword `
            --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons `
            --data-dir=/tmp/oct_ui_data --no-http --max-cron-threads=0 --workers=0 --log-level=warn)
        if ($LASTEXITCODE -ne 0) { throw 'Synthetic preview fixture failed.' }
        $marker = @($seedOutput | Where-Object { $_ -like 'OCT_UI_FIXTURE=*' })
        if ($marker.Count -ne 1) { throw 'Missing preview fixture result.' }
        $fixture = $marker[0].Substring('OCT_UI_FIXTURE='.Length) | ConvertFrom-Json
        $credentialPath = Join-Path ([IO.Path]::GetTempPath()) "$Container.json"
        $temporaryCredential = @{ login=$fixture.login; password=$uiPassword; database=$Database }
        [IO.File]::WriteAllText($credentialPath, ($temporaryCredential | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
        if ((Working-Fingerprint) -cne $before) { throw 'Working fingerprint changed during preview startup.' }
        $previewResult = @{ database=$Database; container=$Container; port=$port;
            url="http://127.0.0.1:$port"; credential_file=$credentialPath;
            order_id=$fixture.order_id; order_name=$fixture.order_name; before=$before }
        if ($WithCampaign) { $previewResult.campaign = $fixture }
        Write-Output ('OCT_UI_PREVIEW=' + ($previewResult | ConvertTo-Json -Depth 8 -Compress))
    }
    else {
        Assert-PreviewNames
        $credentialPath=Join-Path ([IO.Path]::GetTempPath()) "$Container.json"
        Remove-Preview
        if ((Working-Fingerprint) -cne $before) { throw 'Working fingerprint changed during cleanup.' }
        Write-Output 'Owned preview container, DB and credential file removed; scoped working fingerprint unchanged.'
    }
}
catch {
    $operationError = $_
    if ($Action -eq 'Start' -and ($containerAttempted -or $ownedContainer -or $ownedDatabase -or $credentialPath)) {
        try { Remove-Preview }
        catch {
            throw ('Preview startup failed: ' + $operationError.Exception.Message + ' ' + $_.Exception.Message)
        }
    }
    throw $operationError
}
finally {
    $databasePassword=$null
    $uiPassword=$null
    $seed=$null
    $temporaryCredential=$null
    $config=$null
    $resolvedText=$null
    Pop-Location
}
