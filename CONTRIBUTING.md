# Contributing

## Language policy

All repository content must be written in English. This includes source code, identifiers, comments, user-interface labels, documentation, commit messages, issue text, and pull-request descriptions.

## Development workflow

1. Identify the task, approved scope and acceptance criteria in [docs/TASKS.md](docs/TASKS.md).
2. Create a focused `codex/` branch from `main` for approved implementation.
3. Keep changes small, record unresolved business decisions, and add relevant behavioral tests.
4. Run checks proportionate to risk under [docs/REVIEWER.md](docs/REVIEWER.md).
5. Request a separate review of the actual diff, repair verified defects within scope, and rerun affected checks. Stop after at most two autonomous review/repair rounds.
6. Update `CHANGELOG.md` when behavior changes. Report the result for Product Owner acceptance; leave the task in Review until explicitly accepted.
7. Commit or open a pull request only within the authorized workflow. Remote creation, pushing and publishing require explicit authorization; local review works without GitHub.

## Available checks

For documentation-only changes, run the repository check, whitespace/link checks,
and a focused review. For runtime changes, also run the relevant Odoo tests and
smoke test after inspecting its shared-service effects:

```powershell
python .\scripts\check_repository.py
.\scripts\smoke-test.ps1
```

Do not commit `.env`, database dumps, generated Python files, logs, or credentials.
See [AGENTS.md](AGENTS.md) for concise working rules and
[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for verified capabilities and
practical Codex usage. Never run the live upgrade or bootstrap as a document check.
