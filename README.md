# Operations Control Tower 2.0

An Odoo 19 Community portfolio project that turns operational priorities, blockers, ownership, and deadlines into one management workspace.

## Business problem

Operational follow-up is often scattered across spreadsheets, messages, and meeting notes. That makes ownership unclear, hides blockers, and weakens management reporting. Operations Control Tower provides a compact, structured workflow for the items that need management attention.

## Current capabilities

- Status-driven workflow with waiting, resolution, and closure states
- Manufacturing-oriented business areas and impact classification
- Owner, priority, deadline, status, and next-action tracking
- Overdue highlighting
- Kanban, list, form, calendar, graph, pivot, and search views
- Separate Operations User and Operations Manager access levels
- Optional demonstration records with relative deadlines
- Fictional portfolio scenarios for powdered-drink operations
- Automated model, workflow, validation, and security tests
- PostgreSQL and Odoo container health checks

## Architecture

```text
Browser -> 127.0.0.1:8069 -> Odoo 19 -> PostgreSQL 15
                                |
                                +-> custom addon
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design and security boundaries.

## Prerequisites

- Docker Desktop with Docker Compose v2
- PowerShell 7 or Windows PowerShell 5.1
- At least 4 GB of memory available to Docker

## Quick start

```powershell
git clone <repository-url>
cd Operations-Control-Tower
Copy-Item .env.example .env
# Replace the placeholder password in .env before continuing.
.\scripts\bootstrap.ps1
```

Open `http://localhost:8069` after the bootstrap script reports success. The bootstrap creates the `operations_control_tower` database and loads the optional portfolio demonstration records.

The bootstrap script securely prompts for an Odoo administrator password and requires at least 12 characters. The value is passed only to a temporary setup container and is not written to the repository.

See [docs/SETUP.md](docs/SETUP.md) for detailed operations, troubleshooting, and resolved implementation notes.

## Development commands

```powershell
.\scripts\start.ps1
.\scripts\upgrade.ps1
.\scripts\smoke-test.ps1
.\scripts\stop.ps1
```

The smoke test uses a disposable database and does not update the development database.

## Demonstration

Follow [docs/DEMO.md](docs/DEMO.md) for a short portfolio walkthrough.

## Repository structure

```text
addons/operations_control_tower/  Custom Odoo addon
config/                            Environment documentation
docs/                              Architecture, setup, and demo notes
scripts/                           Bootstrap and validation commands
.github/workflows/                 Continuous integration
compose.yaml                       Local Odoo and PostgreSQL stack
```

## Testing

Local validation:

```powershell
python .\scripts\check_repository.py
.\scripts\smoke-test.ps1
```

GitHub Actions repeats repository checks and installs the addon into a clean database.

## Known limitations

- The current domain model focuses on operational control items rather than full project management.
- External system integrations are not included in the MVP.
- KPI definitions are demonstration examples and should be replaced with organization-specific measures.
- The Docker configuration is intended for local development, not public production hosting.

## Roadmap

1. Replace demonstration records with a real operational dataset.
2. Add organization-specific KPI definitions and targets.
3. Add integration adapters only after source-system contracts are defined.
4. Add backup automation and production deployment guidance.

## License

This project is licensed under the GNU Lesser General Public License v3.0. See [LICENSE](LICENSE).
