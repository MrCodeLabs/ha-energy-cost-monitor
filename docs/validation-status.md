# Validation status and remaining gates

## Local verification — 28 October 2026 — guided initial sources

Branch `feature/guided-source-setup`, based on main `1342c7b`. All 180 local
Python tests and Ruff passed. After normalizing selector translation keys,
the four focused wizard tests, Ruff, pinned hassfest (one integration, zero
invalid) and all five real HA 2026.10.2 phases passed again: fresh 6/12 samples,
migrated 6/12/18 including restore. Temporary containers were removed.
Standard custom-integration and upstream rich warnings appeared without test failures.

The fresh lab flow now selects roles and individual sensors through guided steps,
without source JSON. This is an integration-flow test, not browser/mobile visual
verification or a HACS installation of this unpublished branch. Existing-entry
reconfiguration remains advanced. Full regional billing, study, EV parity, guided
import and card setup remain open. See [guided setup and limits](guided-setup.md).
Main CI run 40386095060 succeeded; this local branch has no hosted CI result yet.

## Local verification — 26 October 2026 — application migration

Branch `feature/legacy-application-migration`, based on merged main `3d086d5`.
176 Windows/Python 3.12 tests, Ruff and card behavior tests passed. Pinned real
HA 2026.10.2 passed all five phases: fresh 6/12 samples, migrated 6/12/18 including
paired restore. The migrated phases convert a synthetic supply profile and frozen
report, then verify archived CSV and escaped HTML through the real application API
after restart/restore. No private data enters the container. Temporary containers
were removed. These local changes have not been committed or run in hosted CI.

See [conversion semantics, acceptance and downgrade restrictions](application-migration.md).
This does not prove full regional billing, study/mode parity, native-versus-legacy
EV energy equivalence, current production source freshness, mobile UX or full HAOS
restore. Original sessions are explicitly archived results, not recomputed ones.
The completed HACS installation/update on main is a separate earlier test; this
unpublished branch was not installed via HACS.

## Latest verification — 25 October 2026 — application workflows

Local branch `feature/application-workflows`, based on merged main `2540253`.
169 tests passed on Windows/Python 3.12.14 and Linux/Python 3.14. Ruff,
JavaScript syntax and card behavior tests passed. Hassfest: one integration,
zero invalid. Real HA 2026.10.2 passed all five phases (fresh 6/12 samples,
migrated 6/12/18), including authenticated HTTP 401/403/admin checks, profile
writes, report retrieval, paired-store backup and process restart/restore.
The Node card suite uses DOM doubles, not a real browser. Hosted CI has not run
for this local branch. Standard custom-integration and upstream rich SyntaxWarning
messages appeared in the lab; no integration test failed.

Implemented: live EV-session view, optional reference-price capture, immutable
profile versions, frozen HTML/CSV reports and admin API/card. See
[workflow instructions and boundaries](application-workflows.md). Full regional
billing, legacy profile/report conversion, browser/mobile UX and full HAOS restore
remain open. This revision is prepared for the owner-requested branch publication; no release, production change or HACS catalog submission.


## Latest verification — 2026-10-24 — legacy reconciliation and EV sessions

- Added verified-bundle reconciliation into a fresh legacy-format database, preserving new allocations without replaying counters; explicit signal mappings convert canonical units.
- Added resume-barrier/baseline reset, marked closure of pre-cutover sessions, and conservative native EV session reconstruction with pauses, gaps and unknown/edge energy.
- Fixed a cutover regression: late reports timestamped before migration could seed baselines and change old intervals. They now remain anomalies without becoming baselines.
- Validation: 155 tests passed on Windows/Python 3.12.14 and Linux/Python 3.14; Ruff passed. Five real HA phases passed. A separate local synthetic harness verified actual legacy-engine reads and resumed ingestion. Full application parity remains open; no publication or production change.

See [reconciliation procedure and exact limits](reconciliation.md).

## Latest verification — 24 October 2026

The 139-test baseline passed again. The next step adds verified `restore-bundle`
and continued collection after restoration. All 145 tests passed on Windows
Python 3.12.14 and Linux Python 3.14, plus Ruff and hassfest. The real HA lab
passed five phases, including a third process loading the restored migrated
ledger and increasing its samples from 12 to 18. See [current lab evidence](lab-validation.md)
and [restore procedure](migration.md). These changes remain local and uncommitted.
The earlier dated entries below describe earlier revisions. Full old-application
replay, feature parity, HACS UI installation and production replacement remain open.

Last consolidated: 23 October 2026. This records completed checks; it is not a live status monitor or a release announcement.

## Published versus local work

| Scope | Evidence | Limit |
| --- | --- | --- |
| Published lab/CI work | Commit `14b9e95`, draft [PR #4](https://github.com/MrCodeLabs/ha-energy-cost-monitor/pull/4); [PR run 40004088767](https://github.com/MrCodeLabs/ha-energy-cost-monitor/actions/runs/40004088767) passed all 11 jobs | PR was open and unmerged at last verification; no beta release |
| Hosted checks | Ruff, six OS/Python test jobs, real HA lab, hassfest, HACS validation, aggregate CI result | HACS validation excludes Brands; no deployment |
| Local migration work | `feature/history-migration`, based on `14b9e95`; 134 tests passed on Windows Python 3.12.14 and Linux Python 3.14; Ruff and hassfest passed | Uncommitted/unpublished; these changes have no hosted CI result yet |
| Real HA migration rehearsal | HA 2026.10.2: fresh and migrated stores each tested across two processes; 6 then 12 new samples; synthetic historical energy preserved; backup hooks/snapshot exercised | Headless synthetic tests, not full HA OS/Supervisor restore or complete UI/lifecycle coverage |
| HACS download rehearsal | HACS 2.0.5 real download/extraction backend fetched main and the lab branch; HA loaded the package; repeated download preserved the ledger | No OAuth/browser installation transaction; component runtime code was identical between those revisions, so this does not prove a runtime-version upgrade |

## Latest local follow-up

Verified recovery bundle added on 23 October 2026: both era databases and a
checksum manifest are produced from one snapshot; historical mappings are
independently reconstructed and compared row by row. 139 tests and Ruff passed
on Windows/Python 3.12.14. The earlier 134-test Linux/real-HA result applies to
the previous revision, not this follow-up. No new hosted CI result or release.
See [recovery procedure and limitations](migration.md#verified-recovery-bundle).

## What migration guarantees

The [offline migration](migration.md) archives original rows, explicitly maps historical energy intervals, records a cutover and uses schema 2 to reject an old schema-1 writer. Verified export restores the archived original logical rows. A consistent SQLite snapshot and HA writer pause/resume are implemented.

Archiving profiles, sessions and report bodies does not implement their new application workflows. Export does **not** replay measurements collected after cutover into the old application. Preserve the new ledger separately until application reconciliation and rollback are implemented and tested.

## Next development sequence

1. Review the local migration diff, privacy boundary and failure cases. On an explicit publication request, commit/push it separately and run hosted CI. Review PR #4 separately; its passing checks do not validate unpublished changes.
2. Complete application migration and rollback: explicit source identity mapping, restart-safe cutover and reconciliation of post-cutover measurements. Prove closed-window comparison and a rollback after new measurements without loss or silent reinterpretation.
3. Close functional gaps against the existing workflow: event/signal capture, EV sessions and partial sessions, independent live-price fetch/cache/backfill, versioned profiles, dated regional bill components, daily quality/study progress, frozen HTML/CSV reports, authenticated API/card and retention of at least 400 days. Record acceptance evidence for each feature before treating replacement as ready.
4. Rehearse full HACS installation and a genuine runtime-version upgrade, broader HA lifecycle/UI behavior, and backup/restore in an isolated environment. Use synthetic configurations for public evidence.
5. Once parity and recovery gates pass, perform the separately managed production transition with a fresh backup, closed-window comparisons and explicit rollback criteria. Then evaluate a labeled beta/custom-repository installation, independent-user feedback and a separate default HACS catalog submission, including Brands.

## Information boundary

Further migration development can use synthetic fixtures. Actual invoice validation later needs dated contract validity, agreed power and excess-power treatment, export/netting/VAT assumptions, the precise indexed-price basis, and a closed-period invoice. Keep originals and household configuration private; publish only invented or thoroughly sanitized examples. Public tariff sources should be researched and dated by the implementer. Credentials must never be shared in issues or test fixtures.

Current content checks do not prove that all historic Git metadata is anonymous. Review author/committer identity and reachable history separately before publishing. No production changes or public release are implied by a passing test.
