# Local Setup

## Prerequisites

- Docker Desktop with Docker Compose v2
- PowerShell 7 or Windows PowerShell 5.1
- Python 3 for repository checks

## Fresh base installation

Use these steps only for a new, disposable local installation. Bootstrap installs
the base control-item addon and its demo records, then sets the administrator
password. It does not install either optional integration addon. Do not rerun
bootstrap against an existing database to reset credentials or reproduce a demo.

1. Copy `.env.example` to `.env`.
2. Replace the placeholder database password in `.env` with a local secret.
3. Run `./scripts/bootstrap.ps1` from PowerShell and choose an administrator password when prompted.
4. Open `http://localhost:8069`.
5. Sign in with the `admin` account and the password selected during bootstrap.

The `.env` file is excluded from Git. Bootstrap passes the chosen administrator
password to a temporary setup container; it does not save it in the repository.
Never commit local credentials.

## Existing databases and historical upgrades

Preserve existing data and credentials. An upgrade is a data-changing operation,
not a setup check. The historical `19.0.4.1.0` migration closes all existing
control items and inserts synthetic scenarios. Other historical migrations also
change records. Fresh installs do not need these migrations replayed.

Before any existing-database upgrade, obtain approval, verify a backup/restore
plan, and validate the actual version path on a disposable copy. The following
command is an operational reference, not an instruction to run during this
walkthrough:

```powershell
./scripts/upgrade.ps1
```

## Validation

The upgrade script updates only `operations_control_tower` and temporarily stops
Odoo. It does not install or update the optional promise or campaign addons.

Run commands from the repository root. For text-only changes:

```powershell
python .\scripts\check_repository.py
git diff --check
```

The base smoke command is:

```powershell
./scripts/smoke-test.ps1
```

It checks repository text, compiles the base addon, starts shared Compose
services, installs the base addon into an `oct_test_<epoch>_<PID>` database
without demo XML, runs its eight methods, and checks service health. It attempts
database and filestore cleanup; the older script does not assert database-drop
success. Verify cleanup separately. The test database is separate, but Docker
services, PostgreSQL and filestore infrastructure are shared.

For the optional addon and standard fulfilment observations:

```powershell
.\scripts\validate-fulfilment.ps1 -WithPromise
```

For the new bounded campaign source, explicitly opt into its separate mode:

```powershell
.\scripts\validate-fulfilment.ps1 -WithCampaign
```

`-WithCampaign` includes the promise selection and campaign addon/tests/probes;
it does not replace the default standard-field diagnostic or promise-only mode.
TASK-0007 records81 passing local methods and11 campaign probe cases, the
independent-review gate and owner-acceptance status. A command is an execution
procedure, not proof that a new run or environment has passed.

Prerequisites: the base `operations_control_tower` database must already exist,
the Compose database and Odoo services must be running, and the required images
must already be available locally. This runner does not start services or pull
images. It reads a scoped fingerprint of the working database, creates its own
`oct_scenario_<GUID>` database, installs the standard test modules and optional
addon there, and verifies cleanup. Its one-off containers use a temporary data
directory rather than the shared filestore.

The campaign mode adds standard Purchase/Manufacturing dependencies only in that
owned test DB. Its end-to-end fixtures record standard receipt/production/
dispatch events rather than treating dates as physical completion. New campaign
results must be read from TASK-0007's actual revision/command/evidence, not the
earlier promise-only test record below.

The recorded TASK-0005 execution passed 30 methods (8 base + 22 optional), the
standard observations, and real-connection/Form probes. These are dated local
results, not a claim about a new run or remote CI. The seven reported standard
business-rule gaps remain gaps. See [TASKS.md](TASKS.md) and
[the browser evidence](evidence/task-0005/README.md).

GitHub Actions currently compiles and tests only the base addon. It does not run
either optional integration suite or connection probes. These commands do not prove
migration safety, production readiness or every browser interaction.

## Optional promise preview

An offline walkthrough using the saved images needs no installation; see
[DEMO.md](DEMO.md). To create a fresh local preview, first satisfy the same
running-services/base-database/local-images prerequisites above, then run:

```powershell
.\scripts\preview-dispatch.ps1 -Action Start
```

The helper creates a fresh named scenario database and labeled one-off container,
binds a generated port to `127.0.0.1`, and seeds a synthetic Sales/Coordinator
user and confirmed order. It does not install the optional addon in the working
database. Start prints an `OCT_UI_PREVIEW=` JSON metadata line containing `url`,
`database`, `container`, `order_name` and `credential_file`.

Open the returned URL. Open the returned temporary credential file privately in
a local editor and use its login/password only for this preview. Do not print
the credential JSON into a terminal, chat, screenshot or committed file. Keep the
exact returned database/container metadata for cleanup.

After the walkthrough, replace both placeholders below with those exact returned
identities and run Stop. Do not guess names or substitute the working database:

```powershell
.\scripts\preview-dispatch.ps1 -Action Stop `
    -Database '<returned-database>' -Container '<returned-container>'
```

Stop verifies resource ownership before removing the preview container,
database and temporary credential file, then checks the scoped working
fingerprint. Normal Start/Stop was exercised during TASK-0005; interruption,
startup failure and cleanup failure paths were not fault-injected. If cleanup
fails, retain the exact metadata and investigate rather than deleting guessed
resources. A missing container can prevent later automatic database deletion
because ownership can no longer be proved. Do not use volume deletion to clean
up a preview.

## Optional campaign preview

The same guarded helper has an explicit campaign mode exercised under TASK-0007:

```powershell
.\scripts\preview-dispatch.ps1 -Action Start -WithCampaign
```

All base-database/running-service/local-image prerequisites, temporary credential
handling and exact-identity Stop instructions above still apply. Only its fresh
owned preview DB gets operations_campaign_automation and its dependencies;
the existing working DB is not updated. HTTP remains bound to a generated
localhost port, cron is disabled and its filestore remains container-local.
Do not publish this preview or expose it to the network.

The synthetic HALY fixture seeds 500 opening finished units, one warehouse/product
pool, and orders A200/B600/C100 with explicit Consumer Complete/Corporate Partial
policies and accepted dates 15/16/17 December 2026. Expected initial reservations
are 200/300/0. No raw-material purchase, BoM or manufacturing fixture is included;
no shipment or production is completed. Opening inventory is synthetic setup,
not evidence of a physical receipt. Dates are examples, not an SLA.

The preview user combines Sales, Coordinator, Stock Manager and Operations
Manager roles for screen navigation. Separated-role security checks belong to
the runtime suite, not this combined-role login. Output retains the promise
preview's top-level order metadata and adds `campaign.orders.A/B/C` with order,
picking, promise and blocker IDs. Use [DEMO.md](DEMO.md#campaign-walkthrough-under-validation)
for the checks and [saved campaign evidence](evidence/task-0007/README.md) for
actual execution, repair and review status. Partly prepared shortages require
explicit warehouse unprepare/recheck before additional allocation; prepared stock
is never silently unpicked.

Stop uses the same exact returned resource identities; `-WithCampaign` is not
needed for Stop. A campaign preview is database-separated but shares Docker/
PostgreSQL infrastructure. Interrupted cleanup, backup/restore, production
deployment and load behavior are not established by starting this preview.

## Operations

```powershell
./scripts/start.ps1
./scripts/stop.ps1
docker compose ps
docker compose logs --tail=100 odoo
```

Named volumes preserve PostgreSQL data and the Odoo filestore between container
restarts. Do not run `docker compose down -v` during setup, validation or cleanup;
it deletes persistent local data.

## Troubleshooting

- If port 8069 is already in use, change `ODOO_PORT` in `.env`.
- If the database password changes after PostgreSQL has initialized, restore the
  known local configuration or use an approved credential-recovery procedure.
  PostgreSQL applies its bootstrap password only to an empty data directory.
  Preserve volumes; do not recreate them as a password fix.
- If a module upgrade fails, review `docker compose logs --tail=200 odoo` before retrying.

## Resolved implementation issues

- The addon declares `web` as a dependency so a command-line database initialization always installs the browser client.
- The upgrade script stops the long-running Odoo service before the update and
  attempts to restart it afterward. This does not prove a failed migration or
  historical upgrade path is safe.
- The `19.0.3.0.0` migration assigns generated references to records created before reference sequencing was introduced.
- Odoo 19 access groups use privileges and company-aware record rules instead of the legacy group-category pattern.
- Smoke cleanup is attempted, not guaranteed. The newer scenario/preview helpers
  check owned database removal; their documented failure-path limits still apply.
