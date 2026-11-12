"""Synthetic append-only history import and all-or-nothing refusal."""

from contextlib import closing
from datetime import datetime
import json
import sqlite3
import unittest
from zoneinfo import ZoneInfo

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.application import ApplicationStore
from energy_cost_monitor.history_import import inspect_legacy, import_history
from energy_cost_monitor.sources import parse_config
from energy_cost_monitor.study import Study, add_months
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

    def legacy_study(self):
        first = datetime(2026, 1, 31, tzinfo=ZoneInfo("Europe/Ljubljana"))
        windows = [int(add_months(first, n).timestamp()) for n in range(4)]
        with closing(sqlite3.connect(self.old)) as db, db:
            db.execute("INSERT INTO meta VALUES('study',?)", (json.dumps({
                "start": windows[0], "end": windows[-1], "windows": windows,
                "validated_at": windows[0] - 3600,
            }),))
            db.execute("INSERT INTO reports VALUES(?,?,?,?,?)", (
                "month-1", *windows[:2], windows[1], json.dumps({"csv": "invented\n1"})
            ))
        return windows

    def test_study_continues_original_schedule_and_reuses_archived_report(self):
        windows = self.legacy_study()
        self.assertTrue(inspect_legacy(self.old)["study_available"])
        engine, store = self.prepare()
        result = self.run_import(engine, store, resume_study=True)
        self.assertTrue(result["study_resumed"])
        reopened = ApplicationStore(store.path)
        study = Study(reopened)
        state = study.status()
        self.assertEqual(state["windows"], windows)
        archived = state["reports"]["month-1"]
        self.assertEqual(reopened.report(archived)["kind"], "legacy_frozen")
        self.assertEqual(study.advance(engine, windows[2] - 1), state)
        second = study.advance(engine, windows[2])
        self.assertEqual(second["reports"]["month-1"], archived)
        report = reopened.report(second["reports"]["month-2"])
        self.assertEqual((report["start"], report["end"]), tuple(windows[1:3]))
        self.assertEqual(Study(ApplicationStore(store.path)).advance(engine, windows[2]), second)

    def test_resuming_legacy_study_does_not_overwrite_current_study(self):
        self.legacy_study()
        engine, store = self.prepare()
        Study(store).save({"state": "cancelled", "reports": {}})
        before = engine.path.read_bytes(), store.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "study_already_configured"):
            self.run_import(engine, store, resume_study=True)
        self.assertEqual(before, (engine.path.read_bytes(), store.path.read_bytes()))
