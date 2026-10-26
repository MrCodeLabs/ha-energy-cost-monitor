# Legacy application migration — 26 October 2026

This offline tool creates a **new** application database from a legacy snapshot.
It never writes the source, overwrites an output, activates HA or contacts a price
provider. Use it alongside ledger migration and keep the complete original archive.

```sh
python -m energy_cost_monitor.application_migration private/legacy.sqlite3 \
  private/application.sqlite3 --horizon 2027-01-01 --active-profile ORIGINAL_HASH
```

The date is invented. Choose an exclusive local-date comparison horizon, not an
assumed contract expiry. Select the original profile hash explicitly. Private
`settings.legacy_conversion` maps original profile/report IDs to new IDs.

## Converted data

- Profiles become supply-only versions bounded by the horizon. Local validity
  dates/timezone (including DST), fixed import/export prices and monthly charges
  minus discounts are retained. All quotes remain reference, never confirmed.
- Indexed import **and export** use saved prices plus respective markups. Supported
  bases: `quarter_hour` and `hourly_reference`. Hourly averaging requires a complete
  real UTC hour; gaps remain unknown. Unsupported bases and overlaps fail safely.
- Conversion rounds to 12 decimal places, ROUND_HALF_UP. Original SQLite REAL
  values remain in the ledger archive. No live fetch binding is enabled.
- Old reports appear in the existing list with an archive label. Original JSON
  strings and SHA-256 are retained; CSV is returned verbatim. HTML is a new safe
  wrapper with escaped evidence, **not byte-identical old HTML or recalculation**.
- EV sessions are read from `legacy_sessions`, labeled as archived, preserving
  energy, mode/event fields and durations. Open sessions display a partial boundary
  at cutover and keep their original null end separately. The new session algorithm
  is not asserted to reproduce the old results.

Validation errors publish no destination. Application schema remains version 1,
but older report renderers do not understand converted report bodies: **do not
downgrade code over converted data**. Preserve both current stores and restore the
previous code with its matching paired backup separately; never erase new samples.

## Remaining differences

VAT, network tariffs, levies, study progress/checks and EV modes remain in the
original archive; they are **not equivalent new workflows**. Archived mode fields
do not implement new event capture. Daily heat-pump estimates are not cumulative
meters; old interval rows remain archived rather than silently reinterpreted.

Offline profiles allow 2 MB of historical quotes; HTTP writes remain 256 KB.
Larger imports can be read/activated but cannot be saved through that endpoint.
Future contracts and ongoing indexed prices require separate configuration and
formula validation. Import does not enable a different live averaging formula.

The native coverage rule requires 900 seconds; the prototype accepts 899 seconds.
Preserve energy/seconds exactly and report classification differences. Compare
supply costs on the same complete quarters, never against a gross regional bill.

## Acceptance

1. Snapshot/hash the source; choose the active profile and horizon. Review source
   identities, units and freshness independently before any activation.
2. Migrate both stores to fresh private paths. Compare every original row, energy,
   seconds, price formula and session body against the old engine on closed windows.
3. Freeze a new report; snapshot and restore **both** stores to vacant paths.
   Reopen and compare views, report/CSV and original-row rollback.
4. Resolve regional billing, study and EV-mode gaps before production replacement.

Synthetic tests cover no-clobber/error cleanup, hourly gaps, negative/missing
prices, report escaping/checksums, session cutover and store reopening. Empty
private report tables do not prove nonempty report migration. No full HAOS restore,
new live-price equivalence, production deployment or release is implied.

## Slovenščina

Pretvorba pripravi novo zasebno aplikacijsko zbirko. Prenese dobavne profile in
stare zamrznjene izračune; omrežnine, dajatev, študije in zajema EV načinov še ne
nadomesti. Uporabi isto zaključeno obdobje in izvorno urno/četrturno metodo cen.
Izvirnik ostane ohranjen. Pred aktivacijo preveri dejanske vire, pri obnovi pa obe zbirki.
