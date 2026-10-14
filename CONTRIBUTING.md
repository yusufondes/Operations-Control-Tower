# Contributing

## Language policy

All repository content must be written in English. This includes source code, identifiers, comments, user-interface labels, documentation, commit messages, issue text, and pull-request descriptions.

## Development workflow

1. Create a focused branch from `main`.
2. Keep changes small and document any business-rule assumptions.
3. Run the repository checks and Odoo smoke tests.
4. Update `CHANGELOG.md` when behavior changes.
5. Open a pull request with the problem, solution, and validation evidence.

## Required checks

```powershell
python .\scripts\check_repository.py
.\scripts\smoke-test.ps1
```

Do not commit `.env`, database dumps, generated Python files, logs, or credentials.
