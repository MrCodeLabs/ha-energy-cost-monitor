# Design and extraction boundary

Status: proposed public architecture with an implemented development source boundary, 18 October 2026. The full accounting/HA API contract is not implemented.

## Data flow

Configured Home Assistant energy counters and optional signals feed an accounting core. The core stores samples, UTC quarter-hour intervals, quality flags, versioned profiles, EV sessions and report snapshots. An authenticated API supplies a companion dashboard and downloads.

The existing prototype uses a separate SQLite database and serializes database work. The public design must retain consistent backup/restore and must not place measured data under a public web directory.

## Boundaries

1. Source mapping: entities, units, freshness, maximum plausible increments and optional capabilities.
2. Accounting: counter deltas, gaps, resets, time allocation, coverage and session boundaries.
3. Pricing: source adapters, cached original responses, units, effective contract versions and confirmation flags.
4. Regional model: calendars, tariff blocks and dated rules; initial scope is Slovenia.
5. Presentation: authenticated summaries, charts, reports and a companion card.

Current household entity names, contract settings, device identifiers and deployment scripts are not public defaults. Optional sources must not prevent a minimal configuration from working. A heat-pump daily estimate is a different input type from a cumulative meter.

The first boundary is implemented in `energy_cost_monitor/sources.py` and `observations.py`: validated immutable mappings and detached observations with explicit quality reasons. See [source configuration](source-configuration.md) for the development schema, capability rules, alias restrictions and unit/freshness checks. Configured power limits are retained for the future counter-delta layer; no stateful accounting or interval coverage is computed yet. A missing optional source does not insert a zero or invalidate unrelated meters. Daily estimates remain outside cumulative-meter readiness. No HA adapter, storage, tariff engine or presentation is included in this step.

## Accounting invariants

- Unknown is not zero. Incomplete measurements must remain visible.
- Energy allocated across a boundary is an estimate, not a distributor meter reading.
- EV and heat-pump consumption are subsets of household consumption and must not be added twice.
- The price of charging energy does not prove its physical grid/solar/battery origin.
- Missing prices must not stop energy collection.
- A report retains the source data and assumptions used when frozen.
- A supplier comparison is not automatically a complete bill or an estimate of actual payment.

## Lifecycle and compatibility work

Public extraction must define validated configuration, data migrations, task cleanup, versioned storage, backup hooks and restore behavior. The current prototype's YAML startup is not sufficient evidence of this lifecycle. UI configuration is a usability goal; it is not presented as a universal HACS requirement.

The production prototype is not moved or updated by project setup. Public development and production deployment remain separate operations.
