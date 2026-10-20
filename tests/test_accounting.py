"""Synthetic continuity, allocation and storage tests for the extracted ledger.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
"""

from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.observations import Observation
from energy_cost_monitor.sources import parse_config


ROOT = Path(__file__).resolve().parents[1]
START = 1_800_000_000  # Exact UTC quarter-hour, unrelated to household measurements.


def configuration(name="minimal"):
    return json.loads((ROOT / "examples" / f"{name}.json").read_text(encoding="utf-8"))


def sample(config, timestamp, energy):
    result = {}
    for source in config.sources.values():
        if source.kind == "binary":
            value = "off"
        elif source.kind == "cumulative_energy":
            value = energy * {"Wh": 1000, "kWh": 1, "MWh": 0.001}[source.unit]
        else:
            value = 0
        result[source.entity_id] = Observation(str(value), source.unit, timestamp)
    return result


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ecm-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "ledger.sqlite3"
        self.config = parse_config(configuration())
        self.engine = AccountingEngine(self.path, self.config, max_gap_seconds=120)

    def ingest(self, offset, energy, *, engine=None, **overrides):
        engine = engine or self.engine
        timestamp = START + offset
        states = sample(engine.config, timestamp, energy)
        for role, value in overrides.items():
            source = engine.config.sources[role]
            states[source.entity_id] = Observation(value, source.unit, timestamp)
        return engine.ingest(timestamp, states)

    def test_minimal_quarter_hour_has_known_energy_and_full_coverage(self):
        for minute in range(16):
            self.ingest(minute * 60, 100 + minute / 10)
        summary = self.engine.summary(START, START + 900)
        self.assertAlmostEqual(summary.energy_kwh["house"], 1.5)
        self.assertAlmostEqual(summary.energy_kwh["import"], 1.5)
        self.assertEqual(set(summary.energy_kwh), {"house", "import"})
        self.assertEqual(summary.coverage, {"house": 1, "import": 1})
        self.assertEqual(summary.joint_coverage, 1)
        self.assertEqual(self.engine.anomalies(), ())

    def test_first_absolute_counter_reading_is_only_a_baseline(self):
        self.ingest(0, 1234)
        row = self.engine.intervals(START, START + 900)[0]
        self.assertIsNone(row.energy_kwh["house"])
        self.assertEqual(row.covered_seconds["house"], 0)
        self.assertFalse(row.ready)

    def test_zero_consumption_still_has_full_coverage(self):
        for offset in range(0, 901, 60):
            self.ingest(offset, 10)
        summary = self.engine.summary(START, START + 900)
        self.assertEqual(summary.energy_kwh["import"], 0)
        self.assertEqual(summary.joint_coverage, 1)

    def test_energy_crossing_boundary_is_prorated_and_conserved(self):
        self.ingest(870, 10)
        self.ingest(930, 10.2)
        rows = self.engine.intervals(START, START + 1800)
        for row in rows:
            self.assertAlmostEqual(row.energy_kwh["import"], 0.1)
            self.assertEqual(row.covered_seconds["import"], 30)
            self.assertFalse(row.complete["import"])
        self.assertAlmostEqual(sum(row.energy_kwh["import"] for row in rows), 0.2)

    def test_missing_buckets_remain_in_coverage_denominator(self):
        for offset in range(0, 901, 60):
            self.ingest(offset, offset / 600)
        rows = self.engine.intervals(START, START + 2700)
        self.assertEqual(len(rows), 3)
        self.assertIsNone(rows[1].energy_kwh["import"])
        self.assertIsNone(rows[2].energy_kwh["import"])
        summary = self.engine.summary(START, START + 2700)
        self.assertEqual(summary.expected_intervals, 3)
        self.assertEqual(summary.coverage["import"], 1 / 3)
        self.assertEqual(summary.joint_coverage, 1 / 3)

    def test_recovery_after_unavailable_preserves_unassigned_delta(self):
        self.ingest(0, 10)
        self.ingest(60, 10, house="unavailable")
        self.ingest(120, 10.2)
        row = self.engine.intervals(START, START + 900)[0]
        self.assertIsNone(row.energy_kwh["house"])
        gap = next(a for a in self.engine.anomalies() if a["role"] == "house" and a["reason"] == "gap")
        self.assertAlmostEqual(gap["unassigned_kwh"], 0.2)
        self.ingest(180, 10.3)
        row = self.engine.intervals(START, START + 900)[0]
        self.assertAlmostEqual(row.energy_kwh["house"], 0.1)
        self.assertEqual(row.covered_seconds["house"], 60)

    def test_long_gap_does_not_fill_intervals_or_charge_on_return(self):
        self.ingest(0, 10)
        self.ingest(3600, 11)
        summary = self.engine.summary(START, START + 4500)
        self.assertIsNone(summary.energy_kwh["house"])
        self.assertEqual(summary.joint_coverage, 0)
        gap = next(a for a in self.engine.anomalies() if a["role"] == "house")
        self.assertEqual(gap["unassigned_kwh"], 1)

    def test_continuity_limit_is_configurable_and_inclusive(self):
        short = AccountingEngine(Path(self.temp.name) / "short.sqlite3", self.config, max_gap_seconds=60)
        for engine in (short, self.engine):
            self.ingest(0, 0, engine=engine)
            self.ingest(120, 0.1, engine=engine)
        self.assertIsNone(short.summary(START, START + 900).energy_kwh["house"])
        self.assertEqual(self.engine.summary(START, START + 900).energy_kwh["house"], 0.1)

    def test_configured_power_limit_rejects_jump_and_then_recovers(self):
        raw = configuration()
        for source in raw["sources"].values():
            source["max_power_kw"] = 1
        config = parse_config(raw)
        engine = AccountingEngine(Path(self.temp.name) / "limited.sqlite3", config, max_gap_seconds=120)
        self.ingest(0, 0, engine=engine)
        self.ingest(60, 0.1, engine=engine)  # 6 kW exceeds this configured 1 kW limit.
        self.ingest(120, 0.11, engine=engine)
        self.assertAlmostEqual(engine.summary(START, START + 900).energy_kwh["house"], 0.01)
        jump = next(a for a in engine.anomalies() if a["role"] == "house")
        self.assertEqual(jump["reason"], "counter_jump")
        self.assertEqual(jump["delta_kwh"], 0.1)
        self.assertIsNone(jump["unassigned_kwh"])

    def test_exact_power_limit_is_not_lost_to_float_rounding(self):
        self.ingest(0, 10)
        self.ingest(60, 10.2)  # Exactly 12 kW for one minute.
        self.assertAlmostEqual(self.engine.summary(START, START + 900).energy_kwh["house"], 0.2)
        self.assertEqual(self.engine.anomalies(), ())

    def test_reset_starts_new_baseline_without_counting_absolute_value(self):
        self.ingest(0, 10)
        self.ingest(60, 0.5)
        self.ingest(120, 0.6)
        self.assertAlmostEqual(self.engine.summary(START, START + 900).energy_kwh["house"], 0.1)
        reset = next(a for a in self.engine.anomalies() if a["role"] == "house")
        self.assertEqual(reset["reason"], "counter_reset")
        self.assertIsNone(reset["unassigned_kwh"])

    def test_reset_and_jump_during_gap_are_not_labeled_valid_unassigned_energy(self):
        for name, value, reason in (("reset", 0, "counter_reset"), ("jump", 100, "counter_jump")):
            engine = AccountingEngine(Path(self.temp.name) / f"{name}.sqlite3", self.config, max_gap_seconds=120)
            self.ingest(0, 10, engine=engine)
            self.ingest(60, 10, engine=engine, house="unknown")
            self.ingest(180, value, engine=engine)
            event = engine.anomalies()[-2]  # house, then import for the shared meter.
            self.assertEqual(event["reason"], reason)
            self.assertIsNone(event["unassigned_kwh"])

    def test_duplicate_and_older_samples_do_not_change_saved_state(self):
        self.ingest(0, 0)
        self.ingest(60, 0.1)
        before = self.engine.latest_observations()
        self.assertFalse(self.ingest(60, 500))
        self.assertFalse(self.ingest(30, 500))
        self.assertEqual(self.engine.latest_observations(), before)
        self.assertAlmostEqual(self.engine.summary(START, START + 900).energy_kwh["house"], 0.1)

    def test_reopening_preserves_baseline_intervals_and_idempotency(self):
        for minute in range(8):
            self.ingest(minute * 60, minute / 10)
        self.engine = AccountingEngine(self.path, self.config, max_gap_seconds=120)
        self.assertFalse(self.ingest(420, 999))
        for minute in range(8, 16):
            self.ingest(minute * 60, minute / 10)
        summary = self.engine.summary(START, START + 900)
        self.assertAlmostEqual(summary.energy_kwh["house"], 1.5)
        self.assertEqual(summary.joint_coverage, 1)

    def test_reopening_preserves_broken_continuity(self):
        self.ingest(0, 10)
        self.ingest(60, 10, house="unknown")
        reopened = AccountingEngine(self.path, self.config, max_gap_seconds=120)
        self.ingest(120, 10.2, engine=reopened)
        self.assertIsNone(reopened.summary(START, START + 900).energy_kwh["house"])
        self.assertAlmostEqual(reopened.anomalies()[-1]["unassigned_kwh"], 0.2)

    def test_independent_instances_on_same_database_do_not_duplicate_energy(self):
        other = AccountingEngine(self.path, self.config, max_gap_seconds=120)
        self.ingest(0, 0)
        self.assertFalse(self.ingest(0, 0, engine=other))
        self.ingest(60, 0.1, engine=other)
        self.assertFalse(self.ingest(60, 0.1))
        self.assertAlmostEqual(self.engine.summary(START, START + 900).energy_kwh["house"], 0.1)

    def test_bad_unit_and_stale_observation_break_continuity(self):
        self.ingest(0, 10)
        entity = self.config.sources["house"].entity_id
        self.engine.ingest(START + 60, {entity: Observation("10000", "Wh", START + 60)})
        self.engine.ingest(START + 240, {entity: Observation("10.1", "kWh", START)})
        self.ingest(300, 10.2)
        self.assertIsNone(self.engine.summary(START, START + 900).energy_kwh["house"])
        reasons = {a["reason"] for a in self.engine.anomalies()}
        self.assertEqual(reasons, {"unit_mismatch", "stale", "gap"})

    def test_optional_ev_failure_does_not_block_independent_house_coverage(self):
        config = parse_config(configuration("optional-capabilities"))
        engine = AccountingEngine(Path(self.temp.name) / "optional.sqlite3", config, max_gap_seconds=120)
        for minute in range(16):
            overrides = {"ev_connected": "unknown"} if minute == 5 else {}
            self.ingest(minute * 60, minute * 0.02, engine=engine, **overrides)
        summary = engine.summary(START, START + 900)
        self.assertEqual(summary.coverage["house"], 1)
        self.assertEqual(summary.coverage["ev"], 0)
        self.assertEqual(summary.joint_coverage, 0)
        self.assertAlmostEqual(summary.energy_kwh["house"], 0.3)
        self.assertAlmostEqual(summary.energy_kwh["ev"], 0.26)
        self.assertNotIn("heating", summary.energy_kwh)
        ev_gap = next(a for a in engine.anomalies() if a["role"] == "ev" and a["reason"] == "gap")
        self.assertAlmostEqual(ev_gap["unassigned_kwh"], 0.04)

    def test_daily_estimate_reset_is_stored_without_cumulative_accounting(self):
        config = parse_config(configuration("optional-capabilities"))
        engine = AccountingEngine(Path(self.temp.name) / "daily.sqlite3", config, max_gap_seconds=120)
        self.ingest(0, 10, engine=engine, heating="4")
        self.ingest(60, 10.02, engine=engine, heating="0.1")
        reading = engine.latest_observations()["readings"]["heating"]
        self.assertEqual(reading, {"value": 0.1, "unit": "kWh", "quality": "estimated"})
        self.assertNotIn("heating", engine.summary(START, START + 900).energy_kwh)
        self.assertFalse(any(a["role"] == "heating" for a in engine.anomalies()))

    def test_failed_ingest_rolls_back_sample_baselines_and_partial_allocation(self):
        self.ingest(0, 0)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER synthetic_failure BEFORE INSERT ON intervals "
                       "WHEN NEW.role='import' BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.ingest(60, 0.1)
        self.assertEqual(self.engine.latest_observations()["timestamp"], START)
        self.assertIsNone(self.engine.summary(START, START + 900).energy_kwh["house"])
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DROP TRIGGER synthetic_failure")
        self.assertTrue(self.ingest(60, 0.1))
        self.assertAlmostEqual(self.engine.summary(START, START + 900).energy_kwh["house"], 0.1)

    def test_configuration_change_is_rejected_without_modifying_database(self):
        self.ingest(0, 10)
        before = self.path.read_bytes()
        variants = []
        raw = configuration()
        for source in raw["sources"].values():
            source["max_power_kw"] = 20
        variants.append((parse_config(raw), 120))
        variants.append((self.config, 60))
        for config, gap in variants:
            with self.assertRaisesRegex(ValueError, "database_configuration_mismatch"):
                AccountingEngine(self.path, config, max_gap_seconds=gap)
            self.assertEqual(self.path.read_bytes(), before)

    def test_unrelated_blank_and_non_sqlite_files_are_preserved(self):
        for name, data in (("blank", b""), ("other", b"synthetic non-SQLite input")):
            path = Path(self.temp.name) / name
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "unsupported_database"):
                AccountingEngine(path, self.config, max_gap_seconds=120)
            self.assertEqual(path.read_bytes(), data)
        path = Path(self.temp.name) / "unrelated.sqlite3"
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE synthetic_existing_data(value TEXT)")
            db.execute("INSERT INTO synthetic_existing_data VALUES('retain me')")
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "unsupported_database"):
            AccountingEngine(path, self.config, max_gap_seconds=120)
        self.assertEqual(path.read_bytes(), before)

    def test_newer_schema_is_rejected_and_preserved(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA user_version=2")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "unsupported_database"):
            AccountingEngine(self.path, self.config, max_gap_seconds=120)
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_table_is_detected_before_collection(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DROP TABLE baselines")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "unsupported_database"):
            AccountingEngine(self.path, self.config, max_gap_seconds=120)
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_database_is_not_silently_recreated_during_collection(self):
        self.path.unlink()
        with self.assertRaises(sqlite3.OperationalError):
            self.ingest(0, 0)
        self.assertFalse(self.path.exists())

    def test_invalid_parameters_fail_before_storage_or_state_changes(self):
        for gap in (True, 0, -1, 901, float("nan"), float("inf")):
            path = Path(self.temp.name) / "invalid.sqlite3"
            with self.assertRaises(ValueError):
                AccountingEngine(path, self.config, max_gap_seconds=gap)
            self.assertFalse(path.exists())
        for timestamp in (True, -1, float("nan"), float("inf"), "bad", 10**1000):
            with self.assertRaises(ValueError):
                self.engine.ingest(timestamp, {})
        self.assertIsNone(self.engine.latest_observations())

    def test_queries_require_aligned_bounded_windows(self):
        for start, end in ((START + 1, START + 900), (START, START + 901),
                           (START, START), (START + 900, START),
                           (START, START + 401 * 86400), (START, float("inf"))):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                self.engine.summary(start, end)

    def test_dst_shaped_windows_include_92_and_100_distinct_utc_buckets(self):
        for first, last, expected in (
            ("2026-03-29T00:00:00+01:00", "2026-03-30T00:00:00+02:00", 92),
            ("2026-10-25T00:00:00+02:00", "2026-10-26T00:00:00+01:00", 100),
        ):
            start, end = (datetime.fromisoformat(value).timestamp() for value in (first, last))
            rows = self.engine.intervals(start, end)
            self.assertEqual(len(rows), expected)
            self.assertEqual(len({row.start for row in rows}), expected)
            self.assertEqual(self.engine.summary(start, end).expected_intervals, expected)
        first = datetime.fromisoformat("2026-10-25T02:00:00+02:00").timestamp()
        second = datetime.fromisoformat("2026-10-25T02:00:00+01:00").timestamp()
        self.assertEqual(second - first, 3600)

    def test_returned_results_cannot_mutate_persistent_history(self):
        self.ingest(0, 0)
        self.ingest(60, 0.1)
        returned = self.engine.latest_observations()
        returned["readings"].clear()
        self.assertTrue(self.engine.latest_observations()["readings"])
        row = self.engine.intervals(START, START + 900)[0]
        with self.assertRaises(TypeError):
            row.energy_kwh["house"] = 99


if __name__ == "__main__":
    unittest.main()
