# Roadmap

## Product completion gate — 26 October 2026

The [configuration-only product goal](docs/product-goal.md) governs the remaining
work: implement general configurable features, not household patches. HACS
installation alone does not complete the product.

- [ ] Replace required source JSON entry with guided sensor/capability forms.
- [ ] Provide forms for supported pricing, export, regional, EV and study settings.
- [ ] Provide guided import/recovery and card setup without required code/file edits.
- [ ] Validate clean installation by another user with different synthetic inputs.
- [ ] Verify update persistence and privacy of all distributed artifacts.

**26 October 2026, local follow-up:** [offline legacy application migration](docs/application-migration.md)
now converts supply profiles and exposes archived reports/sessions. Original study,
regional and mode data remain archived; equivalent new workflows are still open.
This is not production readiness or a published release.

**Local development, 25 October 2026:** live session views, optional reference-price fetches,
versioned profiles, frozen HTML/CSV reports and an admin API/card are implemented on
`feature/application-workflows`. See [usage, backup boundary and remaining gates](docs/application-workflows.md).
No production deployment or public release is implied.


Updated: 23 October 2026. Only checked items are complete in this development tree; local changes are not a public release.

## Project setup

- [x] Define a separate public project, scope and privacy boundary.
- [x] Document comparable existing projects and the intended distinction.
- [x] Add English/Slovenian entry points, a license and an experience journal.

## Local application layer — 25 October 2026

- [x] Add live conservative session views, optional price fetching/cache and immutable profile versions.
- [x] Add frozen supply HTML/CSV reports, HA-admin API and a bundled development card.
- [x] Verify actual HTTP authorization, paired-store snapshots and restart/restore in the isolated HA lab.
- [ ] Verify real Lovelace/browser/mobile UX, downloads and independent user configuration.
- [ ] Convert legacy profiles/reports for the new UI and validate regional full-bill cases.

## First public implementation

- [x] Inspect the prototype source boundary and record unresolved transfer permissions in docs/provenance.md.
- [x] Refresh upstream code/docs, issue/PR and related frontend comparison before implementation.
- [x] Add an HA-independent source mapping with validated units and explicit freshness/power thresholds.
- [x] Model optional solar, battery, EV and heat-pump capabilities with scoped observation quality gates.
- [x] Add synthetic source examples for a minimal household and optional capabilities, with behavior tests.
- [x] Resolve owner attribution/MIT permission and extract reviewed cumulative-meter accounting with synthetic tests.
- [x] Connect validated sources to the meter ledger; enforce configured increment thresholds and per-role interval coverage.
- [x] Add synthetic metering scenarios for the minimal household and optional capabilities.
- [x] Extract a separate supply-price/scenario model with effective dates, explicit missing prices and synthetic cost calculations.
- [x] Define one-instance support with reserved runtime, fixed private storage and stable diagnostic entity ID.
- [x] Connect the source/ledger boundary to a development HA adapter with an explicit per-meter report-time sampling policy.
- [x] Implement setup, options, reconfigure, reload/unload, task cancellation and recovery; verify isolated adapter contracts with real SQLite/executor work.
- [x] Verify the adapter in a disposable HA installation with real config-entry/platform behavior; run hassfest and add a dedicated Linux HA CI job (local execution and hosted PR #4 checks passed).
- [ ] Extend real HA coverage to browser UX, disable/re-enable, removal/re-add and cancellation during writes.
- [ ] Preserve existing measurements, profiles and frozen reports during migration; never silently replace a user's database.
- [x] Implement offline archival migration with explicit interval mapping, schema-2 downgrade guard and verified original-row export.
- [x] Build a consistent recovery bundle retaining both eras and independently verifying historical interval mapping.
- [x] Verify bundle restoration to a new ledger and continued collection in a third real HA process.
- [x] Export native intervals/snapshots into the legacy format and verify resumed legacy ingestion without cross-era counter bridging.
- [x] Reconstruct native EV sessions with explicit partial/unknown energy for offline reconciliation.
- [ ] Complete live session/profile/report workflows and full application rollback/feature parity.
- [ ] Package the companion card and document its distribution and authenticated API access.

## Accounting and evidence

- [x] Keep explicit effective dates, sources, units and confirmation status for supply-price scenarios.
- [ ] Add separately sourced Slovenian tariff/holiday rules and remaining contract assumptions.
- [x] Separate supply pricing from collection, including local-calendar subscription allocation.
- [ ] Distinguish supplier comparison, known bill components, full bill estimate, credit and actual payment.
- [x] Test missing observations, counter resets/jumps, stale inputs, restarts, duplicate samples and atomic rollback.
- [x] Test distinct UTC intervals for 23/25-hour windows and include missing intervals in coverage.
- [x] Test negative/missing supply prices, local DST subscription allocation, contract expiry/switches and explicit hourly/quarter-hour price periods.
- [ ] Test regional holiday calendars, regulated tariff expiry and provider-specific market-index/averaging assumptions.
- [ ] Add synthetic golden invoice cases with stated rounding rules and tolerances.
- [ ] Verify frozen HTML/CSV equivalence, migration, consistent backup and an isolated restore.
- [x] Preserve synthetic frozen report bodies in migration and verify archived rows on export; test consistent SQLite snapshot and HA writer pause/resume.
- [ ] Validate the tariff model against dated official sources before describing any rules as current.

## Public beta

- [ ] Add complete installation, upgrade, removal and rollback instructions.
- [ ] Add sanitized screenshots and a worked example with invented values.
- [x] Configure CI for core behavior tests on Linux/Windows, Python lint and dependency update proposals.
- [x] Confirm the first hosted CI run across the full OS/Python matrix.
- [x] Require the `CI result` check in main branch protection.
- [x] Add hassfest and HACS validation for the integration (Brands excluded).
- [x] Add card syntax/behavior tests; real browser UX remains open.
- [ ] Test a clean Home Assistant installation and an independent user's configuration.
- [ ] Review all distributed files and Git history for private data and secrets.
- [ ] Publish an explicitly labeled first beta and documented compatibility range.

## HACS and sharing

- [ ] Meet current HACS integration requirements, including metadata and brand registration.
- [ ] Support adding the repository by URL after validation; default-catalog submission is a separate milestone.
- [ ] Describe the prototype experience with dated evidence and limitations.
- [ ] Add measured monthly/final comparisons only after the corresponding observation windows finish.
- [ ] Collect feedback and prefer upstream contributions where an improvement belongs in an existing project.

Current evidence and ordered next steps are consolidated in [validation status](docs/validation-status.md). Offline archival migration and backup hooks are locally tested; application rollback after new measurements, feature parity and full HACS installation/upgrade remain open. No production deployment is performed by this development work.
