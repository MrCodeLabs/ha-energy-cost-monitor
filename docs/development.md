# Development

Start with README.md, ROADMAP.md, docs/architecture.md and AGENTS.md.

The development tree contains HA-independent source mapping, observation validation, a SQLite cumulative-meter ledger and detached supply-scenario comparison, with standard-library behavior tests. It has no HA integration tests, CI results or supported Home Assistant versions yet. See [source configuration](source-configuration.md), [accounting](accounting.md), [pricing](pricing.md) and the [provenance record](provenance.md).

From the repository root, using Python 3.12 or later:

```sh
python -m unittest discover -s tests -v
```

No production configuration is needed. Named-timezone pricing tests require IANA timezone data (from the operating system or the `tzdata` package, commonly needed on Windows). The local Python 3.12.14 environment already has this data. Local verification on 20 October: **81 tests passed**, including 27 new pricing tests.

Tests validate source configuration, metering continuity, gaps, resets/jumps, coverage, transaction rollback, reopening, explicit price validity/units/status, negative/missing prices, common-evidence comparisons, decimal rounding and local-day subscription shares. An integration test reprices actual synthetic ledger output while verifying database bytes remain unchanged. They do not validate real tariffs, the HA lifecycle, migration, backup/restore or a complete electricity bill.

Storage tests create and remove their own temporary databases. In restricted environments, set `TEMP` and `TMP` to an existing writable development directory before launching Python. On Windows, database fixtures explicitly close connections before temporary-directory cleanup.

Use synthetic fixtures for counters, contracts, resets, missing prices and time transitions. Add explicit expected amounts and rounding tolerances. Test the Home Assistant adapter lifecycle separately from the accounting core. Test backup restoration in isolation.

Before submitting code, review the complete diff and new files for private data, verify source licenses and run checks appropriate to the change. Never copy a private repository's history or a production database into this repository.

The public project is independent of any production installation. Deployment needs its own backup, validation, rollback and post-change verification.
