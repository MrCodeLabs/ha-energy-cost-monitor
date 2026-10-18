# Roadmap

Updated: 18 October 2026. Only checked items are complete in this public project.

## Project setup

- [x] Define a separate public project, scope and privacy boundary.
- [x] Document comparable existing projects and the intended distinction.
- [x] Add English/Slovenian entry points, a license and an experience journal.

## First public implementation

- [ ] Review private prototype source provenance and extract only reusable code and tests.
- [ ] Replace fixed entity IDs and thresholds with validated configuration and supported units.
- [ ] Make solar, battery, EV and heat-pump sources optional; quality gates must match configured capabilities.
- [ ] Separate the accounting core, Slovenian tariff/calendar logic, data adapters and presentation.
- [ ] Add synthetic examples for a minimal household and optional EV/battery/heat-pump capabilities.
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

The first development task is configurable source mapping and capability-based validation, preceded by a fresh review of the relevant existing implementations.
