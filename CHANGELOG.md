# Changelog

## Local development — 2026-10-20 — continuous integration

- Added GitHub Actions for Ruff and the complete synthetic suite on Ubuntu/Windows with Python 3.12–3.14.
- Pinned action revisions and development dependencies; use the same tzdata package on both operating systems.
- Added a stable `CI result` gate, read-only token permissions, time limits and cancellation of superseded runs.
- Added weekly Dependabot proposals for Actions and Python development requirements.
- Documented local commands, branch-protection setup and the separate pre-publication privacy review.
- Activated the `main-ci` repository ruleset: require PRs, an up-to-date branch and `CI result` from GitHub Actions, with no bypass actors and no force pushes/deletions.

Validation: 81 tests passed locally on Windows/Python 3.12.14, Ruff 0.17.1 passed and actionlint 1.7.12 accepted the workflow. The [first hosted PR run](https://github.com/MrCodeLabs/ha-energy-cost-monitor/actions/runs/39472304035) passed lint, all six OS/Python test combinations and `CI result`. Application code and tests are unchanged.

Limitations: repository rules are external settings and are not inherited by forks. There is no deployment or release automation; HA/card/HACS checks await their packages. Next: review and merge the CI PR; development continues with the single-instance HA adapter and sampling policy.

## Local development — 2026-10-20 — supply scenarios

- Added strict immutable EUR/excluding-VAT supply scenarios with versioned validity, price sources/status, explicit import/export prices and monthly subscriptions.
- Added decimal interval calculations, negative-price support, explicit missing/incomplete reasons and comparisons on identical usable intervals across offers.
- Added local-calendar subscription allocation for partial days, month changes, leap years and 23/25-hour DST days; monetary summaries round once to cents.
- Added two invented reference offers and documented scope, rounding, coverage and provenance.

Validation: 81 tests passed on Python 3.12.14, including 27 new pricing tests. Synthetic ledger repricing leaves database bytes unchanged. Pricing/calendar tests use the available IANA timezone database. `git diff --check` passed; all 27 candidate files passed scoped privacy/whitespace checks and 39 local Markdown links resolved. No actual provider rates or regulated tariff rules were validated.

Limitations: supply comparison only; no VAT, network charges, levies, credit/payment settlement, live price fetching, profile persistence or frozen reports. Prices are constant only within explicit supplied periods; no provider-specific averaging is inferred. Partial comparisons include only common interval subscription shares. Next: single-instance HA adapter and explicit sampling policy, with independent lifecycle tests. Production was not changed.

## Local development — 2026-10-20

- Recorded the owner's authorship confirmation and permission to transfer reviewed prototype code under MIT.
- Adapted cumulative-meter accounting to configured sources, power limits, freshness dependencies and an explicit continuity limit.
- Added atomic SQLite storage, persistent baselines, estimated UTC quarter-hour allocations, per-role coverage and explicit gap/reset/jump anomalies.
- Kept daily estimates outside cumulative totals; rejected incompatible database/configuration changes without replacing history.
- Refreshed the upstream metering comparison and added developer API documentation.

Validation: 54 behavior tests passed on Python 3.12.14, including minimal/optional configurations, restarts, duplicate samples, rollback and 23/25-hour shaped UTC windows. Restricted Windows testing used a writable development temporary directory; SQLite fixtures explicitly close their connections. Diff, candidate-file privacy checks and local Markdown links passed.

Limitations: allocation uses collection times and assumes uniform energy between accepted observations. It is not measured distributor interval data. There is no price/scenario model, HA adapter, migration, backup/restore, retention or installable package. Next: isolate supply prices/scenarios and test synthetic costs before adding the HA lifecycle. Production was not changed.

## Local development — 2026-10-18

- Added validated source mappings, explicit freshness/power thresholds and optional solar/battery/EV/heat-pump capabilities.
- Added detached observations with unit normalization, scoped freshness dependencies and explicit unknown/estimated quality.
- Added synthetic examples and standard-library behavior tests for minimal and optional configurations.
- Refreshed upstream comparison and recorded unresolved prototype transfer permissions; no private code or third-party implementation was imported.

Validation: 25 behavior tests passed on Python 3.12.14; `git diff --check` passed. All 20 repository candidate files were checked for local Markdown links, private paths/addresses, common token/key patterns and 27 known private source entity identifiers, with no matches or broken links. These scoped checks are not a comprehensive security audit.

This is unreleased development work. Power limits are stored for future counter-delta checks; accounting, HA setup/lifecycle, storage, card packaging and installation are still pending. Next: resolve provenance and connect the accounting core with synthetic continuity tests. Production was not changed.

## Project setup — 2026-10-18

- Added a public project description, Slovenian entry point, development roadmap and architecture boundaries.
- Documented existing alternatives and a template for sharing measured experience.
- Added MIT licensing and public-data rules.

This is a documentation baseline, not a software release. No production configuration or integration code is included.
