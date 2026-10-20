# Cumulative-meter ledger

Implemented for local development on 20 October 2026. This is the energy-measurement part of accounting; it does not calculate prices or a bill. The owner's permission and extraction boundary are recorded in [provenance](provenance.md).

## Development API

`AccountingEngine(path, config, max_gap_seconds=...)` accepts a validated [source configuration](source-configuration.md) and an explicit continuity limit greater than zero and at most 900 seconds. Use a new private development database path outside public web directories. The limit is a sampling policy, not a device-specific default.

```python
import json
from pathlib import Path

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.observations import Observation
from energy_cost_monitor.sources import parse_config

config = parse_config(json.loads(Path("examples/minimal.json").read_text()))
engine = AccountingEngine("development.sqlite3", config, max_gap_seconds=120)
start = 1_800_000_000  # Synthetic UTC quarter-hour boundary.
entity = config.sources["import"].entity_id
for minute in range(16):
    timestamp = start + minute * 60
    engine.ingest(timestamp, {entity: Observation(100 + minute / 10, "kWh", timestamp)})
result = engine.summary(start, start + 900)
assert abs(result.energy_kwh["import"] - 1.5) < 1e-9
assert result.coverage["import"] == 1
```

The minimal example deliberately aliases house/import to one counter. Totals are always returned per role; the ledger never adds house, import, EV or heat-pump readings together. Repeating collection timestamps returns `False` without updating the stored sample. Older samples are also ignored; historical backfill is not supported.

## Continuity and quality

The first usable reading establishes a baseline. Later readings pass the configured unit/freshness checks and per-meter `max_power_kw` limit before contributing a delta. Baselines and continuity survive reopening. A reset or excessive positive jump records an anomaly and establishes a new baseline without counting that change.

An invalid observation breaks continuity only for its affected meter. On recovery, a nonnegative plausible delta across that gap is retained as `unassigned_kwh`, without filling intervals. An excessive elapsed time has the same effect. Resets/jumps remain rejected changes, not valid unassigned consumption. No missing value becomes zero.

Accepted deltas are distributed uniformly between **collection timestamps** into UTC 900-second buckets. This is an allocation estimate even when coverage is complete. `reported_at` checks freshness only. Polling a cached reading can allocate zero before a later update and can make that update appear to exceed the configured power limit. Integrations with coarse or irregular counter reporting require an adapter/sampling policy review; these results must not be advertised as measured distributor quarter-hours.

Daily energy estimates and signals are saved in detached normalized snapshots. They are not cumulative totals and do not participate in interval coverage. Daily estimate allocation and EV session detection are future work.

## Queries

`intervals(start, end)` returns every UTC bucket in the half-open window, including missing buckets. Boundaries must be multiples of 900 seconds, the window must be nonempty, and it cannot exceed 400 days. Callers convert local calendar boundaries to UTC. Tests cover 23/25-hour shaped windows, not Slovenian holiday or tariff rules.

Each bucket exposes per-role energy, covered seconds and a complete flag. Entirely missing energy is `None`; measured zero is `0`. A complete bucket needs 900 covered seconds. `ready` requires completeness for all configured cumulative roles. An EV dependency failure can therefore reduce joint coverage while house/import remain complete.

`summary` returns accepted allocated energy, which can be **partial**, alongside the fraction of complete buckets per role and joint coverage. Missing buckets stay in the denominator. Unassigned energy is available separately through `anomalies()` and is excluded from interval totals. Consumers must show coverage alongside totals and must not present partial values as a full-period bill.

## Storage and limits

Each ingest uses one SQLite transaction for sample, baselines, anomalies and allocations. A failure rolls all of them back. Connections close after each operation; write transactions serialize updates and duplicate detection. This synchronous development API belongs in a serialized executor when a future HA adapter calls it.

New files use application ID `0x45434D31`, schema version 1 and a configuration identity hash. Existing files must match the schema and configuration. Unrelated, blank, unsupported or differently configured databases are rejected without replacement. A missing database during collection is an error, not permission to recreate it. This is a new public development schema and does not open or migrate prototype databases.

There is no retention policy, migration, backup/restore API, multi-instance HA lifecycle, tariff calendar, report or network access in this module. The separate [supply-scenario model](pricing.md) consumes detached intervals without changing this database. Changing source settings requires a future explicit migration/reconfiguration policy; deleting history is not the workaround.

## Slovenska navodila

Jedro iz kumulativnih števcev izračuna prirastke in jih enakomerno razporedi v 15-minutne intervale UTC. Upošteva nastavljene meje moči, svežino, vrzeli in ponastavitve; dnevna ocena TČ ostane ločena. Skupaj s porabo vedno prikaži pokritost. Popolna pokritost ne pomeni izmerjene četrturne porabe distributerja.

Preizkusi uporabljajo izmišljene podatke in začasne zbirke. Produkcijske zbirke ne odpiraj s tem razvojnim jedrom. Dobavne cene/scenariji so izvedeni v ločenem modulu; življenjski cikel HA, migracije, obnova in namestitev še niso izvedeni. Naslednji korak je priklop in preizkus HA za eno instanco z izrecno politiko zbiranja meritev.
