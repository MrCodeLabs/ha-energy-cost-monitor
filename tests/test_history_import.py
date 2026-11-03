"""Synthetic append-only history import and all-or-nothing refusal."""

import sqlite3
import unittest

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.application import ApplicationStore
from energy_cost_monitor.history_import import inspect_legacy, import_history
from energy_cost_monitor.sources import parse_config
from test_accounting import START, configuration, sample
import test_application_migration


class HistoryImportTests(unittest.TestCase):
    setUp = test_application_migration.ApplicationMigrationTests.setUp

    def prepare(self, start=START + 1800):
        config = parse_config(configuration())
        engine = AccountingEngine(self.root / "live.sqlite3", config,
                                  max_gap_seconds=300, sampling_mode="report")
        engine.ingest(start, sample(config, start, 10))
        store = ApplicationStore(self.new)
        return engine, store

    def run_import(self, engine, store, **changes):
        args = dict(expected_sha256=inspect_legacy(self.old)["sha256"],
                    role_mapping={"house": "meter", "import": "meter"},
                    horizon="2027-01-01", active_profile=inspect_legacy(self.old)["profiles"][0], activate=True)
        args.update(changes)
        return import_history(self.old, engine, store, self.root / "backup", **args)

    def test_preserves_native_samples_imports_history_and_reopens(self):
        engine, store = self.prepare()
        result = self.run_import(engine, store)
        self.assertTrue(result["imported"])
        self.assertEqual(self.old.read_bytes(), self.original)
        with engine._db() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM samples").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM legacy_profiles").fetchone()[0], 1)
        AccountingEngine(engine.path, engine.config, max_gap_seconds=300, sampling_mode="report")
        self.assertTrue(store.profiles()["active"])
        self.assertTrue((self.root / "backup/ledger.sqlite3").exists())
        self.assertTrue((self.root / "backup/application.sqlite3").exists())

    def test_overlap_refuses_without_modifying_either_store(self):
        engine, store = self.prepare(START)
        before = engine.path.read_bytes(), store.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.run_import(engine, store)
        self.assertEqual(before, (engine.path.read_bytes(), store.path.read_bytes()))

    def test_failure_after_ledger_writes_rolls_back_both_databases(self):
        engine, store = self.prepare()
        with store.db(True) as db:
            db.execute("CREATE TRIGGER refuse BEFORE INSERT ON profiles BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
        with self.assertRaises(sqlite3.Error):
            self.run_import(engine, store)
        with engine._db() as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertFalse(db.execute("SELECT 1 FROM sqlite_master WHERE name='legacy_profiles'").fetchone())
        self.assertEqual(store.profiles()["versions"], [])

    def test_changed_source_refused_before_backup(self):
        engine, store = self.prepare()
        with self.assertRaises(ValueError):
            self.run_import(engine, store, expected_sha256="0" * 64)
        self.assertFalse((self.root / "backup").exists())
