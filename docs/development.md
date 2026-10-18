# Development

Start with README.md, ROADMAP.md, docs/architecture.md and AGENTS.md.

The development tree contains HA-independent source mapping and observation validation, with standard-library behavior tests. It has no HA integration tests, CI results or supported Home Assistant versions yet. See [source configuration](source-configuration.md) and the [provenance record](provenance.md).

From the repository root, using Python 3.12 or later:

```sh
python -m unittest discover -s tests -v
```

No dependencies or production configuration are needed. Local verification used Python 3.12.14. Tests validate the source boundary, not the accounting engine, HA lifecycle or a complete electricity bill.

Use synthetic fixtures for counters, contracts, resets, missing prices and time transitions. Add explicit expected amounts and rounding tolerances. Test the Home Assistant adapter lifecycle separately from the accounting core. Test backup restoration in isolation.

Before submitting code, review the complete diff and new files for private data, verify source licenses and run checks appropriate to the change. Never copy a private repository's history or a production database into this repository.

The public project is independent of any production installation. Deployment needs its own backup, validation, rollback and post-change verification.
