# Energy Cost Monitor for Home Assistant

Compare electricity supply offers, follow energy measurements and EV sessions,
and save reproducible reports using existing Home Assistant sensors. The
integration reads data; it does not control your devices.

**Development preview — updated 2 November 2026.** Install through a HACS custom
repository in a separate test instance. This is not a stable release, a HACS
default-catalog entry, or a complete utility-bill calculator.

**[Start here: installation and user guide](docs/getting-started.md)** ·
**[Slovenska navodila](README.sl.md)**

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

[PR #11](https://github.com/MrCodeLabs/ha-energy-cost-monitor/pull/11) merged these
workflows into `main` (`532012e`). The isolated HA 2026.10.2 laboratory verified
setup forms, synthetic import, report creation, study controls and HACS download
and restart. Earlier data, four profile versions and two reports survived the
update; all 27 package files matched the tested code. All 207 Python tests and
branch/PR/main CI checks passed. See [acceptance evidence](docs/acceptance-2026-11-02.md).

This does not establish compatibility with every HA version or a full HAOS
restore. Complete invoice reconciliation, opening/carry-forward credit, payouts,
2027 regional rules and independent-user acceptance remain open. Missing values
stay unknown. **Do not replace an existing production implementation yet.**

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
