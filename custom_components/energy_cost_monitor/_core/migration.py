"""Explicit offline migration of a legacy snapshot; never modify the source.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
Legacy records retain their original bodies and collection-time semantics.
"""

from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
import zipfile

from .accounting import AccountingEngine, INTERVAL_SECONDS, MIGRATED_SCHEMA_VERSION, _timestamp


TABLES = {
    "meta": "key TEXT PRIMARY KEY, value TEXT NOT NULL",
    "profiles": "hash TEXT PRIMARY KEY, captured REAL, body TEXT",
    "samples": "ts REAL PRIMARY KEY, body TEXT NOT NULL",
    "intervals": "ts INTEGER PRIMARY KEY, body TEXT NOT NULL",
    "anomalies": "id INTEGER PRIMARY KEY, ts REAL, metric TEXT, reason TEXT, kwh REAL",
    "price_fetches": "id INTEGER PRIMARY KEY, captured REAL, body TEXT NOT NULL",
    "prices": "ts INTEGER PRIMARY KEY, duration INTEGER, eur_kwh REAL, captured REAL",
    "sessions": "id INTEGER PRIMARY KEY, start REAL, end REAL, body TEXT NOT NULL",
    "reports": "id TEXT PRIMARY KEY, start REAL, end REAL, generated REAL, body TEXT",
}


def _ro(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA trusted_schema=OFF")
    return db


def _validate_legacy(db):
    objects = db.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    tables = {name for kind, name in objects if kind == "table"}
    if tables != set(TABLES) or any(kind not in {"table", "index"} for kind, _ in objects):
        raise ValueError("unsupported_legacy_schema")
    for name, definition in TABLES.items():
        expected = [part.strip().split()[0] for part in definition.split(",")]
        actual = [r[1] for r in db.execute(f'PRAGMA table_info("{name}")')]
        if actual != expected:
            raise ValueError("unsupported_legacy_columns")
    if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("legacy_integrity_failure")


def _copy_table(source, target, name, *, prefix=""):
    definition = TABLES[name]
    target.execute(f'CREATE TABLE "{prefix}{name}"({definition})')
    columns = len(definition.split(","))
    digest = hashlib.sha256()
    count = 0
    for row in source.execute(f'SELECT * FROM "{name}" ORDER BY rowid'):
        # Legacy columns are text/numbers, not executable schema or pickles.
        encoded = json.dumps(row, ensure_ascii=False, allow_nan=False).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        target.execute(f'INSERT INTO "{prefix}{name}" VALUES({",".join("?" for _ in range(columns))})', row)
        count += 1
    return {"rows": count, "sha256": digest.hexdigest()}


def _publish(path, destination):
    path.chmod(0o600)
    with path.open("r+b") as file:
        os.fsync(file.fileno())
    # Atomic no-clobber publication on the same filesystem (including NTFS).
    os.link(path, destination)


def migrate_legacy(source, destination, config, *, role_mapping, cutover, max_gap_seconds=300):
    """Import mapped closed intervals and preserve every original row separately.

    Requires an offline consistent snapshot and an aligned cutover after all old
    samples/intervals. No automatic HA activation, profile reinterpretation or
    recomputation of old intervals occurs. Source configuration is explicit.
    """
    source, destination = Path(source).resolve(), Path(destination).absolute()
    cutover = _timestamp(cutover)
    if cutover % INTERVAL_SECONDS:
        raise ValueError("unaligned_cutover")
    if set(role_mapping) != set(config.required_roles) or any(
        not isinstance(metric, str) or not metric for metric in role_mapping.values()
    ):
        raise ValueError("explicit_mapping_required_for_every_role")
    if destination.exists() or source == destination:
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(_ro(source)) as old, tempfile.TemporaryDirectory(
        prefix="ecm-migrate-", dir=destination.parent
    ) as temporary:
        old.execute("BEGIN")
        _validate_legacy(old)
        latest = old.execute("SELECT MAX(ts) FROM samples").fetchone()[0]
        last_interval = old.execute("SELECT MAX(ts) FROM intervals").fetchone()[0]
        if (latest is not None and _timestamp(latest) >= cutover) or (
            last_interval is not None and _timestamp(last_interval) + INTERVAL_SECONDS > cutover
        ):
            raise ValueError("cutover_overlaps_legacy_history")
        path = Path(temporary) / "ledger.sqlite3"
        AccountingEngine(path, config, max_gap_seconds=max_gap_seconds, sampling_mode="report")
        with closing(sqlite3.connect(path)) as target, target:
            evidence = {name: _copy_table(old, target, name, prefix="legacy_") for name in TABLES}
            converted = 0
            for ts, body in old.execute("SELECT ts,body FROM intervals ORDER BY ts"):
                if _timestamp(ts) % INTERVAL_SECONDS:
                    raise ValueError("unaligned_legacy_interval")
                record = json.loads(body)
                energy, seconds = record["energy"], record["seconds"]
                if not isinstance(energy, dict) or not isinstance(seconds, dict):
                    raise ValueError("invalid_legacy_interval")
                for role, metric in role_mapping.items():
                    value, coverage = energy.get(metric), seconds.get(metric)
                    if value is None and coverage is None:
                        continue  # Missing remains absent, never zero.
                    if (type(value) not in (float, int) or type(coverage) not in (float, int)
                            or not math.isfinite(value) or not math.isfinite(coverage)
                            or value < 0 or not 0 < coverage <= INTERVAL_SECONDS):
                        raise ValueError("invalid_legacy_coverage")
                    target.execute("INSERT INTO intervals VALUES(?,?,?,?)", (ts, role, value, coverage))
                    converted += 1
            manifest = {"version": 1, "cutover": cutover, "role_mapping": role_mapping,
                        "tables": evidence, "converted_role_intervals": converted,
                        "historical_semantics": "legacy_collection_time"}
            target.execute("INSERT INTO meta VALUES('migration',?)", (json.dumps(manifest, sort_keys=True),))
            target.execute("INSERT INTO meta VALUES('collection_not_before',?)", (str(cutover),))
            target.execute(f"PRAGMA user_version={MIGRATED_SCHEMA_VERSION}")
        _publish(path, destination)

        return manifest



def snapshot(source, destination):
    """Consistent no-clobber SQLite backup; source is opened read-only."""
    destination = Path(destination).absolute()
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(_ro(source)) as original, tempfile.TemporaryDirectory(
        prefix="ecm-backup-", dir=destination.parent
    ) as temporary:
        path = Path(temporary) / "snapshot.sqlite3"
        with closing(sqlite3.connect(path)) as target:
            original.backup(target)
            if target.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("backup_integrity_failure")
        _publish(path, destination)


def export_legacy(source, destination):
    """Export original records for rollback rehearsal; new ledger is retained.

    This does not translate post-cutover data into the old application's format.
    Keep the migrated ledger/backup alongside this export to avoid losing them.
    """
    destination = Path(destination).absolute()
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(_ro(source)) as original, tempfile.TemporaryDirectory(
        prefix="ecm-export-", dir=destination.parent
    ) as temporary:
        original.execute("BEGIN")
        manifest_row = original.execute("SELECT value FROM meta WHERE key='migration'").fetchone()
        if manifest_row is None or json.loads(manifest_row[0])["version"] != 1:
            raise ValueError("unsupported_migration_archive")
        manifest = json.loads(manifest_row[0])
        path = Path(temporary) / "legacy.sqlite3"
        with closing(sqlite3.connect(path)) as target, target:
            for name, definition in TABLES.items():
                target.execute(f'CREATE TABLE "{name}"({definition})')
                digest, count = hashlib.sha256(), 0
                for row in original.execute(f'SELECT * FROM "legacy_{name}" ORDER BY rowid'):
                    encoded = json.dumps(row, ensure_ascii=False, allow_nan=False).encode("utf-8")
                    digest.update(len(encoded).to_bytes(8, "big"))
                    digest.update(encoded)
                    target.execute(f'INSERT INTO "{name}" VALUES({",".join("?" for _ in definition.split(","))})', row)
                    count += 1
                if {"rows": count, "sha256": digest.hexdigest()} != manifest["tables"][name]:
                    raise ValueError("legacy_archive_changed")
            _validate_legacy(target)
        _publish(path, destination)


def recovery_bundle(source, destination, config, *, max_gap_seconds=300):
    """Freeze both eras and verify historical mapping before publishing a ZIP.

    This is a data recovery artifact, not activation of the old application.
    All comparisons use a single SQLite snapshot even if collection continues.
    """
    destination = Path(destination).absolute()
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ecm-recovery-", dir=destination.parent) as temporary:
        work = Path(temporary)
        current, legacy, expected = (work / name for name in
                                     ("ledger.sqlite3", "legacy.sqlite3", "expected.sqlite3"))
        snapshot(source, current)
        AccountingEngine(current, config, max_gap_seconds=max_gap_seconds, sampling_mode="report")
        export_legacy(current, legacy)
        with closing(_ro(current)) as db:
            manifest = json.loads(db.execute("SELECT value FROM meta WHERE key='migration'").fetchone()[0])
            cutover = manifest["cutover"]
            migrate_legacy(legacy, expected, config, role_mapping=manifest["role_mapping"],
                           cutover=cutover, max_gap_seconds=max_gap_seconds)
            # Independently rebuild the mapping from the verified legacy archive.
            # Exact row comparison detects loss, extra rows, changed energy and
            # changed coverage; totals alone could conceal compensating errors.
            compared = 0
            with (closing(_ro(expected)) as baseline,
                  closing(db.execute("SELECT * FROM intervals WHERE start < ? ORDER BY start,role",
                                     (cutover,))) as actual,
                  closing(baseline.execute("SELECT * FROM intervals ORDER BY start,role")) as expected_rows):
                for row in expected_rows:
                    if next(actual, None) != row:
                        raise ValueError("historical_intervals_changed")
                    compared += 1
                if next(actual, None) is not None:
                    raise ValueError("historical_intervals_changed")
            if db.execute("SELECT 1 FROM samples WHERE ts < ? LIMIT 1", (cutover,)).fetchone():
                raise ValueError("native_samples_overlap_history")
            report = {
                "version": 1, "cutover": cutover,
                "historical_role_intervals_verified": compared,
                "native_samples": db.execute("SELECT COUNT(*) FROM samples").fetchone()[0],
                "latest_native_sample": db.execute("SELECT MAX(ts) FROM samples").fetchone()[0],
                "native_role_intervals": db.execute(
                    "SELECT COUNT(*) FROM intervals WHERE start >= ?", (cutover,)).fetchone()[0],
                "application_rollback_ready": False,
                "post_cutover_policy": "retained_in_ledger_not_replayed_into_legacy",
                "files": {},
            }
        for path in (current, legacy):
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            report["files"][path.name] = {"sha256": digest, "bytes": path.stat().st_size}
        archive = work / "recovery.zip"
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as output:
            for path in (current, legacy):
                output.write(path, path.name)
            output.writestr("manifest.json", json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
        # CRC verification catches a broken artifact before no-clobber publication.
        with zipfile.ZipFile(archive) as check:
            if check.testzip() is not None:
                raise ValueError("recovery_archive_corrupt")
        _publish(archive, destination)
        return report


def restore_bundle(source, destination, config, *, max_gap_seconds=300):
    """Verify a recovery artifact and restore the new ledger to a fresh path.

    Never extract archive paths or overwrite a database. The legacy database
    stays in the original bundle; this does not activate either application.
    """
    destination = Path(destination).absolute()
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ecm-restore-", dir=destination.parent) as temporary:
        work = Path(temporary)
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            if len(names) != 3 or set(names) != {"ledger.sqlite3", "legacy.sqlite3", "manifest.json"}:
                raise ValueError("unsupported_recovery_members")
            if archive.getinfo("manifest.json").file_size > 1024 * 1024:
                raise ValueError("oversized_recovery_manifest")
            report = json.loads(archive.read("manifest.json"))
            if (not isinstance(report, dict) or report.get("version") != 1
                    or not isinstance(report.get("files"), dict)
                    or set(report["files"]) != {"ledger.sqlite3", "legacy.sqlite3"}):
                raise ValueError("unsupported_recovery_manifest")
            for name in ("ledger.sqlite3", "legacy.sqlite3"):
                info = report["files"][name]
                if (not isinstance(info, dict) or type(info.get("bytes")) is not int
                        or info["bytes"] != archive.getinfo(name).file_size
                        or not isinstance(info.get("sha256"), str)):
                    raise ValueError("invalid_recovery_file_metadata")
                digest = hashlib.sha256()
                with archive.open(name) as incoming, (work / name).open("xb") as output:
                    while chunk := incoming.read(1024 * 1024):
                        digest.update(chunk)
                        output.write(chunk)
                if digest.hexdigest() != info["sha256"]:
                    raise ValueError("recovery_checksum_mismatch")
        # Revalidate actual database identity, original-row digests and mapped
        # historical intervals rather than trusting the ZIP's summary fields.
        verified = recovery_bundle(work / "ledger.sqlite3", work / "verified.zip", config,
                                   max_gap_seconds=max_gap_seconds)
        if {key: value for key, value in report.items() if key != "files"} != {
            key: value for key, value in verified.items() if key != "files"
        }:
            raise ValueError("recovery_manifest_mismatch")
        exported = work / "verified-legacy.sqlite3"
        export_legacy(work / "ledger.sqlite3", exported)
        with closing(_ro(work / "legacy.sqlite3")) as supplied, closing(_ro(exported)) as expected:
            _validate_legacy(supplied)
            for name in TABLES:
                with (closing(supplied.execute(f'SELECT * FROM "{name}" ORDER BY rowid')) as actual_rows,
                      closing(expected.execute(f'SELECT * FROM "{name}" ORDER BY rowid')) as expected_rows):
                    for row in expected_rows:
                        if next(actual_rows, None) != row:
                            raise ValueError("recovery_legacy_mismatch")
                    if next(actual_rows, None) is not None:
                        raise ValueError("recovery_legacy_mismatch")
        _publish(work / "ledger.sqlite3", destination)
        return report


def main():
    """Explicit offline operator interface; never infer a production path."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["migrate", "snapshot", "export-legacy", "recovery-bundle",
                                             "restore-bundle"])
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--cutover", type=float, help="Aligned UTC epoch seconds after all source data")
    parser.add_argument("--max-gap-seconds", type=float, default=300)
    args = parser.parse_args()
    if args.operation == "migrate":
        if args.config is None or args.mapping is None or args.cutover is None:
            parser.error("migrate requires --config, --mapping and --cutover")
        from .sources import parse_config
        config = parse_config(json.loads(args.config.read_text(encoding="utf-8")))
        mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
        migrate_legacy(args.source, args.destination, config, role_mapping=mapping,
                       cutover=args.cutover, max_gap_seconds=args.max_gap_seconds)
    elif args.operation in {"recovery-bundle", "restore-bundle"}:
        if args.config is None:
            parser.error(f"{args.operation} requires --config")
        from .sources import parse_config
        config = parse_config(json.loads(args.config.read_text(encoding="utf-8")))
        operation = recovery_bundle if args.operation == "recovery-bundle" else restore_bundle
        operation(args.source, args.destination, config, max_gap_seconds=args.max_gap_seconds)
    elif args.operation == "snapshot":
        snapshot(args.source, args.destination)
    else:
        export_legacy(args.source, args.destination)
    print("Completed; source retained. No Home Assistant configuration was changed.")


if __name__ == "__main__":
    main()
