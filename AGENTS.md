# Project instructions

- Work only in `C:\Users\yusuf\Operations-Control-Tower`. The repository is the implementation source of truth; chat proposals are historical context, not completion evidence.
- Communicate with the Product Owner in Turkish. Keep code, identifiers, tests, repository documentation, UI labels, and commit messages in English.
- Before implementation, locate the task and explicit approval in [docs/TASKS.md](docs/TASKS.md). Brainstorming and general enthusiasm are not approval. Ask about unresolved business rules; do not invent them.
- The Product Owner owns scope, architectural approvals, and final acceptance. Codex implements approved tasks; a separate reviewer reports findings; executed validation supplies evidence.
- Read only relevant context: [architecture](docs/ARCHITECTURE.md) for component changes, [decisions](docs/DECISIONS.md) for design choices, [status](docs/PROJECT_STATUS.md) for verified capabilities. Do not require every document for minor edits.
- Prefer standard Odoo 19 Community features and supported ORM/model/view extensions. Assess compatibility before proposing dependencies. Do not add Sales, Inventory, Purchase, Quality, WMS, or other modules without explicit approval.
- Preserve ACLs, record rules, company boundaries, transaction integrity, and existing data. Test changed permissions and business behavior with synthetic data. Distinguish real integrations from simulations.
- For complex approved work, record a short implementation plan in the task before coding. Deliver the smallest coherent change and relevant tests.
- Run checks proportionate to risk. `python .\scripts\check_repository.py` checks repository text, XML and CSV; it is not a secret scanner. `git diff --check` checks tracked changes.
- Runtime validation uses `.\scripts\smoke-test.ps1`: disposable test database, shared Docker services. It starts services and writes ignored bytecode. Inspect its effects before running; never substitute the working database. See [validation boundaries](docs/REVIEWER.md#validation-boundaries).
- Never run bootstrap, upgrade, destructive migrations, volume removal, dependency upgrades, or infrastructure changes as routine checks. Obtain specific authorization for data-changing operations and use a disposable copy for migration tests.
- Record command, environment/database, code revision or file digest, exit status, result, and skipped checks in the task. Test-file existence and health responses do not prove acceptance.
- After implementation and checks, request a separate reviewer using [docs/REVIEWER.md](docs/REVIEWER.md). Minor documentation changes need only a focused review. Limit autonomous review/repair cycles to two; escalate unresolved critical findings or further repairs.
- The reviewer must not edit, stage, commit, mutate services/data, or repair findings. The current subagent interface inherits permissions and does not enforce a distinct read-only sandbox; never claim otherwise.
- Rerun affected checks after fixes. Code changed after review needs renewed review of the relevant diff. Report confirmed defects, risks, coverage gaps, optional improvements, and unverified assumptions separately.
- Move tasks to `Review` for handover. Mark `Done` only with acceptance evidence and explicit Product Owner approval.
- Keep secrets, credentials, private keys, database files/dumps and exported business data out of Git. Inspect candidate contents and ignored/untracked files; ignore rules cannot remove already tracked secrets. Never print resolved secrets.
- Preserve the initial commit and existing history. Do not change global Git config, destructively reset Git, modify production data, or delete/reset the working database.
- Do not add remotes, push, publish, deploy, install untrusted tools, or introduce external services without explicit authorization.
- Use [CONTRIBUTING.md](CONTRIBUTING.md) for the shared contribution workflow. No custom slash command, recurring automation, or fully automated pipeline is installed by these documents.

## Review focus

Compare the actual diff and approved acceptance criteria. Prioritize authorization, cross-company access, data loss, migrations, regressions, and missing behavioral tests. Cite the triggering case and file/line for defects; avoid speculative or cosmetic blockers.
