# Design and extraction boundary

## Configuration boundary — direction confirmed 26 October 2026

The [product goal](product-goal.md) requires one shared HACS package and a
configuration-only user experience. Household differences belong in validated
private HA settings, not generated code, local patches or a private fork.
Guided forms/import must feed the same validated core models; JSON and offline
tools may remain optional development interfaces. Keep code installation separate
from private stores, preserve settings across updates, and explicitly version
data migrations. This is an acceptance requirement, not a completed UI claim.

**24 October 2026:** [legacy reconciliation and EV session reconstruction](reconciliation.md) now provide a separate compatibility export. Original-only `export-legacy` semantics remain unchanged. Full application parity is still open.

Status: source validation, cumulative-meter storage, detached supply-scenario comparison and a single-instance development HA adapter, 23 October 2026. Full HA validation and regional bill components remain pending.

## Intended complete data flow

Configured Home Assistant energy counters and optional signals feed an accounting core. The core stores samples, UTC quarter-hour intervals, quality flags, versioned profiles, EV sessions and report snapshots. An authenticated API supplies a companion dashboard and downloads.

The public implementation uses a separate SQLite database and serializes database work. Consistent backup/restore remains a requirement; measured data must not be placed under a public web directory.

## Boundaries

1. Source mapping: entities, units, freshness, maximum plausible increments and optional capabilities.
2. Accounting: counter deltas, gaps, resets, time allocation, coverage and session boundaries.
3. Pricing: source adapters, cached original responses, units, effective contract versions and confirmation flags.
4. Regional model: calendars, tariff blocks and dated rules; initial scope is Slovenia.
5. Presentation: authenticated summaries, charts, reports and a companion card.

Current household entity names, contract settings, device identifiers and deployment scripts are not public defaults. Optional sources must not prevent a minimal configuration from working. A heat-pump daily estimate is a different input type from a cumulative meter.

The core lives in `custom_components/energy_cost_monitor/_core/`. The root `energy_cost_monitor` package preserves standalone imports without loading HA. `sources.py` and `observations.py` provide validated immutable mappings and detached observations with explicit quality reasons. See [source configuration](source-configuration.md) for the schema, capability rules, alias restrictions and unit/freshness checks.

`accounting.py` implements cumulative deltas, configured power/continuity limits, estimated UTC allocation and per-role coverage in a dedicated SQLite database. Sample, baseline, anomaly and interval writes are atomic. Stored schema/configuration identity prevents accidental reuse of incompatible files. See the [ledger contract and limits](accounting.md). A missing optional source does not insert a zero or invalidate unrelated meters. Daily estimates remain snapshots outside cumulative accounting.

`pricing.py` consumes detached ledger intervals and immutable scenarios. It validates explicit price validity, units, provenance and confirmation status, then calculates import/export supply and local-calendar subscription shares using decimals. Only complete energy intervals are priced; comparisons share the same usable buckets. The [pricing contract](pricing.md) distinguishes partial evidence, full-window supply totals and unverified reference assumptions. It does not write to SQLite or control collection. Live price adapters, persisted/frozen scenario workflows, session boundaries, broader HA validation, full application restore, regional tariffs and presentation remain future work. Local archival migration and SQLite snapshot/backup hooks are described below.

## Accounting invariants

- Unknown is not zero. Incomplete measurements must remain visible.
- Energy allocated across a boundary is an estimate, not a distributor meter reading.
- EV and heat-pump consumption are subsets of household consumption and must not be added twice.
- The price of charging energy does not prove its physical grid/solar/battery origin.
- Missing prices must not stop energy collection.
- A report retains the source data and assumptions used when frozen.
- A supplier comparison is not automatically a complete bill or an estimate of actual payment.

## Lifecycle and compatibility work

The [development adapter](ha-adapter.md) has config/reconfigure/options flows, a collection-quality sensor and one reserved runtime. It polls detached states on the event loop, passes only configured observations to an executor, uses per-meter report timestamps and drains pending writes before releasing the runtime. Only polling cadence can change without storage migration. Startup/reload and collection failures break continuity conservatively. Existing databases are validated, never silently replaced or deleted.

Isolated lifecycle contracts are tested with HA doubles; headless actual HA loading and platform behavior have also passed. Broader UI/lifecycle coverage remains open. See [current validation status](validation-status.md). An explicit offline legacy migration now preserves original records and mapped intervals; HA backup hooks pause/drain the writer. See [migration and rollback limits](migration.md). Retention and complete application rollback remain open. UI configuration is not presented as a universal HACS requirement.

The production prototype is not moved or updated by project setup. Public development and production deployment remain separate operations.


## Application layer — 25 October 2026

The new [application workflows](application-workflows.md) use a separate schema-1
SQLite database (profiles, price provenance/cache, frozen reports), one async
application lock, executor transactions and HA backup/shutdown draining. The meter
schema and independent collector remain unchanged. A ledger read transaction
captures intervals/samples consistently; the serialized application operation then
selects one profile/cache revision. Frozen reports retain both snapshots, with
explicit capture and observation cutoffs, rather than re-evaluating later prices.
The admin REST view follows the active runtime across reload. Public card code
contains no configuration or data; actual data routes require HA admin permission.
The new app store is deliberately outside the existing meter recovery ZIP and must
be included in paired HA backups. Legacy archive conversion remains separate.
