<div align="center">

<img src="custom_components/energy_cost_monitor/brand/icon.png" alt="Energy Cost Monitor" width="160" />

# Energy Cost Monitor for Home Assistant

[![Marketplace: Custom repository](https://img.shields.io/badge/Marketplace-Custom-41BDF5.svg)](https://www.home-assistant.io/integrations/marketplace/#custom-repositories)
[![0.1.0](https://img.shields.io/badge/release-0.1.0-007ec6.svg)](https://github.com/MrCodeLabs/ha-energy-cost-monitor/releases/tag/0.1.0)
[![License: MIT](https://img.shields.io/badge/license-MIT-97CA00.svg)](LICENSE)
[![Support via Revolut](https://img.shields.io/badge/Revolut-support-007ec6.svg?logo=revolut&logoColor=white)](https://revolut.me/alesvucina)
[![Support via PayPal](https://img.shields.io/badge/PayPal-support-007ec6.svg?logo=paypal&logoColor=white)](https://paypal.me/AlesVucina)
[![Open Energy Cost Monitor in Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MrCodeLabs&repository=ha-energy-cost-monitor&category=integration)

</div>

Compare electricity supply offers, follow energy measurements and EV sessions,
and save reproducible reports using existing Home Assistant sensors. The
integration reads data; it does not control your devices.

Add Energy Cost Monitor as a custom repository in Home Assistant Marketplace.
Use HACS on Home Assistant 2026.10.2.

**[Start here: installation and user guide](docs/getting-started.md)** ·
**[Slovenska navodila](README.sl.md)**

## What's new in 0.1.0

- Navigate between overview, prices, charging, reports and settings on desktop or mobile.
- Add rates and validity dates with a guided price editor. Compare offers by name.
- Rename imported offers while retaining their rates and earlier reports.
- Resume collection after SQLite recovers an interrupted write at startup.

[Release notes](https://github.com/MrCodeLabs/ha-energy-cost-monitor/releases/tag/0.1.0) ·
[Changelog](CHANGELOG.md)

Previous releases are listed in [GitHub Releases](https://github.com/MrCodeLabs/ha-energy-cost-monitor/releases).

## What you can configure

- Guided sensor selection; solar, battery, EV and heat-pump sources are optional.
- An automatic admin sidebar panel with pricing, profile and report forms.
- Effective-dated import/export prices, subscriptions and optional reference prices.
- EV counter-session settings, observed modes, Slovenian 2026 regional references
  and study warm-up/monthly/final reporting.
- Guided import of a supported legacy Energy Cost Monitor SQLite copy.

The supported setup path requires no user-written code or JSON/YAML edits.
The bundled panel defaults to English, follows Slovenian HA user language settings,
and requires an HA administrator. Other languages fall back to English.
One integration instance is supported per HA installation.

## Verified scope and limits

An isolated 2026.11 laboratory exercised clean installation, beta upgrade,
SQLite recovery and rollback with synthetic data. Earlier HACS acceptance on
2026.10.2 is documented in the [acceptance evidence](docs/acceptance-2026-11-02.md).
Use the [upgrade and recovery instructions](docs/getting-started.md#7-updates-backups-and-removal)
for an existing installation.

Regional estimates cover Slovenia's 2026 rules. Invoice reconciliation, credit
carry-forward, payouts, 2027 rules and full HAOS restore are outside the verified
scope of this release.

## Privacy and help

Settings, measurements and reports stay in your HA storage. Optional Energy-Charts
requests send a zone/date to the provider, which can see your network address.
The public repository contains general code and synthetic examples.

For [issues](https://github.com/MrCodeLabs/ha-energy-cost-monitor/issues), include
HA/HACS versions, the installed commit and sanitized reproduction steps. Do not
upload tokens, private logs, invoices, meter identifiers or household databases.

## Project documentation

- [User guide](docs/getting-started.md): install, configure, verify, update and recover.
- [Frontend languages](docs/frontend-language.md): English default, Slovenian translation and validation scope.
- [Roadmap](ROADMAP.md) and [product goal](docs/product-goal.md): remaining work.
- [Validation history](docs/validation-status.md) and [changelog](CHANGELOG.md).
- [Architecture](docs/architecture.md), [development](docs/development.md),
  [alternatives](docs/alternatives.md) and [provenance](docs/provenance.md).

Licensed under [MIT](LICENSE); retained source attribution is documented in the
provenance record. Historical development records describe their tested revision,
not the current installation procedure.
