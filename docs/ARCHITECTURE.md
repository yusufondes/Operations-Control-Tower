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

## Verified integration boundaries

Verified on 2026-10-15 against baseline commit
`d62b6bc2de98ef3e500a2c177d57d007b37ece68`.
The addon version is `19.0.4.1.0`; its only declared dependencies are
`base` and `web`. It does not extend sales orders, products, stock moves,
purchase orders, quality checks or external-system messages.

In the base addon, inventory, procurement, quality and maintenance are business-
area labels and fictional control-item examples. Their labels do not implement
those ERP processes. The optional integrations below add the explicitly approved
Sales/stock/supply boundaries, not WMS, carrier or supplier APIs. Further external
boundaries require an approved task and compatibility assessment.

The status field accepts eight selections. It does not enforce a business-state
transition graph, resolution prerequisites, quality release, or automatic
order-readiness recalculation. Analysis views count control items; they are not
stock-accuracy or on-time-delivery KPI engines.

## Test and upgrade boundaries

The existing smoke script creates a disposable database on the same PostgreSQL
server and shares the Compose services and Odoo filestore. It starts services,
writes ignored bytecode, runs fresh-install tests without demo XML, checks the
main health endpoint, and attempts cleanup. It does not validate upgrades,
historical migrations or browser behavior; verify cleanup separately.

The historical `19.0.4.1.0` migration closes all control items and inserts ten
synthetic scenarios. Do not replay it on working data as a validation step.
Future upgrade testing needs a disposable copy and an approved data-preservation
plan. Keep the working database out of governance-only checks.

Images use version tags rather than immutable digests. Named volumes are local
persistence, not a verified backup or recovery strategy.
See [REVIEWER.md](REVIEWER.md) for actual command effects and quality gates,
[DECISIONS.md](DECISIONS.md) for approval status, and
[PROJECT_STATUS.md](PROJECT_STATUS.md) for dated observations.

## Optional warehouse promise integration - TASK-0004

Source now includes operations_dispatch_promise, depending on sale_stock and
the unchanged operations_control_tower addon. This is a separate planning and
customer-response slice; it is not installed in the working database. The
control addon remains base/web-only. No deployment or data migration is implied.

oct.dispatch.promise has one protected record per sales order with original,
current and estimated warehouse dates, responsible user and promise revision.
oct.dispatch.proposal stores the proposed date/reason, order-scope snapshot,
base revision, pending/final/stale state and manual customer-response evidence.
Responses are employee-entered references, not authenticated customer consent.
Finalized records cannot be edited/deleted through ordinary CRUD, even by a
coordinator; private server methods enforce the allowed actions atomically.
Default context values cannot fabricate revisions or finalized history.

Read/search access follows the source sales order dynamically, plus company
rules. A separate coordinator group permits workflow actions but grants no
Sales access itself. Actions also require source-order write access. System/
database administrators are not subject to a tamper-proof audit guarantee.

Actions lock the order and existing lines, then touch an ORM-written guard
revision. Sales-line scope changes and confirmation/cancellation bump a scope
revision; snapshots include quantities/UoMs and completed stock moves. This
handles changed-and-restored quantities and REPEATABLE READ phantom insertion.
Competing operations receive a refresh/retry error; callers cannot bypass the
workflow with context flags. SQL is used for row locks, not business-data writes.

Stale applicability is computed when read. A stale pending row is finalized
when a response/replacement proposal is recorded; responses to old proposals
remain evidence without changing the current promise. Corporate partial
dispatch is not blocked while waiting. With only operations_dispatch_promise
installed, the current date is a planning reference: no stock allocation or
consumer-dispatch policy is changed. Neither integration rewrites standard
commitment_date, stock deadlines or picking schedules; no calendar cutoff or
capacity guarantee is introduced.

validate-fulfilment.ps1 -WithPromise installs/tests the optional addon only in
an owned scenario DB, runs the existing standard-field diagnostic separately
from promise tests, and runs validate_dispatch_promise.py for real-connection
races and the server-side Form helper. The latter deliberately commits synthetic
fixtures in that guarded DB so other connections can see them. Owned DB removal
also removes those fixtures. Form helper validation is not browser rendering.
Cleanup and final working-fingerprint checks now have independent error handlers;
forced host/process termination can still bypass cleanup.

## Optional bounded campaign automation - TASK-0007

The source implementation has recorded local validation and explicit owner
acceptance for the bounded TASK-0007 source/test delivery, not a published release or a
working-database installation. operations_campaign_automation depends on
operations_dispatch_promise, purchase_stock and sale_mrp. Standard Odoo remains
the inventory, purchase, manufacturing and completed-dispatch source of truth.
Neither this addon nor a date change physically completes those processes.

oct.campaign.pool configures one company/warehouse stock location, an explicit
product set and responsible user. One pool per warehouse is supported, including
inactive configurations. The stock scope is frozen once a linked campaign order
has been confirmed. Supported goods are storable and untracked; the source must
be the warehouse stock location with one-step make-to-stock customer deliveries.
Multi-step/MTO/ambiguous routes and uncovered unmanaged demand are rejected,
not silently routed or reprioritized. Already reserved outside demand is kept.

Quotation fields explicitly select the pool and Consumer Complete or Corporate
Partial policy. Partner is_company does not infer that contract. Pool/policy/
warehouse/company are frozen after confirmation. Protected confirmation records
retain event time, sequence and actor; cancellation/reconfirmation gets a new
current timestamp without rewriting prior history. Mutable date_order is not
the secondary reservation key.

Reconciliation expands to competing moves in the configured company/product/
source scope, not just the caller's batch. Eligible unprepared demand is ordered
by current accepted warehouse date, current confirmation timestamp and order ID.
Incomplete consumers retain their allocated stock. Picked/prepared and completed
quantities, plus outside reservations, are not reclaimed. Pending/rejected/stale
proposals and operational estimates cannot substitute for the accepted date.
An order without that date is blocked from campaign allocation and dispatch.

Pool mutexes and ORM-written revisions coordinate confirmation, promise responses,
assignment, recorded receipts/production, cancellation and matching move/line
preparation edits. The lock order starts with the pool before the source order.
Private in-process identity tokens distinguish native nested operations; caller
context skip flags do not confer those capabilities. Warehouse actions use
bounded technical access to the linked stock/order scope, not a Sales role grant.
Public pool reconciliation needs Stock Manager or Stock User plus Coordinator;
Sales-only coordinators cannot use it to acquire stock permissions. Company and
source-order security on promise/confirmation history remains in force.

Manual move/raw-line preparation is capped at its pre-call allocated base-UoM
quantity. Batch/default-context/UoM paths use the same atomic bound. Only exact
allocation/completion/private nested-preparation identity capabilities bypass
that bound, not sudo, caller flags or the broader lifecycle event capability.
Public unreserve reconciles priority; direct demand cancellation/retargeting must
use the Sales lifecycle. Ordinary metadata/date updates do not alter entitlement.
Picked moves remain protected as a whole, including partial preparation. To
extend a partly prepared shortage after new stock, warehouse users explicitly
review/unprepare and Check Availability; automatic unpicking/top-up is not claimed.

Consumer finalization checks every current physical line/UoM and a single
customer picking before stock mutation. Move/raw-line/state/mapping paths are
guarded too. Corporate partials preserve the outstanding balance through
backorders; automatic balance cancellation is not a partial-dispatch shortcut.
Combined quant dimensions account for other reservations to reject supported
negative-stock or double-spend attempts. Normal inbound returns are distinct
from unsupported consumer replacement shipments after a prior dispatch.

Derived status and one idempotent source-linked control item provide a responsible
owner and next action for missing promises, shortages and supply risk. Late
confirmed purchase dates for components of open production are a bounded
one-level BoM signal, not recursive procurement, exact demand pegging or a
capacity/arrival guarantee. No supplier/customer/carrier messages are sent.

validate-fulfilment.ps1 -WithCampaign opts into fresh-install tests and
validate_campaign.py in the owned DB while retaining the legacy diagnostic and
promise-only modes. preview-dispatch.ps1 -WithCampaign seeds only opening stock
and synthetic orders in a separate owned preview; it does not manufacture or
dispatch. TASK-0007 and evidence/task-0007 own the executed 81-method/11-case
results, review gate and limitations. Source existence alone is not test evidence.

## Customer-approved shipment batches - TASK-0018

The campaign source now adds protected oct.shipment.plan and plan-row history.
Each numbered batch has one latest date and explicit quantities in the source
sales-line UoMs; all remaining goods must be covered. Coordinators use a
transient proposal/response form. Source-order access and global company rules
apply. CRUD cannot fabricate approvals, including sudo/default-context paths.
Customer evidence is entered by staff; no external customer message is sent.

The latest accepted plan supersedes only remaining work; pending/rejected plans
do not change it. A dedicated protected scope revision detects quantity changes
and restoration without invalidating legitimate completed batches. Completed
native stock moves retain protected plan/batch links, not editable delivery
counters. Acceptance and dispatch serialize through the existing pool/order
mutex protocol. Prepared work must be reviewed/unprepared before new acceptance.

Allocation sorts each batch's quantity against other demand by its latest date,
confirmation event and order ID. Native unchained MTS reservation receives an
additional quantity per request; native move states are recomputed afterwards.
Chained-origin moves are rejected for batch-plan allocation because the native
reservation branch does not honor the same forced-quantity cap. Prepared and
outside reservations are preserved. One exact next batch is dispatched at a
time; early is allowed, overdue or quantity-changed dispatch requires new
approval. Native backorders retain outstanding quantities.
Latest-date checks use the warehouse partner timezone, falling back to the
company partner timezone and then UTC; an RPC timezone cannot extend the day.

A date-only proposal cannot rewrite an accepted quantity plan. With no accepted
batch plan, corporate partial dispatch is blocked; complete remaining dispatch
against the accepted original commitment is still permitted. Consumer behavior
is unchanged. No live installation, upgrade, migration, carrier integration,
capacity feasibility or production guarantee follows from source delivery.
TASK-0018 owns fresh execution/review evidence, not the earlier 81-method count.
