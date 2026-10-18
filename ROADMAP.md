# Roadmap

Updated: 18 October 2026. Only checked items are complete in this public project.

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
- [ ] Resolve source attribution/licensing and extract only cleared accounting code and tests.
- [ ] Connect the validated mapping to accounting and HA; enforce configured increment thresholds and interval-quality gates.
- [ ] Separate the accounting core, Slovenian tariff/calendar logic, data adapters and presentation.
- [ ] Add synthetic accounting scenarios for the minimal household and optional capabilities.
- [ ] Define one-instance support first or implement isolated storage and unique IDs for multiple instances.
- [ ] Implement and test setup, options, reload/unload, task cancellation and recovery from invalid configuration.
- [ ] Preserve existing measurements, profiles and frozen reports during migration; never silently replace a user's database.
- [ ] Package the companion card and document its distribution and authenticated API access.

## Accounting and evidence

- [ ] Keep explicit effective dates, sources, units and confirmation status for tariffs and contract assumptions.
- [ ] Distinguish supplier comparison, known bill components, full bill estimate, credit and actual payment.
- [ ] Test negative prices, missing data, counter resets/jumps, stale inputs, restarts and duplicate samples.
- [ ] Test DST, holiday calendars, tariff expiry, and hourly versus quarter-hour market-price assumptions.
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

Completed locally on 18 October 2026: configurable source mapping and capability-based observation validation, preceded by a fresh upstream review. See [configuration and limitations](docs/source-configuration.md). This is development code, not an installable integration. Next: resolve transfer permissions, adapt the accounting core to this boundary and add synthetic interval/continuity tests, then test the HA lifecycle independently.
