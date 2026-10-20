# Development

Start with README.md, ROADMAP.md, docs/architecture.md and AGENTS.md.

The development tree contains HA-independent source mapping, observation validation, a SQLite cumulative-meter ledger and detached supply-scenario comparison, with standard-library behavior tests. The [first hosted CI run](https://github.com/MrCodeLabs/ha-energy-cost-monitor/actions/runs/39472304035) passed on 20 October 2026 across the full matrix. It has no HA integration tests or supported Home Assistant versions yet. See [source configuration](source-configuration.md), [accounting](accounting.md), [pricing](pricing.md) and the [provenance record](provenance.md).

From the repository root, using Python 3.12 or later:

```sh
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m unittest discover -s tests -v
```

Use a separate virtual environment for development dependencies. No production configuration is needed. Named-timezone pricing tests require IANA timezone data (from the operating system or the `tzdata` package, commonly needed on Windows). The pinned development requirements include Ruff and tzdata. Set `PYTHONTZPATH` to an empty string before starting Python to use the same pinned timezone data as CI. Local verification on 20 October: **81 tests passed** on Windows/Python 3.12.14.

## Continuous integration

[CI](../.github/workflows/ci.yml) runs on pushes, pull requests targeting `main`, and manual dispatch:

- Ruff checks Python errors and unused/undefined names with the repository's explicit rule set.
- The complete synthetic suite runs on Ubuntu and Windows, with Python 3.12, 3.13 and 3.14. Both operating systems use pinned tzdata rather than the runner's timezone database.
- `CI result` succeeds only if lint and every test matrix entry succeed. A failed, cancelled or skipped dependency cannot pass this gate.

Actions are pinned to full commit SHAs, the token has `contents: read` only, and checkout does not persist credentials. Jobs have time limits and superseded runs are cancelled. Tests use temporary synthetic databases; the workflow has no deployment, release upload, production access or additional secrets. It uses `pull_request`, not `pull_request_target`.

[Dependabot](../.github/dependabot.yml) checks Actions and development requirements weekly and proposes updates for review. It does not automatically merge them. Its configuration becomes active after it reaches the default branch.

After the first hosted run succeeds, configure a branch ruleset for `main` requiring a pull request and the `CI result` status check. The workflow file alone does not enforce branch protection. Repository settings have not been changed by this addition.

This workflow is not a private-data or secret scanner. Review file contents and both author/committer email metadata before pushing; a public CI run happens after upload and cannot prevent that initial disclosure. Use an appropriate GitHub noreply identity when committing. Local validation covers Ruff, the workflow syntax with actionlint 1.7.12 and the Python 3.12 test suite; GitHub execution also confirmed all six OS/Python combinations.

HA lifecycle/card tests, hassfest and HACS validation will be added when the corresponding integration and card files exist. Passing core CI is not evidence of Home Assistant compatibility or installability.

## Test scope and contribution

Tests validate source configuration, metering continuity, gaps, resets/jumps, coverage, transaction rollback, reopening, explicit price validity/units/status, negative/missing prices, common-evidence comparisons, decimal rounding and local-day subscription shares. An integration test reprices actual synthetic ledger output while verifying database bytes remain unchanged. They do not validate real tariffs, the HA lifecycle, migration, backup/restore or a complete electricity bill.

Storage tests create and remove their own temporary databases. In restricted environments, set `TEMP` and `TMP` to an existing writable development directory before launching Python. On Windows, database fixtures explicitly close connections before temporary-directory cleanup.

Use synthetic fixtures for counters, contracts, resets, missing prices and time transitions. Add explicit expected amounts and rounding tolerances. Test the Home Assistant adapter lifecycle separately from the accounting core. Test backup restoration in isolation.

Before submitting code, review the complete diff and new files for private data, verify source licenses and run checks appropriate to the change. Never copy a private repository's history or a production database into this repository.

The public project is independent of any production installation. Deployment needs its own backup, validation, rollback and post-change verification.
