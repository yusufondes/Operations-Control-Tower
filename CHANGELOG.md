# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog, and the project uses Odoo-compatible semantic versioning.

## [Unreleased]

### Added

- TASK-0018: customer-approved shipment batch quantities and latest dispatch
  dates in campaign addon `19.0.2.0.0`, with protected manual response history,
  proposal/response forms, source-scope guards and per-batch allocation priority
- Early exact-batch dispatch; renewed approval for changed quantities or late
  dispatch; corporate partials no longer follow from policy selection alone
- Focused consent, quantity/date, backorder, source-security and form tests;
  runtime evidence and installation limits are recorded in TASK-0018

- Optional `operations_dispatch_promise` addon, version `19.0.1.0.0`, depending on
  `sale_stock` and the base control-tower addon
- Separate original/current warehouse dispatch commitments, internal estimates,
  date proposals and manually recorded customer-response history
- Role, source-order and company checks; protected history, stale-scope detection
  and concurrency safeguards for the approved promise workflow
- Guarded disposable standard-fulfilment validation and browser-preview helpers,
  synthetic fixtures, and saved browser evidence
- Project instructions, task/approval records, review protocol, decisions and
  verified capability documentation
- Optional `operations_campaign_automation` source, version `19.0.1.0.0`,
  depending on the promise addon, `purchase_stock` and `sale_mrp`; TASK-0007
  local validation is recorded separately from review/acceptance, not a release
- Configured one-step make-to-stock, untracked-goods pool; explicit quotation
  consumer/corporate policy; accepted warehouse date -> protected confirmation
  timestamp -> order ID reservation priority; retained incomplete-consumer stock
- Complete-consumer dispatch guards and corporate partial backorders without
  implicit balance cancellation, prepared/outside-reservation protection,
  missing-promise blocking and derived supply-risk owner/next-action visibility
- Explicit `-WithCampaign` validation/preview modes preserving the default and
  promise-only paths; preview seeds synthetic opening stock/orders only

### Fixed

- CI startup verification waits for the Compose healthcheck and retries
  transient HTTP failures within bounded time limits. TASK-0012 records the
  original connection-reset evidence and the actual remote verification.
- Documentation distinguishes current public-sharing preparation from
  historical private-publication and initial-setup snapshots. The preferred
  business presentation uses visibility-independent GitHub wording.
- Local preview helper supports Windows PowerShell 5.1 schema-readiness polling
  and JSON-based exact ownership inspection. Cleanup skips already-absent DBs
  and blocks DB deletion after failed container cleanup. TASK-0008 records real
  Start/Stop/login and mocked guard checks; local packaging is tracked in
  TASK-0011, separately from any remote publication.
- Manual preparation cannot claim unallocated campaign stock through saved
  move quantities, raw lines, UoMs or context defaults; public unreserve
  reconciles priority and direct demand cancellation/retargeting is guarded

- Project copyright header and base-addon author metadata now name Yusuf Ondes
  following the owner's declaration; LGPL/GPL and third-party notices are unchanged
- Stale-response wizard notification navigation now includes a complete nested
  form action; the response evidence remains saved without changing the promise

### Validation and limits

- TASK-0012 made the repository public on 2026-10-15 after source/history,
  retained Actions logs/artifacts and screenshot disclosure checks. Anonymous
  README and preferred 14-slide PDF/PowerPoint downloads matched reviewed
  files. Both remote jobs, 8 base methods, health and cleanup passed in run
  38769265214. This does not establish optional-suite remote coverage or
  production readiness. The original 17-slide pair is clearly archived.
- Source was pushed to the owner's Private GitHub repository on 2026-10-15,
  preserving both initial histories. TASK-0006 records exact source hash, remote
  verification and the first Actions failure: repository checks and 8 base tests
  passed, but the subsequent startup-health check returned curl 56. That first
  run did not pass; no visibility change, release tag, deployment or live
  installation occurred at that earlier checkpoint.
- TASK-0007 was explicitly accepted for its bounded source/test delivery on
  2026-10-15 after final independent review, 81 passing methods and 11 campaign
  cases. This is not a working-system installation, published release or remote
  CI pass; its documented limits remain.
- TASK-0004/TASK-0005 were explicitly accepted for source and disposable-test
  scope on 2026-10-15. The recorded local regression passed 30 methods
  (8 base + 22 optional), connection/Form probes and the browser walkthrough.
- Existing GitHub Actions covers the base addon only. No remote CI pass is
  claimed by these local results.
- No optional-addon installation in the working database or production rollout.
  No automated outbound communication or authenticated customer consent.
  The accepted promise-only addon does not allocate or enforce dispatch; the
  new bounded campaign source adds those guards separately. TASK-0007 records
  81 passing methods, 11 campaign probes and browser repair evidence; independent
  review and explicit owner acceptance are separate gates, not inferred passes.
- Campaign scope excludes unsupported routes/uncovered unmanaged competition,
  consumer replacement flows, formal quality release, carrier/WMS adapters and
  capacity guarantees. Supply risk uses a one-level BoM/open-production/late-PO
  signal, not exact order pegging. Physical events must still be recorded.
  Standard diagnostic, shared-infrastructure and failure-path limits remain.

## [19.0.4.1.0] - 2026-10-14

### Added

- Powdered-drink portfolio scenarios for inventory, production, quality, procurement, logistics, maintenance, and integrations
- Manufacturing-oriented business area values
- Resolved and Closed search filters

### Changed

- Closed the original generic demonstration items
- Made the Overview open-items filter active by default

## [19.0.4.0.0] - 2026-10-14

### Changed

- Replaced manual progress tracking with an editable status selection
- Added responsible, information, and third-party waiting states
- Added separate Resolved and Closed states
- Updated Kanban grouping, filters, analysis, tests, and documentation for the status-driven workflow

## [19.0.3.1.0] - 2026-10-14

### Added

- Operations User and Operations Manager access levels
- Company-aware record rules
- Multi-company consistency checks
- Calendar, graph, and pivot analysis views
- Disposable-database smoke testing
- GitHub Actions validation
- English-only repository policy and automated language guard

## [19.0.2.0.0] - 2026-10-14

### Added

- Operational control item workflow
- Kanban, list, form, and search views
- Progress and overdue validation
- Docker health checks
- Initial architecture and setup documentation
