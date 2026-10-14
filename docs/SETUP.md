# Local Setup

## Prerequisites

- Docker Desktop with Docker Compose v2
- PowerShell 7 or Windows PowerShell 5.1
- Python 3 for repository checks

## First run

1. Copy `.env.example` to `.env`.
2. Replace the placeholder database password in `.env` with a local secret.
3. Run `./scripts/bootstrap.ps1` from PowerShell and choose an administrator password when prompted.
4. Open `http://localhost:8069`.
5. Sign in with the `admin` account and the password selected during bootstrap.

The `.env` file is intentionally excluded from Git. The application password is not stored in a file. Never commit local credentials.

## Existing database

Apply model, security, data, and view updates with:

```powershell
./scripts/upgrade.ps1
```

## Validation

Run the complete local validation suite with:

```powershell
./scripts/smoke-test.ps1
```

The suite validates repository text files, compiles the addon, installs it into a disposable database, runs tagged Odoo tests, checks the health endpoint, and removes the disposable database.

## Operations

```powershell
./scripts/start.ps1
./scripts/stop.ps1
docker compose ps
docker compose logs --tail=100 odoo
```

Named volumes preserve PostgreSQL data and the Odoo filestore between container restarts. Avoid `docker compose down -v` unless permanent local data deletion is intended.

## Troubleshooting

- If port 8069 is already in use, change `ODOO_PORT` in `.env`.
- If the database password changes after PostgreSQL has initialized, recreate the local database volume or restore the original password. PostgreSQL applies its bootstrap password only when the data directory is empty.
- If a module upgrade fails, review `docker compose logs --tail=200 odoo` before retrying.

## Resolved implementation issues

- The addon declares `web` as a dependency so a command-line database initialization always installs the browser client.
- The upgrade script stops the long-running Odoo service before updating the schema, then starts it again even when the upgrade fails. This prevents requests from reaching a partially upgraded registry.
- The `19.0.3.0.0` migration assigns generated references to records created before reference sequencing was introduced.
- Odoo 19 access groups use privileges and company-aware record rules instead of the legacy group-category pattern.
- Disposable smoke-test databases and their filestore directories are removed after every run.
