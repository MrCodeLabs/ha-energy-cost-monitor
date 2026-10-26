# Energy Cost Monitor for Home Assistant

**Local development, 25 October 2026:** live session views, optional reference-price fetches,
versioned profiles, frozen HTML/CSV reports and an admin API/card are implemented on
`feature/application-workflows`. See [usage, backup boundary and remaining gates](docs/application-workflows.md).
No production deployment or public release is implied.


A project for comparing electricity supply scenarios and explaining energy costs using Home Assistant measurements, with visible data quality and reproducible reports.

**Status, 23 October 2026: configurable sources, persistent metering, supply-scenario comparison and a single-instance HA development adapter.** The adapter has isolated lifecycle contract tests and a successful headless lab test on real Home Assistant 2026.10.2; see [lab evidence and limits](docs/lab-validation.md). There is no public release or supported HACS beta; a local development card is now available (see the current status above).

[Slovenska navodila](README.sl.md) · [Roadmap](ROADMAP.md) · [Design](docs/architecture.md) · [Alternatives](docs/alternatives.md) · [Experience journal](docs/experience.md)

## Intended scope

- Read existing energy measurements without controlling chargers, batteries, heating or other devices.
- Compare import and export costs under multiple supply contracts, including fixed charges and effective dates.
- Preserve missing data, counter resets, uncertain prices and estimated allocations as explicit quality information.
- Produce interval summaries, EV session summaries and frozen HTML/CSV comparison reports.
- Start with a documented Slovenian tariff model and configurable source entities. Support for other countries is future work.

These describe the intended public product. They are not a compatibility claim or a promise of a complete utility bill.

## What exists today

This development tree connects an HA-independent [source configuration boundary](docs/source-configuration.md) and observation validation to a [cumulative-meter ledger](docs/accounting.md). It stores counter deltas, estimated UTC interval allocations, anomalies and coverage in a separate SQLite database. Solar, battery, EV and heat-pump inputs are optional. Synthetic tests cover continuity, restarts and transaction rollback.

The [supply-scenario model](docs/pricing.md) applies explicitly versioned import/export prices and monthly subscriptions to the same covered intervals across offers. It preserves missing prices, reference status and partial coverage. Calculations use decimal arithmetic and exclude VAT, network charges and levies.

The [HA adapter](docs/ha-adapter.md) collects using per-meter report timestamps, preserves gaps and drains pending database writes during unload/reload. It provides setup/reconfigure/options flows and a collection-quality sensor. Sources and storage identity are explicit; prices remain independent of collection.

The owner has authorized reviewed prototype transfers under MIT; the extraction is documented in the [provenance record](docs/provenance.md). Offline archival migration, SQLite snapshot and HA backup hooks are implemented locally; full application rollback and feature parity remain pending, alongside live price adapters, regional tariff calendars and broader HA validation. Household configuration, databases, invoices and private Git history will not be imported.

## Choose an existing tool where it fits

For an energy sensor plus a price sensor, consider [Dynamic Energy Cost](https://github.com/martinarva/dynamic_energy_cost) or [Powercalc cost sensors](https://docs.powercalc.nl/sensor-types/cost-sensor/). The intended distinction here is a combined contract-comparison and reporting workflow, rather than another basic cost sensor. See the dated [comparison](docs/alternatives.md).

## Installation and contribution

The self-contained component is for disposable development labs only; see the [lab procedure and limits](docs/ha-adapter.md). Do not overwrite a production prototype. HACS packaging is being validated for disposable labs only; see [the HACS lab procedure](docs/hacs-lab.md). A supported beta still requires broader HA lifecycle/UI testing, full application migration/restore checks and complete upgrade/rollback instructions.

Issues may discuss the scope and design. Use synthetic examples; do not upload access tokens, private logs, account or meter identifiers, invoices, or production databases. See [development guidance](docs/development.md).

GitHub Actions checks Python lint and synthetic tests on Linux/Windows with Python 3.12–3.14, with weekly Dependabot update proposals. The [first hosted PR run](https://github.com/MrCodeLabs/ha-energy-cost-monitor/actions/runs/39472304035) passed on 20 October 2026; this is not an HA compatibility check or a deployment pipeline. See [CI setup and local commands](docs/development.md#continuous-integration).

## License

New content in this repository is licensed under the [MIT License](LICENSE). Any future imported code must have its origin and license reviewed and its required notices retained.
