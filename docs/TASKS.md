# Task registry

This file owns task scope, approval, validation evidence, and acceptance. Architecture facts belong in ARCHITECTURE.md; durable decisions in DECISIONS.md; the current snapshot in PROJECT_STATUS.md. A task label alone grants no authority.

## States and approvals

`Draft -> Needs Decision -> Approved -> In Progress -> Review -> Done`

Use `Blocked` with the blocking dependency and next action, and `Cancelled` with the reason. Return incomplete reviewed work to `In Progress`; material scope changes return to `Needs Decision`. Preserve approval and acceptance history.

- Draft: proposal only.
- Needs Decision: an identified question prevents a scope decision.
- Approved: the Product Owner explicitly approved the recorded scope.
- In Progress: approved implementation is underway.
- Review: delivered for review or Product Owner acceptance; not accepted yet.
- Done: evidence satisfies the criteria and the Product Owner explicitly accepted it.
- Unanswered questions, enthusiasm, and earlier assistant promises do not constitute approval.
- Record approver, date (Europe/Berlin), chat/request reference, and exact approved scope. If approval is only available in chat, summarize it here without claiming a signed or immutable audit trail.
- Planning authorization permits analysis and proposals, not the implementation being discussed.
- Code changes after validation/review invalidate the affected evidence until rechecked.

## Task template

Copy this section for a new task:

- ID / title / state:
- Business problem and expected value:
- Scope / exclusions:
- Standard Odoo functionality considered and Community compatibility:
- Proposed custom behavior, or none:
- Data model / integration effects (real vs simulated), or not applicable:
- Acceptance criteria (observable input, action, expected outcome):
- Error and edge cases:
- Security, authorization and multi-company expectations:
- Validation strategy and data isolation:
- Dependencies and unresolved decisions:
- Implementation plan (for complex tasks):
- Approval record (Product Owner, date, request reference, scope):
- Validation evidence (command, environment/database, revision or relevant file digest, exit status, result):
- Skipped checks and reasons:
- Review report and repair rounds (maximum two without further authorization):
- Acceptance record (Product Owner, date, request reference, criteria accepted):

## TASK-0001 - Establish project operating workflow

State: Review

Business problem: earlier discussions mixed proposals, implementation, and test claims. Provide a small, auditable workflow for approved development and evidence-based acceptance.

Scope: create the requested governance documents; adapt verified architecture and existing contribution guidance; conservatively improve .gitignore; verify current Codex review capabilities; demonstrate review on this documentation diff.

Exclusions: ERP behavior, application code, schema/data changes, new modules/dependencies, deployment, remote creation, push, new services, and global Git settings.

Standard Odoo: retain Odoo 19 Community and the existing addon; no new functionality or compatibility dependency is introduced.

Custom behavior / data and integration effects: documentation only; no application or database changes. Reviewer uses existing session tools with an explicit no-edit contract.

Acceptance criteria:

1. AGENTS.md is concise and points to relevant specialist documents.
2. The task registry defines all requested states, explicit approval, required task fields, and Product Owner acceptance for Done.
3. REVIEWER.md defines evidence categories, severity, permissions, fallback, risk-based validation and a two-round repair limit.
4. ARCHITECTURE.md and PROJECT_STATUS.md distinguish verified control-item features from proposed ERP integrations.
5. DECISIONS.md distinguishes approved decisions, observed facts, and unresolved proposals.
6. Ignore rules cover local secrets, private keys and database artifacts while legitimate source and SQL migrations remain visible. No tracked secret is hidden by an ignore claim.
7. Existing business logic, scripts, manifest, CI and runtime configuration match baseline commit d62b6bc2de98ef3e500a2c177d57d007b37ece68.
8. A separate reviewer inspects the actual diff and new files, with its permission limitations documented.
9. Validation commands, results, revision and skipped checks are recorded; no complete automation or strict reviewer isolation is claimed without evidence.
10. A practical planning/approval/implementation/review/acceptance guide is delivered and the task awaits Product Owner acceptance.

Edge cases: untracked governance documents must be included in review; ignored public certificates or database fixtures require explicit review; stale task evidence must be rechecked; unavailable subagents use the documented manual fallback.

Security: no .env values in outputs, no live database writes, no persistent permission widening, no Git history rewrite.

Validation strategy: repository checker, tracked diff whitespace, local-link/content inspection, Git ignore positive/negative checks, redacted secret scan, source-tree comparison, read-only runtime checks, and focused independent review. No runtime test is required for this documentation-only change.

Dependencies: baseline commit exists; repository access and current session collaboration tools are available.

Implementation plan: inspect repository and tools; write governance files and ignore rules; run safe checks; demonstrate review; repair confirmed documentation defects within the limit; hand over for acceptance.

Approval record: Yusuf Ondes, 2026-10-15 (Europe/Berlin), attached request "Codex Project Operating System - Initial Setup", sections 11-12, in the current Codex chat. Authorizes this setup and non-destructive review demonstration, not new ERP feature implementation. Original attachment ID: f5a26697-7c2e-4683-8e18-e3816d9463c8. Setup approval does not mean final acceptance.

Validation evidence (2026-10-15, Europe/Berlin): repository root above,
baseline d62b6bc2de98ef3e500a2c177d57d007b37ece68 plus the eight governance/ignore
working-tree files listed in PROJECT_STATUS.md. No staging or new commit.

| Executed command/check | Environment / exit | Observed result |
| --- | --- | --- |
| python .\scripts\check_repository.py | Host, no DB, 0 | Passed for 42 text files, including new Markdown files. |
| git diff --check | Repository, no DB, 0 | No tracked whitespace errors. New files were separately covered by the repository checker. |
| git diff --exit-code d62b6bc2de98ef3e500a2c177d57d007b37ece68 -- addons scripts compose.yaml .github config | Repository, no DB, 0 | No implementation, script, CI or runtime configuration changes. |
| git check-ignore --quiet --no-index -- PATH, asserted in PowerShell loops | Repository, no DB, assertion wrapper 0 | 26 ignored-artifact cases and 9 visible-source cases passed without creating files. Positive calls exit 0; negative calls exit 1 as expected. |
| PowerShell candidate audit using git ls-files --cached --others --exclude-standard, regex matching and in-memory .env-value comparisons | Host, no DB, 0 | 42 candidates scanned; no high-confidence token/private-key/credential-URL/JWT patterns or exact local-secret matches. Values were never printed. No tracked sensitive-artifact filenames. Heuristic, not an exhaustive secret scanner. |
| PowerShell Markdown-link audit using regex matches and Test-Path | Host, no DB, 0 | All relative file links in candidate Markdown resolved. Remote links were not network-tested by this check. |
| docker compose config --quiet | Existing local configuration, no DB write, 0 | Configuration parsed without displaying resolved secrets. |
| Invoke-RestMethod -Uri http://127.0.0.1:8069/web/health -TimeoutSec 5 | Existing local Odoo, read-only, wrapper 0 | status=pass. This is service evidence, not UI or business acceptance. |
| docker ps --format and psql SELECT queries via docker exec | Existing containers / operations_control_tower, read-only, 0 | Healthy Odoo/PostgreSQL; installed addon version and 14 item states recorded in PROJECT_STATUS.md. |
| codex --version; codex --help; codex review --help | Installed CLI, no DB, 0 | Version 0.159.2; native review options present. Sandbox temp-directory permission warnings occurred; no review execution was inferred from help. |
| Get-FileHash -Algorithm SHA256 on the eight changed files | Host, no DB, 0 | Content fingerprints produced in this chat for the pre-review working tree. |

Ignore test inputs (exact paths; no files created):

- Expected ignored: .env, .env.local, secrets/example.txt,
  credentials/example.json, private.pem, private.key, identity.p12, identity.pfx,
  id_rsa, id_ed25519, local.db, local.db-journal, local.sqlite, local.sqlite3,
  local.sqlite-wal, local.sqlite-shm, local.sqlite3-wal, local.sqlite3-shm,
  snapshot.dump, snapshot.backup, snapshot.bak, snapshot.sql.gz,
  snapshot.sql.zip, pgdata/PG_VERSION, filestore/data,
  addons/test/__pycache__/test.pyc.
- Expected visible: .env.example, AGENTS.md, docs/TASKS.md, docs/REVIEWER.md,
  docs/DECISIONS.md, docs/PROJECT_STATUS.md, addons/test/migrations/001.sql,
  addons/test/fixtures/sample.json, config/README.md.

Skipped checks and reasons: no smoke, compileall, bootstrap, live upgrade,
migration, demo-data load or browser interaction test was run. This task changes
only documentation/ignore rules, and live data/schema changes are excluded.
No remote CI, native /review execution, custom role-loader or repair-cycle
automation is claimed. Existing baseline smoke results are historical evidence,
not rerun evidence for this setup.

Review demonstration, round 1: separate agent /root/setup_reviewer inspected the
actual three tracked changes and all five untracked governance documents under
REVIEWER.md. It also read the attached approval and relevant baseline source.
Result: No confirmed defects found. No repairs required; zero repair rounds used.

The reviewer independently checked HEAD/branch/no remotes, tracked diff,
untracked scope, whitespace, and source/script/CI/Compose equality with the
baseline. Read-only Git required scoped escalation after sandbox worktree
errors; no persistent permission change was made. It read files, searched source
and computed SHA256 hashes. It did not read .env, mutate data/services, stage,
commit or edit files.

Report categories:

- Confirmed defects: none.
- Potential risks: shared-service smoke effects, incomplete cleanup assertions,
  broad ignore exceptions and heuristic secret-scan limits remain disclosed.
- Missing coverage: no new runtime behavior; upgrade/demo/browser tests, native
  /review, CLI review execution and custom-role loading remain unexecuted.
- Optional improvements: recheck final evidence additions and fingerprints.
- Unverified assumptions: reviewer treated runtime, secret-scan and count
  results as developer execution evidence; it did not independently rerun them.

Reviewed SHA256 fingerprints below identify the independent review snapshot.
TASKS.md and PROJECT_STATUS.md then received only this outcome/evidence addendum;
their later hashes belong in the final execution transcript rather than
self-referential hashes inside those files.

| File | Reviewed SHA256 |
| --- | --- |
| AGENTS.md | 97540F75FCA6E2F5753D6FEC82E598903B756B161083122725D96BFA01B8D72F |
| .gitignore | 5BEC12697B4006C52FE17213CFF3CAC299425E145F5866AA404F263ACF750851 |
| CONTRIBUTING.md | 406EDDBA87C65B19D3BE03F60441F721729156E6413A816AAC74E6E2F604705B |
| docs/ARCHITECTURE.md | 567E20BE49205B1077600BC106C2A035D4C834D8FDEAC60B2103902B47456906 |
| docs/DECISIONS.md | 95A94CA6B5FEE3542C200F4320A557E31DCA55E3604D9ACDF6143676B51740DB |
| docs/REVIEWER.md | 016D7E8176D5F5D0201426B0AC73B955982B91B3CB9053B30F69E1FC50B0F62D |
| docs/TASKS.md | DFB9E5269E4F32D1F3034FA853621A5639979085A1F601B03AF4459DA4C4210B |
| docs/PROJECT_STATUS.md | 786B2E4DB56A30D9BC3742670EFBBB3D3A423CE7D882B2D9DE5B249277E470BD |

Additional main-agent read-only check:
docker exec operations-control-tower-db-1 psql -U odoo
-d operations_control_tower -Atc
"SELECT COUNT(*), md5(string_agg(row_to_json(t)::text, '' ORDER BY id)) FROM operations_control_item t;"
returned 14 rows with fingerprint 17f2a87362f026a248dc420227dd452f (exit 0).
This fingerprints that table at check time, not the entire database or a backup.

Demonstrated: separate-agent delegation, actual-diff inspection and reporting.
Not demonstrated: strict read-only sandbox, a repair cycle, unattended
orchestration, an ERP feature delivery cycle, or Product Owner acceptance.
Implementation is ready for acceptance; retain Review until that decision.

Acceptance record: not yet provided. Do not mark Done.

## TASK-0002 - Define one order-to-dispatch portfolio scenario

State: Needs Decision

Business problem and value: identify a demonstrable operational coordination problem that the Product Owner can explain to technical and operations audiences.

Proposed scope: use the Christmas/New Year campaign as a fictional context for
own production and discounted consumer/corporate orders. Analyze normal
fulfilment, stock shortage, quality hold, and supplier-delay variants; identify
actors, actions, records, expected outcomes and completion conditions. Compare
standard Community functionality with the gap that could justify custom code.

Exclusions: implementation, modules, data imports, migrations, selecting all nine previously discussed candidate areas, and assuming real HOLY practices.

Standard Odoo: assess Sales, Inventory, Purchase, Manufacturing and
quality-location options against the actual Community environment before any
dependency proposal; this is planning, not authorization to install.

Custom behavior: undecided; consider order blocker/owner/next-action visibility only if standard features leave an evidenced gap.

Data/integration effects: none during planning; proposed examples use a fictional company and synthetic data. Real vs simulated external interfaces must be identified.

Proposed acceptance criteria: one understandable end-to-end scenario, named users and actions, a standard/custom gap table, explicit first-release exclusions, observable outcomes, and open decisions ready for Product Owner approval.

Error/edge cases: partial delivery, withheld quality release, overdue supplier arrival, a shared blocker affecting multiple orders, and an order with no blockers.

Security/authorization: propose who may release a hold or authorize partial shipment; do not assume all operations users may do so.

Validation strategy: inspect applicable standard functionality and trace example outcomes; no live changes or runtime migrations.

Confirmed business rules: own production, two customer types and corporate
partial shipments (D-007); earlier promised dispatch date takes precedence over
customer type (D-008); equal dispatch dates use earlier order confirmation
(D-009); individual consumers receive one complete customer shipment when all
products and quantities are ready (D-010); date-change proposals take effect
only on explicit customer acceptance, with rejection retaining the existing
commitment (D-011). These decisions do not prove implementation.

Dependencies/open decisions: reservation handling for incomplete consumer orders;
missing-date handling and identical confirmation timestamps; per-order vs per-shipment promises; reservation
and quality-release authority; production recipes, capacity, supplier lead
times and working calendars; learning priorities and available time.
The proposed three-working-day target remains unapproved.

Business-rule approval record: Yusuf Ondes, 2026-10-15, current chat's explicit
choices referenced in D-007/D-008/D-009/D-010/D-011. The latest instruction
confirmed the customer-approved date-change flow only. Overall first-release scope, technical design,
module installation and feature implementation are not approved. Planning
evidence is the illustrative walkthrough below, not an executed system test.
TASK-0001 acceptance remains separate and pending.

### Illustrative walkthrough - not an approved fixture

All quantities, dates, customer names and production timing here are proposed
synthetic assumptions, not facts or approved capacity commitments. One product
is used to make the allocation arithmetic inspectable. No data is loaded.
For this example only, 500 units are unreserved, quality-cleared and otherwise
eligible. The consumer full-order rule is now approved in D-010; quantities,
dates, readiness and production timing remain illustrative assumptions.

| Demand | Type | Quantity | Promised dispatch | Initial allocation | Remaining |
| --- | --- | ---: | --- | ---: | ---: |
| ORDER-A | Individual consumer | 200 | 2026-12-15 | 200 | 0 |
| ORDER-B | Corporate | 600 | 2026-12-16 | 300 | 300 |
| ORDER-C | Individual consumer | 100 | 2026-12-17 | 0 | 100 |

Expected reasoning: ORDER-A precedes ORDER-B by its date; ORDER-B receives the
remaining 300 before ORDER-C despite the latter being a consumer order.
No order exceeds its demand and initial allocations total exactly 500.
On dispatch of those quantities, 400 units of demand remain open. The corporate
order is only partly dispatched, not fully fulfilled.

Proposed normal path: suppliers provide required inputs, production completes
400 additional eligible units before dispatch on 2026-12-16, then 300 satisfy
ORDER-B and 100 satisfy ORDER-C. Total dispatched becomes 900 with zero
remaining demand. Actual recipes, quantities, capacity and quality checks must
be specified before this can become an executable acceptance test.

Proposed disruption: packaging from one supplier delays those 400 units until
2026-12-18. The remaining 300 for ORDER-B and 100 for ORDER-C miss their
illustrative promises. Procurement confirms the revised arrival; production
assesses readiness; operations sees affected demand and next actions.
Under D-011, a revised estimate/proposed date does not replace the accepted
commitment while awaiting a response or after rejection. Explicit acceptance
establishes the new operative date for the covered dispatch; retain the original
and change evidence. This does not settle which quantities a corporate promise
covers. Rejected changes leave the risk visible; meeting the date is not guaranteed.

Installation, runtime tests and implementation: not performed. Overall task
approval, implementation plan, acceptance and Done status: not yet provided.

Planning-document validation, 2026-10-15: from the repository root, no database,
python .\scripts\check_repository.py passed for 42 files (exit 0);
git diff --check passed (exit 0); and git diff --exit-code
d62b6bc2de98ef3e500a2c177d57d007b37ece68 -- addons scripts compose.yaml .github
config returned 0. No application/script/runtime changes. Runtime checks were
not needed or run for this planning-document update.

Separate focused review by /root/planning_review found no confirmed defects
in D-007/D-008, TASK-0002 or the corresponding status. It confirmed the
approval boundaries and numerical walkthrough. Its Git access was sandbox
limited, so it relied on the root's Git evidence; it read documents directly
and made no edits. Zero repair rounds. This evidence note was then appended;
the preceding review did not constitute Product Owner acceptance of the draft.

### Standard-versus-custom assessment - planning evidence

Assessment date: 2026-10-15 (Europe/Berlin). The Product Owner agreed to continue
the previously described standard-feature comparison. This authorizes planning,
not module installation, implementation, migration or task acceptance.
TASK-0002 remains Needs Decision.

Sources inspected: public official Odoo 19.0 source, plus read-only files in the
existing container under /usr/lib/python3/dist-packages/odoo. No ORM workflow
was executed. Source availability is not proof that the modules are installed
or configured. The custom addon still declares only base/web.

| Need | Standard candidate and evidence | Remaining check / custom-development decision |
| --- | --- | --- |
| Customer orders and dispatch records | sale + sale_stock + stock provide the order/delivery link. | Define consumer/corporate contract policy; person/company fields alone do not define it. |
| Corporate partial dispatch | stock has backorder records and Ask/Always/Never settings. | Verify 600 ordered, 300 shipped, 300 still open across repeated shipments. Never cancels outstanding demand and cannot satisfy retained-balance behavior. |
| Own production | mrp contains BoMs and manufacturing orders; its manifest declares LGPL-3 and product/stock/resource dependencies. | Define synthetic recipe, units, yield and feasible timing; verify installation and actual stock consumption/output. |
| Raw-material procurement | purchase + purchase_stock link orders to receipts. | Verify supplier delay and component availability in the scenario; no real supplier API is required. |
| Stock and shortage visibility | Standard forecast reports show incoming/outgoing demand and manufacturing needs. | Compare these reports and standard activities with the proposed coordination view before claiming a reporting gap. |
| Dispatch-date allocation | Standard reservation methods are configurable; different assignment paths use different sort criteria. | D-008 needs behavioral verification. Do not assume a universal earliest-date rule or commission a custom allocation engine yet. |
| Full consumer shipment | Standard shipping policy influences planning/readiness. | D-010 now requires complete consumer dispatch; source does not establish a hard partial-validation prohibition. Verify UI/direct-validation bypasses before selecting configuration or an extension. |
| Quality eligibility | Location/routes may support a segregated stock flow. | A location name alone is not a quality block. Define release authority and prove exclusion before treating this as a safeguard; no Quality app dependency is assumed. |
| Shared blockers, owners and actions | The current Control Item holds owner/next action; standard records also support operational follow-up. | Assess links from one blocker to affected orders/production/procurement. Extend only for a demonstrated coordination gap, without copying stock or order balances. |

Primary references:

- [Manufacturing manifest](https://github.com/odoo/odoo/blob/19.0/addons/mrp/__manifest__.py)
- [Sales/stock bridge manifest](https://github.com/odoo/odoo/blob/19.0/addons/sale_stock/__manifest__.py)
- [Purchase/stock bridge manifest](https://github.com/odoo/odoo/blob/19.0/addons/purchase_stock/__manifest__.py)
- [Reservation methods](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/shipping_receiving/reservation_methods.html)
- [Partial delivery and backorders](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/shipping_receiving/setup_configuration/multipack.html)
- [Forecast report](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/reporting/forecast.html)
- [Picking assignment and validation](https://github.com/odoo/odoo/blob/19.0/addons/stock/models/stock_picking.py)
- [Move assignment after arrivals](https://github.com/odoo/odoo/blob/19.0/addons/stock/models/stock_move.py)
- [Reservation scheduler](https://github.com/odoo/odoo/blob/19.0/addons/stock/models/stock_rule.py)
- [Sales commitment field](https://github.com/odoo/odoo/blob/19.0/addons/sale/models/sale_order.py)
- [Sales procurement dates](https://github.com/odoo/odoo/blob/19.0/addons/sale_stock/models/sale_order_line.py)
- [Quant location gathering](https://github.com/odoo/odoo/blob/19.0/addons/stock/models/stock_quant.py)
- [Partner classification fields](https://github.com/odoo/odoo/blob/19.0/odoo/addons/base/models/res_partner.py)

Access limits: direct official documentation page fetches timed out; cached
official search excerpts were accessible. Public GitHub source was accessible
and independently inspected by /root/odoo_standard_audit. No third-party app
store claims are used. The public 19.0 branch is mutable; installed-file
fingerprints below identify the local source cross-check instead of assuming
exact online/runtime equivalence.

#### Critical source observations

Installed stock_picking.py action_assign (lines 1203-1215) sorts urgency before
deadline/date/ID. Installed stock_move.py _trigger_assign (2634-2655) uses
priority/date/ID and related-reference preference; stock_rule.py (710-713)
uses reservation date, priority, date and ID. These paths do not establish the
same global promise-date allocation. Existing reservations and late-added
earlier commitments require separate cases.

Installed sale.order.commitment_date (sale_order.py 88-92) is labeled customer
Delivery Date. sale_stock procurement (sale_order_line.py 292-293) derives its
deadline from that field and offsets planned date by security lead time.
Do not silently map it to the promised warehouse dispatch date in D-008.
Select an explicitly defined mapping or justify a separate field after review.

The public validation/backorder trace does not show move_type='one' as a hard
partial-dispatch guard. A readiness label cannot establish authorization.
The installed backorder selection confirms that Never cancels remaining
products (stock_picking.py 133-139).

Installed stock_quant.py gathering includes descendants of a source location
(line 759). Quarantine beneath a reservable source is not sufficient evidence
of exclusion. Test sibling segregation/routes, direct moves and release
permissions. Customer segmentation likewise needs a business definition:
company/person is not automatically a shipping-contract policy.

Local source cross-check: docker exec operations-control-tower-odoo-1 python3
-c <read-only pathlib/ast/hashlib audit>, exit 0, no database used. Three
manifests and the following sources were read; no source method was called.
The source subagent only inspected public files and made no runtime claim.

| Installed source relative to odoo package | SHA256 |
| --- | --- |
| addons/stock/models/stock_picking.py | 96fe35c33865609889cbf8747fdd4d2be18a67a0bfa554507ff207f18bb2ee25 |
| addons/stock/models/stock_move.py | 88b0c0445fad6291122cefae290c4822d981fb45e441d8e8ef211aa82bdeb3fb |
| addons/stock/models/stock_rule.py | 6ba0d0f12b2b8062ed771a0a6140e79bfa53a0c3970f2d531e8cd41691617114 |
| addons/sale/models/sale_order.py | c2e51afe8919f3de53ad6504477a01fbebf4bb58cfd56836aa65d001a1734514 |
| addons/sale_stock/models/sale_order_line.py | 1adf21d433c965029f77a83df9d4f91b5e34ce81dcf4157b3b6c2aae0d8fee16 |
| addons/stock/models/stock_quant.py | 6d894fea409598074a04d8ca805d7d4f974b5b34357e0ce915ec58d492a19362 |

### Proposed first-release boundary - not approved

First demonstrate standard Community flows with one company, one warehouse,
one manufactured SKU, a simple synthetic BoM, two suppliers, and the three
illustrative orders above. Use discounts as entered order data; no live web
shop, payment service or pricing engine is required for this demonstration.

Candidate applications are Sales, Inventory, Purchase and Manufacturing,
including assessed standard bridge/transitive dependencies. This is not an
instruction to install them or alter the current addon manifest.

The normal path is procurement/receipt of inputs, production of the outstanding
400 units, and dispatch with the corporate balance retained between shipments.
The disruption path delays a required packaging input, exposes affected demand
and records the responsible actor, next action and revised estimate.

Run a comparison with standard forecasts, source-record links and activities.
Only then select a minimal custom extension, if needed: explicit dispatch
promise semantics, a shared-blocker link/view using the existing Control Item,
or a narrowly scoped reservation guard. A separate allocation engine and a
duplicate stock ledger are not justified by this source review.

Formal quality automation remains an unresolved scope choice. Proposed V1 may
include a basic, verified eligible-stock boundary if required by the selected
scenario; it must not claim a quality-release safeguard from location labels.
Advanced CAPA, maintenance, real WMS/carrier APIs, production deployment,
capacity optimization and high-volume performance claims are outside this
proposed first release unless separately justified and approved.

### Proposed validation cases - not executed

Before installing anything, approve a disposable scenario database/environment,
the module set and working-data preservation checks. The current smoke script
tests only the existing addon; it cannot prove this new scenario. If services
or filestore are shared, disclose that instead of claiming stack isolation.

| Case | Proposed observable outcome / decision gate |
| --- | --- |
| Normal arithmetic | In the stated unreserved eligible-stock fixture, allocate 200/300/0 from 500; after production of 400, outstanding quantities become zero, with no double allocation or negative eligible stock. |
| Corporate backorders | Successive dispatches retain the unshipped balance; only the actually dispatched amount counts as shipped. Test accidental remaining-demand cancellation explicitly. |
| Date before customer segment | With the stated unique dates, allocation follows A/B/C regardless of which is consumer/corporate. |
| Conflicting urgency and automatic arrival | Run manual reservation, incoming-stock auto-assignment and scheduler separately; record whether each respects D-008 under urgency/reference differences. A mismatch needs a configuration or limited-extension decision, not a fabricated pass. |
| Already reserved stock | Record behavior when a later promise already holds stock; the expected reallocation/override policy needs approval before this becomes a passing acceptance test. |
| Equal dispatch dates | D-009 requires the earlier-confirmed order to receive priority. Customer type must not override this secondary criterion. This is a future behavioral test, not an executed result. |
| Missing dates or identical confirmation timestamps | Expected outcome still needs a decision. Stable ID as a final tie-break and review of missing promises remain proposals. |
| Packaging delay | Remaining 300/100 units have a visible impacted promise and accountable next action. D-011 requires separate original/current/proposed dates and customer-response history in the future design. |
| Date change accepted | Only an explicit response covering the proposal updates the operative date for the affected dispatch. Preserve the original date and acceptance evidence. No automatic acceptance is inferred. |
| Date change rejected or unanswered | Retain the existing commitment and its risk/overdue visibility; a proposed date does not silently alter planning priority. On rejection, record the next operational action without promising impossible fulfilment. |
| Consumer full shipment | Under approved D-010, no partial customer dispatch when any required product or quantity is missing; one complete dispatch when all are ready. Test multiple lines and both UI/direct validation. These outcomes are requirements, not executed results. |
| Quality eligibility and company boundaries | If included, held stock stays unavailable to reservation/dispatch and unauthorized release is rejected. No cross-company access through any new links. |
| Repeat/reversal | Repeated updates do not duplicate blockers or allocate twice; cancellation and date changes need defined reconciliation rules. |

Decisions needed before the first implementation scope: incomplete-consumer
reservation handling; missing dates/identical confirmation timestamps; warehouse-dispatch promise semantics and
partial-order deadlines; existing reservations; quality scope/authority; and
approval of a disposable validation environment and candidate modules.

The equal-date tie-break was subsequently approved in D-009. The approved
ordering is promised dispatch date, then order confirmation time. Consumer
full shipment was subsequently approved in D-010; do not request that approval
again. Date renegotiation is approved in D-011: propose, then use the new date
only if explicitly accepted; otherwise retain the existing promise. Corporate
promise scope (complete fulfillment vs agreed partial schedule), proposal
authority and response evidence remain design questions, not new approvals.

Assessment-document checks, 2026-10-15: python .\scripts\check_repository.py
passed for 42 text files; git diff --check passed; git diff --exit-code
d62b6bc2de98ef3e500a2c177d57d007b37ece68 -- addons scripts compose.yaml .github
config returned 0. All commands ran from the repository root, without a test
database, and exited 0. No ERP scenario/runtime/installation test was executed.
The reviewed revision is the uncommitted planning-document content over that
baseline; source-code audit fingerprints appear above.

Separate focused review by /root/planning_review found no confirmed defects.
It reviewed source-vs-runtime claims, approval limits and consistency with the
source audit; it did not independently rerun Odoo source/runtime verification.
Reviewed TASKS.md SHA256:
7634F643465D008348DF2D4905F0F4FF7C60B6CF9B83C48E0EE8DC2F1C18DB73.
Reviewed PROJECT_STATUS.md SHA256:
B4D29BF446CA46646D79E356E8C463DB13C56E0A44A18C43BF172B510B487148.
Zero repair rounds. This evidence-only note was added after that review;
TASK-0002 remains Needs Decision, with no Product Owner acceptance inferred.

D-009 documentation update: the Product Owner's latest yes is recorded as
approval of a business rule only. No feature, module, data or schema change
was performed. From the repository root, without a database, python
.\scripts\check_repository.py passed for 42 files, git diff --check passed,
and the baseline comparison for addons/scripts/compose.yaml/.github/config
returned no changes (all exit 0). Separate focused /root/planning_review found
no confirmed defects in the three changed planning documents and confirmed
that stable ID remains a proposal. Zero repair rounds; no Odoo scenario test
was run. Reviewed revision: D-009 and corresponding TASK-0002/status text over
baseline d62b6bc2de98ef3e500a2c177d57d007b37ece68, plus this evidence-only note.

D-010 update: the latest explicit Product Owner approval establishes complete
consumer dispatch, alongside existing corporate partial shipment. Scenario
implementation, module installation and overall task acceptance remain
unapproved. Validation covers documentation only, without a runtime database.

Executed D-010 checks from the repository root: python
.\scripts\check_repository.py passed for 42 files; git diff --check passed;
git diff --exit-code d62b6bc2de98ef3e500a2c177d57d007b37ece68 -- addons scripts
compose.yaml .github config returned 0. All exited 0. No runtime test was needed
or run. Focused /root/planning_review found no confirmed defects in the three
planning documents, confirmed the approval limits and open questions, and made
no edits. Zero repair rounds. Reviewed TASKS.md SHA256 before this evidence note:
52F04A865E32D7A0023FB9471A2CC278C0760843DD1D616866F477F36564FBDE.

D-011 planning update, 2026-10-15: recorded the Product Owner's explicit
customer-acceptance rule, including separate pending/accepted/rejected handling.
From the repository root, no database: python .\scripts\check_repository.py
passed for 42 files; git diff --check passed; baseline comparison for addons,
scripts, compose.yaml, .github and config returned no changes (all exit 0).
No runtime test was needed or executed for these documentation-only edits.
Separate /root/planning_review found no confirmed defects or approval overreach;
it read relevant documents without mutations or runtime checks. Zero repairs.
Reviewed TASKS.md SHA256 before this evidence-only note:
9895EF83F62F27767FF34F22829C5EF2FFC223ED2D394452E301901A9234C797.
TASK-0002 remains Needs Decision; no general implementation approval or
Product Owner acceptance of the full task is inferred.

## TASK-0003 - Validate the standard fulfilment baseline

State: Review

Approval: Yusuf Ondes, 2026-10-15 (Europe/Berlin), explicitly approved continuing
the immediately preceding first-delivery plan in this chat. This authorizes a
separate disposable test database and standard Odoo Sales/Inventory/Purchase/
Manufacturing validation for the stated synthetic scenario. It supersedes the
earlier prohibition on module installation only within this test database;
the working database and current addon dependencies remain unchanged.
TASK-0001 and TASK-0002 acceptance is not inferred.

Business problem/value: establish which approved fulfilment rules standard
Community actually supports before proposing custom application behavior.

Scope: repeatable repository-local validation runner and ORM scenario; one
manufactured SKU, one warehouse, two input suppliers, 500 initial finished units,
three orders of 200/600/100, receipt/production of 400 more units, corporate
backorders, date/confirmation ordering observations, consumer full-dispatch
behavior, supplier delay and date-change capability assessment.

Exclusions: custom allocation/promise features, working DB changes, live customer
messages, new services/dependency versions, deployment, remotes and push.
No standard-behavior mismatch is to be silently fixed as part of this task.

Standard Odoo: install sale_management, sale_stock, purchase_stock, mrp,
sale_mrp and their standard dependencies only in a fresh named test database.
Install the unchanged current control addon there for compatibility checks.
Use ORM, normal purchase/receipt/manufacturing/dispatch actions and synthetic
data. Do not write SQL into Odoo business tables.

Acceptance criteria:
1. Unique guarded oct_scenario_<guid> DB; refuse existing or working DB targets.
2. Module installation succeeds in the disposable DB.
3. Standard procurement, receipts, production and corporate backorders preserve
   the synthetic demand arithmetic; verify 500 initial + 400 produced = 900
   dispatched with no double-counted remaining balance.
4. Observe date priority under manual/automatic reservation and urgency;
   observe same-date confirmation ordering and consumer partial-validation
   enforcement. Report unsupported rules as gaps, not green acceptance.
5. Assess supplier delay and customer date proposal/accept/reject requirements;
   retain a clear distinction between an observed standard field/action and a
   not-yet-implemented business workflow.
6. Remove only the owned test DB; use an ephemeral container data directory so
   the test does not create filestore data in the shared Odoo volume.
7. Verify working module states and control-item fingerprint before/after;
   preserve the working database and initial Git history.
8. Record actual commands, revision/digests, environment, exit/results, skipped
   cases and independent review before handover. Owner acceptance is separate.

Security/edge cases: no logged credentials, no .env contents in reports; reject
an unsafe DB name; no fallback to operations_control_tower. Cleanup failure
must fail validation. Shortages, repeat backorders and lower-priority competing
orders must not be confused with fulfilled demand.

Implementation plan: inspect installed APIs; implement guarded runner/scenarios;
run static checks and fresh installation; execute observations with assertions;
verify cleanup/main-state preservation; review actual changes and rerun affected
checks within at most two repair rounds; report gaps and proposed next scope.

Isolation: test database is separate; PostgreSQL/Compose services and Docker
network are shared. One-off Odoo has no cron threads and uses an ephemeral data
directory. The ORM shell disables HTTP. Odoo's test-enable mode overrides
no-http during addon tests; bind its listener to container loopback, with no
published service ports. Do not claim full stack isolation.

### Execution evidence - 2026-10-15

Runtime command from the authoritative repository: .\scripts\validate-fulfilment.ps1.
Revision: uncommitted validation scripts over baseline
d62b6bc2de98ef3e500a2c177d57d007b37ece68; application code is unchanged.
Environment: existing Compose services, Odoo 19.0-20260926, PostgreSQL 15.
No image pull, bootstrap, working DB upgrade or service restart was performed.

First run: oct_scenario_76b2d34d3e7444498171c0ccabc812dd, exit 1. Fresh install
and eight addon test methods passed. Earlier scenario assertions passed, but
the final incoming-assignment probe failed because stock.move no longer accepts
the old name field. Removed that fixture field, strengthened open-order date
propagation evidence, and reran the complete runner. This was development/debug,
not a completed acceptance run. Cleanup and working-state comparison passed.
Test-enable also activated an unpublished HTTP listener despite no-http; the
runner now explicitly binds that test-only listener to container loopback.

Second run: oct_scenario_86391de1fbcf410dbef5ecb8c35e394a, exit 0. Requested
modules and standard transitive/auto-installed dependencies installed in the
disposable DB. Unchanged control addon: 0 failures, 0 errors in 8 test methods
(the stats counter includes fixtures and reports 12). ORM observations completed:

| Case | Observed result | Business interpretation |
| --- | --- | --- |
| Standard install | All six requested modules installed | Pass within the test DB only. |
| Input shortage | MO confirmed, zero raw inputs reserved | Shortage visible; no proof of a hard negative-stock block. |
| Purchase delay | Receipt deadline followed input PO date change to 2030-12-20 | Date propagation works; customer renegotiation/feasibility workflow remains a gap. |
| Main demand | Initial allocation 200/300/0; produce 400 from two purchased inputs; deliver 200/600/100 | 500 + 400 = 900; final finished and component stock zero; no open customer pickings. |
| Corporate backorders | 300, then 200, then 100; balances 300 then 100 | Repeated partial dispatch preserves demand arithmetic. |
| Promise vs urgency | Later urgent order reserved 1; earlier promise reserved 0 | Universal promise-first policy is not enforced. |
| Equal promise | Later confirmation reserved 1; earlier confirmation reserved 0 | Synthetic confirmation tie-break rule not enforced. |
| Consumer complete policy | Requested 2, sent 1, remaining backorder 1, picking_policy=one | Standard readiness preference does not enforce the approved hard block. |
| Prior reservation | Later order kept 1; newly entered earlier order got 0 | No automatic reallocation; the business reallocation policy remains undecided. |
| Incoming auto-assignment | New receipt allocated 1 to earlier promise, 0 to later | Works for this controlled path, not proof of universal ordering or scheduler behavior. |
| Direct date change | Admin edited an open consumer order date; open move deadline followed | Explicit customer acceptance is not an enforced standard gate. |
| Date meaning | Standard commitment_date is customer Delivery Date | A warehouse dispatch promise still needs an explicit design. |

The machine result groups these into 11 cases: 3 passes, 7 gaps, 1 observation.
A successful runner exit means its observations/assertions completed, NOT that
the business requirements all pass. No custom gap fixes were implemented.

Both owned test databases were dropped and their absence verified. The script
rolled back all scenario ORM fixtures before removal. One-off container data
directories were ephemeral, not shared filestore paths. Their synthetic test
data was intentionally removed and is reproducible by rerunning the script.
Working DB before/after: eight named module states unchanged; control items 14,
row-content MD5 17f2a87362f026a248dc420227dd452f unchanged. This is a scoped
preservation check, not a bytewise proof for every working database table.

Static checks from repository root, no DB: check_repository.py passed for 44
text files; Python AST parse and PowerShell parser passed; isolated guard tests
accepted 1 valid name and rejected 5 unsafe names in PowerShell, and accepted
1/rejected 3 in Python. These guard checks executed only extracted guard code,
not the full runner, and do not simulate a dropped connection or host crash.

Limitations/skips: administrator ORM only, one company/warehouse, one primary
manufactured SKU plus isolated probe products, one-unit BoM inputs, synthetic
500-unit stock seeded with the standard stock.quant ORM helper. Standard purchases,
receipts, manufacturing and dispatch actions run after seeding. Fixture dates
are December 2030; equal-promise confirmation timestamps are deliberately set
after action_confirm. This is neither real historical audit evidence nor a
Christmas calendar configuration. Customer Delivery Date is a zero-lead proxy
only. No browser, scheduler run, carrier, quality, multi-company business-flow,
multi-line consumer, migration, concurrency, capacity/lead-time feasibility,
live supplier arrival or customer accept/reject workflow test was performed.
Addon access-control tests passed, but that is not Sales/Inventory role coverage.
No external messages were sent; no remote, push, deployment or new commit.

Final checks from repository root: text checker 44 files, Python AST,
PowerShell parser, git diff --check, existing application/setup/CI/config
baseline comparison all passed (exit 0). The baseline comparison included
addons, compose.yaml, .github, config, smoke-test.ps1, bootstrap.ps1,
upgrade.ps1 and check_repository.py; only the new validation scripts were added.
Working HTTP health passed, both existing services stayed healthy, and separate
read-only enumeration found no remaining scenario DB or one-off container.
The .env file remains untracked/ignored. Changed candidate contents had zero
configured DB-password exact matches or high-confidence token/private-key
pattern matches; values were not printed. This scan is heuristic, not proof
that every possible secret pattern is covered. Git HEAD remains the initial
commit, with no remote and no new commit.

Local Odoo image ID used by the runner matches the running service image:
sha256:dd9013e669caaa23d26765dc55814655eaeecca7cfc2c265dbabae913bce22fd.
Validated and reviewed script SHA256:
- validate-fulfilment.ps1: DAC39531D635E8EF21DD8965191ADB33B2C1AC5F946DFDA54F2CD503FFCFC0D0
- validate_fulfilment.py: 4AB3E16565F6E7EF172336C86ACB88F3B2551F4444B67B957B06D7DBD4BF0E4E

Separate final reviewer /root/validation_audit read both full scripts, task and
status additions, relevant decisions and the review protocol. It found no
confirmed defects. Non-blocking risk: a drop/absence-verification exception
skips the final fingerprint comparison because cleanup and comparison share
one try; the runner still fails explicitly. Process/host termination can bypass
cleanup. Fault-injected createdb/drop failures, interruptions and fingerprint
mismatches were not exercised. These are coverage limits, not reproduced data
loss or a claim that cleanup always succeeds. Scripts were not changed after
review. One final review round, zero requested repair rounds.

Reviewer commands: Get-Content (including numbered views), Get-FileHash,
git status --short and git diff --stat against the baseline. It did not read
.env, run runtime tests or mutate files/services/data. Runtime results were
developer evidence, not independently rerun. No separate technical read-only
sandbox was configured. Pre-evidence-note reviewed document SHA256:
TASKS.md 3310F7EFABEF2C5896F155E05A2AC48F6FC5942F119DD6B329E23F13252B1449;
PROJECT_STATUS.md 5754F42DD94CF2BAF5301349A257D65CBBB4B723BB86BE9DCE3EA926FD118D42.
This final status/evidence note changes those document hashes only.

Acceptance: not yet provided; do not mark Done automatically.

## TASK-0004 - Dispatch promise and customer-response gate

State: Done

Final acceptance: Yusuf Ondes, 2026-10-15 (Europe/Berlin), explicitly accepted
the TASK-0004/TASK-0005 Review handover and requested continuation to Done.
Accepted scope is the reviewed source/disposable-test delivery, including the
TASK-0005 UI repair and evidence, not a working-system installation. See the
shared acceptance closeout at the end of TASK-0005. Earlier pending-acceptance
statements below are historical records, superseded by this explicit acceptance.

Planning authorization: Yusuf Ondes, 2026-10-15 (Europe/Berlin), said to continue
after the offer to prepare a small, testable development scope for promised
dispatch date -> proposal -> customer acceptance/rejection. This authorizes this
draft, not custom implementation, module installation or working DB changes.
TASK-0003 remains Review; its acceptance is not inferred from permission to plan.

Implementation approval: Yusuf Ondes, 2026-10-15 (Europe/Berlin), explicitly
answered yes to proceeding with TASK-0004 and its three recommended choices,
developing/validating only in a disposable test database. The scope and A01-A12
below are now the approved implementation target, not completed capabilities.
Corporate remaining-order coverage, manual coordinator response evidence and
stale-scope protection are recorded in D-012. Working DB installation remains
excluded; TASK-0001/0002/0003 final acceptance is not inferred.

Implementation plan recorded before code: add the optional
operations_dispatch_promise addon (depends sale_stock and unchanged control
addon); implement one order promise plus protected proposal/response history,
dedicated coordinator and source-sale/company access, server-side guarded CRUD,
order/line row locking and revision/scope snapshots; add a compact sales form
entry and input wizard. Compute stale applicability from current scope, retain
stale response evidence and finalize obsolete proposals on response/reproposal;
do not hook or block stock dispatch. Build normal-role/security/rollback tests
and a genuine independent-transaction race probe. Extend the guarded runner
with explicit optional-addon test selection, preserving the standard diagnostic.
Run static/fresh-install/scenario/form checks, verify owned DB cleanup and
working fingerprint, then separate review and at most two repairs. No commit,
push, working DB install, scheduler or stock-date mutation.

Business problem/value: standard commitment_date is a customer Delivery Date
and permits direct edits without a customer-response gate (TASK-0003). Preserve
what was promised and distinguish it from an unaccepted proposal or estimate.
D-011 supplies the approved core rule; detailed choices below are proposals.

### Small first delivery - proposed, not implemented

- An order-level warehouse dispatch promise, distinct from standard customer
  Delivery Date: original date, currently accepted date, current operational
  estimate, responsible user and company. An initial promise is recorded by an
  authorized user, not inferred from an estimate, old Delivery Date or chat.
- A change proposal tied to that order, its current promise revision and an
  explicit remaining-order quantity snapshot. Record proposed date, reason,
  proposing user/time and the covered lines/quantities/UoMs.
- One active pending proposal per order. Pending or rejected proposals and
  estimates do not alter the operative promise. Explicit acceptance updates the
  current promise atomically and preserves original date and response history.
- Record the customer respondent, response channel/time, who entered it and a
  synthetic/manual evidence reference or note. An authorized employee records
  the response; this is not authenticated customer consent or an outbound message.
- A compact sales-order view shows original/current/estimated dates, proposal,
  response and history. An optional link to an existing control item is deferred;
  do not duplicate sales demand as a control-item workflow.

Non-goals: allocation engine, reservation/reallocation, urgency/tie-break policy,
consumer full-dispatch guard, per-batch schedules, carrier arrival promises,
quality release, capacity guarantee, automated emails/portal/signatures,
external integrations, live installation, migration, deployment or commit/push.
Standard Delivery Date, stock move deadline and picking scheduled dates remain
unchanged in this slice. The new field is an auditable planning reference, not
an implemented warehouse scheduling or dispatch enforcement engine. Accepting
a proposal here does not claim stock is available or reschedule stock moves.

### Decisions requested - recommended V1 package

| Choice | Recommended proposal | Alternative/deferred scope |
| --- | --- | --- |
| Corporate promise coverage | One date covers completion of all outstanding quantities on the order; partial dispatch remains permitted, earlier completed batches are not rewritten. | Individual dates/quantities per batch require a separate schedule design. |
| Authority and evidence | Dedicated promise coordinator role plus ordinary access to the sale order/company; manually record customer response and evidence. A manager cannot waive customer acceptance. | Customer-authenticated portal/email ingestion is deferred. |
| Proposal applicability | Snapshot remaining demand and promise revision. A later quantity/product/UoM change, partial dispatch, cancellation or reconfirmation makes it stale; do not apply it silently. Re-propose against the changed balance. | Dynamic coverage would require explicit amendment rules. |

Additional proposed boundaries for that package: use calendar dates for warehouse
dispatch promises (not an unapproved three-business-day SLA). Keep actual event
timestamps separately in UTC with normal user-timezone display. A late original
promise remains visible; lateness does not delete it or block operational efforts
to ship. Initial/original promise is frozen after establishment. Revised customer
responses produce new history rather than overwriting finalized events. A
cancelled order or one with nothing outstanding cannot accept a new proposal.
Missing initial promise cannot be silently replaced by a forecast; reject a
change proposal until an authorized initial commitment has been recorded.
Do not bulk-populate existing orders. Calendar-date display does not establish
a warehouse cutoff, working-day calendar or automated overdue calculation;
those need a later explicitly defined timezone/calendar policy.

While a proposal is pending, ordinary corporate partial shipment is not blocked
by this feature. The resulting changed balance invalidates the old proposal;
the still-current promise remains in force until a fresh proposal is accepted.
Do not change existing consumer shipment behavior under this task and do not
claim that D-010 is enforced. A stale response is retained as history but cannot
change the operative promise; it requires a new applicable proposal.

### Proposed architecture, security and consistency

Prefer a small optional integration addon depending on sale_stock and the
existing control addon, preserving the base/web-only control addon. Exact name,
fields and supported Odoo hooks are implementation-design work after approval,
not a newly installed module or verified API contract. Use normal ORM records
for the order promise and proposal/history; keep all related records in the
same company and enforce access to their source sales order.

Readonly widgets and hidden buttons are not security. Server-side create/write/
unlink and public action paths must reject direct edits to protected promise,
state and finalized history, including caller-supplied context flags. Limit
mutations to authorized operations; preserve standard sales ACLs/record rules,
do not grant sales access merely through a control-tower group, and do not use
blanket sudo or SQL writes to business tables. System/database administrators
are outside the tamper-proof guarantee; no legal-grade immutable audit claim.

Acceptance must recheck state, order/company permissions, remaining-demand
snapshot and promise revision in one atomic operation. A repeated identical
response must not apply twice; a conflicting, stale or cancelled response must
not replace a newer commitment. Design a tested serialization/uniqueness guard
for racing submissions; a caller-set context bypass is not sufficient. No
superuser-only test can establish ordinary-role security or company isolation.

### Proposed acceptance and test matrix - not executed

| ID | Input/action | Required observable result |
| --- | --- | --- |
| A01 | Establish an initial promise, then propose a later date | Original/current remain equal to the initial date; proposal is separate. Standard customer Delivery Date and stock scheduling fields are unchanged. |
| A02 | Leave proposal unanswered; change the operational estimate | Current/original dates unchanged; no implicit acceptance, no sent message. |
| A03 | Authorized coordinator records explicit acceptance with required response evidence | Current date changes once; original date, old revision, quantities, author and evidence remain traceable. |
| A04 | Record rejection | Original/current unchanged; rejection remains visible. It does not assert the original date is physically achievable. |
| A05 | Corporate 600 units, already dispatched 300; propose/accept for outstanding 300 | Coverage is 300, not 600; original dispatch records untouched. It does not promise a per-batch date. |
| A06 | Pending proposal, then partial dispatch or changed/cancelled/reconfirmed demand; attempt old acceptance | Proposal/response is stale; no date update. New proposal needs the current remaining scope. |
| A07 | Repeat acceptance, send conflicting response, or race two proposals/responses | At most one applicable outcome per revision; no double event, lost update or overwritten newer promise; clear failure/idempotent result. |
| A08 | Ordinary user, portal user, wrong-company coordinator or direct ORM/context manipulation attempts protected mutation | Access rejected, no partial data changes; an authorized same-company coordinator still needs source-order access. Test read leakage and history edits/deletion too. |
| A09 | Missing initial date, malformed/missing response evidence, no outstanding demand or cancelled order | Invalid action rejected atomically with a clear message; existing late commitment remains visible. |
| A10 | Transaction fails while applying response | Promise and event changes roll back together; no half-applied acceptance. |
| A11 | Install optional integration only in a fresh disposable DB and run regressions | Existing eight addon methods and applicable standard-baseline arithmetic remain green; no working DB/module-state changes; owned test DB cleanup verified. |
| A12 | Accept a first change, then reject or leave unanswered a second proposal | Keep the most recently accepted promise, not the original date; all history remains visible. |

Testing proposal: normal-role ORM transaction tests, two-company positive and
negative tests, direct-field/action bypass tests, a genuine two-transaction race
test, focused sales-form UI verification and controlled test-DB regressions.
Record skips explicitly. Do not run bootstrap, live upgrade or historical reset
migrations; use the guarded runner pattern and ephemeral data directory. An
approved implementation may extend test selection for the optional addon, but
must preserve the original standard-behavior diagnostic as baseline evidence.

Proposed implementation sequence after explicit scope approval: inspect hooks;
record a short implementation plan; build the optional model/security/view slice
and negative tests; run static/fresh-install/runtime/UI checks in owned test DB;
request independent review; repair at most twice; hand over in Review. Any later
installation in the working database needs a separately approved rollout plan.

Planning-only validation, 2026-10-15: from the authoritative repository,
python .\scripts\check_repository.py passed for 44 text files; git diff --check
passed; baseline comparison for addons, compose.yaml, .github, config and
existing setup/check/smoke scripts returned no changes. All exited 0, no DB.
TASK-0003 validation script digests still match their reviewed values above.
No service/runtime, module installation, data mutation or business test ran.
Git HEAD remains d62b6bc2de98ef3e500a2c177d57d007b37ece68; no commit or remote.

Separate focused /root/planning_review read the actual task, O-010 and status
addition under AGENTS/REVIEWER and found no confirmed defects or approval
overreach. It re-read the final response-evidence/calendar/A12 clarification.
Optional suggestion: explicitly assert stale-response history preservation
in A06; the body already requires that history. No repairs requested.
The reviewer read documents only, with no .env or runtime/data access. It did
not independently rerun static checks. Inherited permissions are not a distinct
technical read-only sandbox. One focused review, zero repair rounds.
Reviewed pre-evidence-note SHA256:
TASKS.md A3BF226A6F0A619BC7276DF61B0FB96594145C48395590E6B2214D8C9E750A9A;
DECISIONS.md 21CB1413F241FDAC7F1B9A9FF47E9DECD40C18554D315FECE2F61724FE198E31;
PROJECT_STATUS.md 5CF621C791CD9C16A1684DAF9B198F6722F26E7B50582034F92E5EB08E89959F.
At that planning stage the task remained Needs Decision: implementation and
the package were not yet approved. The later approval above supersedes this.
The preceding planning evidence predates the implementation approval above.
Implementation validation and review evidence follow below. Acceptance: not provided.

### Implementation and executed validation - 2026-10-15

Delivered source: optional operations_dispatch_promise addon, guarded promise/
proposal records, manual response wizard, coordinator/company/source-sale
security, calendar-date form views, 21 normal-role transaction test methods,
and the guarded runner's -WithPromise option. The base control addon, Compose,
CI, bootstrap/upgrade/smoke/check scripts remain at the initial baseline.
No working-database install, stock scheduling change, customer message or commit.

Scope snapshots include non-service goods lines, ordered/delivered/remaining
quantities, products/UoMs, revision and completed stock move metadata. Original
date and finalized history are protected at server level. The applied field
means Promise Date Changed: true only for an applicable accepted response.
respond() separately returns whether the response was applicable (including a
valid rejection); stale responses return false and are retained without a date
change. An identical retry is idempotent; a conflicting final response is refused.
The sales form and workflow notice distinguish manual evidence from customer
authentication and warehouse planning reference from operational scheduling.

Actual command for every run, from C:\Users\yusuf\Operations-Control-Tower:
.\scripts\validate-fulfilment.ps1 -WithPromise.
Environment: existing shared Compose services, Odoo 19.0-20260926/PostgreSQL15,
same local image ID recorded in TASK-0003. Source revision is the uncommitted
TASK-0004 tree over d62b6bc2de98ef3e500a2c177d57d007b37ece68.

| Owned disposable database | Exit/result | Development action |
| --- | --- | --- |
| oct_scenario_536d68e8054945acb18f04a722661d06 | 1; 18 errors in 26 methods | Required related order/company fields needed precompute; test helper needed a concrete exception class instead of a tuple. Fixed; form alert roles clarified. |
| oct_scenario_f237f38d237c43df8564875a0182a55f | 1; 1 error in 26 methods | Old pending state was not flushed before replacement INSERT hit partial unique index. Added explicit ORM flush. |
| oct_scenario_7eca77fc5d1e4191a481b40ca91e392c | 0; 27 methods, all scenarios/probes passed | Included added context-default spoof protection test. Then added warehouse-only and mixed-access regressions. |
| oct_scenario_e053454e5b7b4b7e86c3483c5d26a63a | 0; 29 methods, 0 failures/0 errors; scenarios/probes passed | Final 8 base + 21 integration test methods. No test assertion was relaxed to hide a functional failure. |

All four owned DBs were dropped and their absence verified; before/after
working module states and the 14-item MD5 matched TASK-0003. Read-only working
DB query additionally returned 0 installed operations_dispatch_promise modules
and 0 sale_order oct_dispatch_* columns. No shared filestore path was used.
The runner now attempts the final working fingerprint even if cleanup fails;
its failure paths still lack fault injection/forced-interruption coverage.

Final runtime evidence:
- All A01-A10/A12 core cases are covered by ordinary coordinator/denied-role
  tests, including exact evidence, last accepted date, stale history, changed/
  restored quantities, cancellation/reconfirmation, duplicate/conflicting
  responses, protected CRUD/context defaults, source write access, mixed
  source/company read filtering and injected atomic-response rollback.
- A05 uses a real 300/600 stock dispatch and verifies remaining 300 without
  rewriting prior completed moves. The additional stock-only, non-superuser
  warehouse test completes a pending-proposal partial dispatch without Sales
  or Coordinator membership, then verifies stale applicability/current promise.
- A11 fresh install and base regression pass; the standard arithmetic remains
  500 + 400 = 900 with corporate batches 300/200/100 and zero final stock/open
  pickings. Its seven standard-field diagnostic gaps remain gaps; they are not
  failures of this separately scoped manual promise workflow.
- Independent real connections, backend PIDs 86267 and 86269, prove competing
  proposals/responses are refused while locked, finalized conflicting responses
  cannot overwrite, and identical retry is idempotent. Another two-connection
  case establishes an old REPEATABLE READ snapshot, commits a new sales line,
  refuses the stale accepting transaction, then refreshes and records a stale
  response without changing the date. Handled NOWAIT/serialization SQL ERROR
  log lines are intentional probe stimuli, not unhandled suite failures.
- Resolved inherited Sales form contains the new page. Odoo Form helper loads
  wizard modifiers and runs proposal -> accepted-response -> current-date
  change as the normal coordinator. This is server-side form verification,
  NOT browser rendering or visual interaction testing.

Static checks: text/XML/CSV checker passed for 58 files; 11 Python AST parses
and PowerShell parser passed; git diff --check and scoped unchanged-baseline
comparison passed (all exit0, no DB). In-memory candidate scan found zero
configured DB-password exact matches or high-confidence private-key/token
patterns; no values printed. Heuristic scan is not a completeness guarantee.

Limitations/skips: no browser render/manual UI acceptance, external customer
authentication, email/supplier/carrier integration, working DB rollout, migration,
load test, calendar cutoff, stock-priority or consumer-complete enforcement.
Concurrency is controlled interleaving with distinct real DB connections, not
production load. The probe commits synthetic fixtures solely in the guarded
owned DB; they are removed with that DB. System/database admins are outside
the tamper-proof guarantee. Shared infrastructure is not full-stack isolation.

Additional default-path regression: .\scripts\validate-fulfilment.ps1 (without
-WithPromise) exited 0 in oct_scenario_4ff000cdbd24457494443698a950f458. Eight
base methods passed, 900-unit arithmetic and all 11 standard-field diagnostic
observations completed. Owned DB removal and working fingerprint comparison
passed. All five TASK-0004 execution databases are now removed; final read-only
enumeration found no scenario DB or one-off container. Both services remained
healthy and working /web/health returned pass. The .env file is ignored/untracked;
HEAD remains the original commit and no remote exists.

Separate final review: /root/validation_audit read the complete actual optional
addon, all 21 tests, three validation scripts and relevant task/decision/status/
architecture changes. It found no confirmed defects or authorization overreach;
no functional repairs were requested. It independently verified source hashes
and examined runtime evidence, but did not rerun tests, read .env or mutate any
file/service/data. Commands were read-only file reads/searches, Get-FileHash,
scoped git status and aggregate calculations. Its inherited permissions are not
a technically separate read-only sandbox.

Non-blocking risk: scope/guard hooks lock and write metadata for all sale-line
changes, including orders without promises. Regression and stock-only tests
pass, but load/contention and other integration writers are untested. Additional
unexecuted variants: product/UoM changes, line removal/reparenting, simultaneous
stock completion versus acceptance, forced interruption and cleanup faults.
Browser rendering remains unverified; server Form helper is not a substitute
for visual/user acceptance. No production safety or capacity guarantee.

Reviewer suggested qualifying one standard-diagnostic docstring. Only that
docstring was clarified after the 29-method run; no executable statement changed.
Text/AST checks passed and the reviewer re-read it and independently confirmed
the final hashes. The subsequent default-path run executed the clarified script.
One final review round plus focused clarification reread; zero functional repair
rounds. No unreviewed executable change remains.

Final source aggregate SHA256 (13 addon source files + 3 validation scripts):
4E66FD5EB12B74FC32C549F1B133F50147C2C80607C08104AF5D4AE721D0A09F.
Algorithm: case-sensitive PowerShell Sort-Object on project-relative forward-
slash paths; rows '<path> <UPPER_SHA256>', UTF-8 joined with LF, no trailing LF.
Key individual reviewed SHA256:
- models/dispatch_promise.py: 73F53CFB305D235699B03067230FE1AF7495F4FB54B17D40FF6A8F783B78F33C
- models/sale_order.py: 08CF4488145C14542583A4B98B1D62204650F73ADD3A974C53B64222CCBD7BD4
- tests/test_dispatch_promise.py: 928083327817838592FECA6D1D4889FE915E3777ACAEC417F02C0974DB9F7FBC
- scripts/validate-fulfilment.ps1: 3AD970FF60990651661A2558F957205AB7CB2119E184C50B95A99EB83B8D9ABC
- scripts/validate_dispatch_promise.py: E0E8929CA3D468386830C5D322F933E920F313FE5883BFB3A5D839C374EF161A
- scripts/validate_fulfilment.py: 0C9242582F3EFA2105429B9684B98D677CBA76D0BF0285409006FB6EE52F4C8B

Reviewed pre-handover-note document SHA256:
TASKS.md 31DF57BC7A74BA7FDB2A8994D339BA295BBDAEEF36B22956A1D00D759E0D2C5B;
PROJECT_STATUS.md 3707EC5F8F296CF88B0D4DECC252DC0D32C556B1155727E1EB2F60AECD2ACD63;
ARCHITECTURE.md 628F52B629EFAEC245F0B3725EE222323B09E2ADA0D99F1F1F96B6EEA1DD34F4;
DECISIONS.md A28B4B2872CCD5F0068F0FB696F9E5BBAF8EDCDAA9860B83AD9C2CAA6886584A.
This final evidence/status note changes document hashes only. Handover is Review,
not Done. Product Owner acceptance and any working-system rollout are separate.

## TASK-0005 - Browser verification of the promise workflow

State: Done

Final acceptance: Yusuf Ondes, 2026-10-15 (Europe/Berlin), explicitly accepted
the immediately preceding TASK-0004/TASK-0005 Review handover. The shared
acceptance closeout below records scope, evidence and remaining exclusions.

Approval: Yusuf Ondes, 2026-10-15 (Europe/Berlin), explicitly said to continue
after the TASK-0004 handover identified screen-level acceptance verification as
the next step. This authorizes a disposable local browser preview and synthetic
UI interactions, not a working DB install, load test, deployment or acceptance.
At this approval TASK-0004 was in Review; the confirmed browser defect below
subsequently reopened it for a narrow repair.

Plan before implementation: add narrowly guarded preview/seed helpers; generate
an owned oct_scenario_<guid> database and oct-ui-<guid> one-off Odoo container;
bind a temporary HTTP port to host 127.0.0.1 only, same approved local image,
no cron, database listing disabled and DB filter exact. Keep filestore in the
owned container's /tmp data directory, not the shared volume. Seed a synthetic
ordinary Sales/Coordinator user and one confirmed goods order. A random test
credential stays only in a generated user-temp file outside Git, is not printed,
and is removed with cleanup. Do not reuse working credentials or reset admin.

Use the supported browser-control API to verify actual rendered forms: initial
15 December 2026; pending proposal18; estimate19 leaves promise15; accepted18
keeps original15; rejected20 keeps accepted18; proposal21 becomes stale after
scope change and its response is retained without changing accepted18. Verify
readonly/history navigation, required fields/cancel behavior, notices and
standard Delivery Date. Capture synthetic-only screenshot evidence.

Cleanup must target only the generated container/database/credential file with
name/ownership-label checks and verified absence. Compare working module states
and 14-item fingerprint before/after. No browser automation against the working
Odoo port. Preserve all existing source and reviewed implementation; report any
new defects instead of claiming owner acceptance. Validate helpers statically,
record actual UI results/limits and request a focused separate review.

Browser finding, 2026-10-15: initial/pending/estimate/accept/reject flows passed.
Stale-response submit persisted its evidence and preserved current18/original15,
but the notification's nested next window action raised Odoo Client Error:
undefined.map in _preprocessAction. Browser reload confirmed Stale/Accepted,
date unchanged and revision2; no lost data or reapplication was observed.
This is a confirmed P2 action-contract defect in the already approved TASK-0004
UI, not a new feature. Reopen that incomplete deliverable In Progress for one
narrow repair: include explicit form views in _form_action; add a stale-wizard
next-action regression, rerun runtime checks and the real browser case, then
renew independent review. No new business rule or working-system change.

The source-only reviewer confirmed installed Odoo action_service.js uses
action.views.map; clean_action normalizes only the outer returned action, while
display_notification returns nested params.next without normalization. This
explains why server-only Form happy-path tests did not catch the client failure.
Evidence/review/acceptance: pending. No Done is inferred from automated UI checks.

### Executed browser and repair evidence

The minimal explicit views descriptor was added to _form_action. One new test,
test_a06_stale_response_wizard_returns_complete_notification_next_action, runs
the stale-response wizard as the ordinary coordinator and asserts the nested
action contract, retained evidence, applied=false and unchanged date/revision.
The addon now contains22 integration methods; the original8 remain unchanged.

Actual browser: supported in-app browser, default desktop viewport, ordinary
Sales/Coordinator synthetic user. Owned DB/container:
oct_scenario_6ce183d5caee400eb994c5d000a6fb60 /
oct-ui-6ce183d5caee400eb994c5d000a6fb60, host loopback63840 only. Original/current15,
pending18, estimate19, accepted18 and rejected20 were visibly verified. The first
stale21 response reproduced the client error but persisted correctly. After
restarting only the owned preview container to load the fix, fresh proposal22
at650 units became stale after quantity651. Recording Accepted now showed the
warning and normal form, no error modal. Original15/current18/estimate19 and
revision2 remained after reload; stale response and applied=false were visible.
Proposal23 without a reason stayed in the wizard with required-fields notice;
Cancel left no proposal23. History forms had no Edit and disabled booleans.
Standard Delivery Date remained Dec14,13:00 Berlin by browser DOM observation
(fixture UTC12:00 and read-only SQL unchanged). Screenshot07 documents Other Info
navigation only: the date value is below its crop and is not pixel evidence.

Seven synthetic-only JPGs and case/defect details are saved under
[browser evidence](evidence/task-0005/README.md). This is developer verification,
not authenticated customer consent, owner acceptance or a working-system install.

Runtime command after repair: .\scripts\validate-fulfilment.ps1 -WithPromise,
exit0; owned DB oct_scenario_45be0767fd2e4897b2a0ea09ca43c3c9. Odoo reported
30 methods, zero failures/errors. Standard900 arithmetic and corporate300/200/100
batches passed; the seven standard diagnostic gaps remain. Two independent real
connections (backend90848/90850), old-snapshot/new-line and Form probes passed.
Expected handled SQL lock/serialization errors are probe stimuli. The runner
verified owned DB removal and unchanged scoped working fingerprint.

Preview helper hardening: exact-name plus matching ownership-label discovery
recovers a container even after nonzero compose-run; cleanup uses its immutable
ID, independent error aggregation and exact temporary credential removal/absence
verification. Stop never infers DB ownership from an absent/unproven container.
Seed shell now has init-identical explicit addons-path. No seed content changed.
Updated normal Start/Stop ran exit0 in fresh
oct_scenario_5ad50051b0e8410693b3a18a9ea10ac0 /
oct-ui-5ad50051b0e8410693b3a18a9ea10ac0. This is not fault-injection coverage.

Both previews' containers, DBs and exact temporary credential files were removed
and absence verified. Final enumeration: no scenario DB, UI or one-off container.
The browser tab was closed. Whole-browser-session before/after working module
states and14-item fingerprint matched 14:17f2a87362f026a248dc420227dd452f.
Optional addon installed count0 and sale_order integration column count0 in the
working DB. Both services stayed healthy and /web/health returned pass. This
fingerprint is scoped, not a complete DB diff; no working service restart.

Static checks after repair: repository checker61 text files, Python AST12files,
PowerShell parser2scripts, git diff --check and original-addon baseline comparison
passed (exit0; no test DB). In-memory scan of68 Git candidate files found0 exact
configured DB-password matches,0 high-confidence token/private-key patterns and
0 sensitive candidate filenames. Values were not printed; images are synthetic
and visually inspected. The scan is heuristic, not a comprehensive secret audit.
The .env file remains ignored/untracked.

Final18-file source aggregate SHA256:
702DEAB9663CB6A6EDD0B21C9B5417CEC4FAEC82B934ECCCE9B73C391400C2FE.
Scope:13 optional-addon .py/.xml/.csv +5 validation/preview scripts. Same sorted
path/hash UTF8/LF algorithm as TASK-0004. Individual changed/new SHA256:
- models/dispatch_promise.py: C636D362C783B16D3234852C90660F66EA9F1658BD007155096897A7E0D873CD
- tests/test_dispatch_promise.py: 0EAC2C1DA100FB581F3544CFA507EE48B882836C63E4219DC4074BC834866A43
- scripts/preview-dispatch.ps1: F85C942E9AD02644839649DFCFE418735DC6F25990D137C2205FDA294F885E0F
- scripts/seed_ui_preview.py: EE7D55CA2EED995F8754C7EA46C79287E14AB7B0E9170CAF3A2B551CECAE280C

No new business rules, deployment, migration, commit, remote or push. HEAD remains
d62b6bc2de98ef3e500a2c177d57d007b37ece68. Owner acceptance remains absent. This is
one functional UI repair after the prior final source review, not a third
autonomous repair round.

### Renewed independent review and handover

/root/validation_audit completed renewed final review round2: no remaining
confirmed defects, no additional functional repairs requested. It read the
changed action/test, complete preview/seed helpers, latest task/status/evidence
documents and visually inspected all seven JPGs. It independently matched the
four individual source hashes and18-file aggregate above. The only evidence
clarification was to distinguish cropped screenshot07 from the DOM date check;
that clarification was reread. No executable changes followed this review.

Commands: read-only Get-Content, rg --files, Get-FileHash, in-memory aggregate
calculation and local view_image. It did not read .env, rerun runtime tests, use
the live browser, mutate files/services/DBs, stage or commit. Runtime evidence
was considered, not independently re-executed. Permissions are inherited;
written read-only restrictions are not a separate technical sandbox.

Remaining helper risks: failure before cleanup (Compose/fingerprint resolution)
may leave resources requiring explicit recovery. If container removal succeeds
but DB deletion fails, a later Stop deliberately refuses orphan-DB deletion
without the missing container's ownership proof. Cleanup/fingerprint failures,
forced interruption and startup-failure recovery were not fault-injected. Normal
Start/Stop and the separate whole-session baseline comparison passed. Earlier
load, scope-variant, concurrent-stock-completion, migration and browser-matrix
gaps remain. No production-readiness or authenticated-consent claim.

Pre-final-status-note reviewed document SHA256:
- TASKS.md: 91E3A099F0A76500B815E6D1D22B05E3303C6DFE740D5C73588656273E93A547
- PROJECT_STATUS.md: 80703DE558E0C8870056D60AC3DBEE7BFD5B2E455F8AEDF9946285D61977D21B
- evidence/task-0005/README.md: E89C56A0DD1B757574E0735C0FEBE54943C549482A14A6E901EA22287AECDCC0

One additional read-only SQL diagnostic selected unquoted current_date, which
PostgreSQL evaluates as today's date. That output was excluded from promise-date
evidence; current18 is proven by the actual browser/reload and ORM regression.
The quoted/ordinary column observations and Delivery Date query were unaffected.

TASK-0004 and TASK-0005 are handed over in Review, not Done. These final review/
status notes change documentation only. Product Owner acceptance and a later
working-system rollout remain separate actions requiring direction.

### Product Owner acceptance and Done closeout - 2026-10-15

Yusuf Ondes replied to the Review handover: "Devam et. Dan olana kadar devam et.
Kabul ediyorum." This is explicit acceptance ("I accept"), not inferred from
earlier implementation approvals. It closes only TASK-0004 and TASK-0005 as Done.
TASK-0001 remains Review, TASK-0002 Needs Decision and TASK-0003 Review.

Accepted deliverables: the approved A01-A12 promise/manual-response slice in
source and disposable validation, the narrow stale-response UI action repair,
30 passing methods, controlled standard/concurrency/Form results, actual browser
evidence, verified test cleanup and the renewed no-confirmed-defect review.
The accepted18-file source aggregate remains:
702DEAB9663CB6A6EDD0B21C9B5417CEC4FAEC82B934ECCCE9B73C391400C2FE.
Baseline HEAD remains d62b6bc2de98ef3e500a2c177d57d007b37ece68. Done records
acceptance of this uncommitted delivery; it does not imply a committed release.

All documented coverage gaps and non-goals remain. No working DB installation,
deployment, migration, stock-priority/consumer-completeness feature, external
communication, new commit, remote or push is authorized by this closeout. No
functional code, configuration, service or database was changed during closeout.

Closeout validation: python .\scripts\check_repository.py and git diff --check
passed (exit0, no DB); the18-file aggregate still matches the accepted source.
Runtime tests were not repeated for documentation-only status changes; their
executed evidence above remains the basis of acceptance.

Focused separate acceptance-closeout review completed: /root/validation_audit
found no confirmed documentation defects or scope issues. It verified only
TASK-0004/TASK-0005 are Done, earlier task states remain unchanged, exclusions
remain explicit and the18-file source aggregate independently matches. Commands
were read-only file/search/hash checks; no secrets, runtime tests, edits,
services, DB or Git mutations. This is a documentation review, not another
functional repair round.

Reviewed document hashes before this final review note:
- TASKS.md: 91B0E1FF3471B03D853E84DF7D403D1AB7A47FE98663ED05A271A7CABC13F8D4
- PROJECT_STATUS.md: 57682F5411ABA9E05FB2F8708C52E319C1511A3724BD86BA45ADCB932B3E1E34
- evidence/task-0005/README.md: B1D415618954FA5DE09603F4FF7CE092F76477F464A06D9478A79BBFE1F899C2

## TASK-0006 - Prepare a truthful portfolio source publication

State: In Progress

Current ownership update,2026-10-15: Yusuf Ondes explicitly stated that the code
belongs to him and asked to continue. This resolves the ownership question on
the basis of the owner's declaration, not an independent provenance audit.
Narrow follow-up plan before metadata edits: replace only the project copyright
header and base-addon author HOLY with Yusuf Ondes; preserve the complete LGPL/
GPL text, FSF/third-party notices, version/dependencies and functional source.
Record D-014, update current publication prose and run text/manifest/license-body
checks plus focused independent review. No DB/module update or Git publication.
Earlier unverified-attribution notes below describe the preceding preflight.

Approval: Yusuf Ondes, 2026-10-15 (Europe/Berlin), requested finishing the
remaining work and uploading to GitHub today for sharing. This authorizes local
publication preparation. GitHub destination/visibility and the intended scope
(accepted MVP versus additional stock rules) are not yet specified. No remote
or publication is performed until those choices are resolved. Original HOLY
authorship/copyright is unverified; do not replace attribution without evidence.

Plan before edits: correct public README/demo/setup/changelog to describe both
addons, actual local test/browser evidence and exact CI coverage; add safe
preview prerequisites/cleanup and warnings before any historical upgrade.
Use synthetic data only, preserve license terms and original implementation.
Keep a concise current-status summary separate from historical task evidence.
Run static/local-link checks, verify accepted executable hashes remain unchanged,
and request focused independent review. Before any later commit/push, repeat
candidate/index/history secret gates, inspect the exact staged scope, verify
destination and report the resulting commit/URL only after actual success.

Preparation criteria:
- Public entry docs distinguish base bootstrap from optional disposable preview.
- The accepted promise workflow and screenshot evidence are easy to find.
- Thirty local test methods are not misrepresented as a remote CI result.
- Missing stock-priority/full-consumer enforcement and known gaps stay explicit.
- Setup does not recommend volume destruction or unsafe historical migration.
- No code/module/service/data changes, license replacement or unapproved branding.

Publication criteria, pending decisions: agreed release scope, verified owner/
attribution, confirmed repository/visibility and authenticated access; reviewed
and secret-checked local commit; actual push result and repository link. Do not
claim the complete campaign fulfilment engine or mark this task Done from docs.

Read-only preflight: HEAD d62b6bc2de98ef3e500a2c177d57d007b37ece68, no remotes,
68 Git candidates. In-memory exact configured-DB-secret and high-confidence
token/private-key scan found0 hits in candidates and the one-commit history;
0 sensitive candidate filenames. .env is ignored. This heuristic is not a
complete secret audit. Repository checker61textfiles and git diff --check passed
(exit0, no DB). Existing 30-method/browser results are from TASK-0004/0005, not
new executions in this publication-preparation task.

Naming update: the owner subsequently chose HALY as the fictional company.
D-013 records this for current scenario/publication prose only. Authorship/
copyright verification, release scope and GitHub destination/visibility remain
open; no license notice or application/company record was changed.

Preparation evidence,2026-10-15: README, SETUP, DEMO, CHANGELOG and current status
now describe both addons, the synthetic HALY scenario, real screenshot evidence,
base-only CI and the remaining unimplemented stock rules. Historical status
sections are explicitly labeled. Setup distinguishes fresh bootstrap from
data-changing upgrade and gives guarded preview/credential/Stop guidance.

Checks from the authoritative repository, all exit0/no DB:
- python .\scripts\check_repository.py:61textfiles passed.
- git diff --check:passed; new/untracked text included in repository checker.
- Local Markdown target/anchor inspection:26links across7documents,0 problems.
- Protected baseline comparison: base addon, LICENSE, CI, Compose, config and
  existing bootstrap/upgrade/smoke/check scripts unchanged from HEAD.
- Accepted18-file aggregate recomputed unchanged:
  702DEAB9663CB6A6EDD0B21C9B5417CEC4FAEC82B934ECCCE9B73C391400C2FE.

Focused independent /root/validation_audit review found no remaining confirmed
documentation defects or scope issues. One overly broad supplier-delay phrase
was clarified to supplier-delay-to-customer coordination and reread. The reviewer
read the7documents, spot-checked source/CI/notices, independently checked26links
(including6anchors), and matched the18-file aggregate. It did not read .env,
use network, run runtime tests, mutate files/services/data or write Git. No
technical read-only isolation is claimed. One documentation review round; no
functional source change or runtime repair.

Reviewed hashes before this final state/evidence note:
- README.md: 41C2F664BBE9536A6713E833E69D270C363F4C7AA20BE052B8DECFFE350FF809
- SETUP.md: 06A8A17894C7CAC671678E0E061D15FAE83E21ED3F979C57E0361565746A7C9B
- DEMO.md: AE14F2EA3387A3AD370B43C0AF0A9BBA2367E17D929B24CE8C354EC90A7A8ED0
- CHANGELOG.md: D0252A2DBC259A4F94D052178F9E045EE08873A2542A875405716F38831E476B
- TASKS.md: 661F59A25D937FE4BB73461F8ADA51481516385F0434D1CC3B4967DFC7334725
- PROJECT_STATUS.md: 4FE7B4450290594F535B74BC34D220D204479BABE312027251962B3C092CA985
- DECISIONS.md: 23540134F88FB436844E107AAC6744BE8112C809002AD9C232D81E8B00C20774

Decisions pending at the preceding pre-declaration handoff (historical):
publish accepted MVP now versus implement further
rules first; GitHub repository destination and visibility; whether existing
HOLY software attribution is the owner's placeholder or third-party credit.
HALY naming alone does not establish that ownership. The user's publication
intent is recorded; do not ask for generic permission again once these details
are resolved. No guessed destination or visibility, attribution replacement,
commit, remote, push, release tag or live installation was performed.

Not re-executed: fresh-clone setup, runtime/browser suites, remote authentication,
remote links/CI and publication. Current docs are reviewed local preparation,
not proof of a published release or complete campaign engine. Remaining stock
policies need explicit scope/decisions before further functional implementation.

Current follow-up,2026-10-15: ownership/attribution is resolved by the owner's
explicit declaration under D-014. Only the project copyright header and base
manifest author changed to Yusuf Ondes. HALY remains the fictional scenario.
Current publication decisions are the release scope and GitHub target/visibility;
the earlier ownership question must not be asked again. No remote, commit, push
or working-system update was performed.

Metadata checks,all exit0/no DB: repository checker61textfiles; git diff --check;
normalized license comparison against HEAD with only the project header replaced;
full manifest comparison/AST parse proving only author changed and version,
LGPL-3,base/web dependencies unchanged;18-file accepted source aggregate unchanged
at702DEAB9663CB6A6EDD0B21C9B5417CEC4FAEC82B934ECCCE9B73C391400C2FE.
Other base-addon files, CI, Compose, config and original operational scripts
remain unchanged. Runtime tests were not repeated for attribution-only edits;
the prior30-method result remains dated evidence, not a fresh-run claim.

Focused attribution follow-up review: /root/validation_audit found no remaining
confirmed defects or scope issues. It independently checked the exact two-line
Git diff, current ownership/HALY separation and18-file aggregate. Only project
metadata changed; the aggregate excludes LICENSE/base manifest, which were
reviewed separately. Commands were read-only document/hash checks and scoped
Git diff; no secrets, network, tests, files/services/data or Git mutations. This
is metadata/documentation review, not another functional repair round.

Reviewed pre-final-note SHA256:
- LICENSE: C28D36DB6B06A1714EF3110F5507A1F23D0D50FE9C55D61803749A489D1C6C15
- Base manifest: 4C57BB3F3ABABEE05BAE784BF9AB67193FED7D239506B3E69E75A862F22CB67D
- README.md: 85B1D967959644E4DB88546AE5F2E27C4AE5681736DE174261579338371049E2
- CHANGELOG.md: 7201899B8E36F899C52454C79107B0BD9395F416C4BADFEBD32CA6F8EE2CEDB1
- TASKS.md: 1103FCA04D0F4B036B4BE31543BFCBA16697E73450F0207D35F69DE3A2F81745
- PROJECT_STATUS.md: 3EDDDA3DD50BF5D05215FEC91180BAE760980C66C1B319F298C568E281A1AA0D
- DECISIONS.md: 2C6DD7F70E3881723F354852F2A9ECE2172BBD12AFD08A814285FB1DD63F2B85

Publication order update: the owner now explicitly requires campaign automation
and its relevant validations before GitHub. Defer publication under TASK-0006;
do not request GitHub details during that work. No remote/commit/push is implied.

Publication authorization,2026-10-15 (Europe/Berlin): after explicitly accepting
TASK-0007, Yusuf Ondes supplied https://github.com/yusufondes/Operations-Control-Tower
and authorized committing, adding its remote and pushing to that exact repository.
The approved publication scope is the reviewed current portfolio source,
governance/history, validation helpers and synthetic evidence, including the
accepted promise/campaign deliveries; it does not install, deploy or run them
against the working database. Preserve the initial commit and licenses. No tag,
GitHub Release, hosting, force push, repository recreation, permission change,
dependency install or global Git configuration change is authorized or needed.

Publication execution plan before writes:
1. Verify root/main/baseline/local author, exact tracked+untracked candidate scope,
   ignore behavior and in-memory candidate/history secret checks. Recompute the
   accepted functional digest; no functional changes or runtime rerun intended.
2. Verify the exact remote's owner/existence/visibility and refs; do not assume
   public visibility or overwrite remote history. Existing Git Credential Manager
   may supply authenticated Git access; never print/store credentials in source.
3. Complete focused independent publication-doc/content review, stage only the
   verified scope and repeat index secret/whitespace/content checks. Create an
   English local commit as the already configured repository-local Yusuf identity.
4. Add origin only if absent and the target is verified, then normal push of main
   without force. Verify remote main equals the local commit, repository contents
   and actual Actions status. Report exact hash/URL and any authentication/CI limit.
5. Record executed results, not intended success. Leave this publication task in
   Review at handover; Done still requires explicit acceptance of this new delivery.

Initial new preflight: root/main/baseline/local author match;99 candidates
(37 tracked+62 untracked), only ignored.env plus generated bytecode outside scope;
no remote or active Git hooks. Git2.56.0.windows.1 and Credential Manager2.9.1
available, GitHub CLI absent. The exact URL returned unauthenticated API404 and
the noninteractive Git ref check failed; visibility/existence/access is not yet
verified. Asked the owner to confirm the browser URL/visibility while continuing
safe local gates. No remote has been added and no push is claimed.

Publication gate execution,2026-10-15:99 candidates and37 blobs in the original
commit passed high-confidence private-key/token/credential-URL scans and exact
comparison of1 real local.env secret, used only in memory;0 matching contents,
0 sensitive candidate names and0 files>=50MiB. Ignore probes for.env,.env.test,
private.key,backups,filestore and.sqlite3 matched. No staged files at preflight,
no active/custom Git hooks and no URL rewrite rules. This remains a heuristic
gate, not a complete secret/provenance audit. Git local name/email match the
owner's supplied identity; no configuration changes were necessary.

Static commands all exited0: python .\scripts\check_repository.py (79 text files),
git diff --check,31 addon AST parses,2 PowerShell parser checks,68 present local
Markdown targets and docker compose config --quiet. The accepted20-file
functional aggregate remainsFEDA78AD52AA0A4EBBBF43E01BE14A00CC93ABDA582D21CB77D568C9F1C0B289.
No functional edits, runtime rerun, working-DB write or service changes occurred.
The prior81-method/11-case result is dated accepted evidence, not a new CI run.

Access follow-up: existing Credential Manager credentials authenticated the
GitHub API as yusufondes, but the exact repository endpoint still returned404.
Credentials stayed in memory and no values were printed. Therefore target
existence/visibility/access is unverified, not assumed public or nonexistent;
the owner was asked to confirm the browser URL/visibility. Continue the approved
local commit after index review, but do not add a remote or push to an unverified
target, create a replacement repository or alter repository permissions.

Focused publication review /root/publication_gate found no confirmed content,
licensing or disclosure blocker to the authorized local commit. It read all
relevant public docs/manifests, inspected the publication candidate inventory,
searched publishable source text for disclosure risks and visually inspected
all20 synthetic images; it did not comprehensively rereview functional code;
independently matched the20-file functional digest; verified99 candidates and
the narrow copyright-only license diff. No secrets read, network/runtime rerun,
Git writes or service/data mutations. Target verification remains required.
The first index whitespace check exposed five previously untracked documents
with an extra EOF blank line. Removed only those blank lines; no substantive
instruction, decision, test or functional code changed. Final index gate follows.

Index gate:99 indexed files,71 changed paths (9 modified+62 added),0 deletions,
0 unstaged/untracked candidates. git diff --cached --check and repository79-text
check passed. Scanning the actual99 index blobs found0 high-confidence patterns,
0 exact local-secret matches and0 sensitive filenames. The reviewer independently
checked index inventory/whitespace, unchanged functional digest and final docs;
no confirmed local-commit blocker remains. GitHub repository access remains
unverified, so remote addition/push are not claimed by this local checkpoint.

## TASK-0007 - Complete the bounded campaign automation before publication

State: Done

Implementation authorization: Yusuf Ondes,2026-10-15 (Europe/Berlin), explicitly
requested full campaign automation, relevant validation and verification before
GitHub, whose details will be supplied later. This authorizes implementing the
remaining D-008/D-009/D-010 rules and the HALY campaign scenario, not the unrelated
nine-area ERP roadmap or live deployment. Preserve existing data/services; use
owned disposable DBs for all runtime work. Owner acceptance still remains separate.

Supported goal: own manufacture from raw materials/two synthetic suppliers;
discounted individual/corporate orders; accepted warehouse-promise priority,
earlier-confirmation secondary order; complete consumer dispatch and corporate
partial balances; original/manual-response history; accountable disruption
visibility. Automation applies rules when real receipt/production/dispatch events
are recorded; it must not pretend physical work or customer consent occurred.

Plan before implementation:
1. Inspect installed Odoo19 stock/confirmation/receipt/MRP/scheduler paths and
   existing promise/security/lock contracts. Use standard inventory as truth.
2. Add a separate optional operations_campaign_automation addon. PhaseA implements
   the already approved D-010 independently: explicit quotation order policy
   Consumer Complete or Corporate Partial (unset means outside this addon),
   frozen after confirmation; no inference from partner.is_company. Enforce
   complete current physical demand in a single customer picking before quant
   mutation, including move finalization and raw-line bypass protection. Keep
   corporate partials, normal receipts/returns and unconfigured orders intact.
3. Test incomplete quantities/multiple products/UoMs/duplicate lines, split and
   mixed pickings, backorder/context/direct paths, policy tampering, stock-only
   roles and company isolation. Explicitly reject unsupported ambiguous flows
   rather than claim universal route/replacement support.
4. Owner policy package is requested while PhaseA proceeds: incomplete-consumer
   reservation retention; reclaiming unpicked campaign reservations while
   preserving picked/outside reservations; missing promise; exact ties and
   reconfirmation. D-009 expressly left final ID ties open. Do not silently choose
   these business outcomes from the instruction to finish.
5. After decisions, implement the shared-pool priority/reconciliation path,
   protected confirmation history and accepted-date integration with stable
   pool/order locking. Cover confirmation/manual/receipt/MO/scheduler/cancel paths;
   detect unmanaged competition/unsupported routes rather than stealing stock.
6. Add an explicit campaign validation mode, keeping the legacy standard
   diagnostic and accepted promise-only regression available. Run original and
   new tests, real two-connection races, end-to-end purchase/production/dispatch
   and disruption scenarios, real browser checks, static/secret/link checks,
   cleanup and before/after working-state checks. Record image/revision/digests,
   command/DB/exit/results/skips, then independent review (at most two repairs).
7. Hand over in Review with evidence; Done needs owner acceptance. No GitHub,
   working DB install, historical migration, external messages or production claim.

Acceptance targets:500+400=900 with A200/B600/C100, initial200/300/0 and corporate
300/200/100; all supported allocation entry points obey the approved priority;
consumer partial attempts fail atomically, including bypasses; pending/rejected/
stale dates never reprioritize; accepted changes do; repeated updates are
idempotent; no cross-company data/stock leakage, double reservation or supported
negative-stock dispatch; failure/concurrency rollback; meaningful disruption
owner/next-action visibility; all test resources removed and working state kept.

Pre-code audits were read-only and are design evidence, not executed tests:
stock.move._action_assign is shared across manual/arrival/MO/scheduler paths;
sorting only the passed moves misses competitors outside the batch. Completion
can bypass button_validate through stock.move._action_done and raw move lines.
Partner entity shape is not a shipment contract; picking.sale_id can hide mixed
orders. Existing promise _dispatch_lock requires Sales write and must not grant
that permission to a stock-only operator. Stock quants permit negative results
in standard forced workflows; no-negative needs an explicit supported guard.
Direct root inspection: main Odoo image dd9013e669caaa23d26765dc55814655eaeecca7cfc2c265dbabae913bce22fd.

Open policy package and PhaseA implementation/validation are pending. No full
automation, runtime pass or task acceptance is claimed by this plan.

Subsequent explicit approval: the owner approved the complete structured stock
policy package. D-015 now resolves the hold/reallocation/missing-date/exact-tie/
reconfirmation choices; continue the full plan rather than stopping at PhaseA.
Use a separate optional addon with pool-controlled one-step make-to-stock goods
scope. Reject ambiguous/unmanaged competition and unsupported routes; preserve
outside/picked reservations. Capture policy/pool at quotation and protect after
confirmation. Existing accepted manual promise/response security remains intact.

Preparation/concurrency implementation boundary: D-015's prepared-reservation
protection requires the same configured-pool mutex before matching stock
move/move-line quantity or picked edits, creation/removal and finalization.
Apply hooks only to existing/proposed records matching a configured campaign
company/product/source pool; unrelated stock operations immediately delegate
unchanged. This is source in the new optional addon, not a running-service
modification. Read-only SQL confirms0 installed operations_campaign_automation
modules in the working DB; its original14-item fingerprint still matches.
Any runtime exercise installs only in a generated owned disposable DB. Never
install/update the working DB to test these hooks or bypass an approval rejection.

Implementation and developer validation, before independent-review repair:
the optional campaign addon and guarded -WithCampaign runner/preview exist.
Seven fresh developer runs were needed; early failures exposed raw-line direct
state edits, standard merge/negative-delta cleanup guards, and test-fixture role/
field/assertion-placement errors. Each failed owned DB was removed and the
working module/control fingerprint remained unchanged. These iterations are
development tests, not seven formal review/repair rounds.

Full pass command .\scripts\validate-fulfilment.ps1 -WithCampaign, exit0,
DB oct_scenario_e5bb075dbbb341f390f6306996adc166, removed/absence verified.
70 methods passed (8 base+22 promise+40 campaign),0 failures/0 errors; standard
diagnostic seven gaps remain separate; promise real-connection/Form probe passed;
campaign11cases passed, including500+400=900, two raw suppliers/own production,
300/200/100 corporate batches, supply-risk ownership/idempotence, scheduler,
six genuine connection-pair races and nonnegative/non-over-reserved invariants.
See evidence/task-0007/README.md for exact environment, scope, digest and UI cases.

Formal independent review round1, /root/campaign_reviewer: one confirmed P1.
Manual preparation only locked the pool; public picking.do_unreserve followed
by a later order's saved quantity/picked edit could bypass date priority. A
standalone saved preparation could also over-reserve before validation rejected
it. Existing tests wrapped preparation+validation in one rollback and missed
that persistence boundary. No other confirmed defect was reported; source-only
review, not a separate technical read-only sandbox or repeated runtime execution.
Reviewed19-file aggregate79BCC94D8E35603BC769121782731EF8B4F13C0A0F66C850C091AAB6EAFEE55C.

Root reproduced the P1 in guarded owned preview DB7f3f44f09dc841a5a7e7a6304e4a9357:
Stock-only actor, earlier B acceptedDec14 remaining300/reserved200; later A
acceptedDec15 demand200/reserved0. B.do_unreserve; A.quantity200+picked; A.validate
completed the later shipment. All reproduction mutations rolled back; no commit.
Repair plan: cap manual preparation at pre-call priority allocation; use a
private identity capability for validated nested stock edits, never a Boolean/
sudo exemption; reconcile public unreserve; test saved move/raw-line preparation
independently of validation, immediate quant invariants and valid corporate
partial preparation. Rerun full validation/UI and request formal round2 review.
TASK-0007 remains In Progress; no accepted/completed campaign claim yet.

Repair1 verification: .\scripts\validate-fulfilment.ps1 -WithCampaign exit0,
ownedDB01139697254b4567a180cfa7c43457c5 removed/absence verified.78 methods passed
(8+22+48), all11 campaign cases plus legacy/promise probes passed. Added saved
preparation/default/UoM/batch checks, public-unreserve reconciliation, guarded
Sales demand/cancellation/retargeting, final physical-drift guards and the explicit
partly-prepared consumer unprepare/recheck workflow. A native completion-date
regression in the repair was corrected and the full suite rerun, not waived.
Root's fresh-process Stock-only probe refused all three saved preparation paths
immediately, preserved200 physical/reserved and0 late delivery; all edits rolled back.

Formal round2 found a new P1 in the first repair: an unrelated product's parent
move could mint the private preparation capability for caller-supplied nested
move_line_ids. A malformed pool-product line then bypassed the raw-line checks.
Root reproduced physical100/reserved100->101 with a Stock-only actor, rollback
verified. Second/final repair restricts capability minting to matching-pool
native quantity inverses, never explicit one-to-many commands (including mixed
quantity/picked input). Nested create/update/link stay independently checked.
Three new regression methods verify immediate invariants and normal outside
quantity entry; no broad EVENT/sudo/Boolean exemption was introduced.

Final runtime command .\scripts\validate-fulfilment.ps1 -WithCampaign, exit0,
ownedDB oct_scenario_146c2c80ae8d41ef8792d6717fe2e8d8, removal/absence verified.
81 methods passed (8 base+22 promise+51 campaign),0 failures/0 errors. All11
campaign cases passed:500+400=900, two input suppliers/own manufacture,
corporate300/200/100, supplier-risk ownership/idempotence, date-response policy,
actual scheduler, six distinct-connection pairs107348/107349 and seven final
nonnegative/non-over-reserved quants. Old promise probes107302/107304 and Form
helper passed; standard diagnostic's seven gaps remain explicitly separate.
Expected lock/serialization errors were deliberately refused/retried, not ignored.

Final20-file aggregateFEDA78AD52AA0A4EBBBF43E01BE14A00CC93ABDA582D21CB77D568C9F1C0B289.
See evidence/task-0007/README.md for scope/hash algorithm, environment and13
unaltered UI images. Final browser: unauthorized preparation Save rejected;
valid corporate50-unit partial Done with next backorder. Fresh Stock-only nested
create/mixed/update/link probes all refused with physical/reserved100 unchanged;
ordinary outside quantity1 remained allowed. Every probe fixture was rolled back.

Final read-only resource inventory: no oct_scenario DB and no oct-ui container;
preview credential file absent. Only owned preview containers were restarted,
never shared services. Main Odoo/PostgreSQL healthy; health200; modules unchanged
and14:17f2a87362f026a248dc420227dd452f retained. No optional live installation,
historical migration, external message, commit, remote, push or publication.
Final reviewer closure and static/secret-gate results follow below; explicit
owner acceptance is still required before Done.

Final static/secret checks, all exit0 and no DB mutation: repository checker79
text files; AST31 addon Python files; both validation/preview PowerShell parsers;
68 local link targets present (not a remote-link/browser-matrix check);
git diff --check; docker compose config --quiet.99 final candidates yielded0
high-confidence private-key/token and0 exact local-secret matches,1 actual
local secret compared only in memory.37 files in the only existing commit also
yielded0 matches. Sensitive candidate filenames/staged changes/remotes absent;
ignore checks matched .env/.env.test/private.key/backups/filestore/sqlite3.
This is a heuristic scan, not a completeness guarantee or provenance audit.

Formal independent round2 closure,2026-10-15, /root/campaign_reviewer:
no remaining confirmed defects in the reviewed final source. Both P1 findings
are closed: pre-call allocation bounds/public-unreserve reconciliation prevent
saved-preparation priority bypass; scoped capability minting excludes explicit
move_line_ids and unrelated parents, preserving independent nested-line checks.
The reviewer read all campaign source/security/views/tests, validation/preview
helpers, the narrow legacy diagnostic change and relevant task/decision/public
documentation; inspected screenshots09-13; read installed Odoo source/Git; and
independently recomputed the20-file aggregate above with an exact match. Important
SHA256s: dispatch.py4C0BB604080A6AB9110266DF9006D372C9E39B4011235A491708FC50D47EBA28;
test_campaign.py02D1833F1E58D1F003ACA0A0E17F066A600A0A86411A0C2791C871742000427E.

Review was read-only by instruction, not a separate technical sandbox. Runtime,
reproduction, cleanup and secret scans were developer evidence considered by
the reviewer, not independently rerun; the reviewer did not read .env or change
files/data/services. No third review/repair cycle was started. Documented limits
remain: configured one-step untracked MTS goods, whole prepared-move protection,
explicit unprepare/recheck for extra consumer allocation, one-level risk signals,
unverified pure Purchase/MRP-only roles, and no load/restore/migration/cleanup-
fault/browser-matrix/production guarantee. No remaining confirmed defect blocks
handover of this approved bounded scope. TASK-0007 is now Review; Done requires
explicit Product Owner acceptance. No commit, remote, push or live rollout.

Acceptance closeout,2026-10-15 (Europe/Berlin): Product Owner Yusuf Ondes
explicitly accepted the delivery in this chat (English translation: "Okay, I
accept the delivery."), then asked what information is needed for GitHub.
TASK-0007 is Done for the approved bounded source/test delivery against the
recorded81 methods,11 campaign cases, browser evidence, final independent
review and20-file aggregateFEDA78AD52AA0A4EBBBF43E01BE14A00CC93ABDA582D21CB77D568C9F1C0B289.
This supersedes earlier pending-acceptance states in this task's chronology;
all documented exclusions and validation limits remain. It does not accept
other pending tasks or authorize working-DB installation, release creation,
commit, remote addition, push, hosting or deployment. TASK-0006 remains Needs
Decision for publication choices and explicit authority to perform the writes.
Only acceptance/status documentation changes in this closeout; no functional
code or runtime validation is changed or rerun. Git preflight still shows main
at the initial baseline, no remote and uncommitted implementation changes.

Acceptance-only closeout checks: python .\scripts\check_repository.py exit0
(79 text files); git diff --check exit0; the same20-file functional aggregate
above recomputed unchanged; no staged files or remotes. Separate read-only
/root/acceptance_closeout reviewed the six acceptance-document updates and found
no confirmed defects or expanded authority; other task states were preserved.
This was a focused new acceptance-record check, not a third source repair round.
No .env read, runtime rerun, Git write, dependency install or service/data change.
GitHub CLI was not found on PATH; authentication by other methods was not tested.
