"""Entirely invented legacy profile/report conversion and read-only comparison."""

from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from energy_cost_monitor.application import ApplicationStore, render_report
from energy_cost_monitor.application_migration import convert_profile, migrate_application
from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.migration import migrate_legacy, snapshot
from energy_cost_monitor.sources import parse_config
from test_accounting import START, configuration
from test_migration import create_legacy


def legacy_profile():
    version = {"from": "2020-01-01", "until": None, "import_net": .20, "export_net": .05,
               "monthly_net": 3, "discount_net": 1, "source": "Invented tariff"}
    indexed = {k: v for k, v in version.items() if k not in {"import_net", "export_net"}}
    indexed.update(import_markup_net=.02, export_markup_net=-.01)
    return {"schema_version": 1, "timezone": "Europe/Ljubljana", "retention_days": 400,
            "suppliers": {"fixed": [version], "indexed": [indexed]}, "market": {"basis": "quarter_hour"},
            "vat": [{"rate": .22}], "network": [], "site": [], "levies": []}


class ApplicationMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old, self.new = self.root / "old.sqlite3", self.root / "app.sqlite3"
        create_legacy(self.old)
        with closing(sqlite3.connect(self.old)) as db, db:
            db.execute("UPDATE profiles SET body=?", (json.dumps(legacy_profile()),))
            db.execute("UPDATE sessions SET body=?", (json.dumps({"kwh": 2.5, "partial": False,
                       "charging_seconds": 100, "pause_seconds": 20, "events": []}),))
        self.original = self.old.read_bytes()

    def convert(self):
        return migrate_application(self.old, self.new, horizon="2030-01-01", active_profile="synthetic")

    def test_conversion_prices_report_sessions_and_restore(self):
        evidence = self.convert()
        app = ApplicationStore(self.new)
        profile = app.profiles()["versions"][0]["profile"]
        fixed, indexed = [s["versions"][0] for s in profile["scenarios"]]
        self.assertEqual(fixed["import"][0]["value"], "0.2")
        self.assertEqual(fixed["subscription"]["value"], "2")
        self.assertEqual(indexed["import"][0]["value"], "0.01")
        self.assertEqual(indexed["export"][0]["value"], "-0.02")
        self.assertTrue(fixed["from"].endswith("+01:00"))
        self.assertEqual(profile["indexed_import"], {})
        report = app.report(evidence["reports"]["invented"])
        self.assertEqual(render_report(report, "csv"), "a,b\n1,2")
        self.assertIn("&lt;h1&gt;Frozen", render_report(report, "html"))
        self.assertNotIn("<h1>Frozen", render_report(report, "html"))
        self.assertTrue(app.reports()[0]["legacy"])
        config = parse_config(configuration())
        ledger = self.root / "ledger.sqlite3"
        migrate_legacy(self.old, ledger, config, role_mapping={"house": "meter", "import": "meter"}, cutover=START+900)
        engine = AccountingEngine(ledger, config, sampling_mode="report", max_gap_seconds=300)
        view = app.view(engine, START, START+900, now=START+900)
        self.assertEqual(view["sessions"][0]["body"]["kwh"], 2.5)
        self.assertTrue(view["sessions"][0]["legacy"])
        self.assertTrue(view["sessions"][0]["body"]["partial"])
        self.assertIsNone(view["sessions"][0]["original_end"])
        self.assertEqual(view["sessions"][0]["end"], START+900)
        self.assertEqual(app.view(engine, START+900, START+1800, now=START+1800)["sessions"], [])
        snapshot(self.new, self.root / "restored-app.sqlite3")
        restored = ApplicationStore(self.root / "restored-app.sqlite3")
        self.assertEqual(restored.profiles(), app.profiles())
        self.assertEqual(restored.report(evidence["reports"]["invented"]), report)
        self.assertEqual(self.old.read_bytes(), self.original)

    def test_existing_destination_is_never_overwritten(self):
        self.convert()
        before = self.new.read_bytes()
        with self.assertRaises(FileExistsError):
            self.convert()
        self.assertEqual(self.new.read_bytes(), before)

    def test_invalid_profile_or_report_leaves_no_output_and_source_unchanged(self):
        with self.assertRaises(ValueError):
            migrate_application(self.old, self.new, horizon="2030-01-01", active_profile="wrong")
        self.assertFalse(self.new.exists())
        with closing(sqlite3.connect(self.old)) as db, db:
            db.execute("UPDATE reports SET body='{}'")
        before = self.old.read_bytes()
        with self.assertRaises(ValueError):
            self.convert()
        self.assertFalse(self.new.exists())
        self.assertEqual(self.old.read_bytes(), before)

    def test_missing_and_overlapping_prices_and_unsupported_basis(self):
        p = legacy_profile()
        result = convert_profile(p, [], horizon="2030-01-01")
        self.assertEqual(result["scenarios"][1]["versions"][0]["export"], [])
        p["market"]["basis"] = "daily_average"
        with self.assertRaisesRegex(ValueError, "basis"):
            convert_profile(p, [], horizon="2030-01-01")
        p["market"]["basis"] = "quarter_hour"
        with self.assertRaisesRegex(ValueError, "overlapping"):
            convert_profile(p, [(START, 3600, .1, START), (START+900, 900, .2, START)], horizon="2030-01-01")

    def test_unknown_and_negative_prices_remain_explicit(self):
        p = legacy_profile()
        p["suppliers"]["fixed"][0]["import_net"] = None
        result = convert_profile(p, [(START, 900, -.05, START)], horizon="2030-01-01")
        self.assertEqual(result["scenarios"][0]["versions"][0]["import"][0]["status"], "unknown")
        self.assertEqual(result["scenarios"][1]["versions"][0]["import"][0]["value"], "-0.03")

    def test_frozen_body_integrity_is_checked(self):
        evidence = self.convert()
        report = ApplicationStore(self.new).report(evidence["reports"]["invented"])
        changed = copy.deepcopy(report)
        changed["original_body"] += " "
        with self.assertRaisesRegex(ValueError, "changed"):
            render_report(changed, "csv")
        self.assertEqual(report["original_sha256"], hashlib.sha256(report["original_body"].encode()).hexdigest())

    def test_hourly_reference_averages_complete_utc_hours_only(self):
        p = legacy_profile()
        p["market"]["basis"] = "hourly_reference"
        start = START // 3600 * 3600
        prices = [(start+i*900, 900, value, start) for i, value in enumerate([.1,.2,.3,.4,.9])]
        result = convert_profile(p, prices, horizon="2030-01-01")
        quotes = result["scenarios"][1]["versions"][0]["import"]
        self.assertEqual(quotes[0]["value"], "0.27")
        self.assertIsNone(quotes[1]["value"])
