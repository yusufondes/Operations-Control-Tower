# Security Policy

## Supported scope

The current release is a local development and portfolio demonstration. It is not a production deployment template.

## Reporting a vulnerability

Do not publish sensitive vulnerability details in a public issue. Contact the repository owner privately and include the affected version, reproduction steps, impact, and any suggested mitigation.

## Local security boundaries

- Odoo binds to `127.0.0.1` by default.
- PostgreSQL is not published to the host network.
- Secrets belong in the ignored `.env` file.
- Default or demonstration passwords must be changed before use.
- Backups and exported business data must never be committed.
