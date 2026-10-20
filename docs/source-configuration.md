# Source configuration boundary

Implemented for local development on 18 October 2026. This schema is not a Home Assistant YAML configuration or an installation interface. The package uses Python's standard library and does not access HA, devices, files, databases or the network when parsing or normalizing observations. Loading example JSON is a caller's responsibility.

## Configuration

Use `parse_config(mapping)` from `energy_cost_monitor.sources`. Schema version 1 accepts `schema_version`, an optional `capabilities` list (empty by default), and a `sources` object. Unknown fields, unsupported versions and duplicate capabilities are rejected. The result is detached from the input and read-only. Validation errors expose a field path and code, without echoing supplied values.

Every source has an explicit `entity_id`, `kind` and positive finite `max_age_seconds`. Numeric sources also require a supported `unit`; binary sources omit it. Energy sources require a positive finite `max_power_kw`. These are user-selected limits, never inferred from the device model. Numbers in the examples are invented, not recommended electrical limits.

| Role | Capability | Kind | Requirement |
| --- | --- | --- | --- |
| `house`, `import` | Base | `cumulative_energy` | Both required |
| `export` | Base | `cumulative_energy` | Optional; absence means unmeasured, not zero export |
| `pv` | `solar` | `cumulative_energy` | Required when enabled |
| `charge`, `discharge` | `battery` | `cumulative_energy` | Both required when enabled |
| `ev` | `ev` | `cumulative_energy` | Required when enabled |
| `heating`, `water` | `heat_pump` | `cumulative_energy` or `daily_energy_estimate` | At least one when enabled |
| `house_power`, `grid_power` | Base | `power` | Optional |
| `pv_power` | `solar` | `power` | Optional |
| `battery_power`, `battery_soc` | `battery` | `power`, `percentage` respectively | Optional |
| `ev_power`, `ev_connected` | `ev` | `power`, `binary` respectively | Optional |

Supported units are `Wh`, `kWh`, `MWh` for energy, `W`, `kW`, `MW` for power and `%` for percentage. Entity domains are `sensor` for numeric sources and `binary_sensor` for the connection signal. Other HA helpers and custom connection-state encodings are outside this first boundary.

Sources for disabled capabilities are rejected. Reusing an entity for different roles is rejected except identical `house`/`import` definitions in a household without solar, battery or a configured export meter. That explicit alias represents the same measured counter in an import-only home; it never adds consumption twice. It does not prove the home's physical topology. Enabling a generation/storage capability requires independent measurements.

An energy source may declare `freshness_sources`, a list of configured signal roles. An unusable dependency invalidates only that energy source. Dependencies on other energy sources or dependencies on signals from signals are rejected, preventing cycles. No vendor-wide freshness group is assumed. A signal not listed as a dependency does not gate meters merely because it is configured.

## Detached observations

`normalize_snapshot(config, observations, now=utc_timestamp)` takes observations keyed by entity ID. Each `Observation` contains `value`, `unit` and `reported_at` (UTC Unix seconds). A future HA adapter should supply the actual state unit and `last_reported`, not the last time the value changed. An unchanged counter or zero power can still be fresh. Missing timestamps are unknown, not automatically fresh.

Readings normalize to kWh, kW, percent or boolean. The observed unit must match the configured unit exactly; a unit change needs configuration review. Missing or unsupported units never fall back to kWh. Numeric zero and binary `off` remain valid. Negative grid power means export; negative battery power means charging. Other negative power, negative energy and percentages outside 0–100 are invalid. Price data does not pass through this module; the separate [supply-scenario model](pricing.md) supports negative prices.

Quality values are `valid`, `estimated`, `missing`, `unavailable`, `invalid_value`, `invalid_timestamp`, `future_timestamp`, `stale`, `unit_mismatch`, `out_of_range` and `dependency_unavailable`. Invalid readings have `value=None`. Daily energy estimates remain labeled `estimated`. `ev_connected` accepts HA `on`/`off` or explicit booleans; an unknown state never becomes a disconnect.

`required_roles` contains only configured cumulative-energy roles, including configured export and cumulative heat-pump meters. Daily estimates and independent signals do not participate. `Snapshot.ready` describes the current usability of those meters. It does **not** establish interval coverage, a successful daily reference check, readiness of EV session reporting, a study start or bill completeness. The separate [meter ledger](accounting.md), added on 20 October, consumes `max_power_kw`, checks continuity and computes interval coverage. A valid single reading is not evidence of a plausible increment. Daily estimates remain separate.

## Synthetic examples and verification

- [Minimal import-only household](../examples/minimal.json): no optional equipment or fabricated export value.
- [Optional capabilities](../examples/optional-capabilities.json): independent meters, EV/PV freshness dependencies and daily heat-pump estimates.

Run from the repository root with Python 3.12 or later:

```sh
python -m unittest discover -s tests -v
```

The suite exercises invalid configuration, independent capabilities, known unit conversions, absent and stale states, scoped dependency failures, estimated inputs, alias restrictions and recovery. It uses invented entities and detached observations only. The local run used Python 3.12.14; other Python versions and HA lifecycle/compatibility are not validated by this suite.

## Slovenska navodila

To je razvojni model, ne konfiguracija za namestitev v HA. Primera sta izmišljena. Najmanjši primer potrebuje števec hišne porabe in prevzema; pri hiši brez proizvodnje/hranilnika lahko oba pomenita isti števec z enakimi nastavitvami. Oddaja brez merilnika ostane neznana. Zmožnosti `solar`, `battery`, `ev` in `heat_pump` omogoči le z ustreznimi viri; dnevna ocena TČ ostane ocena. Svežino in največjo moč določi za svoje vire. Prag moči uporablja merilno jedro pri preverjanju prirastkov.

Preizkuse zaženi z zgornjim ukazom iz korena projekta. Rezultat `ready` potrjuje samo trenutno uporabnost nastavljenih kumulativnih števcev. Dobavna primerjava je izvedena ločeno; celoten račun, namestitev, življenjski cikel HA in produkcijska migracija ostajajo odprti. [Pregled izvora](provenance.md) beleži potrditev avtorstva in dovoljenje za pregledani prenos pod MIT.
