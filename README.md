# Energy Cost Monitor for Home Assistant

A project for comparing electricity supply scenarios and explaining energy costs using Home Assistant measurements, with visible data quality and reproducible reports.

**Status: project setup and public development plan, 18 October 2026. This repository does not yet contain an installable integration or dashboard card.** An existing private prototype is being prepared for general use. There is no public release or HACS installation yet.

[Slovenska navodila](README.sl.md) · [Roadmap](ROADMAP.md) · [Design](docs/architecture.md) · [Alternatives](docs/alternatives.md) · [Experience journal](docs/experience.md)

## Intended scope

- Read existing energy measurements without controlling chargers, batteries, heating or other devices.
- Compare import and export costs under multiple supply contracts, including fixed charges and effective dates.
- Preserve missing data, counter resets, uncertain prices and estimated allocations as explicit quality information.
- Produce interval summaries, EV session summaries and frozen HTML/CSV comparison reports.
- Start with a documented Slovenian tariff model and configurable source entities. Support for other countries is future work.

These describe the intended public product. They are not a compatibility claim or a promise of a complete utility bill.

## What exists today

The private prototype has an accounting engine, a Home Assistant adapter, an authenticated reporting API, a dashboard card and behavioral tests. It uses UTC quarter-hour intervals with a local calendar, a separate SQLite database, versioned profiles and backup support.

Public extraction still requires configurable inputs, synthetic examples, an installation lifecycle, migration and restore checks, and a review of source provenance. Household configuration, databases, invoices and private Git history will not be imported.

## Choose an existing tool where it fits

For an energy sensor plus a price sensor, consider [Dynamic Energy Cost](https://github.com/martinarva/dynamic_energy_cost) or [Powercalc cost sensors](https://docs.powercalc.nl/sensor-types/cost-sensor/). The intended distinction here is a combined contract-comparison and reporting workflow, rather than another basic cost sensor. See the dated [comparison](docs/alternatives.md).

## Installation and contribution

There is currently nothing to install. Do not copy this repository into `custom_components` or add it to HACS yet. The first public implementation will have explicit supported inputs, installation instructions, tests and a release status.

Issues may discuss the scope and design. Use synthetic examples; do not upload access tokens, private logs, account or meter identifiers, invoices, or production databases. See [development guidance](docs/development.md).

## License

New content in this repository is licensed under the [MIT License](LICENSE). Any future imported code must have its origin and license reviewed and its required notices retained.
