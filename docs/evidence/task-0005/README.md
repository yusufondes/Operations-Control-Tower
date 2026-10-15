# TASK-0005 browser evidence

Executed 2026-10-15 (Europe/Berlin), using the supported in-app browser API.
These are synthetic test records, not real customer communications. The images
are developer evidence, not acceptance by themselves; explicit Product Owner
acceptance was subsequently received on2026-10-15 and is recorded in TASKS.md.
Authoritative repository: C:\Users\yusuf\Operations-Control-Tower.

## Environment and boundaries

- Local image ID: sha256:dd9013e669caaa23d26765dc55814655eaeecca7cfc2c265dbabae913bce22fd.
- Odoo 19.0-20260926, PostgreSQL15, ordinary Sales/Coordinator test user.
- Owned DB: oct_scenario_6ce183d5caee400eb994c5d000a6fb60.
- Owned container: oct-ui-6ce183d5caee400eb994c5d000a6fb60.
- Preview bound to host 127.0.0.1:63840 only; no cron, exact DB filter,
  database listing disabled and ephemeral container-local data directory.
- No browser actions targeted working port8069. Shared PostgreSQL/network/image
  infrastructure means this is not a fully isolated stack.
- Random temporary login credential was not printed or copied into this folder.

## Observed UI cases

| Case | Actual result | Screenshot |
| --- | --- | --- |
| Establish15, propose18, estimate19 | Original/current15 retained while proposal pending; estimate distinct | [01](01-pending.jpg) |
| Accept18, then reject20 | Current18, original15, estimate19, revision2; both responses visible | [02](02-accepted-rejected.jpg) |
| Propose21 at600 units, change quantity to650 | Stale warning and scope snapshot600; old proposal cannot apply | [03](03-stale-before.jpg) |
| Submit Accepted for stale21, before repair | Response persisted, date unchanged; client navigation threw undefined.map | [04](04-stale-ui-error.jpg) |
| After repair: propose22 at650, change to651, submit Accepted | Warning and normal promise form; Stale/Accepted retained, applied=false, date18/revision2 unchanged after reload | [05](05-stale-response-fixed.jpg) |
| Attempt proposal23 without reason | Missing-required-fields notice; wizard stays open; Cancel creates no proposal23 | [06](06-required-reason.jpg) |
| Standard customer Delivery Date | Browser DOM still showed Dec14,1:00PM in Europe/Berlin (fixture UTC12:00); not overwritten by warehouse promise | [07](07-standard-delivery-unchanged.jpg) shows Other Info navigation only; the value is below the image crop |

The promise/history forms expose no Edit button and history booleans are
disabled. This is visual evidence, not proof of authorization; role/company/
direct-CRUD tests are recorded separately under TASK-0004. Four proposal rows
remain after cancel. No authenticated customer consent, email send, carrier
integration, stock-priority enforcement or owner acceptance is asserted.

## Confirmed defect and repair

P2: a stale response returned display_notification with a nested window action
missing views. Odoo normalizes only the outer action, while its client expects
action.views.map. The response transaction succeeded before client navigation.
Reload confirmed preserved data; repeating the failed response was unnecessary.

The existing _form_action now explicitly returns views=[(False,"form")]. No
business/date rule changed. A new ordinary-coordinator stale-response wizard
regression checks the action contract, saved evidence, applied=false and
unchanged date/revision. Only the label-proven owned preview container was
restarted to load this fix; working services were not restarted.

## Automated regression after repair

Command: .\scripts\validate-fulfilment.ps1 -WithPromise. Exit0.
Fresh DB: oct_scenario_45be0767fd2e4897b2a0ea09ca43c3c9, subsequently removed.
30 test methods (8 original +22 integration), zero failures/errors. Standard
500+400=900 arithmetic and corporate300/200/100 batches passed. Seven standard
business-rule diagnostic gaps remain gaps, not acceptance passes. Two real
connection probes (backend90848/90850), old-snapshot/new-line protection and
server Form helper passed. Expected NOWAIT/serialization log errors were handled
probe stimuli, not unhandled failures. Working scoped fingerprint unchanged.

## Cleanup and source identity

Both UI helper runs completed with exit0: the browser DB/container above and a
fresh normal-path helper check using oct_scenario_5ad50051b0e8410693b3a18a9ea10ac0
and oct-ui-5ad50051b0e8410693b3a18a9ea10ac0. The hardened helper's Start/Stop path
was exercised; startup-failure recovery was source-reviewed, not fault-injected.
Both labeled containers and owned DBs were removed, both exact temporary
credential files were absent, and final enumeration found no oct_scenario_ DB
or one-off container. The temporary browser tab was closed.

Whole-session before/after working module states and 14-control-item fingerprint
matched: 14:17f2a87362f026a248dc420227dd452f. This is a scoped integrity check,
not a complete database comparison. The optional addon and sale_order integration
columns were still absent from the working DB. Both services remained healthy;
working /web/health returned pass.

Baseline HEAD remains d62b6bc2de98ef3e500a2c177d57d007b37ece68. No new commit,
remote or push. Final executable/source aggregate SHA256 across 13 addon sources
and 5 validation/preview scripts:
702DEAB9663CB6A6EDD0B21C9B5417CEC4FAEC82B934ECCCE9B73C391400C2FE.
Same case-sensitive path/hash, UTF8/LF algorithm as TASK-0004. This excludes
Markdown and images. Documentation/review evidence is recorded in TASKS.md.

This single desktop viewport/session does not establish mobile/browser-matrix
coverage, load capacity, cleanup fault recovery, migration safety or production
readiness. See TASKS.md for final hashes, cleanup, independent review and handover.

Independent renewed round2 review found no remaining confirmed defects or further
functional repairs; it inspected all seven images and matched the source hashes.
Yusuf Ondes subsequently explicitly accepted the Review handover on2026-10-15.
TASK-0004/TASK-0005 are Done for this source/disposable-test scope. Documented
limits remain; no working-system deployment or new commit is implied.
