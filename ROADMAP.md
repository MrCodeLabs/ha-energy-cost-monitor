# Roadmap

Updated: 20 October 2026. Only checked items are complete in this public project.

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
- [ ] Define one-instance support first or implement isolated storage and unique IDs for multiple instances.
- [ ] Connect the source/ledger boundary to HA with an explicit sampling policy for coarse or irregular counter reports.
- [ ] Implement and test setup, options, reload/unload, task cancellation and recovery from invalid configuration.
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
- [ ] Run CI for behavior tests, card tests, hassfest and HACS validation where applicable.
- [ ] Test a clean Home Assistant installation and an independent user's configuration.
- [ ] Review all distributed files and Git history for private data and secrets.
- [ ] Publish an explicitly labeled first beta and documented compatibility range.

## HACS and sharing

- [ ] Meet current HACS integration requirements, including metadata and brand registration.
- [ ] Support adding the repository by URL after validation; default-catalog submission is a separate milestone.
- [ ] Describe the prototype experience with dated evidence and limitations.
- [ ] Add measured monthly/final comparisons only after the corresponding observation windows finish.
- [ ] Collect feedback and prefer upstream contributions where an improvement belongs in an existing project.

Completed locally on 20 October 2026: owner permission under MIT, cumulative-meter extraction, SQLite persistence and the separate supply-scenario model; 81 source/metering/pricing tests passed. See [ledger limitations](docs/accounting.md) and [pricing semantics](docs/pricing.md). This is development code, not an installable integration. Next: define the single-instance HA adapter and sampling policy, then independently test its lifecycle. Prototype database migration, backup/restore, live price adapters, regional bill rules and frozen reports remain unverified or unimplemented.
