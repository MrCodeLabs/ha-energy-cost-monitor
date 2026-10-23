# Development

Start with README.md, ROADMAP.md, docs/architecture.md and AGENTS.md.

The development tree contains HA-independent metering/pricing and a single-instance [HA development adapter](ha-adapter.md). Its contract tests use explicit HA API doubles, real SQLite/executor work and real `probatio` schemas. They are not a complete HA runtime test. The API review targets Core 2026.10.2; no supported HA compatibility range is claimed. See [source configuration](source-configuration.md), [accounting](accounting.md), [pricing](pricing.md) and [provenance](provenance.md).

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

On 20 October 2026, the repository's [main-ci ruleset](https://github.com/MrCodeLabs/ha-energy-cost-monitor/rules/25495068) was activated for `main`. It requires a pull request, an up-to-date branch and `CI result` from GitHub Actions. It blocks deletion and force pushes, has no bypass actors and requires zero approving reviews so a sole maintainer can merge a passing PR. The workflow file alone does not enforce branch protection; forks need their own repository rules.

This workflow is not a private-data or secret scanner. Review file contents and both author/committer email metadata before pushing; a public CI run happens after upload and cannot prevent that initial disclosure. Use an appropriate GitHub noreply identity when committing. Local validation covers Ruff, the workflow syntax with actionlint 1.7.12 and the Python 3.12 test suite; GitHub execution also confirmed all six OS/Python combinations.

The current workflow also discovers the new adapter contract tests. The next gate is real HA fixtures in a dedicated Linux job and hassfest; HACS and card validation follow their corresponding milestones. Passing core/contract CI is not evidence of Home Assistant compatibility or supported installation. The adapter branch has not yet been run on GitHub.

## Test scope and contribution

Tests validate source configuration, metering continuity, gaps, resets/jumps, coverage, transaction rollback, reopening, explicit price validity/units/status, negative/missing prices, common-evidence comparisons, decimal rounding and local-day subscription shares. An integration test reprices synthetic ledger output without modifying it. New tests cover report-time sampling, repeated reads, independent meters, coalesced tasks, cancellation while writing, setup/rollback, options/reload/unload, shutdown and invalid configuration recovery. Real tariffs, the complete HA runtime, migration, backup/restore and full bills remain unverified.

Storage tests create and remove their own temporary databases. In restricted environments, set `TEMP` and `TMP` to an existing writable development directory before launching Python. On Windows, database fixtures explicitly close connections before temporary-directory cleanup.

Windows `asyncio` also requires a loopback socket pair for its event loop. A
network-restricted sandbox can hang in Python's `socket.accept` before any async
test runs. Permit that local test execution; do not change network settings or
skip cancellation tests to conceal the environment failure. Tests contact no
household devices or remote services.

Use synthetic fixtures for counters, contracts, resets, missing prices and time transitions. Add explicit expected amounts and rounding tolerances. Test the Home Assistant adapter lifecycle separately from the accounting core. Test backup restoration in isolation.

Before submitting code, review the complete diff and new files for private data, verify source licenses and run checks appropriate to the change. Never copy a private repository's history or a production database into this repository.

For this repository, create commits with the public identity `MrCodeLabs` and
`21204857+MrCodeLabs@users.noreply.github.com` for both author and committer.
Before committing, check `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT`;
environment overrides can take precedence over local Git configuration. Before
pushing, inspect both names and emails on every new commit. A noreply address
alone does not anonymize a personal name. Tools that create commits remotely may
ignore local Git configuration, so use local Git with the verified identity.

The public project is independent of any production installation. Deployment needs its own backup, validation, rollback and post-change verification.
