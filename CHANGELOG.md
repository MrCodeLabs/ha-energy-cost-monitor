# Changelog

## Local development — 2026-10-18

- Added validated source mappings, explicit freshness/power thresholds and optional solar/battery/EV/heat-pump capabilities.
- Added detached observations with unit normalization, scoped freshness dependencies and explicit unknown/estimated quality.
- Added synthetic examples and standard-library behavior tests for minimal and optional configurations.
- Refreshed upstream comparison and recorded unresolved prototype transfer permissions; no private code or third-party implementation was imported.

Validation: 25 behavior tests passed on Python 3.12.14; `git diff --check` passed. All 20 repository candidate files were checked for local Markdown links, private paths/addresses, common token/key patterns and 27 known private source entity identifiers, with no matches or broken links. These scoped checks are not a comprehensive security audit.

This is unreleased development work. Power limits are stored for future counter-delta checks; accounting, HA setup/lifecycle, storage, card packaging and installation are still pending. Next: resolve provenance and connect the accounting core with synthetic continuity tests. Production was not changed.

## Project setup — 2026-10-18

- Added a public project description, Slovenian entry point, development roadmap and architecture boundaries.
- Documented existing alternatives and a template for sharing measured experience.
- Added MIT licensing and public-data rules.

This is a documentation baseline, not a software release. No production configuration or integration code is included.
