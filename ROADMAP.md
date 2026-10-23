# Roadmap

Updated: 23 October 2026. Only checked items are complete in this development tree; local changes are not a public release.

## Project setup

- [x] Define a separate public project, scope and privacy boundary.
- [x] Document comparable existing projects and the intended distinction.
- [x] Add English/Slovenian entry points, a license and an experience journal.

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
- [ ] Verify the adapter in a disposable HA installation with real config-entry/platform fixtures; run hassfest and add a dedicated Linux HA CI job.
- [ ] Preserve existing measurements, profiles and frozen reports during migration; never silently replace a user's database.
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
- [ ] Validate the tariff model against dated official sources before describing any rules as current.

## Public beta

- [ ] Add complete installation, upgrade, removal and rollback instructions.
- [ ] Add sanitized screenshots and a worked example with invented values.
- [x] Configure CI for core behavior tests on Linux/Windows, Python lint and dependency update proposals.
- [x] Confirm the first hosted CI run across the full OS/Python matrix.
- [x] Require the `CI result` check in main branch protection.
- [ ] Add card tests, hassfest and HACS validation when the integration/card packages exist.
- [ ] Test a clean Home Assistant installation and an independent user's configuration.
- [ ] Review all distributed files and Git history for private data and secrets.
- [ ] Publish an explicitly labeled first beta and documented compatibility range.

## HACS and sharing

- [ ] Meet current HACS integration requirements, including metadata and brand registration.
- [ ] Support adding the repository by URL after validation; default-catalog submission is a separate milestone.
- [ ] Describe the prototype experience with dated evidence and limitations.
- [ ] Add measured monthly/final comparisons only after the corresponding observation windows finish.
- [ ] Collect feedback and prefer upstream contributions where an improvement belongs in an existing project.

Completed locally on 23 October 2026: single-instance development adapter, report-time sampling and isolated lifecycle contract tests. See [adapter scope and next verification gate](docs/ha-adapter.md), [ledger limitations](docs/accounting.md) and [pricing semantics](docs/pricing.md). Next: actual disposable HA validation and hassfest, followed by explicit migration/backup/restore work. Prototype migration, live price adapters, regional bill rules and frozen reports remain unverified or unimplemented. No production installation is authorized by this development step.
