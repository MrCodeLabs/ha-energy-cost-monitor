# Disposable Home Assistant validation

## Restore follow-up — 24 October 2026

All five current lab phases passed: fresh ledger creation/restart (6 then 12
samples), migrated ledger creation/restart/restore (6, 12, then 18 samples).
Before the third migrated process, the stopped writer's ledger is bundled,
retained under a separate filename and restored to the vacant lab path using
`restore-bundle`. HA boots the persisted config entry, preserves historical
energy and resumes collection. No production configuration or data is used.
145 behavior tests passed on Windows/Python 3.12.14 and Linux/Python 3.14;
Ruff and pinned hassfest passed (one integration, zero invalid). No hosted CI
was run for this uncommitted revision. HA logs include its usual custom-component
notice and an upstream Rich SyntaxWarning; neither caused a failed assertion.

**Consolidated status, 23 October 2026:** see [published checks, latest local evidence and remaining gates](validation-status.md). Earlier dated observations below describe their tested revision; they do not imply full application migration or a complete HACS installation transaction.

Verified locally on 23 October 2026 with the official Home Assistant 2026.10.2
container (Python 3.14). Run `bash lab/run.sh` on a Linux Docker host. The script
creates fresh temporary configuration, mounts only this repository read-only,
and removes its synthetic runtime afterward. Do not substitute a real HA config.

The container runs as the invoking user, with no network, exposed ports, devices,
capabilities or production mounts, and with bounded memory/CPU/processes. It uses
real HA bootstrap, loader, config flows, config entries, platform and state
machine; there are no HA test doubles in this test. Synthetic states are injected
directly into that state machine, rather than obtained from physical devices.

Verified assertions:

- User flow creates and loads one integration and its diagnostic sensor.
- Usable inputs report `collecting`; unavailable inputs report `incomplete`.
- Entry reload replaces the runtime and preserves SQLite history.
- Shutdown followed by a second container/process loads the persisted entry and
  retains earlier samples; both runs pass SQLite `quick_check`.
- Official hassfest: one integration, zero invalid integrations.

The HA and hassfest image digests are pinned in the scripts/workflow. The HA lab
and hassfest jobs are included in the required aggregate `CI result`; these new
jobs passed on GitHub Actions for PR #4 at `14b9e95`; subsequent migration/restore changes have only local lab results. Upgrades must
update the pins and repeat validation. Hassfest invocation follows the
[official action](https://github.com/home-assistant/actions/tree/master/hassfest).

This is headless Core validation, not a Supervisor/HAOS restore, browser UX test,
HACS certification or production compatibility claim. Browser translations,
real-device timing, disable/re-enable, removal/re-add and write-cancellation under
the real runtime need broader coverage; isolated contract tests cover several of
these paths. No production or private configuration is part of this test.

## Replacement gate

Do not point the new adapter at an older database. Its schema and measurement
semantics differ; rejection is deliberate and does not migrate history. Before a
replacement, require an explicit versioned migration, preservation of original
records and assumptions, restored-copy comparison, functional parity, and a
rollback that does not overwrite measurements collected after cutover.

Live price ingestion, persisted profiles, sessions, authenticated presentation,
frozen reports, regional billing and retention remain incomplete. Backup pause/resume hooks and offline recovery are implemented; full application rollback remains open.
Successful lab and hassfest results do not remove these blockers. Production
cutover belongs in the operator's infrastructure project with private evidence,
fresh backups and before/after comparisons.

## Slovenščina

Pravi HA 2026.10.2 uspešno prestane ustvarjanje vnosa, diagnostični senzor,
manjkajoče podatke, reload in ponovni zagon procesa z ohranjeno zgodovino.
Hassfest je uspešen. Laboratorij nima omrežja in uporablja samo izmišljene podatke.
CI opravila so objavljena v PR #4, nove migracijske dopolnitve pa ostajajo lokalne. Celotna funkcionalna zamenjava in
produkcijski prehod ostajajo odprti; test ni dokaz obnovitve celotnega HA.

## Migration follow-up — 23 October 2026

The lab now repeats creation/restart for both a fresh ledger and a synthetically
migrated schema-2 ledger. Historical energy survives both processes. Backup hooks
pause collection while a consistent snapshot is taken, then resume it. All four
phases passed locally (6 then 12 new samples per scenario), along with 134
behavior tests on Windows/Python 3.12 and Linux/Python 3.14. These migration
changes are local and have not run on hosted CI.
