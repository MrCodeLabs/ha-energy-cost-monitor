# Development

Start with README.md, ROADMAP.md, docs/architecture.md and AGENTS.md.

The initial repository contains documentation only. There are no executable integration tests, CI results or supported Home Assistant versions yet. Add meaningful behavior tests together with the first code extraction, rather than placeholder tests that only prove files exist.

Use synthetic fixtures for counters, contracts, resets, missing prices and time transitions. Add explicit expected amounts and rounding tolerances. Test the Home Assistant adapter lifecycle separately from the accounting core. Test backup restoration in isolation.

Before submitting code, review the complete diff and new files for private data, verify source licenses and run checks appropriate to the change. Never copy a private repository's history or a production database into this repository.

The public project is independent of any production installation. Deployment needs its own backup, validation, rollback and post-change verification.
