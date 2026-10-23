# Home Assistant development adapter

Implemented locally on 23 October 2026. This is an unreleased, single-instance
adapter with isolated contract tests. The API review targets Home Assistant
**2026.10.2**, including its `probatio` form schemas. A complete HA installation,
loader/frontend behavior, hassfest and HACS validation have **not** been run.
This is not a supported compatibility range or a production installation guide.

## Package and configuration

The self-contained development component is
`custom_components/energy_cost_monitor/`. Its `_core/` directory contains the
canonical HA-independent source, observation, accounting, pricing and collector
modules. The repository-level `energy_cost_monitor` package keeps the existing
standalone imports working without importing HA. There is no second engine copy,
unpublished PyPI dependency, external service or production credential.

For the next **disposable HA lab** check, place only that component directory in
the lab's `custom_components`, restart the lab and use Settings → Devices &
services → Add integration → Energy Cost Monitor. Do not overwrite an existing
prototype installation. Paste the full contents of [minimal.json](../examples/minimal.json)
into the source JSON field, after creating matching synthetic sensors in that
lab. The [optional example](../examples/optional-capabilities.json) exercises
additional capabilities. These entity names and thresholds are invented test
inputs, not suggested household settings.

The setup form requires the validated source mapping and a maximum report gap
of 30–900 seconds (form default 300). Units, freshness and power limits remain
explicit per source. Options change only the polling interval: 5–300 whole
seconds (default 30), no longer than the maximum gap or any source freshness
limit. Polling reads HA's state machine; it never calls a device update or control
service. Missing entities do not block setup; they remain missing until reported.

One config entry is supported, enforced in the manifest, config flow and runtime
reservation. The flow uses a fixed unique ID; the diagnostic sensor uses the
entry ID. A second setup cannot open another writer while the first is starting,
running or draining during unload.

## Sampling contract

The adapter always opens the ledger with `sampling_mode="report"`:

- `State.last_reported` supplies each source timestamp. `last_changed` is never
  used as freshness. Missing timestamps and restored states do not establish a
  usable live observation.
- Repeated polling of the same report does not advance that meter's baseline,
  allocate zero consumption, or shorten the next increment's power-limit window.
  Independently reporting meters keep independent baseline timestamps.
- A new, equally valued report contributes measured zero change over its report
  window. An older report or a conflicting value at the same timestamp breaks
  continuity without rewinding the baseline.
- Source freshness still uses collection time. Unavailable/stale states, unit
  errors and missing dependencies break continuity. A plausible delta across a
  gap is retained as unassigned energy, never allocated or priced.
- Report gaps beyond the configured limit are not interpolated. Accepted deltas
  are uniformly allocated between report times into UTC quarter-hours; even
  complete coverage is an estimate, not distributor interval evidence.
- Startup/reload explicitly breaks continuity. No consumption is inferred across
  time when this collector was not observing the source. After a storage error,
  recovery also breaks continuity before accepting a new baseline.

This solves repeated **reads** of a cached report, not every device's reporting
behavior. If a source integration republishes a cached or coarsely rounded value
with new timestamps, HA cannot prove the meter's actual measurement time. Such
sources may still trip the plausibility limit; they need source-specific evidence
before use. Polling can miss a transient reset or unavailable state between two
polls. It does not reconstruct missed intermediate reports or fetch HA history.

## Storage, lifecycle and recovery

The single ledger lives at `.storage/energy_cost_monitor.sqlite3` under the HA
configuration directory, outside public web content and separate from Recorder.
Source mapping, units, thresholds, gap and sampling mode are part of its identity.
Existing collection-time ledgers and prototype schemas are rejected, not migrated
or replaced. The old standalone collection-time mode and identity remain intact.

Reconfigure can correct an entry with invalid settings. If a ledger already
exists, corrected settings must match its identity; changing source entities,
thresholds, capabilities or the maximum gap needs a future explicit migration.
Reconfiguration validation is read-only. Options may change cadence without
changing measurement identity and trigger one reload through the update listener.
Failed entries without that listener explicitly request reload after correction.

SQLite work runs in an executor, with at most one owned collection task and no
unbounded queue. Busy timer ticks reuse the in-flight task. Unload first unloads
the sensor platform, removes the timer/stop/update listeners, stops new requests
and waits for the current database operation to close. Cancellation is propagated
only after executor work or cleanup finishes; cancellation cannot stop a SQLite
thread. A platform refusing unload leaves collection running. Failed setup rolls
back its listeners and runtime reservation, allowing a later corrected retry.

Storage access failures during setup request HA retry. Invalid configuration or
an incompatible existing database produces a configuration error. During
collection, expected storage failures set a diagnostic error and retry on the next
tick; warning messages do not include source values, entity IDs or storage paths.
A missing database during collection is never silently recreated.

The collection sensor has states `collecting`, `incomplete` and `storage_error`.
Attributes contain the last collection time and quality codes by generic role.
`collecting` describes usable current inputs, **not** full interval coverage,
successful billing or validated savings. No cost totals or control services are
exposed. Pricing remains independent of collection.

Removing the integration retains the database. Re-adding with matching settings
reuses it; different settings are refused. Never delete the ledger to bypass an
identity error. Before future migrations, prepare a consistent backup and test
restore in isolation. Migration, retention, backup/restore hooks, profiles and
frozen reports remain outside this step. Snapshot/anomaly storage is currently
unbounded, so long-running deployment is not ready.

## Verification and next gate

The standard suite includes real SQLite/executor tests for report-time sampling,
independent meters, unavailable/stale/reset/jump behavior, restart gaps,
transaction rollback, busy-tick coalescing, repeated cancellation and failed
storage recovery. Adapter contract tests execute setup, flows, sensor updates,
options/reload, unload, shutdown and rollback with explicit HA API doubles and
real `probatio` validation. These doubles are identified in `tests/ha_contract.py`;
they are not an HA loader, event bus or config-entry manager.

Next: run the package in a disposable HA 2026.10.2 environment with synthetic
sensors and real config-entry/platform fixtures, then add hassfest and a dedicated
Linux HA test job. Verify setup forms/translations, disabled/re-enabled entries,
rapid reload, shutdown during a write and removal/re-add before claiming HA
compatibility. Existing CI runs the core and contract tests on its current matrix;
this branch has not been published or run on hosted CI.

## Slovenska navodila

Adapter je razvojna izvedba za **eno instanco**. Konfiguracija virov je JSON iz
sintetičnega primera; v možnostih se spreminja samo interval zajema. Viri, enote,
pragovi in največji razmik poročil po nastanku zbirke ostanejo vezani na njeno
identiteto. Nezdružljiva zbirka se ne prepiše, odstranitev integracije je ne izbriše.

Zajem uporablja čas poročila senzorja, ohrani neznano ter ob ponovnem zagonu ne
zapolni vrzeli. Diagnostični senzor kaže stanje zajema, ne potrjenega računa.
Preizkusi uporabljajo začasne zbirke in izmišljene podatke. Celoten HA še ni
preizkušen; naslednji korak je ločen laboratorijski HA, hassfest in nato preizkus
migracije/obnove. Produkcijska namestitev in zasebni prototip ostaneta ločena.
