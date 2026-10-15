# TASK-0007 campaign validation evidence

Date:2026-10-15 (Europe/Berlin). Synthetic, local-only validation.
Authoritative source: C:\Users\yusuf\Operations-Control-Tower.
Validation baseline HEAD:d62b6bc2de98ef3e500a2c177d57d007b37ece68; changes were
uncommitted at that checkpoint. Later source commits/publication are recorded
under TASK-0006; the tested functional digest below remains the evidence anchor.

## Validation and review gate

The first full runtime pass was not the final acceptance gate. Independent
review round1 found a manual-preparation priority bypass; round2 identified a
nested raw-line capability gap in the first repair. Both were reproduced with
Stock-only users in the owned preview DB, fixed and regression-tested. All
reproduction changes were rolled back. Final independent round2 review found no
remaining confirmed defects and independently matched the20-file digest below.
The reviewer read source/docs and images09-13, without rerunning runtime or
secret scans or changing files/services/data. TASK-0007 records the formal report
and the explicit2026-10-15 owner acceptance; it is Done for this bounded source/
test delivery. Acceptance did not rerun these tests or authorize live installation,
commit or publication; all recorded evidence and limits below are unchanged.

Command: `.\scripts\validate-fulfilment.ps1 -WithCampaign`, exit0.
Final owned DB:`oct_scenario_146c2c80ae8d41ef8792d6717fe2e8d8`, removal verified.
Odoo19.0-20260926, actual container image
`sha256:dd9013e669caaa23d26765dc55814655eaeecca7cfc2c265dbabae913bce22fd`,
PostgreSQL15. Shared services, database-separated tests, no live installation.

Final observations after both repairs:

- 81 methods:8 base,22 promise,51 campaign;0 failures/0 errors.
- Standard diagnostic remains separate with seven known standard-field gaps.
  Those gaps are not campaign passes or newly unresolved owner decisions.
- Promise probe: real independent connections, new-line phantom and Form helper.
- Campaign probe:11 passing cases, including two400-unit raw-material POs,
  own400-unit production,500+400=900 dispatched, initial allocation200/300/0,
  corporate batches300/200/100 and final main-SKU stock0.
- Supplier-risk date2030-12-21, one source-linked owned blocker, repeated updates
  without duplicates; pending/rejected dates do not reprioritize, accepted dates do.
- Real standard scheduler entry and six distinct-connection pair probes:
  supply/allocation, acceptance/allocation, move preparation, raw-line preparation,
  earlier-order and new-line REPEATABLE READ phantoms. Backend IDs differ within
  each pair. Deliberately caught lock/serialization errors are expected evidence.
- Final seven probe quants were nonnegative and not over-reserved.
- Working module states and14-item fingerprint remained
  `14:17f2a87362f026a248dc420227dd452f`.

Final tested20-file aggregate:
`FEDA78AD52AA0A4EBBBF43E01BE14A00CC93ABDA582D21CB77D568C9F1C0B289`.
Scope:15 campaign addon source files plus validate-fulfilment.ps1,
validate_campaign.py, validate_fulfilment.py, preview-dispatch.ps1 and
seed_campaign_preview.py. The legacy diagnostic changed only a stale message
that incorrectly called the already approved policy open; its gaps remain gaps.
Algorithm: sorted relative slash-normalized path + colon + uppercase fileSHA256,
joined with LF, UTF-8 without final LF, then SHA256.

## Real browser observations

Owned preview DB:`oct_scenario_7f3f44f09dc841a5a7e7a6304e4a9357`;
container:`oct-ui-7f3f44f09dc841a5a7e7a6304e4a9357`, loopback only.
Synthetic Sales/Coordinator/Stock Manager/Operations Manager user, not admin.
Ordinary Stock-only dispatch permissions are separately covered by runtime tests.

The preview starts with synthetic opening stock500 and no physical production or
dispatch. UI interactions subsequently record one fabricated customer response
and synthetic corporate dispatches300/100/50 while retaining each balance.
This UI path is separate from the900-unit purchase/MRP probe; it has no production
fixture. No real customer is contacted.

| File | Visible observation |
| --- | --- |
| [01](01-consumer-ready.png) | Consumer Complete, Ready, frozen policy/pool and confirmation history. |
| [02](02-consumer-partial-blocked.png) |100 of200 consumer units rejected before physical dispatch. |
| [03](03-owned-risk-item.png) | Source-order risk item with owner, Blocked state and next action. |
| [04](04-accepted-date-history.png) | Original Dec16 retained; manually accepted Dec14 current date and evidence history. |
| [05](05-accepted-priority-reserves-500.png) | Accepted earlier date reallocates unprepared stock to B:500 against600 demand. |
| [06](06-corporate-300-dispatched.png) | Corporate300-unit picking Done; backorder created. |
| [07](07-corporate-backorder-preserved.png) | Backorder demand300, remaining available reservation200. |
| [08](08-campaign-aware-notice.png) | Wizard notice accurately explains campaign reprioritization and no outbound message. |
| [09](09-manual-preparation-priority-blocked.png) | First repair rejects a saved200-unit preparation with zero allocation, before dispatch validation. |
| [10](10-repaired-corporate-partial.png) | Valid within-allocation100-unit corporate partial remains Done after the first repair. |
| [11](11-repaired-backorder-preserved.png) | Its balance remains200 demand with100 reserved. |
| [12](12-final-preparation-guard.png) | Final source again rejects the unauthorized preparation save. |
| [13](13-final-corporate-partial-done.png) | Final source permits a50-unit corporate dispatch and creates the next backorder. |

Screenshots01-07 use the pre-review-repair source. Screenshot08 follows an
update of only the campaign addon in this owned preview DB to load corrected
wizard XML; no working DB update or historical migration occurred. Browser
DOM observations accompany the screenshots; no pixel editing was performed.
Saved images are evidence, not a live service or authenticated customer consent.

Screenshots09-11 verify the first repaired source;12-13 verify the final20-file
revision above after restarting only the owned preview container. Fresh-process
post-repair probes also verified immediate refusal of saved move/raw-line/default
preparation and nested create/mixed/update/link commands, with physical/reserved
quantities unchanged. Normal outside-product quantity entry remained allowed.
These probes used ordinary Stock-only actors and rolled back every fixture edit.

## Limits

One-step make-to-stock, untracked configured goods only. Unsupported/unmanaged
competition fails closed. One-level BoM/open-MO/late-PO risk is a signal, not exact
pegging, capacity calculation or a guaranteed feasible date. The procurement/MRP
fixture includes Stock Manager; pure Purchase/MRP-only roles were not verified.
Native Sales cancellation activity logging uses a combined Sales+Stock actor;
Sales-only confirmation and Stock-only dispatch remain separate fixtures.
Prepared moves are protected as a whole. A partly prepared short consumer needs
explicit warehouse review/unprepare and Check Availability before extra
reservation; the system does not silently unpick or automatically top up it.
No load, migration/restore, cleanup-failure injection, browser matrix, carrier/WMS,
formal quality release, external messages, working installation or publication.

## Cleanup and publication safety

All generated scenario DBs and UI preview containers are absent in the final
read-only inventory. Stop verified the exact labeled preview container, its DB
and temporary credential file were removed. No shared Odoo/PostgreSQL service
was restarted; only the owned preview was restarted for code reloads. Main
services remain healthy, health endpoint200, module states/control fingerprint
unchanged. No optional campaign/promise installation in the working DB.

Heuristic secret gate:99 final candidate files and37 files in the only existing commit
had0 high-confidence token/private-key or exact local-secret matches;1 actual
local secret value was compared only in memory. No sensitive candidate filenames,
staged changes or remotes. All13 synthetic PNGs were visually inspected without
credentials. Final static checks:79 text files,31 addon Python ASTs,2 PowerShell
parsers,68 local link targets, Git whitespace and Compose validation all passed.
Pattern scans are not a completeness guarantee.
