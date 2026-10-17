# Portfolio Demonstration

This source portfolio has a base control-item workspace, an accepted optional
warehouse dispatch-promise addon, and a bounded optional campaign addon whose
TASK-0007 local validation is recorded separately. All example records and response references
are synthetic. No customer message or authenticated customer consent is produced.

HALY is the fictional company manufacturing its own products in this portfolio;
it has no claimed real-company affiliation, and saved screenshots retain their
historical generic synthetic labels.

## Dispatch promise walkthrough

Start with the saved [TASK-0005 browser evidence](evidence/task-0005/README.md);
no running Odoo installation is needed to inspect it.

The problem: a coordinator needs to distinguish the original warehouse dispatch
commitment, the currently accepted commitment, an internal estimate, and a
proposed change awaiting the customer's response.

| Step | Saved result | Image |
| --- | --- | --- |
| Establish date 15, propose 18, estimate 19 | Original/current remain 15 while the proposal is pending; estimate is separate | [Pending proposal](evidence/task-0005/01-pending.jpg) |
| Record explicit acceptance of 18, then reject 20 | Current becomes 18, original stays 15, estimate stays 19; both responses remain visible | [Accepted and rejected](evidence/task-0005/02-accepted-rejected.jpg) |
| Propose 21 at 600 units, then change demand | The proposal snapshot no longer matches the outstanding order and is stale | [Stale scope](evidence/task-0005/03-stale-before.jpg) |
| Record acceptance for another stale proposal after the repair | Response decision is retained, state is Stale, applied is false, current date remains 18 | [Stale response retained](evidence/task-0005/05-stale-response-fixed.jpg) |
| Attempt a proposal without a reason | Required-field feedback prevents creating the proposal | [Required reason](evidence/task-0005/06-required-reason.jpg) |

The evidence was recorded on 2026-10-15 with December 2026 example dates. These
dates are fixture choices, not a service-level agreement, calendar rule or
promised lead time. The screenshots show a single desktop session. The repaired
client-navigation error is retained in the evidence history, not presented as
current behavior.

The standard customer Delivery Date is separate. Screenshot 07 shows navigation
to Other Info, but its crop does not show the date value. The evidence record
distinguishes the browser DOM observation and automated checks from that image.

## Fresh interactive promise walkthrough

Follow [SETUP.md](SETUP.md#optional-promise-preview) to create the owned disposable
preview, sign in with its temporary coordinator credential, and keep the returned
resource identities for Stop. Never demonstrate this by installing into or
altering the working database.

The seed creates a confirmed synthetic 600-unit order and a fixed standard
Delivery Date of 2026-12-14. On a later run that date may be in the past. It is
not an SLA and is not the initial warehouse promise. Choose fresh dates manually
for the following actions; use the relationships from the saved example rather
than copying expired dates.

1. In Sales, open the order named in the preview metadata. Open its
   **Warehouse Promise** tab and **Open / Establish Promise**. Establish a future
   warehouse dispatch date (the equivalent of example 15).
2. Choose **Propose New Date** for a later date (example 18), enter a synthetic
   reason and record it. Use **Update Estimate** for another date (example 19).
   Confirm that neither action changes the current promise.
3. Open the pending proposal and **Record Customer Response**. Select Accepted
   and supply the required synthetic person, channel, response time and evidence.
   Confirm that current changes to the accepted date while original is retained.
4. Propose another later date (example 20), then record Rejected with synthetic
   evidence. Confirm current still equals the previously accepted date.
5. Propose a new date, change the synthetic order quantity, and reopen the
   proposal. Confirm the stale warning. Record an Accepted response: the response
   remains in history, but the stale proposal does not replace the current date.
6. Try a new proposal without its reason. Observe required-field feedback, then
   Cancel. No additional proposal should be created.
7. Run the exact Stop command with the returned database and container identities,
   as described in SETUP.md, and confirm successful cleanup.

Do not infer stock allocation or customer dispatch behavior from this promise-
only preview. The promise addon alone does not reschedule stock, enforce stock
priority, require complete consumer dispatch, send email or authenticate consent.
The promise covers the current outstanding order balance, not a separate date
for each partial batch.

## Campaign walkthrough under validation

TASK-0018 adds quantity-and-date approval to this walkthrough. Before the first
corporate partial dispatch, use the order's shipment-plan proposal/response
forms to record explicit synthetic consent for all remaining batch quantities
and their latest dispatch dates. Policy selection and a date-only promise are
not partial-shipment consent. Each dispatch must match the next batch in the
applicable accepted plan; a new response is not required for every unchanged
batch. Early exact-batch dispatch is allowed; changed
quantities or postponement require a newly accepted plan. The older browser
screenshots below do not demonstrate these new forms. This extension passed
108 local methods and 13 campaign cases, not a new browser-render check.

The [TASK-0007 browser record](evidence/task-0007/README.md) documents actual
campaign checks, the review-discovered preparation defect and repair proofs.
Review and owner acceptance remain separate gates. The TASK-0005 images above
do not evidence campaign behavior. Use only the owned disposable
[campaign preview](SETUP.md#optional-campaign-preview), never the working DB:

```powershell
.\scripts\preview-dispatch.ps1 -Action Start -WithCampaign
```

Its HALY fixture contains one configured pool/product, 500 synthetic opening
units and three discounted confirmed orders. Promise dates are fixed December
2026 examples, not a working-calendar or lead-time guarantee.

| Order | Explicit policy | Quantity | Accepted warehouse date | Expected initial reservation |
| --- | --- | --- | --- | --- |
| A | Consumer Complete | 200 | 15 December 2026 | 200 |
| B | Corporate Partial | 600 | 16 December 2026 | 300 |
| C | Consumer Complete | 100 | 17 December 2026 | 0 |

The preview metadata includes each order/picking/promise ID, pool/product IDs
and derived blocker IDs. Sign in with its temporary credential privately. The
demonstration user combines Sales, Coordinator, Stock Manager and Operations
Manager roles; that is not the separated-role security test fixture.

Expected checks to record during the walkthrough:

1. Open Sales orders A/B/C and **Campaign Automation**. Inspect the explicit
   policy, protected confirmation history, status and next action. Pool/policy
   cannot be changed on these confirmed orders. The standard customer Delivery
   Date remains separate from the warehouse promise.
2. In **Inventory > Campaign Pools**, inspect the one-step stock source,
   responsible owner and products. **Reconcile Reservations** should preserve
   the date-ordered allocation above, not give corporate status precedence.
3. On A, attempt a short customer dispatch. It must be refused without a
   completed partial consumer shipment. Complete quantities are required for
   every physical line in one customer picking. Do not treat a status change
   or promise date as a recorded physical shipment.
4. On B, a deliberately recorded synthetic 300-unit partial shipment should
   create a remaining 300-unit backorder. Do not select a balance-cancellation
   shortcut: campaign partial dispatch must retain the outstanding demand.
5. On a fresh preview before any preparation, propose an earlier date for C.
   Pending proposals/estimates and rejection must not reorder stock. Explicit
   accepted evidence can reprioritize unprepared quantities; picked/prepared
   or outside reservations remain protected. Preserve the original date and
   response history. Use fresh previews for independent experiments rather
   than claiming previously prepared stock can be reclaimed.
6. Inspect a shortage's owner/next action and source-linked control item.
   This seed creates no raw-material purchase, BoM or manufacturing order, so
   it does not demonstrate supplier-delay screens or produce the extra 400.
7. Stop using the exact returned database/container identities, following
   SETUP.md, and verify owned resources and the credential file were removed.

The full own-manufacturing scenario belongs to the explicit
`validate-fulfilment.ps1 -WithCampaign` run: recorded standard raw-material
receipts and production, then customer dispatch. Its intended arithmetic is
500 + 400 = 900 with corporate batches 300/200/100; TASK-0007 owns the actual
execution results. It does not automatically receive, manufacture or ship
goods merely because a date arrives. Supply-risk status is a one-level BoM/
open-production/late-purchase signal, not exact demand pegging or a guarantee.

Supported scope is configured one-step make-to-stock, untracked storable goods.
Uncovered unmanaged competition and unsupported routes fail closed. Inbound
returns are separate from consumer replacement shipments; multi-step/MTO,
carrier integration, formal quality release and capacity optimization are not
claimed. Partly prepared shortages require explicit warehouse review/unprepare
and Check Availability before extra reservation; nothing silently unpicks stock.
The recorded local campaign pass is not owner acceptance or a rollout.

## Base control-item walkthrough

Use a separate fresh base installation with its optional demo records loaded,
as described in [SETUP.md](SETUP.md#fresh-base-installation). The promise preview
uses no demo XML and is not a substitute for that dataset.

Operational priorities are frequently split across spreadsheets, messages, and meeting notes. The application creates one accountable workflow for deadlines, blockers, owners, impact, and next actions.

### Show the overview

Open **Operations Control > Overview** and point out:

- workflow columns;
- urgent and high-priority items;
- status indicators;
- owners and deadlines;
- the explicit next action on each card.

Explain that every operational scenario is fictional portfolio data. The examples model inventory reconciliation, production, quality, procurement, logistics, maintenance, and integration work for a powdered-drink business.

### Open a control item

Open **Reconcile WMS and Odoo stock for Hydration Lemon tubs**. Demonstrate the business area, impact, owner, priority, status, deadline, and execution notes. Change the Status selection to move the item between workflow columns.

### Show deadline management

Open **Operations Control > Deadlines** to display operational items on the calendar. Return to the list and use the Overdue, Blocked, and Critical Impact filters.

### Show management analysis

Open **Operations Control > Analysis**. Group records by business area and workflow state, then switch between graph and pivot views.

These views count control items. They do not calculate stock accuracy, on-time
delivery or other operational KPI definitions. The WMS, procurement, production
and quality card stories are fictional topics, not implemented integrations.

## Explain engineering evidence

TASK-0005 records 30 passing local methods (8 base + 22 optional), standard
fulfilment observations, connection/Form probes and the browser repair. See
[TASKS.md](TASKS.md) for commands, dates, revisions, gaps and acceptance. The
existing CI workflow covers the base addon only; a workflow file is not proof
of a successful remote run.

The working database has not received the optional addon. Source acceptance and
disposable-test evidence do not establish a production rollout, load capacity,
migration safety, a browser matrix, or completion of the wider fulfilment roadmap.
The campaign delivery has a separate recorded 81-method pass and 11 probe cases
under TASK-0007; see its review/repair and acceptance record. The historical
30-method result alone does not prove that delivery.
