# Offline history migration and backup

**24 October 2026:** [legacy reconciliation and EV session reconstruction](reconciliation.md) now provide a separate compatibility export. Original-only `export-legacy` semantics remain unchanged. Full application parity is still open.

Development implementation, 23 October 2026. This is an operator rehearsal tool,
not automatic HA migration or approval to replace an existing installation.

`energy_cost_monitor.migration` accepts a consistent offline snapshot of the
reviewed legacy nine-table SQLite layout. It creates a **new** database and never
modifies or overwrites the source or an existing destination. Unsupported tables,
views/triggers, invalid coverage and overlapping cutover boundaries are refused.
Temporary output is published atomically without clobbering a racing destination;
the filesystem must support hard links. Linux and NTFS are the target filesystems.

Every original row is retained in `legacy_*` tables, including raw JSON bodies,
profiles, prices, sessions and frozen reports. A versioned migration manifest
records per-table row counts and SHA256 digests. Explicit role mapping converts
stored energy/coverage intervals without recalculating them. Legacy allocation
semantics remain distinct from subsequent report-time collection. Daily estimates
are preserved in the archive and are not silently promoted to cumulative meters.

The UTC cutover must be quarter-hour aligned and later than all original samples
and at least the end of the last stored interval. The new collector rejects
earlier samples and begins with no meter baselines, preserving the transition gap.
Migrated databases use schema 2 so the earlier schema-1-only adapter refuses them.
Unmigrated native ledgers remain schema 1 and are still supported.

## Rehearsal commands

Run from a development checkout, with all input/output files outside Git. Supply
your own reviewed source configuration and a mapping JSON such as
`{"house":"house","import":"import"}`; do not infer household entities.

```sh
python -m energy_cost_monitor.migration snapshot ORIGINAL.sqlite3 SNAPSHOT.sqlite3
python -m energy_cost_monitor.migration migrate SNAPSHOT.sqlite3 NEW.sqlite3 \
  --config sources.local.json --mapping mapping.local.json --cutover UTC_EPOCH_SECONDS
python -m energy_cost_monitor.migration snapshot NEW.sqlite3 NEW-ERA-BACKUP.sqlite3
python -m energy_cost_monitor.migration export-legacy NEW.sqlite3 LEGACY-EXPORT.sqlite3
```

Choose fresh output paths. Before any activation, compare every archive row,
mapped interval, energy total, coverage and frozen report with the snapshot.
Do not upload a snapshot, mapping, profile, SQL dump or CLI error containing a
private path to a public issue.

`export-legacy` verifies archive digests and recreates the original logical rows.
It is **not** an application downgrade that replays new samples into the old
format. Preserve the new ledger and its backup alongside the legacy export.
New-era data remains readable by the new engine. Full old-application continuity
and automatic reconciliation remain a production replacement gate.

## Verified recovery bundle

Before a rollback rehearsal, create one artifact from a consistent snapshot:

```sh
python -m energy_cost_monitor.migration recovery-bundle NEW.sqlite3 RECOVERY.zip \
  --config sources.local.json --max-gap-seconds 300
```

Use the same source configuration and gap policy as the migrated ledger. This
command validates storage identity, verifies every archived table, independently
rebuilds the historical mapping and compares every historical role/interval row
including energy and covered seconds. Missing, changed or extra historical rows
abort publication. All comparisons and both exported databases come from the
same snapshot, even when collection continues on the source.

The ZIP contains `ledger.sqlite3` (both eras), `legacy.sqlite3` (original rows)
and `manifest.json` (SHA256/length per database, cutover, sample/interval counts,
last captured sample, and `application_rollback_ready: false`). Existing output
is never replaced. The archive contains private data, is not encrypted and must
stay in a private backup location; ZIP files are ignored by Git as a precaution.
Checksums detect accidental changes; they are not an authenticity signature.

For an isolated recovery rehearsal, restore to a **new** private database path:

```sh
python -m energy_cost_monitor.migration restore-bundle RECOVERY.zip RESTORED.sqlite3 \
  --config sources.local.json --max-gap-seconds 300
```

The command accepts exactly the three documented archive members, validates
file sizes/checksums, revalidates database identity and historical mapping, and
compares the supplied legacy export with the ledger archive. Summary fields must
match the database contents. No archive paths are extracted. Only after all checks
pass is the recovered ledger published without overwriting any existing file.
The original bundle and its legacy export remain intact. Restore needs temporary
disk space for several database copies and a verification ZIP.

Open the restored ledger with the same configuration and compare its observations
and interval summaries with the frozen snapshot. Restore the legacy export only
in an isolated legacy test environment.
Never activate a second production collector as part of this check. New records
after the snapshot are not part of the artifact: pause/drain the writer before
the final cutover snapshot. Keep the original source until recovery is verified.

The bundle preserves post-cutover data without converting its report-time
semantics into legacy collection-time records. Old-application replay and full
workflow parity remain open. It must not be described as a completed production
rollback. Synthetic tests exercise restart/new measurements, recovery of both
eras, concurrent collection, changed/deleted/extra historical rows, tampered
archives and an existing output file.

## Home Assistant backup

The backup platform pauses new collection and drains any in-flight write before
HA copies configuration. Setup/reload cannot open another writer while the backup
lock is held; unfinished setup makes the backup fail for retry. The post-backup
hook resumes collection and breaks continuity across the pause. SQLite connections
are closed per operation. Offline `snapshot` additionally supports SQLite's
consistent backup API while a source is open elsewhere.

These mechanisms do not establish successful restore of a full HAOS/Supervisor
backup or retention/remote-copy guarantees. Existing sessions/profiles/reports
are preserved as evidence; their new live workflows are separate development.

## Slovenščina

Migracija dela na kopiji v novo datoteko. Ohrani vse izvirne vrstice in preslika
izrecno izbrane energijske intervale. Povratni izvoz preveri kontrolne vsote in
obnovi prvotne logične vrstice; novih meritev ne pretvori nazaj v staro aplikacijo.
Zato ohrani tudi novo zbirko in njeno kopijo. To še ni popoln produkcijski povratek.
HA backup hook začasno ustavi pisca in po kopiji ohrani vrzel kot nepopolne podatke.

Dopolnitev 23. 10. 2026: `recovery-bundle` iz ene konsistentne kopije pripravi obe zbirki in kontrolne vsote ter primerja vse zgodovinske intervale. Paket je zaseben in nešifriran. Nove meritve ohrani v novi zbirki; ne prenese jih v izvajanje stare aplikacije.

Preverjeno 24. 10. 2026: `restore-bundle` obnovi novo zbirko šele po preverjanju vsebine paketa in zgodovinskih intervalov. Pravi HA se iz obnovljene zbirke ponovno zažene in nadaljuje zajem (12 → 18 sintetičnih vzorcev). To ne potrjuje obnove celotnega HAOS ali izvajanja stare aplikacije z novimi meritvami.
