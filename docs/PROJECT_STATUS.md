# Project status and Codex working guide

Snapshot date: 2026-10-17 (Europe/Berlin).
Authoritative repository: `C:\Users\yusuf\Operations-Control-Tower`.

## Current summary

TASK-0018 is in Review (2026-10-17): customer-approved batch quantities and
latest dates, early dispatch and renewed approval for changed quantities/late
dispatch are implemented in campaign source 19.0.2.0.0. Final fresh disposable-
DB validation passed 108 methods (27 new), three promise probes and thirteen
campaign cases, including two new real-connection plan races. Independent final
review found no new confirmed defect after two P2 repairs. Owned DB removal and
scoped working fingerprint equality were verified. No working-DB installation
or browser/upgrade test occurred. The owner has now authorized source commit
and GitHub publication, without deployment or working-database access. See
TASKS for exact digests and execution limits. Remote CI covers the base addon
and health, not the full optional campaign suite validated locally.

TASK-0012 delivered the authorized public source publication, CI-health repair,
disclosure checks and presentation wording update on 2026-10-15. The repository
is public. Anonymous README/PDF/PowerPoint downloads matched the reviewed local
files byte for byte. Reviewed portfolio commit
`96e8693885eba18ea791fc0cdf9caa8d71616557` passed
[remote CI](https://github.com/yusufondes/Operations-Control-Tower/actions/runs/38769265214):
repository checks, 8 base methods, health and cleanup. It does not run the
full 81-method local validation. The task remains Review for owner acceptance;
its receipt separates publication from deployment. No local unit tests,
application features or working databases were changed for this delivery.

TASK-0011 packaged the reviewed preview repair, presentation and regression
evidence in three local commits, ending at
`af3ddf88a203be38255ec548f6e12619dbc43ac4`. That is TASK-0012's baseline,
not a promise that it remains the current Git tip.

Latest local revalidation: TASK-0010 reran all 81 custom methods (0 failures/errors),
3 promise and 11 campaign probes, plus 24 authenticated HTTP cases and 7 admin
configuration checks. Standard-only diagnostics remain 3 passes, 7 gaps and
1 observation, not 11 acceptance passes. Detailed commands, source digests,
harness attempts and coverage exclusions are recorded under TASK-0010 (Review).
No remote CI result is inferred from these local results.

TASK-0008 repaired preview startup/cleanup for Windows PowerShell 5.1 and
verified real Start/Stop/login without working-DB writes. At the TASK-0010
checkpoint, all newly owned test resources were removed, the working fingerprint
and shared-service uptimes matched, and the owner's separate synthetic preview
was preserved. These are dated observations, not a fresh runtime inventory.

Accepted bounded implementation: TASK-0007 passed 81 methods
(8 base + 22 promise + 51 campaign) and 11 campaign cases in an owned temporary
DB, including in-house production, 900 units dispatched and six real-connection pairs.
Independent reviews found manual-preparation and nested raw-line capability
bypasses; both were reproduced, repaired and retested, including standalone
saved preparation and real browser refusal plus valid corporate partial dispatch.
Final independent round 2 review found no remaining confirmed defects and verified
the final 20-file source digest. TASK-0007 is Done after explicit owner acceptance
on 2026-10-15; no live installation is inferred from that acceptance. At that
checkpoint, its test DBs and previews were removed and the working system was unchanged.
See [campaign evidence](evidence/task-0007/README.md) for evidence and limits.

The TASK-0005 browser repair and 30-method result below remain historical evidence
for the accepted promise-only slice, not the total current campaign test scope.

Latest acceptance: Yusuf Ondes explicitly accepted the TASK-0007 handover
on 2026-10-15, after its final review and 81-method/11-case evidence. It is Done
for the bounded source/test delivery, not deployment or publication acceptance.
The separately authorized source push is recorded under TASK-0006. TASK-0004/0005
also remain Done from their earlier explicit acceptance. Earlier Review/
pending-acceptance notes are historical; all exclusions and known gaps remain.

## Initial source publication checkpoint (historical TASK-0006)

Implementation baseline: `d62b6bc2de98ef3e500a2c177d57d007b37ece68`
(initial source commit). The accepted implementation was committed as
`6337012b46251129c3f61cc515b07c2ca30281df`, preserving that initial parent.
The history-preserving merge `8057a3085a946c5aeb8d4546405aec0f653e5ce7`
was pushed and verified on remote main; both original roots were retained.

At TASK-0006, the README/demo/setup/changelog documented accepted behavior and
safe reproduction; static/link checks and independent review passed. After TASK-0007
acceptance, the owner explicitly authorized commit/remote/push to
https://github.com/yusufondes/Operations-Control-Tower. TASK-0006 is Review:
source push succeeded and git/API/tree checks matched remote main to the merge
commit above with 99 files. Origin tracked the approved .git URL; both histories
were retained without force and the repository remained private at that checkpoint.
Earlier authenticated 404 notes are historical; anonymous 404 was expected for
the private repository. First Actions run 38748554245 completed with failure:
repository checks and 8 base Odoo tests passed, but the later startup
HTTP-health check failed with
curl 56/connection reset. Cleanup succeeded. This was not a green CI result;
TASK-0012 now owns the separately authorized CI repair. The workflow's base-only
scope is separate from local 81-method/11-case evidence. That publication did
not install modules in the working DB or deploy a production system. Use
TASK-0012, Git history and Actions for later tips, visibility and statuses.
The owner declared code ownership; D-014 records the narrow correction of the
project copyright header and base-addon author from HOLY to Yusuf Ondes.
LGPL/GPL and third-party notices remain unchanged; this is not an independent
provenance audit. HALY remains fictional scenario branding under D-013, not a
working company-data rename. At the publication preflight no new source commit
or push had occurred and no remote was configured; TASK-0006 owns subsequent
execution results. A request to share does not complete the
then-unimplemented stock-priority/tie/full-consumer rules or the wider roadmap.
TASK-0007 now separately implements/tests the bounded approved rules; it does not
complete the wider roadmap or authorize a working-DB rollout.

## Initial base-addon evidence (historical TASK-0001 snapshot)

The following observations describe the original base-only setup before the
optional integrations and remote publication. They are not the current source
inventory or a fresh runtime check. Read the current summary above for later
implementation and validation; recheck dated runtime observations before use.

- Compose defines Odoo `19.0` and PostgreSQL `15`, named database/filestore volumes,
  loopback port `127.0.0.1:8069`, and no published PostgreSQL port.
- Both existing containers reported running and healthy during this setup.
- Read-only SQL found `operations_control_tower` installed at `19.0.4.1.0`.
  Sales (`sale`), Inventory (`stock`), Purchase and Maintenance reported
  uninstalled. No Community Quality app installation is claimed.
- The working database `operations_control_tower` contains 14 control items:
  4 Closed, 1 Resolved and 9 other active workflow states. These are synthetic
  portfolio scenarios, not real HOLY records.
- The custom addon implements `operations.control.item` with reference, title,
  description, owner, company, area, impact, priority, deadline, next action,
  state and an overdue computation.
- Source contains Kanban/list/form/calendar/graph/pivot/search views,
  assigned-user/manager ACLs and company record rules.
- The state field provides eight choices; enforced process transitions and
  linked sales/stock/quality decisions are not implemented.
- Only `base` and `web` are declared dependencies. WMS reconciliation,
  procurement, shipping and quality stories are card content, not integrations.
- Test source defines eight Odoo test methods. Existence does not prove a pass.
- Git history contains the initial commit; no remote is configured. Local author
  identity remains Yusuf Ondes with the supplied GitHub noreply address.

## Setup delivery (historical TASK-0001 snapshot)

See TASK-0001 for current validation, review and acceptance. The documents define
a human-invoked workflow. The full implementation/test/review/repair/acceptance
cycle has not been exercised by developing an ERP feature.

| File | Responsibility |
| --- | --- |
| ../AGENTS.md | Concise project rules and relevant-context routing. |
| TASKS.md | Task scope, approval, test/review evidence and acceptance. |
| REVIEWER.md | Review protocol, capability limits and validation command effects. |
| ARCHITECTURE.md | Verified components, access and integration boundaries. |
| DECISIONS.md | Approved choices and unresolved proposals. |
| PROJECT_STATUS.md | Dated capabilities, limitations and this working guide. |
| ../CONTRIBUTING.md | Shared contribution steps and risk-based checks. |
| ../.gitignore | Local secrets/private keys/database outputs; no retroactive untracking. |

Existing SETUP.md remains the operational installation reference, not permission
to reset volumes or credentials. Existing README roadmap entries are suggestions;
TASKS.md and explicit Product Owner decisions govern approved work.

No custom role configuration, skill, hook, scheduler, remote, API app or external
service has been introduced. The reviewer uses supported collaboration tools
and the written protocol. It shares inherited permissions; no distinct technical
read-only sandbox or tool allowlist has been established.

## Validation record for this setup (historical TASK-0001 snapshot)

TASK-0001 records executed commands, environment, exit statuses, scope and skipped
checks. Repository validation passed for 42 text files; 26 positive and 9 negative
ignore cases, candidate-secret/local-link checks, tracked whitespace and Compose
parsing passed. Read-only runtime checks confirmed service health and the
observations above. Implementation, scripts, CI and runtime configuration match
the baseline. The relevant documentation revision is the eight-file uncommitted
working tree over that hash; pre-review SHA256 fingerprints were emitted in the
execution transcript. The separate reviewer inspected all eight changed files,
found no confirmed defects and requested no repairs. TASK-0001 records the actual
report, reviewed fingerprints and limits. Delegation and reporting were exercised;
repair automation and technical reviewer isolation were not.

The successful smoke-test execution earlier in this chat preceded the initial
commit. It is historical evidence only, not a runtime test rerun or an acceptance
claim for this setup. The source/script/Compose/CI trees will be compared with the
baseline during this setup.

Runtime tests, module upgrades, migrations, bootstrap and browser acceptance are
not part of documentation-only validation. The existing working database is not
a test target.

## Known limitations and next actions (historical setup snapshot)

- A fresh-install smoke uses a temporary database but shares services and
  filestore. Cleanup success is not fully asserted by its script.
- Smoke excludes demo XML and upgrade paths. The historical `19.0.4.1.0`
  migration closes all items and inserts ten scenarios. Never replay it on the
  working database to prove an upgrade is safe.
- No verified backup/restore process, production deployment or live integrations.
  Container health does not establish business acceptance.
- Image tags can change; no digest pinning or dependency change is authorized.
- The manifest author is HOLY; affiliation/attribution has not been verified.
  Treat branding correction as an open decision, not endorsement.
- Secret/ignore checks are heuristic. Public certificates, key-named source or
  database test fixtures may need narrowly reviewed exceptions. Plain SQL source
  remains visible and must be checked for exported data or credentials.
- GitHub Actions is present in source but no remote CI execution has occurred.
  Its disposable-runner volume cleanup must never be copied to the local stack.
- The current chat's configured working folder differs from this repository.
  Scoped escalations were needed for Git/runtime access and edits; open this
  repository as the Codex project root for future work. These files do not
  reconfigure the desktop project or extend its permissions.
- TASK-0002 is in Needs Decision. Own production, two customer types, corporate
  partial shipments, priority by promised dispatch date and earlier confirmation
  for equal dispatch dates, plus complete consumer dispatch, are confirmed
  business directions in D-007/D-008/D-009/D-010. Customer-approved date changes,
  with rejection retaining the existing promise, are defined in D-011. These are
  not implemented capabilities. Its numerical
  walkthrough was proposed under TASK-0002. TASK-0003 now authorizes and executes
  standard-baseline validation only; custom business features remain unapproved.

## How to Work With This Project in Codex

Open `C:\Users\yusuf\Operations-Control-Tower` as the Codex project root.
Ask Codex to confirm the root, Git status and applicable AGENTS.md before work.
Natural-language examples below are not custom slash commands; the owner may
communicate the equivalent request in Turkish.

1. **Plan:** "Draft TASK-XXXX with an order-to-dispatch example. Compare standard
   Odoo Community functionality and custom gaps. Record unresolved decisions.
   Do not implement." Planning is separate from implementation approval.
2. **Approve:** "I approve TASK-XXXX, the scope and acceptance criteria currently
   recorded in docs/TASKS.md. Implement that scope." Record date and approval
   reference first; changed scope needs renewed approval.
3. **Implement:** "Implement approved TASK-XXXX. Record a short plan if complex,
   add relevant tests, run proportionate checks and request a separate reviewer.
   Preserve the working database and stop for new business decisions."
4. **Review:** "Review TASK-XXXX under docs/REVIEWER.md against COMMIT-HASH,
   including untracked files. Use a separate reviewer with no edits. Present
   evidence and limitations." The main agent handles test execution and repairs;
   at most two autonomous repair rounds are permitted.
5. **Accept:** "I accept TASK-XXXX against the recorded criteria and evidence.
   Mark it Done." Until this explicit acceptance, keep the task in Review.
6. **Commit:** "Commit the reviewed changes for TASK-XXXX locally with an English
   message. Do not add a remote or push." Inspect candidate contents first.

For a native review, open this actual repository, enter `/review`, and choose
uncommitted changes. Availability is documented; this setup's demonstrated path
uses a separate session subagent. Installed CLI help exposes
`codex review --uncommitted`, but its execution has not been tested here.

### Historical planning context (TASK-0002, before TASK-0007)

The next step at this planning checkpoint was to check the numerical walkthrough
against standard Community functionality, then resolve incomplete-consumer
reservation handling, missing-date/identical-confirmation handling, promise
semantics and quality-release authority before approving the first implementation
scope. The proposed three-working-day dispatch target was not approved.

Source-only standard-feature assessment is now recorded in TASK-0002:
standard sales/stock, purchase/receipt and manufacturing building blocks are
available in the inspected Community source. Reservation paths use differing
sort criteria, and the standard customer delivery commitment must not be
silently treated as a promised warehouse dispatch date. These observations
were not runtime acceptance evidence at that planning stage. Proposed custom
first-release boundaries remain under Needs Decision. TASK-0003 later installed
standard modules only in disposable databases, as recorded below.

Date-change planning distinguishes proposed dates from customer-accepted
commitments. An unanswered/rejected proposal preserves the existing promise;
explicit acceptance establishes the changed promise for the covered dispatch.
Original commitments and response history must remain traceable. This is a
business requirement only; no live customer communication or application
implementation has occurred.

## Standard fulfilment validation delivery (historical TASK-0003 snapshot)

TASK-0003 is approved for a disposable standard ERP baseline, not live feature
deployment. New scripts/validate-fulfilment.ps1 and scripts/validate_fulfilment.py
perform fresh standard Sales/Inventory/Purchase/Manufacturing installation,
unchanged addon compatibility tests, guarded ORM scenarios and asserted cleanup.

On 2026-10-15 the full corrected runner exited 0: eight addon methods passed;
500 initial + 400 manufactured units fulfilled orders of 200/600/100. Corporate
dispatches of 300/200/100 preserved backorder balances. Two input suppliers and
normal receipts/manufacturing were exercised with synthetic data.

Seven diagnostic gaps were reported, not accepted requirements: universal date
priority, confirmation tie-break, consumer hard full-dispatch enforcement,
existing-reservation reallocation, separate warehouse-promise semantics,
customer-acceptance/date history lifecycle, and supplier-delay-to-customer
coordination. Reallocation policy is still an open business choice. Incoming
automatic assignment honored the earlier date in one controlled case only.
See TASK-0003 for exact cases, failed first attempt, limitations and review.

Both temporary databases were removed. Working module states and the 14-item
content fingerprint were unchanged. Existing application code, working ERP
module installation and dependencies remain unchanged. Shared infrastructure
means database separation is not full-stack isolation. Test-enable forces an
unpublished HTTP listener; the new runner binds it to container loopback.
The ORM shell disables HTTP and all one-off processes disable cron threads.

Next proposed scope: agree promise/date-change data semantics and the remaining
reservation choices, then draft a small approved custom task with negative
behavioral tests. No automatic acceptance, commit or custom implementation is
implied by a successful diagnostic runner.

Handover: TASK-0003 is in Review, not Done. Separate final review found no
confirmed defects and requested no repairs. Cleanup-error and forced-termination
paths lack fault-injection coverage; a cleanup exception also skips the final
working fingerprint read. These limits are recorded in TASKS.md. Reviewed
scripts remain unchanged. Static/secret-candidate/baseline checks passed,
working health passed, and no temporary DB or one-off container remains.
The original commit remains HEAD; changes are uncommitted and no remote exists.

## Next scoped proposal (historical TASK-0004 stages)

TASK-0004 planning was reviewed, then the Product Owner explicitly approved its
implementation in disposable test databases. It is now Review; this does not
accept TASK-0003. D-012 records order-level outstanding-quantity coverage,
coordinator-recorded manual evidence and stale-scope protection. The separate
operations_dispatch_promise addon now implements these source-level behaviors;
working-database installation remains excluded. Validation/review is recorded
in TASKS.md, separately from the historical planning-only checks.

This first slice records an operative planning commitment only. It does
not alter standard customer Delivery Date, stock deadlines, picking schedules,
allocation priority or consumer partial-dispatch behavior. Those known gaps
remain open. The planning stage made no runtime changes; approved development
now adds separate custom models, permissions and UI in source, tested only in
owned temporary DBs. The working system is not the feature-test target.

TASK-0004 validation now passes in source/test environment: 29 methods (8 base
and 21 integration) with 0 failures/errors; controlled two-real-connection
proposal/response and old-snapshot/new-line races; server-side Form helper
proposal/response workflow; and the unchanged 900-unit standard arithmetic.
Actual runs, development failures/fixes and limits are recorded in TASKS.md.
No browser render or live acceptance was run. All five temporary databases were
removed. Working 14-row fingerprint/module states stayed unchanged, and the new
addon/fields remain absent from the working DB. The default runner path also
passed eight base methods and the standard diagnostic. Independent final review
found no confirmed defects and requested no functional repairs; a docstring-only
clarification was rechecked. Load/contention, some scope-change variants,
simultaneous stock completion/acceptance and cleanup fault injection remain
unverified. No Done/acceptance, working-system rollout or commit is inferred.

## Browser verification and narrow repair (TASK-0005)

The real browser flow was exercised with an ordinary synthetic Sales/Coordinator
user in an owned loopback-only preview, never the working database. Establish,
pending, estimate, accepted/rejected history, required reason, cancel and stale
scope were checked. Stale-response submission exposed a P2 navigation error:
the saved response was correct but the nested window action lacked views.
Explicit form views plus one regression fixed it; a fresh stale response now
returns the warning and normal form while retaining current18/original15 and
revision2 after reload. The standard Delivery Date stayed unchanged by browser
DOM observation; screenshot07 alone does not show its below-crop value.

After repair, .\scripts\validate-fulfilment.ps1 -WithPromise exited0 with30
methods (8 base +22 integration),0 failures/errors, standard900-unit arithmetic
and real-connection/Form probes passed. The diagnostic's seven stock/dispatch
business gaps remain open. [Browser evidence](evidence/task-0005/README.md)
contains seven synthetic screenshots and the confirmed defect/fix chronology.

Both preview Start/Stop paths and the regression DB were cleaned; no scenario DB,
one-off container or temporary login file remained. Whole-session working module
states and14-row fingerprint matched; the optional addon/columns remain absent
from the working database. Both working services stayed healthy. No working
service restart, migration, new commit, remote or push.

Final source aggregate18files:
702DEAB9663CB6A6EDD0B21C9B5417CEC4FAEC82B934ECCCE9B73C391400C2FE.
TASKS.md records exact DBs, source hashes, commands, results and review. Independent
renewed round2 review found no remaining confirmed defects or further functional
repairs. Yusuf Ondes explicitly accepted the handover on2026-10-15; TASK-0004 and
TASK-0005 are now Done. This acceptance is recorded in TASKS.md, not inferred.
No mobile/browser matrix, load test, authenticated customer consent or working-
system rollout.
Helper failure/forced-interruption paths remain untested; Compose/fingerprint
failure before cleanup can require manual recovery. Normal cleanup was verified.
If container removal succeeds but DB deletion fails, a subsequent Stop refuses
the orphan DB without ownership proof; recovery needs a separate verified action.

The acceptance closeout changed documentation only. No new runtime execution,
working-system install, functional change, commit, remote or push. TASK-0001 and
TASK-0003 remain Review; TASK-0002 remains Needs Decision. Completion of this
slice does not complete the overall fulfilment roadmap.
