# Configuration workflow acceptance — 2 November 2026

Tested in a disposable Home Assistant 2026.10.2 laboratory with invented values.
The ECM entry and stores started empty; existing test authentication and HACS were
retained. This is a clean integration setup, not a new HAOS installation.

## Verified

- Guided source setup selected an existing synthetic kWh sensor for house/import,
  set its power limit and saved the reviewed configuration without JSON/YAML.
- The admin sidebar panel appeared automatically, without a Lovelace resource edit.
- Pricing forms created a profile, offer, contract validity, subscription and import
  price period. EV counter settings and a dated regional reference were entered
  through forms. Missing/unconfirmed prices remain explicit.
- Study configuration, start, cancellation, restart and persistence across an HA
  restart worked. Actual elapsed laboratory time only proves the warm-up state.
- A new deterministic test uses real quality checks, SQLite stores and report
  creation to finish a synthetic calendar month and final report. Reopening the
  store does not duplicate or change those reports. It does not wait a real month.
- Browser upload, preview, role mapping and confirmation imported two role intervals,
  one profile and one archived report. Both pre-import stores were backed up.
  A separate future-dated fixture was refused because it overlapped native collection.
  Discarding that staged fixture worked. No household data were uploaded.
- A new frozen report was created through the UI alongside the archived report.
- A 390 × 844 viewport displayed study state and controls without clipping.
- Five real-HA phases passed: fresh collection 7/13 samples; migrated 6/12/18,
  including paired-store restoration. Final browser corrections affect only the card.
- All 207 Python tests, card behavior tests, Ruff and official hassfest passed.
- Reloading the browser retained the entered import price, subscription, EV counter
  settings and dated regional reference, including explicit unknown tariff fields.

## Corrections from the browser test

Saving a form now applies the returned profile/study state immediately, even if
another retained draft prevents the background refresh. Timer refresh no longer
replaces open configuration controls. Card behavior tests cover both conditions.

## Limits

This verifies the exercised integration workflows, not every optional source
combination, a physical mobile app, or a full HAOS restore. Configuration is still
technical in places (ISO timestamps, tariff units). The one-month report test is
deterministic simulation, not measured household parity.

Regional reference totals are not an amount payable: opening credit, carry-forward,
payouts and invoice reconciliation remain open. The calendar is explicitly 2026.
Production replacement still requires a reference bill, agreed block powers,
complete study/regional reconciliation, a fresh full backup and controlled rollback.
Merge and HACS download evidence must be recorded separately after they happen.
