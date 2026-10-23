# Source provenance and extraction record

Reviewed: 23 October 2026.

Source material was reviewed locally for ownership, licensing and suitability for public distribution. Only reviewed general-purpose logic is included. The initial source-boundary step on 18 October imported no private source files. The reviewed metering adaptation on 20 October is described below; no private profiles, fixtures, Git history or deployment scripts are imported.

No standalone license or authorship notice was found in the inspected prototype component on 18 October. On 20 October 2026 the project owner explicitly confirmed that the Energy Cost Monitor prototype is their own code and authorized transferring reviewed general-purpose parts under the repository's MIT license. Local Git history also records the initial accounting source under the owner's authorship. This resolves the ownership/permission question for this prototype; third-party code, if encountered in later transfers, still needs its own review. Private source locations and source-file fingerprints remain in the local continuation plan outside this repository.

The source configuration and snapshot validation modules introduced here are newly written for the public design under this repository's MIT license. Their synthetic examples and tests are also new. They express design requirements learned from the prototype; they do not contain its accounting implementation or household configuration. No third-party implementation was copied. The dated upstream review is in [alternatives.md](alternatives.md).

## Meter accounting extraction — 20 October 2026

`energy_cost_monitor/accounting.py` adapts the owner's prototype meter-baseline, interval-allocation and SQLite transaction design. Attribution is retained as Copyright 2026 MrCodeLabs under MIT. The implementation is reorganized around the public validated source model: configurable continuity and power limits, capability-specific coverage, explicit unknowns, strict storage identity and safe reopening. The continuity tests are newly constructed synthetic cases inspired by the original behavior tests; no production profile or original fixture is imported.

Only cumulative-meter accounting is transferred in this step. Daily estimates remain observations, without treating them as cumulative meters. Supplier profiles, regional tariff rules, prices, sessions, study logic, reports, HA adapters and the card are not part of this extraction. No third-party implementation is imported. Future transfers still require a content/privacy review and preserved attribution.

## Supply scenario model — 20 October 2026

The owner's prototype validity lookup, price-unit/resolution handling and supply/subscription calculation were reviewed under the permission above. `pricing.py` independently implements a strict scenario boundary informed by that design, including half-open validity and local-day subscription allocation. It replaces supplier-specific branching with explicit price periods, uses decimal arithmetic, excludes incomplete energy buckets from pricing and compares only common evidence. Copyright 2026 MrCodeLabs/MIT is retained.

The JSON offers and all pricing tests are newly invented. No supplier names, contractual amounts, private profiles, tax/levy tables, production price responses or private report data were transferred. This step neither imports third-party code nor changes the prototype's source files.

## HA development adapter — 23 October 2026

The existing public core files moved to `custom_components/energy_cost_monitor/_core/`
so the custom component is self-contained. Copyright/MIT notices remain intact;
the root package retains standalone imports. The report-time extension, asynchronous
collector, HA setup/configuration/sensor code and synthetic lifecycle tests were
written for this public design. No additional private source or third-party
implementation was transferred. Upstream code and official HA APIs were reviewed
as documented in [alternatives](alternatives.md). The full HA runtime has not yet
been exercised.
