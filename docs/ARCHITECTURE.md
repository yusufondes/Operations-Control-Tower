# Architecture

## Runtime

```text
Browser → 127.0.0.1:8069 → Odoo 19 → PostgreSQL 15
                              │
                              └→ /mnt/extra-addons/operations_control_tower
```

The web port is bound to loopback, so the development instance is not exposed to the local network by default. PostgreSQL is available only to the internal Compose network.

## Application model

`operations.control.item` is the core aggregate. It stores a generated reference, the operational topic, owner, business area, impact, priority, deadline, next action, company, and workflow status.

The first version intentionally keeps the domain small. Separate project, risk, KPI, and integration models should be added only after real reporting and access-control requirements are known.

## Access model

- **Operations Control Tower / User** can create and update items assigned to them, but cannot delete records.
- **Operations Control Tower / Manager** can manage all items in the active company set and can access analysis views.
- A global company rule keeps records within the companies available to the current user.

Group-specific record rules are additive in Odoo. Managers inherit the user group, and the manager rule deliberately grants access to all records that pass the global company rule.

## Presentation and reporting

- Kanban provides a workflow-first overview grouped by state.
- List and form views support day-to-day editing.
- Calendar highlights dated commitments.
- Graph and pivot views summarize record counts by status and business area.

## Persistence

- `postgres_data`: PostgreSQL database files
- `odoo_data`: Odoo filestore and runtime data
- `addons/`: version-controlled custom application source

Removing containers does not remove the named volumes. Do not use `docker compose down -v` unless permanent database deletion is intended.

## Validation strategy

- Python compilation before deployment
- Odoo XML/model validation during module upgrade
- Transaction tests for status selection, overdue calculation, sequence generation, and access control
- HTTP `/web/health` check
- Disposable test database creation and cleanup
