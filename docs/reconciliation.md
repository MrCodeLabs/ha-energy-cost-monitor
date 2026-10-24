# Reconciliation with the legacy application

Development scope, 24 October 2026. Offline export only; no automatic activation.

```sh
python -m energy_cost_monitor.reconciliation RECOVERY.zip COMPATIBLE.sqlite3 \
  --config sources.local.json --resume-at UTC_EPOCH_SECONDS \
  --signal-mapping signals.local.json
```

First stop/drain the new writer and create a verified recovery bundle. The bundle
remains the authoritative record of both eras. Choose a fresh destination and an
aligned resume boundary strictly after the last captured sample and at or after
the end of every allocated interval. Do not resume the old collector before this
boundary. An already running new writer must not continue after the final bundle.

The cumulative-role mapping comes from the migration manifest and must be
one-to-one for this reverse export. Optional non-cumulative roles require an
explicit mapping to legacy field names. For example, `ev_connected` can map to
`plug`, `ev_power` to `ev_w`, and `battery_soc` to `soc`. Supply all configured
non-cumulative roles; omit `--signal-mapping` only if none exist. Canonical power
is converted from kW to W, binary values to on/off, energy stays kWh. Invalid
readings remain null. Daily estimates are snapshots, never counter deltas.

## Preserved and reconstructed evidence

- Original profiles, prices, frozen reports, samples and historical intervals
  remain unchanged. Original open sessions are closed at cutover as partial,
  explicitly marked as a boundary rather than an observed disconnect; their
  originals remain untouched in the recovery bundle.
- New energy/coverage intervals are copied as allocated, with a report-time flag.
  They are never recomputed by feeding counters through the old calculation.
- New normalized snapshots and unassigned anomaly evidence are exported. No
  rejected counter jump is promoted into interval energy.
- An explicit empty resume-barrier sample and cleared old meter baselines prevent
  the first resumed real sample from bridging to a different accounting regime.
  This creates a visible unmeasured transition, not an invented delta.
- EV connections can be reconstructed when EV energy and connection snapshots
  exist. Unknown connection state does not disconnect a session; gaps and
  unfinished sessions are partial. Charging/pause durations use sampled power
  and are estimates. Only ledger intervals fully inside a session contribute
  energy. Edge intervals are excluded and flagged, so two short sessions cannot
  both receive the same energy. No usable interval means null/unknown energy.

## Tested boundary and remaining work

155 synthetic tests pass on Windows/Python 3.12.14 and Linux/Python 3.14. The
actual legacy Python engine was separately loaded against an invented database
and profile: it read transferred native intervals and resumed ingestion without
bridging a counter jump. That local-only harness and private legacy code are not
shipped in the public repository. The real HA lab passed all five phases with
this revision, including restore/restart (6/12/18 migrated samples).

A regression test also covers sensor reports timestamped before migration: these
are now recorded as anomalies and cannot seed a baseline that changes historical
intervals.

This is not full application parity. Live session UI/events/modes, signal
integrals, price fetching/backfill, new frozen reports, regional bill validation,
profile workflows and the authenticated API/card remain separate work. Existing
frozen reports are not rewritten; missing new reports are not invented. Legacy
presentation may not understand every new provenance/unknown flag. Metadata
therefore explicitly records `full_application_parity: false`. Do not use this
export as proof that a production rollback or whole-HA restore is complete.

## Slovenščina

Ukaz uskladi novo izračunane intervale s staro obliko zbirke in ohrani obnovitveni
paket. Prvi vzorec po vrnitvi ne premosti števcev med različnima načinoma zajema.
Dopolnjena je rekonstrukcija EV sej s premori, vrzelmi in neznano energijo. Izvoz
je preverjen s starim jedrom na izmišljenih podatkih; produkcija ni spremenjena.
Celotna funkcionalna zamenjava, uporabniški prikaz in poročila še niso dokončani.
