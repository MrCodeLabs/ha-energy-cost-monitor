# Changelog

## Documentation — 2026-10-26 — interactive HACS installation

- Record merged PR #5, passing hosted CI, actual HACS custom-repository installation, HA restart and real desktop Lovelace profile/report workflow.
- Document the observed HACS short-SHA ZIP fallback and the distinction between installation, update persistence, full migration and production readiness.

## Local development — 2026-10-25 — application workflows

- Added live conservative EV-session views, optional public reference-price fetching/cache, immutable profile versions and frozen HTML/CSV reports.
- Added an HA-admin API and bundled development card with period selection, simple price form and advanced scenario editing.
- Added a separate private application store, backup/shutdown draining, cancellation recovery and paired-store restore checks.
- Expanded synthetic tests, real HA HTTP authorization/restart/restore coverage and CI card behavior checks. See [usage and limits](docs/application-workflows.md). Full billing and legacy UI parity remain open; no publication or production change.

## Local development — 2026-10-24 — legacy reconciliation and EV sessions

- Added verified-bundle reconciliation into a fresh legacy-format database, preserving new allocations without replaying counters; explicit signal mappings convert canonical units.
- Added resume-barrier/baseline reset, marked closure of pre-cutover sessions, and conservative native EV session reconstruction with pauses, gaps and unknown/edge energy.
- Fixed a cutover regression: late reports timestamped before migration could seed baselines and change old intervals. They now remain anomalies without becoming baselines.
- Validation: 155 tests passed on Windows/Python 3.12.14 and Linux/Python 3.14; Ruff passed. Five real HA phases passed. A separate local synthetic harness verified actual legacy-engine reads and resumed ingestion. Full application parity remains open; no publication or production change.


## Local development — 2026-10-24 — verified restore and HA restart

- Added `restore-bundle`: fixed archive members, size/checksum checks, independent database/history verification, legacy-export consistency and atomic publication to a new ledger path. Existing destinations are never overwritten.
- Added recovery/continued-collection tests and rejection of corrupted contents, misleading counts, extra archive paths, inconsistent legacy data and the wrong source configuration.
- Extended real-HA validation with a third process booted from a restored migrated ledger.
- Validation: all 145 tests passed on Windows/Python 3.12.14 and Linux/Python 3.14; Ruff and hassfest passed. All five HA 2026.10.2 phases passed: fresh 6/12 samples, migrated 6/12/18 samples across creation/restart/restore. No hosted run, publication or production transition for this local revision. Old-application replay and full functional parity remain open.

## Local development — 2026-10-23 — verified recovery bundle

- Added a no-clobber recovery ZIP containing a consistent new ledger, verified legacy export and checksums/counts.
- Independently rebuild and compare historical interval mappings; reject changed energy/coverage, missing/extra rows and overlapping native samples.
- Added tests for recovery after restart/new measurements, snapshot consistency during continued collection, tampering and existing destinations. Explicitly close comparison cursors on failure for Windows cleanup.
- Validation: 139 tests passed on Windows/Python 3.12.14; Ruff passed. This follow-up has not been rerun on Linux/real HA or hosted CI. Full old-application replay remains open.

## Local development — 2026-10-23 — offline migration and backup

- Added no-clobber migration of a consistent legacy snapshot, preserving original
  rows and report bodies with per-table digests. Explicit interval mapping retains
  historical allocation semantics; new collection cannot precede the cutover.
- Migrated databases use schema 2 so older schema-1-only code rejects them.
  Existing unmigrated native databases remain supported.
- Added consistent SQLite snapshots and verified export of original rows.
  Post-cutover data remains in the new ledger; replay into the old application
  is not implemented and full application rollback remains open.
- Added HA backup hooks that drain/pause collection, prevent setup during backup
  and resume without bridging the gap. Added fresh/migrated real-HA lab scenarios.

Validation: 134 local tests passed; four real HA phases passed (fresh/migrated,
creation/restart), as did hassfest and Ruff. This step remains local; hosted CI
for the migration changes has not run. See [migration limits](docs/migration.md).

## Local development — 2026-10-23 — HACS packaging

- Added HACS metadata, lab installation/update/rollback instructions and a required
  HACS CI check for custom repositories. Brands is explicitly excluded until the
  separate catalog submission; other validation checks remain required.
- HACS installation and hosted validation are pending at this preparation stage.


## Local development — 2026-10-23 — real HA lab

- Added a repeatable, network-isolated HA 2026.10.2 container test using real
  bootstrap/config-entry/platform APIs and synthetic sensor states.
- Verified setup, missing inputs, reload, shutdown and a second process with
  persistent history. SQLite checks passed in both phases (5 then 10 samples).
- Official hassfest passed: one integration, zero invalid integrations.
- Added pinned real-HA and hassfest CI jobs to the required aggregate result.

These CI changes have not been published or run on GitHub. No component runtime
code changed. See [evidence and remaining replacement gates](docs/lab-validation.md).
Migration and production replacement remain blocked by incomplete functionality.

## Local development — 2026-10-23 — publication privacy preparation

- Generalized public documentation to focus on the public project, retaining
  licensing and source attribution without private deployment details.
- Ignore `.storage/` directories to exclude future HA lab runtime configuration.
- Document verification of both author and committer names/emails before commit
  and push; local Git uses the public project identity and GitHub noreply.

Validation: documentation/diff checks, root/nested storage ignore checks and both
effective Git identities verified locally. Runtime code is unchanged by this
step; no additional runtime tests were needed. Existing published history is
unchanged, and current-file edits do not remove information from older commits.

## Local development — 2026-10-23 — single-instance HA adapter

- Added a self-contained development component, config/reconfigure/options flows,
  English/Slovenian forms and a diagnostic collection-quality sensor.
- Added a single-instance reservation, fixed private SQLite path, serialized
  executor collection and cancellation-safe setup rollback/reload/unload/shutdown.
- Added report-time accounting with independent meter timestamps. Repeated reads
  no longer advance baselines or create artificial increment-rate spikes. The
  original standalone collection-time API/storage identity is preserved.
- Preserve unknowns and gaps, reject incompatible existing ledgers, retain storage
  on removal and allow cadence-only options without changing measurement identity.
- Moved canonical core modules under the component with existing MIT notices and
  a standalone import facade; no new private or third-party source was copied.
- Refreshed the upstream comparison and reviewed HA 2026.10.2 APIs, including its
  `probatio` schemas. Documented source-reporting limits and the next lab gate.

Validation: **119 tests passed** on Windows/Python 3.12.14, including 38 new
report-sampling, asynchronous collector and HA contract checks. Real SQLite writes
and executor threads are used; the HA APIs are explicit test doubles. Ruff passed.
Windows sandbox restrictions initially blocked asyncio's loopback socket pair;
the suite passed with local test execution permitted. No device/network service
was queried by tests.

Limitations: full HA loading/frontend/platform validation, hassfest, hosted CI for
this branch, HACS, migration/restore, retention and supported beta packaging are
pending. Reconfiguration cannot change the identity of an existing ledger. This
is local, uncommitted development; production and the private prototype are
unchanged. Next: a disposable HA lab with real config-entry fixtures and hassfest,
then explicit migration and isolated backup/restore work.

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
