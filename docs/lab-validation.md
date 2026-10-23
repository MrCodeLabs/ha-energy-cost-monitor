# Disposable Home Assistant validation

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
jobs have been executed locally, **not yet on GitHub Actions**. Upgrades must
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
frozen reports, regional billing, retention and backup hooks remain incomplete.
Successful lab and hassfest results do not remove these blockers. Production
cutover belongs in the operator's infrastructure project with private evidence,
fresh backups and before/after comparisons.

## Slovenščina

Pravi HA 2026.10.2 uspešno prestane ustvarjanje vnosa, diagnostični senzor,
manjkajoče podatke, reload in ponovni zagon procesa z ohranjeno zgodovino.
Hassfest je uspešen. Laboratorij nima omrežja in uporablja samo izmišljene podatke.
Nova CI opravila še niso objavljena. Migracija, celotna funkcionalna zamenjava in
produkcijski prehod ostajajo odprti; test ni dokaz obnovitve celotnega HA.
