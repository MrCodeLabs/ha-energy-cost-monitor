"""Report-time policy against real temporary SQLite ledgers."""

from pathlib import Path
import tempfile
import unittest

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.observations import Observation
from energy_cost_monitor.sources import parse_config
from test_accounting import START, configuration


class ReportSamplingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ecm-report-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "ledger.sqlite3"
        raw = configuration()
        for source in raw["sources"].values():
            source["max_age_seconds"] = 600
            source["max_power_kw"] = 1
        self.config = parse_config(raw)
        self.engine = AccountingEngine(self.path, self.config, max_gap_seconds=300, sampling_mode="report")

    def ingest(self, collected, reported, value):
        entity = self.config.sources["house"].entity_id
        return self.engine.ingest(START + collected, {entity: Observation(value, "kWh", START + reported)})

    def row(self):
        return self.engine.intervals(START, START + 900)[0]

    def test_repeated_poll_does_not_shift_baseline_or_invent_jump(self):
        self.ingest(0, 0, 10)
        for second in range(30, 300, 30):
            self.ingest(second, 0, 10)
        self.assertIsNone(self.row().energy_kwh["house"])
        self.ingest(300, 300, 10.08)  # 0.96 kW over the actual five minutes.
        self.assertAlmostEqual(self.row().energy_kwh["house"], 0.08)
        self.assertEqual(self.row().covered_seconds["house"], 300)
        self.assertEqual(self.engine.anomalies(), ())

    def test_delayed_collection_allocates_at_report_times(self):
        self.ingest(30, 0, 10)
        self.ingest(360, 300, 10.05)
        self.assertEqual(self.row().covered_seconds["house"], 300)

    def test_new_unchanged_report_is_measured_zero_consumption(self):
        self.ingest(0, 0, 10)
        self.ingest(300, 300, 10)
        self.assertEqual(self.row().energy_kwh["house"], 0)
        self.assertEqual(self.row().covered_seconds["house"], 300)

    def test_reports_beyond_gap_are_not_backfilled(self):
        self.ingest(0, 0, 10)
        self.ingest(600, 600, 10.1)
        self.assertIsNone(self.row().energy_kwh["house"])
        self.assertAlmostEqual(self.engine.anomalies()[0]["unassigned_kwh"], 0.1)

    def test_stale_repeated_report_breaks_continuity(self):
        self.ingest(0, 0, 10)
        self.ingest(601, 0, 10)
        self.ingest(602, 602, 10.1)
        self.assertIsNone(self.row().energy_kwh["house"])
        self.assertIn("stale", {a["reason"] for a in self.engine.anomalies()})

    def test_bad_units_unknown_and_future_reports_do_not_become_zero(self):
        entity = self.config.sources["house"].entity_id
        for observed, reason in ((Observation(100, "Wh", START + 60), "unit_mismatch"),
                                 (Observation("unknown", "kWh", START + 60), "unavailable"),
                                 (Observation(100, "kWh", START + 61), "future_timestamp")):
            with self.subTest(reason=reason):
                path = Path(self.temp.name) / f"{reason}.sqlite3"
                engine = AccountingEngine(path, self.config, max_gap_seconds=300, sampling_mode="report")
                engine.ingest(START, {entity: Observation(10, "kWh", START)})
                engine.ingest(START + 60, {entity: observed})
                engine.ingest(START + 120, {entity: Observation(10.01, "kWh", START + 120)})
                self.assertIsNone(engine.summary(START, START + 900).energy_kwh["house"])
                self.assertIn(reason, {a["reason"] for a in engine.anomalies()})

    def test_older_and_conflicting_reports_invalidate_without_rewinding(self):
        self.ingest(60, 60, 10)
        self.ingest(90, 30, 9)
        self.ingest(100, 60, 11)
        self.ingest(120, 120, 10.01)
        self.assertIsNone(self.row().energy_kwh["house"])
        self.ingest(180, 180, 10.02)
        self.assertAlmostEqual(self.row().energy_kwh["house"], 0.01)
        self.assertIn("non_monotonic_report", {a["reason"] for a in self.engine.anomalies()})

    def test_reopen_retains_per_meter_report_timestamp(self):
        self.ingest(0, 0, 10)
        self.ingest(270, 0, 10)
        self.engine = AccountingEngine(self.path, self.config, max_gap_seconds=300, sampling_mode="report")
        self.ingest(300, 300, 10.08)
        self.assertAlmostEqual(self.row().energy_kwh["house"], 0.08)

    def test_adapter_restart_does_not_bridge_unobserved_downtime(self):
        self.ingest(0, 0, 10)
        self.engine.break_continuity()
        self.ingest(60, 60, 10.01)
        self.assertIsNone(self.row().energy_kwh["house"])
        self.ingest(120, 120, 10.02)
        self.assertAlmostEqual(self.row().energy_kwh["house"], 0.01)

    def test_sampling_mode_is_part_of_storage_identity_without_migration(self):
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "database_configuration_mismatch"):
            AccountingEngine(self.path, self.config, max_gap_seconds=300)
        self.assertEqual(self.path.read_bytes(), before)

    def test_asynchronous_meters_keep_independent_coverage(self):
        raw = configuration()
        raw["sources"]["house"]["entity_id"] = "sensor.example_house_energy"
        config = parse_config(raw)
        engine = AccountingEngine(Path(self.temp.name) / "independent.sqlite3", config,
                                  max_gap_seconds=300, sampling_mode="report")
        for collected, house_time, import_time in ((0, 0, 0), (60, 60, 0), (120, 120, 100)):
            states = {source.entity_id: Observation(10 + reported / 6000, "kWh", START + reported)
                      for role, source in config.sources.items()
                      for reported in [house_time if role == "house" else import_time]}
            engine.ingest(START + collected, states)
        row = engine.intervals(START, START + 900)[0]
        self.assertEqual(row.covered_seconds, {"house": 120, "import": 100})
