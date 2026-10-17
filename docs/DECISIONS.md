# Decisions and open questions

Use this log for durable decisions and rationale, not task completion or changing runtime snapshots. Each entry records its basis; a verified fact is not retroactively presented as Product Owner approval.

Historical "not implemented" and open-detail notes below describe their original
decision date/slice. D-012/D-015 and TASK-0007 supersede those bounded campaign
questions. Read PROJECT_STATUS/TASKS for current implementation/test evidence;
do not reopen explicitly approved stock policies from an older entry.

## D-001 - Authoritative repository

Status: Approved. Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: `C:\Users\yusuf\Operations-Control-Tower` is the single development source. Preserve initial commit `d62b6bc2de98ef3e500a2c177d57d007b37ece68` and history. Do not add remotes or push without explicit authorization.

Basis: explicit repository/initial-commit instructions in this chat and the attached setup request, sections 1 and 9. The similarly named OneDrive folder is not the application source.

Consequence: subsequent Codex work should open the actual repository. Repository documents cannot retarget the current desktop chat or grant filesystem access.

## D-002 - Approval and acceptance gates

Status: Approved. Product Owner: Yusuf Ondes. Date: 2026-10-15.

Decision: explicit approval is required for implementation scope; significant architecture/business decisions stay with the Product Owner. Delivered tasks remain Review until acceptance evidence and explicit Product Owner acceptance exist. Limit autonomous review/repair to two rounds.

Basis: attached "Codex Project Operating System - Initial Setup", sections 2, 5 and 8. TASK-0001 records the attachment reference.

Rationale: avoid treating suggestions, assistant promises or green tests as approved scope or accepted work.

## D-003 - Language and portfolio data

Status: Approved. Product Owner: Yusuf Ondes. Date: 2026-10-15.

Decision: Turkish owner communication; English repository content and commit messages. Use a fictional company and synthetic data; distinguish real functionality from simulated systems and do not claim knowledge of real HOLY operations.

Basis: explicit earlier portfolio direction and setup sections 4, 6 and 7.

Consequence: existing product-themed cards are synthetic examples. The README roadmap suggestion to use a real dataset is not approved authorization to acquire or import company data.

## D-004 - Preserve the installed baseline during governance setup

Status: Approved setup constraint, with separately verified implementation facts. Date: 2026-10-15.

Decision: retain Odoo 19 Community, PostgreSQL 15 and the current addon. Do not change ERP features, data, schema, module dependencies or deployment during TASK-0001.

Basis: setup sections 1 and 11. Verified manifest depends only on base and web; architecture and status own detailed evidence.

Consequence: no new Sales, Inventory, Purchase, Quality, WMS or other modules until an approved business requirement and compatibility assessment justify them. No infrastructure or dependency upgrade is part of this setup.

## D-005 - Review capability and enforcement

Status: Verified environment observation and setup implementation choice. Date: 2026-10-15.

Observation: separate session subagents work; the exposed spawn tool has no per-agent permission/allowlist controls. Custom agent instructions cannot establish their own sandbox, per the official documentation cited in REVIEWER.md.

Choice: invoke a separate reviewer with the repository protocol and no-edit instructions. Document inherited permissions honestly. Keep a native/manual review fallback. No unverified custom agent loader, new API application, recurring automation or repository skill is introduced.

Revisit if: a future client exposes verifiable role loading, a stronger permission boundary is required, or repeated work justifies a reusable skill. Product Owner scope authorization is still required for new setup.

## D-006 - Risk-based validation and data preservation

Status: Approved constraint and verified test boundary. Date: 2026-10-15.

Decision: execute proportionate checks and record revision, environment, exit status and result. Preserve working/production data. Runtime and migration tests use disposable databases/copies; automated validation does not replace review or acceptance.

Basis: setup sections 7-9. Script inspection confirms the existing smoke test uses a separate database but shared services; it does not exercise upgrade migrations.

Consequence: governance-only edits use static checks and focused review. Do not execute bootstrap, live upgrade or historical demo-reset migrations to validate documents. Record unexecuted runtime tests without claiming they passed today.

## D-007 - Own production and two customer types

Status: Approved business direction, not implementation authorization.
Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: the fictional company manufactures its own products and can procure
raw materials from different suppliers. It serves individual consumers and
corporate customers. Corporate orders may be dispatched in partial quantities
as stock becomes available.

Basis: explicit choices in this chat to manufacture rather than buy finished
goods, and to include corporate customers with successive partial shipments.
This resolves O-002. It does not approve installing Manufacturing or any other
module, or establish detailed production, individual-customer shipment, or
quality-release rules.

## D-008 - Promised dispatch date determines stock priority

Status: Approved business rule, not implemented.
Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: when eligible customer demand competes for available stock, use the
earlier promised dispatch date before customer type. Corporate status alone
does not confer priority over an individual consumer.

Basis: the Product Owner explicitly accepted the promised-dispatch-date
priority proposal in the latest message in this chat. The date is a dispatch
commitment, not a carrier delivery date.

Equal-date tie-breaking is approved in D-009. Open details: missing dates; authority
and audit for date changes; per-order vs per-shipment promises for partial
orders; reservations, quality eligibility and allocation implementation.
Do not infer priority override powers or an automatic reallocation policy.

## D-009 - Earlier confirmation breaks an equal dispatch-date tie

Status: Approved business rule, not implemented.
Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: when promised dispatch dates are equal, prioritize the order that was
confirmed earlier. Customer type does not precede either date criterion.

Basis: the Product Owner explicitly answered yes to the proposal to prioritize
the earlier-confirmed order when dispatch dates match, in the current chat.
This approves the secondary criterion only; it is not installation,
implementation or task-acceptance authorization.

Open details: equally timed confirmations, missing dates, cancelled/reconfirmed
orders and confirmation-history preservation. A stable ID as a final tie-break
is still a proposal, not part of this approval.

## D-010 - Individual-consumer orders dispatch complete

Status: Approved business rule, not implemented.
Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: dispatch an individual consumer's order in one customer shipment when
all required products and quantities are ready. Corporate orders retain the
partial-dispatch permission in D-007. Neither policy overrides the date-based
stock priority in D-008/D-009.

Basis: the Product Owner explicitly approved the immediately preceding question
about dispatching individual orders once all products are ready, in this chat.
This approves the business policy only. It does not authorize ERP module
installation, application changes, partial-shipment exceptions, or task acceptance.

Design checks: enforce the approved policy on actual customer dispatch, not just
a readiness label. Verify short quantities, multiple product lines and
attempted partial validation in a future approved test scope. Reservation
behavior while a consumer order is incomplete still needs definition.

## D-011 - Customer approval controls a changed dispatch promise

Status: Approved business rule, not implemented.
Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: when the existing dispatch commitment is at risk, propose a new date
to the customer. If the customer explicitly accepts it, plan the affected
dispatch against the accepted date. If the customer rejects it, keep the
existing commitment and pursue operational actions to meet it.

Basis: the Product Owner explicitly specified the propose/accept/reject flow
in the current chat. A proposal is not a confirmed promise; silence must not
be treated as acceptance. Customer rejection does not guarantee that
the original date can physically be met.

Planning consequence: distinguish original commitment, currently accepted
commitment, proposed date and latest operational estimate. Retain the change
history so rescheduling cannot erase the original promise or an actual delay.
Record customer response evidence and the order/quantity it covers. These are
requirements for a future design, not existing model fields or a live workflow.

No approval is given here to send messages, change actual customer orders,
incur expedited-freight/overtime costs, bypass stock/quality controls, install
modules or implement features. Proposal authority, response capture, amendments
and per-order/per-partial-shipment promise scope still need design decisions.

## D-012 - First dispatch-promise slice and approval

Status: Approved implementation boundary, not a completed capability.
Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: implement TASK-0004's separate warehouse dispatch-promise and manually
recorded customer-response gate only in disposable validation databases.
For corporate orders, one promise covers all outstanding quantities; partial
shipments remain allowed. A dedicated coordinator with ordinary sale/company
access records customer respondent/channel/time/evidence, not authenticated
customer consent. A changed remaining scope invalidates the old proposal, whose
response may be retained but cannot change the current promise. Pending/rejected
proposals never replace the last accepted promise. Preserve original date and
finalized history. Use calendar dates, without an inferred SLA/cutoff engine.

Basis: explicit yes to the TASK-0004 proposal and its three recommended choices.
The task owns the accepted implementation/test scope. This resolves O-010 for
the first slice only; detailed per-batch schedules remain deferred.

Boundary: no stock allocation, full-consumer dispatch enforcement, standard
delivery/picking date synchronization, working DB installation, outbound
messages, deployment or task acceptance. An optional integration addon keeps
the existing control addon dependent only on base/web. D-011 operational
scheduling is not fully implemented merely by adding this planning reference.

## D-013 - HALY is the fictional scenario company

Status: Approved naming decision, not authorship or deployment authorization.
Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: use HALY for the fictional own-manufacturing company in the portfolio
scenario and current publication documents. It is not a claim about any real
company or endorsement. Existing screenshots retain their actual synthetic
labels; no screenshot or historical evidence is rewritten to pretend otherwise.

Basis: the owner explicitly proposed HALY as the company name in this chat.
The decision does not establish software copyright ownership or authorize
replacing the existing HOLY license/author notices. Keep that verification
separate from scenario branding; no working DB/company rename is performed.
The later ownership declaration and metadata correction are recorded in D-014.

## D-014 - Owner-declared software attribution

Status: Approved project metadata correction; license terms unchanged.
Product Owner: Yusuf Ondes. Date: 2026-10-15 (Europe/Berlin).

Decision: after explicitly declaring that the code is his and requesting
continuation, Yusuf Ondes is the project copyright holder in the project header
and the base addon's author, replacing the earlier HOLY entries. The optional
addon already names Yusuf Ondes. HALY remains only the fictional scenario name.

This records the owner's declaration; no independent chain-of-title audit is
claimed. Preserve the LGPL/GPL license bodies and FSF/third-party notices. Do not
rename the license, change version/dependencies or update/install a working DB
to apply display metadata. This resolves O-007's attribution decision, not the
remaining business rules, GitHub target/visibility or publication completion.

## D-015 - Campaign reservation and ordering policies

Status: Explicitly approved implementation policy package.
Product Owner: Yusuf Ondes. Date:2026-10-15 (Europe/Berlin).

The owner explicitly approved the complete proposed package in the current
chat's structured answer. Implement D-008/D-009/D-010 with these details:
- Incomplete consumer orders retain stock allocated by date priority but cannot
  dispatch before the complete current physical order is ready.
- Reconcile unpicked/unprepared campaign reservations against current priority;
  preserve prepared/picked and completed quantities and outside reservations.
- Missing accepted warehouse promise means no automatic campaign allocation or
  dispatch, with a visible actionable status. No estimate/Delivery Date fallback.
- Priority key: accepted warehouse dispatch date, current confirmation-event
  timestamp, then smaller stable order ID. Customer type/urgency do not precede
  these. Cancellation/reconfirmation receives a new timestamp; retain history.

This resolves the previously open reservation/tie/missing-date questions for the
bounded HALY scenario. Use explicit shipment policy and a configured warehouse/
product pool; identify unsupported/unmanaged competition rather than rank it
silently. No physical receipt, manufacture or dispatch is inferred from a date.
No live installation, external messages, carrier/WMS, capacity optimization,
formal quality release or nine-area ERP roadmap is authorized by this package.

## D-016 - Quantity-and-date customer shipment approval (TASK-0018)

Status: Explicitly approved implementation policy, 2026-10-17.
Product Owner: Yusuf Ondes, approval in the current chat.

Corporate partial dispatch must follow an explicitly customer-approved plan of
batch quantities and latest dispatch dates. Early dispatch is permitted; a
quantity change or postponement requires renewed customer approval. A proposal
or silence is not consent. Employee-entered contact/channel/time/evidence is
retained; no authenticated portal or outbound integration is inferred.

This supersedes D-012's one-date/automatic corporate-partial permission for
TASK-0018's bounded campaign workflow and resolves O-003 within that scope.
Each accepted batch date ranks only its own quantity. Original promise history,
completed batches, consumer-complete policy and protected reservations remain.
Pending/rejected proposals retain the current accepted plan. Source-scope
changes invalidate applicability; a replacement covers all remaining goods.
Overdue batches require a newly accepted remaining plan before dispatch.

The original full remaining shipment remains possible without a split plan
against its accepted commitment. This is not capacity planning, an assurance
that production can meet the date, a working-DB upgrade or production acceptance.

## Open proposals - not approved

| ID | Proposal/question | Required evidence or decision |
| --- | --- | --- |
| O-003 | Detailed per-batch schedules beyond the original bounded scenario | D-016/TASK-0018 now authorizes explicit quantity/latest-date approval for campaign batches; minimum quantities, capacity planning and integrations remain outside scope. |
| O-004 | Quality hold and release | Assess Community standard flows, actual blocking behavior, roles and possible custom gap. |
| O-005 | A broader blocker engine beyond one derived campaign risk item | TASK-0007 covers the bounded source-linked owner/next action. Additional blocker types or cross-system coordination need separate justification. |
| O-006 | Inventory reconciliation, CSV WMS, supplier/shipment tracking, CAPA, maintenance, alerts, executive KPIs and APIs | Candidate areas only; no nine-module commitment. Select features from an approved scenario. |
| O-008 | Historical demo migration replay and cleanup assertions | Assess a safe upgrade/test-copy strategy before future migrations; changing scripts/behavior is outside this setup. |
| O-009 | Dispatch within three working days | Earlier assistant proposal only; no Product Owner approval or calendar/capacity validation yet. |
