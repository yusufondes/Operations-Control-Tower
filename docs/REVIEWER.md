# Review protocol

## Role and scope

Review the actual diff against the approved task, relevant decisions and existing behavior. Include staged, unstaged and untracked source documents. A separate agent provides a distinct review context, not a guarantee of correctness or independent filesystem permissions.

The reviewer reads/searches source and Git diffs. It must not edit files, stage, commit, fix findings, run mutating tests, start/stop containers, read .env secrets, use external write tools, or change data. The developer executes tests and repairs confirmed defects. Written restrictions are behavioral instructions, not a sandbox.

## Verified environment and limits

Verified on 2026-10-15 in this Codex desktop session:

| Capability | Evidence / limit |
| --- | --- |
| Separate subagents | The session exposes spawn, follow-up, message, wait and interrupt tools; a read-only validation audit was successfully delegated. |
| Per-reviewer permissions | The exposed spawn interface has no per-agent sandbox or tool-allowlist setting. Agents share the workspace and inherit permissions. Strict read-only isolation is not configured. |
| Native app review | The app provides a review-panel opening tool. Official documentation describes /review for local Git changes; actual app review execution is not claimed from that documentation alone. |
| Installed CLI | Local help reports codex-cli 0.159.2 and codex review with --uncommitted, --base and --commit. Help was checked; the CLI reviewer has not been authenticated or exercised here. |
| Custom agent configuration | Official docs describe project agents in .codex/agents/*.toml, inheriting parent permissions. This session's spawn tool cannot select a custom role file; loader behavior has not been verified here, so none is installed. |
| Skills / automation | No repository skill, scheduler, hook, or external Agents API app is needed for the demonstrated manual invocation. Reconsider only after repeated workflow use shows a concrete need. |

The parent session's managed filesystem, network and escalation controls are technical boundaries. This chat remains attached to a different folder; writing this authoritative repository currently requires scoped approval. Reopen Codex in this repository for subsequent work; documents do not change the app's working directory or grants.

Use a separate session with a verified read-only permission mode and restricted tools if stronger isolation is required. Do not claim that a Markdown protocol or custom role creates that boundary. If subagents are unavailable, use native local review where supported, or a human review of the same diff and task; record which fallback actually ran. Do not install a replacement API application.

References checked for the current client:
- [Subagents and inherited permissions](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Local review in the app and CLI](https://learn.chatgpt.com/docs/code-review?surface=app)
- [Project instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

## Invocation

Ask the main Codex agent to delegate the following brief, including the real task ID, baseline hash, changed file list and validation results:

> Review TASK-ID under docs/REVIEWER.md in C:\Users\yusuf\Operations-Control-Tower. Compare the actual working-tree changes and untracked files with BASELINE. Read the approved task and relevant architecture/decisions. Do not edit, stage, commit, run mutating commands or use external write tools. Report evidence categories and file/line references; identify skipped verification. Return the reviewed revision/file digests and limitations.

The main agent must wait for the report, evaluate evidence, and record findings. Include the full uncommitted scope: a normal git diff omits untracked files. Read each new document directly or compare it against an empty file; do not stage just to make review possible.

For manual native review, open the actual repository in Codex, invoke `/review` and select uncommitted changes. Installed CLI help also supports `codex review --uncommitted`; this is a fallback command, not evidence that it has run.

## Review checks and reporting

Prioritize changed behavior and real risks:

- Requirement/acceptance traceability, observable outcomes and no unauthorized scope.
- Correct Odoo ORM, inheritance, constraints, state behavior, and transactions.
- ACLs, record rules, company boundaries, and elevated-access misuse.
- Install/upgrade/migration safety, data preservation and repeated execution.
- Integration contracts, validation, duplicate handling and failure behavior when relevant.
- Tests that exercise changed behavior and realistic failures.
- Accurate documentation and separation of synthetic demos from working capabilities.

Classify each item:

| Category | Evidence expected |
| --- | --- |
| Confirmed defect | Triggering input/condition, expected vs actual outcome, affected file/line, reproducible evidence or direct code reasoning. |
| Potential risk | Plausible impact and the specific missing verification; do not present it as a reproduced bug. |
| Missing test coverage | Changed behavior or boundary without a relevant test, with a concrete scenario. |
| Optional improvement | Non-blocking maintenance suggestion, clearly separate from defects. |
| Unverified assumption | Fact or business rule that still needs evidence or a Product Owner decision. |

Use P0 for immediate critical harm, P1 for a major correctness/security/data risk, P2 for a normal actionable defect, and P3 for a low-impact issue. Cosmetic preferences are not blockers. Report "No confirmed defects found" when appropriate without implying comprehensive safety.

Record task ID, baseline and reviewed revision/digests, scope, validation evidence considered, commands the reviewer ran, findings by category, skipped checks and limitations. The task registry owns the report and repair-round history.

## Review and repair

1. Confirm scope/approval and baseline.
2. Implement the smallest coherent deliverable and relevant tests.
3. Run proportionate checks and save the results.
4. Request a separate review of the actual diff.
5. Evaluate findings; repair only verified defects within approved scope.
6. Rerun affected checks and review the changed parts again.
7. Allow at most two autonomous review/repair rounds. Escalate unresolved P0/P1 issues immediately; obtain Product Owner direction before a third round or scope expansion.
8. Hand over the result in Review. Done requires explicit Product Owner acceptance and evidence.

For low-risk text/ignore changes, one focused review and static checks are sufficient. Never invent a defect to demonstrate the loop. A no-defect review still demonstrates delegation and reporting; it does not demonstrate repair or automatic acceptance.

## Validation boundaries

Run from the repository root and record each command, environment/database, exit code, result, code revision/digests and unexecuted checks.

| Command | Purpose and side effects |
| --- | --- |
| python .\scripts\check_repository.py | Text encoding, prohibited Turkish characters, trailing whitespace, XML syntax, CSV widths. Not a secret scanner, English-language parser, TOML validator or runtime test. |
| git diff --check | Whitespace in tracked diff. Separately inspect new/untracked files. |
| git check-ignore -v --no-index PATH | Check ignore behavior for a candidate path without creating it. Does not remove tracked data. |
| docker compose config --quiet | Parse Compose without printing resolved secrets. Never paste unfiltered resolved configuration. |
| python -m compileall -q .\addons\operations_control_tower | Syntax compilation only; writes ignored bytecode, does not run Odoo tests. |
| .\scripts\smoke-test.ps1 | Fresh addon install and eight test methods in generated oct_test_<epoch>_<PID> DB, plus main service health. Starts shared services, writes bytecode and attempts test DB/filestore cleanup. |
| .\scripts\upgrade.ps1 | Defaults to the working DB and runs module update/migrations; interrupts Odoo. Requires explicit data-change authorization and an appropriate backup/test-copy plan. Not a documentation check. |
| .\scripts\bootstrap.ps1 | Initializes a target DB/demo and changes administrator credentials. Setup action, not a regression check. |

The smoke test shares the Compose project, PostgreSQL server and Odoo filestore with development. It is database-separated, not a fully isolated stack. Cleanup must be verified: database-drop exit status is not asserted by the script and filestore failure only warns.

Fresh-install smoke excludes demo XML and does not test migrations, upgrade paths, browser interactions or future ERP integrations. A passing health endpoint is only process-level evidence. Validate migrations on a disposable copy under separately approved scope before touching the working DB.

CI defines base-addon fresh-install checks. The first remote run passed repository
checks and the eight base methods, then failed its startup HTTP-health step;
TASK-0012 records the authorized repair and subsequent verification. Neither
base-only CI nor a health response establishes optional-suite or production
acceptance. CI's volume-deletion cleanup belongs only to a disposable runner;
never copy it into the local workflow.

Secret gate: inspect staged/unstaged/untracked candidates, filenames and high-confidence token/private-key/credential patterns with value redaction. Check local secret values for exact matches only in memory and report filenames/counts, never values. Pattern scans are a heuristic, not a completeness guarantee. Do not install scanners or services without authorization.
