# Configuration-only continuation — 28 October 2026

Local, unpublished work on `feature/configuration-only-workflows`, based on
merged PR #10. This is not a production-readiness statement.

## Implemented locally

- Optional bounded counter-delta EV sessions with configurable gap, physical power,
  charging and tolerance thresholds, mode changes and mode-level totals.
  This does not change the interval ledger or control a charger.
- Optional read-only EV context and daily-reference source roles.
- Versioned regional reference settings for the Slovenian 2026 calendar: energy,
  agreed power, excess-power mode, levies and VAT. Missing or unconfirmed inputs
  prevent a complete total. No household rates are built into the code.
- Persistent study warm-up and daily cross-check, calendar-month windows and frozen
  monthly/final reports. Background failures are exposed through the admin API.
- Initial EV/regional/study forms and automatic admin sidebar-panel registration.
- Pricing forms for multiple offers, contract versions, import/export periods,
  subscription, provenance and optional reference-index import binding.
- Guided legacy SQLite upload/preview, explicit role mapping, profile selection
  and confirmation. Import is restricted to history preceding native collection.
  Both stores are backed up and updated in one SQLite rollback-journal transaction.
  Uploaded copies can be resumed or discarded; the original user file is untouched.

The supply comparison and regional estimate are separate outputs. A regional total
is not an invoice or an amount payable. Opening monetary credit, carry-forward,
payouts, rounding against a supplier invoice and actual activation dates still need
explicit treatment and verification. Connection power must not be substituted for
agreed billing power. No tariff or calendar is silently carried into 2027.

## Verification and remaining gates

The local suite passed 204 tests after guided import was added. A subsequent
stop-event regression verifies that HA's already-fired one-shot listener is not
removed twice. Ruff and card behavior tests pass. Import tests verify preservation,
overlap refusal, changed-file refusal and rollback of both stores after a forced
failure following ledger writes.

Real HA 2026.10.2 passed all five phases with panel/study and actual authenticated
file upload, preview and import: fresh 7/13 samples, migrated 6/12/18 including
paired-store restore. Hassfest reported one integration, zero invalid. These runs
precede the final upload-resume and one-shot-stop corrections; those changes need
another real-HA pass before publication.

An isolated copy of the existing synthetic UI lab displayed the automatic panel,
saved a revised pricing profile through forms and started the study. The browser
file-upload permission was declined; no browser upload or final end-to-end import
through the UI is claimed. The prior headless API proof is separate. The test
container and local tunnel were stopped, retaining the synthetic configuration.

Still required: final real-HA regression, browser/mobile and clean
configuration-only setup, browser import acceptance and guided recovery,
full regional/report reconciliation and user-specific invoice validation performed
outside the public repository. CSV currently exports energy and supply rows; HTML
also preserves configured regional evidence in its frozen data section.

Personal contracts, bills, photographs, meter identifiers, configuration and private
comparison outputs must remain outside this repository. Public tests use synthetic
values. Installing through HACS does not by itself satisfy these remaining gates.
