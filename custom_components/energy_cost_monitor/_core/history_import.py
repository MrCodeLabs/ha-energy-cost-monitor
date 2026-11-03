"""Explicit legacy-history append with paired backups and one SQLite transaction.

Only closed history preceding native collection is accepted. Existing measurements,
profiles and reports are never overwritten. Callers must pause both live writers.
"""

from contextlib import closing
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import tempfile

from .application import ApplicationStore
from .application_migration import migrate_application
from .migration import TABLES, _ro, _validate_legacy, migrate_legacy, snapshot


def inspect_legacy(path):
    path = Path(path)
    if not 0 < path.stat().st_size <= 100 * 1024 * 1024:
        raise ValueError("unsupported_import_size")
    with closing(_ro(path)) as db:
        _validate_legacy(db)
        metrics = set()
        for (body,) in db.execute("SELECT body FROM intervals"):
            row = json.loads(body)
            for key in row["energy"]:
                if not isinstance(key, str) or not 1 <= len(key) <= 100:
                    raise ValueError("invalid_legacy_metric")
                metrics.add(key)
                if len(metrics) > 100:
                    raise ValueError("too_many_legacy_metrics")
        last_sample = db.execute("SELECT MAX(ts) FROM samples").fetchone()[0]
        last_interval = db.execute("SELECT MAX(ts) FROM intervals").fetchone()[0]
        end = max((last_sample or 0) + 1, (last_interval or 0) + 900)
        if not math.isfinite(end) or end <= 0:
            raise ValueError("invalid_history_boundary")
        profiles = [row[0] for row in db.execute("SELECT hash FROM profiles ORDER BY captured DESC")]
        if not 1 <= len(profiles) <= 100:
            raise ValueError("expected_legacy_profiles")
        counts = {name: db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in TABLES}
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "metrics": sorted(metrics), "profiles": profiles, "counts": counts,
            "cutover": math.ceil(end / 900) * 900}


def import_history(source, engine, store, backup_dir, *, expected_sha256,
                   role_mapping, horizon, active_profile, activate=False):
    """Merge a validated snapshot; attached rollback-journal DBs commit atomically."""
    evidence = inspect_legacy(source)
    if evidence["sha256"] != expected_sha256 or type(activate) is not bool:
        raise ValueError("import_changed_or_invalid")
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    # Preserve a matched pair before any modification, even when validation fails.
    snapshot(engine.path, backup_dir / "ledger.sqlite3")
    snapshot(store.path, backup_dir / "application.sqlite3")
    with tempfile.TemporaryDirectory(prefix="ecm-import-", dir=backup_dir) as temporary:
        ledger, application = Path(temporary) / "ledger.sqlite3", Path(temporary) / "application.sqlite3"
        manifest = migrate_legacy(source, ledger, engine.config, role_mapping=role_mapping,
                                  cutover=evidence["cutover"], max_gap_seconds=engine.max_gap_seconds)
        converted = migrate_application(source, application, horizon=horizon, active_profile=active_profile)
        imported = ApplicationStore(application)
        with imported.db() as check:
            imported_active = imported.active_profile(check)[0]
        with closing(sqlite3.connect(engine.path)) as db:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("ATTACH DATABASE ? AS app", (str(store.path),))
            db.execute("ATTACH DATABASE ? AS incoming", (str(ledger),))
            db.execute("ATTACH DATABASE ? AS incoming_app", (str(application),))
            # Atomic multi-file commit requires on-disk rollback journals, not WAL.
            for schema in ("main", "app"):
                if db.execute(f"PRAGMA {schema}.journal_mode").fetchone()[0] != "delete":
                    raise ValueError("unsupported_import_journal_mode")
                db.execute(f"PRAGMA {schema}.synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("PRAGMA main.user_version").fetchone()[0] != 1:
                    raise ValueError("history_already_imported")
                first_sample = db.execute("SELECT MIN(ts) FROM samples").fetchone()[0]
                first_interval = db.execute("SELECT MIN(start) FROM intervals").fetchone()[0]
                if any(value is not None and value < evidence["cutover"] for value in (first_sample, first_interval)):
                    raise ValueError("history_overlaps_native_collection")
                if db.execute("SELECT 1 FROM app.settings WHERE key='legacy_conversion'").fetchone():
                    raise ValueError("application_history_already_imported")
                for name, definition in TABLES.items():
                    db.execute(f'CREATE TABLE "legacy_{name}"({definition})')
                    db.execute(f'INSERT INTO "legacy_{name}" SELECT * FROM incoming."legacy_{name}"')
                db.execute("INSERT INTO intervals SELECT * FROM incoming.intervals")
                db.execute("INSERT INTO meta SELECT * FROM incoming.meta WHERE key IN ('migration','collection_not_before')")
                for name in ("profiles", "reports"):
                    # Exact hash collisions may be shared; a conflicting body is refused.
                    conflict = db.execute(f"SELECT 1 FROM app.{name} a JOIN incoming_app.{name} b ON a.id=b.id WHERE a.body<>b.body LIMIT 1").fetchone()
                    if conflict:
                        raise ValueError("conflicting_import_content")
                    db.execute(f"INSERT OR IGNORE INTO app.{name} SELECT * FROM incoming_app.{name}")
                db.execute("INSERT INTO app.settings SELECT * FROM incoming_app.settings WHERE key='legacy_conversion'")
                if activate:
                    db.execute("INSERT OR REPLACE INTO app.settings VALUES('active_profile',?)", (imported_active,))
                db.execute("PRAGMA main.user_version=2")
                db.commit()
            except BaseException:
                db.rollback()
                raise
    return {"imported": True, "cutover": evidence["cutover"],
            "converted_role_intervals": manifest["converted_role_intervals"],
            "profiles": len(converted["profiles"]), "reports": len(converted["reports"]),
            "backup": backup_dir.name, "activated": activate}
