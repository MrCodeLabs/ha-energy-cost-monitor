"""Offline legacy migration with entirely invented historical evidence."""

from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.migration import (
    TABLES, export_legacy, migrate_legacy, recovery_bundle, restore_bundle, snapshot,
)
from energy_cost_monitor.sources import parse_config
from test_accounting import START, configuration, sample


def create_legacy(path):
    with closing(sqlite3.connect(path)) as db, db:
        for name, definition in TABLES.items():
            db.execute(f'CREATE TABLE "{name}"({definition})')
        db.execute("INSERT INTO meta VALUES('study_start',?)", (str(START),))
        db.execute("INSERT INTO profiles VALUES('synthetic',?,?)", (START, '{"label":"Invented € profile"}'))
        db.execute("INSERT INTO samples VALUES(?,?)", (START + 800, '{"meter":12}'))
        body = json.dumps({"energy": {"meter": 2.5}, "seconds": {"meter": 900}, "flags": []})
        db.execute("INSERT INTO intervals VALUES(?,?)", (START, body))
        db.execute("INSERT INTO anomalies VALUES(1,?,'meter','gap',0.2)", (START,))
        db.execute("INSERT INTO price_fetches VALUES(1,?,'{}')", (START,))
        db.execute("INSERT INTO prices VALUES(?,900,-0.01,?)", (START, START))
        db.execute("INSERT INTO sessions VALUES(1,?,NULL,?)", (START, '{"partial":true}'))
        db.execute("INSERT INTO reports VALUES('invented',?,?,?,?)",
                   (START, START + 900, START + 900, '{"html":"<h1>Frozen €</h1>","csv":"a,b\\n1,2"}'))


def table_rows(path):
    with closing(sqlite3.connect(path)) as db:
        return {name: db.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall() for name in TABLES}


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old, self.new = self.root / "old.sqlite3", self.root / "new.sqlite3"
        self.config = parse_config(configuration())
        self.mapping = {"house": "meter", "import": "meter"}
        create_legacy(self.old)
        self.original_hash = hashlib.sha256(self.old.read_bytes()).hexdigest()

    def migrate(self, **kwargs):
        return migrate_legacy(self.old, self.new, self.config,
                              role_mapping=self.mapping, cutover=START + 900, **kwargs)

    def test_every_row_and_frozen_report_preserved_and_intervals_queryable(self):
        manifest = self.migrate()
        self.assertEqual(manifest["tables"]["reports"]["rows"], 1)
        with closing(sqlite3.connect(self.new)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)
            for name, rows in table_rows(self.old).items():
                self.assertEqual(rows, db.execute(f'SELECT * FROM legacy_{name} ORDER BY rowid').fetchall())
        engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        summary = engine.summary(START, START + 900)
        self.assertEqual(summary.energy_kwh["import"], 2.5)
        self.assertEqual(summary.coverage["import"], 1)
        self.assertEqual(hashlib.sha256(self.old.read_bytes()).hexdigest(), self.original_hash)

    def test_export_after_new_samples_preserves_both_eras(self):
        self.migrate()
        engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        engine.ingest(START + 900, sample(self.config, START + 900, 13))
        engine.ingest(START + 960, sample(self.config, START + 960, 13.01))
        new_hash = hashlib.sha256(self.new.read_bytes()).hexdigest()
        restored = self.root / "legacy-export.sqlite3"
        export_legacy(self.new, restored)
        self.assertEqual(table_rows(self.old), table_rows(restored))
        self.assertEqual(hashlib.sha256(self.new.read_bytes()).hexdigest(), new_hash)
        backup = self.root / "new-era-backup.sqlite3"
        snapshot(self.new, backup)
        recovered = AccountingEngine(backup, self.config, max_gap_seconds=300, sampling_mode="report")
        self.assertEqual(recovered.latest_observations(), engine.latest_observations())
        self.assertEqual(recovered.summary(START, START + 1800), engine.summary(START, START + 1800))

    def test_native_collection_cannot_overwrite_historical_window(self):
        self.migrate()
        engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        before = self.new.read_bytes()
        with self.assertRaisesRegex(ValueError, "cutover"):
            engine.ingest(START + 850, sample(self.config, START + 850, 12))
        self.assertEqual(self.new.read_bytes(), before)

    def test_recovery_bundle_restores_both_eras_after_restart_and_new_measurements(self):
        self.migrate()
        engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        engine.ingest(START + 900, sample(self.config, START + 900, 13))
        engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        engine.ingest(START + 960, sample(self.config, START + 960, 13.01))
        before = self.new.read_bytes()
        output = self.root / "recovery.zip"
        report = recovery_bundle(self.new, output, self.config)
        self.assertEqual(report["historical_role_intervals_verified"], 2)
        self.assertEqual(report["native_samples"], 2)
        self.assertFalse(report["application_rollback_ready"])
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(set(archive.namelist()), {"ledger.sqlite3", "legacy.sqlite3", "manifest.json"})
            self.assertEqual(json.loads(archive.read("manifest.json")), report)
            restored = self.root / "restored"
            restored.mkdir()
            for name in ("ledger.sqlite3", "legacy.sqlite3"):
                data = archive.read(name)
                self.assertEqual(hashlib.sha256(data).hexdigest(), report["files"][name]["sha256"])
                (restored / name).write_bytes(data)
        recovered = AccountingEngine(restored / "ledger.sqlite3", self.config,
                                     max_gap_seconds=300, sampling_mode="report")
        self.assertEqual(recovered.latest_observations(), engine.latest_observations())
        self.assertEqual(recovered.summary(START, START + 1800), engine.summary(START, START + 1800))
        self.assertEqual(table_rows(restored / "legacy.sqlite3"), table_rows(self.old))
        self.assertEqual(self.new.read_bytes(), before)

    def test_recovery_rejects_changed_missing_and_extra_historical_intervals(self):
        self.migrate()
        for sql in ("UPDATE intervals SET kwh=kwh+1",
                    "UPDATE intervals SET seconds=seconds-1", "DELETE FROM intervals",
                    f"INSERT INTO intervals VALUES({START-900},'house',1,900)"):
            with self.subTest(sql=sql):
                changed = self.root / "changed.sqlite3"
                # Each attempt starts from the same independently preserved source.
                changed.write_bytes(self.new.read_bytes())
                with closing(sqlite3.connect(changed)) as db, db:
                    db.execute(sql)
                output = self.root / "bad.zip"
                with self.assertRaisesRegex(ValueError, "historical_intervals_changed"):
                    recovery_bundle(changed, output, self.config)
                self.assertFalse(output.exists())

    def test_recovery_uses_one_snapshot_when_collection_continues(self):
        self.migrate()
        engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        engine.ingest(START + 900, sample(self.config, START + 900, 13))

        def snapshot_then_collect(source, destination):
            snapshot(source, destination)
            engine.ingest(START + 960, sample(self.config, START + 960, 13.01))

        with patch("energy_cost_monitor.migration.snapshot", side_effect=snapshot_then_collect):
            report = recovery_bundle(self.new, self.root / "concurrent.zip", self.config)
        self.assertEqual(report["native_samples"], 1)
        self.assertEqual(report["latest_native_sample"], START + 900)
        with closing(sqlite3.connect(self.new)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM samples").fetchone()[0], 2)

    def test_recovery_cannot_overwrite_existing_artifact(self):
        output = self.root / "existing.zip"
        output.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            recovery_bundle(self.new, output, self.config)
        self.assertEqual(output.read_bytes(), b"keep")

    def test_recovery_rejects_tampered_archive_without_partial_artifact(self):
        self.migrate()
        with closing(sqlite3.connect(self.new)) as db, db:
            db.execute("UPDATE legacy_reports SET body='changed'")
        output = self.root / "tampered.zip"
        with self.assertRaisesRegex(ValueError, "archive_changed"):
            recovery_bundle(self.new, output, self.config)
        self.assertFalse(output.exists())

    def make_bundle(self):
        self.migrate()
        engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        engine.ingest(START + 900, sample(self.config, START + 900, 13))
        engine.ingest(START + 960, sample(self.config, START + 960, 13.01))
        bundle = self.root / "bundle.zip"
        recovery_bundle(self.new, bundle, self.config)
        return bundle, engine

    def rewrite_bundle(self, bundle, change):
        with zipfile.ZipFile(bundle) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        change(entries)
        modified = self.root / "modified.zip"
        with zipfile.ZipFile(modified, "w") as output:
            for name, data in entries.items():
                output.writestr(name, data)
        return modified

    def test_restore_bundle_and_continue_collecting_after_restart(self):
        bundle, engine = self.make_bundle()
        original = bundle.read_bytes()
        output = self.root / "recovered.sqlite3"
        report = restore_bundle(bundle, output, self.config)
        self.assertEqual(report["native_samples"], 2)
        restored = AccountingEngine(output, self.config, max_gap_seconds=300, sampling_mode="report")
        self.assertEqual(restored.summary(START, START + 1800), engine.summary(START, START + 1800))
        for instance in (restored, engine):
            instance.ingest(START + 1020, sample(self.config, START + 1020, 13.02))
        self.assertEqual(restored.summary(START, START + 1800), engine.summary(START, START + 1800))
        self.assertEqual(restored.latest_observations(), engine.latest_observations())
        self.assertEqual(bundle.read_bytes(), original)
        with self.assertRaises(FileExistsError):
            restore_bundle(bundle, output, self.config)

    def test_restore_rejects_database_corruption_even_with_valid_zip_crc(self):
        bundle, _ = self.make_bundle()
        modified = self.rewrite_bundle(bundle, lambda entries: entries.__setitem__(
            "ledger.sqlite3", entries["ledger.sqlite3"][:-1] + b"X"))
        output = self.root / "recovered.sqlite3"
        with self.assertRaisesRegex(ValueError, "checksum_mismatch"):
            restore_bundle(modified, output, self.config)
        self.assertFalse(output.exists())

    def test_restore_rejects_false_manifest_counts(self):
        bundle, _ = self.make_bundle()

        def change(entries):
            report = json.loads(entries["manifest.json"])
            report["native_samples"] = 0
            entries["manifest.json"] = json.dumps(report).encode()

        output = self.root / "recovered.sqlite3"
        with self.assertRaisesRegex(ValueError, "manifest_mismatch"):
            restore_bundle(self.rewrite_bundle(bundle, change), output, self.config)
        self.assertFalse(output.exists())

    def test_restore_rejects_extra_archive_paths(self):
        bundle, _ = self.make_bundle()
        modified = self.rewrite_bundle(bundle, lambda entries: entries.__setitem__("../outside", b"no"))
        output = self.root / "recovered.sqlite3"
        with self.assertRaisesRegex(ValueError, "members"):
            restore_bundle(modified, output, self.config)
        self.assertFalse(output.exists())
        self.assertFalse((self.root / "outside").exists())

    def test_restore_refuses_inconsistent_legacy_even_when_its_checksum_matches(self):
        bundle, _ = self.make_bundle()

        def change(entries):
            legacy = self.root / "different.sqlite3"
            legacy.write_bytes(entries["legacy.sqlite3"])
            with closing(sqlite3.connect(legacy)) as db, db:
                db.execute("UPDATE reports SET body='different'")
            data = legacy.read_bytes()
            entries["legacy.sqlite3"] = data
            report = json.loads(entries["manifest.json"])
            report["files"]["legacy.sqlite3"] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            entries["manifest.json"] = json.dumps(report).encode()

        output = self.root / "recovered.sqlite3"
        with self.assertRaisesRegex(ValueError, "legacy_mismatch"):
            restore_bundle(self.rewrite_bundle(bundle, change), output, self.config)
        self.assertFalse(output.exists())

    def test_restore_refuses_wrong_configuration(self):
        bundle, _ = self.make_bundle()
        output = self.root / "recovered.sqlite3"
        with self.assertRaisesRegex(ValueError, "configuration_mismatch"):
            restore_bundle(bundle, output, self.config, max_gap_seconds=60)
        self.assertFalse(output.exists())

    def test_destination_never_overwritten(self):
        self.new.write_bytes(b"existing user data")
        for operation in (lambda: self.migrate(), lambda: snapshot(self.old, self.new),
                          lambda: export_legacy(self.old, self.new)):
            with self.assertRaises(FileExistsError):
                operation()
            self.assertEqual(self.new.read_bytes(), b"existing user data")

    def test_malformed_interval_leaves_no_partial_output(self):
        with closing(sqlite3.connect(self.old)) as db, db:
            db.execute("UPDATE intervals SET body=?", (json.dumps({"energy": {"meter": 5}, "seconds": {"meter": 901}}),))
        before = self.old.read_bytes()
        with self.assertRaisesRegex(ValueError, "coverage"):
            self.migrate()
        self.assertFalse(self.new.exists())
        self.assertEqual(self.old.read_bytes(), before)

    def test_unknown_schema_rejected_without_execution(self):
        with closing(sqlite3.connect(self.old)) as db, db:
            db.execute("CREATE VIEW surprise AS SELECT * FROM samples")
        with self.assertRaisesRegex(ValueError, "schema"):
            self.migrate()
        self.assertFalse(self.new.exists())

    def test_cutover_must_follow_every_original_sample(self):
        with closing(sqlite3.connect(self.old)) as db, db:
            db.execute("INSERT INTO samples VALUES(?, '{}')", (START + 900,))
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.migrate()
        self.assertFalse(self.new.exists())

    def test_mapping_must_be_explicit_and_complete(self):
        self.mapping.pop("house")
        with self.assertRaisesRegex(ValueError, "mapping"):
            self.migrate()

    def test_tampered_archive_cannot_be_exported_as_verified_rollback(self):
        self.migrate()
        with closing(sqlite3.connect(self.new)) as db, db:
            db.execute("UPDATE legacy_reports SET body='changed'")
        output = self.root / "bad-export.sqlite3"
        with self.assertRaisesRegex(ValueError, "archive_changed"):
            export_legacy(self.new, output)
        self.assertFalse(output.exists())

    def test_missing_cutover_metadata_refuses_opening_migrated_database(self):
        self.migrate()
        with closing(sqlite3.connect(self.new)) as db, db:
            db.execute("DELETE FROM meta WHERE key='collection_not_before'")
        with self.assertRaisesRegex(ValueError, "migration_boundary"):
            AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")

    def test_missing_historical_values_stay_missing(self):
        with closing(sqlite3.connect(self.old)) as db, db:
            db.execute("INSERT INTO intervals VALUES(?,?)", (START - 900, '{"energy":{},"seconds":{}}'))
        self.migrate()
        engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        self.assertEqual(engine.summary(START - 900, START).coverage["import"], 0)


if __name__ == "__main__":
    unittest.main()
