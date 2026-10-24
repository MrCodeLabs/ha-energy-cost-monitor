"""Compatibility export checks with invented history and observations."""

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.migration import migrate_legacy, recovery_bundle
from energy_cost_monitor.observations import Observation
from energy_cost_monitor.reconciliation import reconcile_legacy
from energy_cost_monitor.sources import parse_config
from test_accounting import START, configuration, sample
from test_migration import create_legacy, table_rows


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old, self.new = self.root / "old.sqlite3", self.root / "new.sqlite3"
        self.config = parse_config(configuration())
        create_legacy(self.old)
        with closing(sqlite3.connect(self.old)) as db, db:
            db.execute("UPDATE intervals SET body=?", (json.dumps({
                "energy": {"house": 2.5, "import": 2.5},
                "seconds": {"house": 900, "import": 900}}),))
        migrate_legacy(self.old, self.new, self.config, role_mapping={"house": "house", "import": "import"},
                       cutover=START + 900)
        self.engine = AccountingEngine(self.new, self.config, max_gap_seconds=300, sampling_mode="report")
        for offset in (900, 960, 1020):
            self.engine.ingest(START + offset, sample(self.config, START + offset, 13 + (offset - 900) / 6000))
        self.bundle = self.root / "bundle.zip"
        recovery_bundle(self.new, self.bundle, self.config)
        self.output = self.root / "compatible.sqlite3"

    def reconcile(self, **kwargs):
        return reconcile_legacy(self.bundle, self.output, self.config, resume_at=START + 1800, **kwargs)

    def test_closed_intervals_reports_and_unknowns_preserved_without_replay(self):
        before = self.bundle.read_bytes()
        report = self.reconcile()
        rows = table_rows(self.output)
        original = table_rows(self.old)
        for name in ("profiles", "prices", "price_fetches", "reports"):
            self.assertEqual(rows[name], original[name])
        self.assertEqual(rows["intervals"][0], original["intervals"][0])
        native = json.loads(rows["intervals"][1][1])
        self.assertAlmostEqual(native["energy"]["import"], .02)
        self.assertEqual(native["seconds"]["import"], 120)
        self.assertNotIn("export", native["energy"])
        self.assertEqual(native["signals"], {})
        self.assertEqual(report["native_role_intervals"], 2)
        self.assertEqual(report["native_samples"], 3)
        self.assertEqual(self.bundle.read_bytes(), before)

    def test_resume_barrier_and_partial_session_prevent_cross_era_continuity(self):
        self.reconcile()
        rows = table_rows(self.output)
        last_ts, body = rows["samples"][-1]
        self.assertEqual(last_ts, START + 1800)
        self.assertNotIn("house", json.loads(body))
        metadata = {key: json.loads(value) for key, value in rows["meta"]}
        self.assertEqual(metadata["meter_baselines"], {})
        self.assertFalse(metadata["ecm_reconciliation"]["full_application_parity"])
        session = rows["sessions"][0]
        self.assertEqual(session[2], START + 900)
        self.assertTrue(json.loads(session[3])["partial"])

    def test_existing_destination_and_early_resume_refused(self):
        with self.assertRaisesRegex(ValueError, "resume_overlaps"):
            reconcile_legacy(self.bundle, self.output, self.config, resume_at=START + 900)
        self.assertFalse(self.output.exists())
        self.output.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            self.reconcile()
        self.assertEqual(self.output.read_bytes(), b"keep")

    def test_delayed_report_does_not_modify_pre_cutover_intervals(self):
        # New independent migration with no native baselines yet.
        fresh = self.root / "delayed.sqlite3"
        migrate_legacy(self.old, fresh, self.config, role_mapping={"house": "house", "import": "import"},
                       cutover=START + 900)
        engine = AccountingEngine(fresh, self.config, max_gap_seconds=300, sampling_mode="report")
        states = {source.entity_id: Observation(10, source.unit, START + 880)
                  for source in self.config.sources.values()}
        engine.ingest(START + 900, states)
        engine.ingest(START + 960, sample(self.config, START + 960, 10.01))
        historical = engine.summary(START, START + 900)
        self.assertEqual(historical.energy_kwh["import"], 2.5)
        self.assertEqual(historical.coverage["import"], 1)
        self.assertIsNone(engine.summary(START + 900, START + 1800).energy_kwh["import"])
        self.assertIn("report_precedes_migration_cutover", {item["reason"] for item in engine.anomalies()})
        recovery_bundle(fresh, self.root / "delayed.zip", self.config)

    def test_optional_signals_units_and_native_sessions_exported(self):
        config = parse_config(configuration("optional-capabilities"))
        path = self.root / "optional.sqlite3"
        mapping = {role: role for role in config.required_roles}
        signals = {"pv_power": "pv_w", "battery_soc": "soc", "ev_power": "ev_w",
                   "ev_connected": "plug", "heating": "heating", "water": "water"}
        migrate_legacy(self.old, path, config, role_mapping=mapping, cutover=START + 900)
        engine = AccountingEngine(path, config, max_gap_seconds=300, sampling_mode="report")
        for offset in (900, 1200, 1500, 1800):
            values = sample(config, START + offset, 13 + (offset - 900) / 6000)
            for role, value in {"ev_connected": "on" if offset < 1800 else "off",
                                "ev_power": 1200, "battery_soc": 45}.items():
                src = config.sources[role]
                values[src.entity_id] = Observation(value, src.unit, START + offset)
            engine.ingest(START + offset, values)
        bundle = self.root / "optional.zip"
        recovery_bundle(path, bundle, config)
        report = reconcile_legacy(bundle, self.output, config, signal_mapping=signals, resume_at=START + 2700)
        self.assertEqual(report["reconstructed_sessions"], 1)
        rows = table_rows(self.output)
        flat = json.loads(rows["samples"][1][1])
        self.assertEqual(flat["ev_w"], 1200)
        self.assertEqual(flat["soc"], 45)
        self.assertEqual(flat["plug"], "on")
        session = json.loads(rows["sessions"][-1][3])
        self.assertAlmostEqual(session["kwh"], .15)
        self.assertEqual(session["covered_seconds"], 900)
        self.assertTrue(session["partial"])  # First native sample is already connected.

    def test_ambiguous_reverse_mapping_is_refused_not_summed(self):
        path = self.root / "ambiguous.sqlite3"
        migrate_legacy(self.old, path, self.config, role_mapping={"house": "house", "import": "house"},
                       cutover=START + 900)
        bundle = self.root / "ambiguous.zip"
        recovery_bundle(path, bundle, self.config)
        with self.assertRaisesRegex(ValueError, "ambiguous_legacy_mapping"):
            reconcile_legacy(bundle, self.output, self.config, resume_at=START + 1800)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
