"""Study warm-up, missing reference and persistent report boundaries."""

from datetime import datetime
from zoneinfo import ZoneInfo
import json
from unittest.mock import patch
import unittest
import test_application
from energy_cost_monitor.study import Study, add_months, quality, validate_study


def settings():
    return {
        "timezone": "Europe/Ljubljana",
        "months": 3,
        "warmup_hours": 48,
        "minimum_coverage": 0.99,
        "require_daily_check": True,
        "daily_absolute_kwh": 0.1,
        "daily_relative": 0.01,
        "reference_age_seconds": 180,
    }


class StudyTests(unittest.TestCase):
    setUp = test_application.ApplicationTests.setUp

    def test_quality_requires_real_reference_and_start_waits(self):
        study = Study(self.store)
        study.configure(settings())
        status = study.advance(self.engine, 1767225600)
        self.assertEqual(status["state"], "warmup")
        self.assertEqual(status["quality"]["daily"]["status"], "insufficient")
        self.assertFalse(status["quality"]["ready"])
        with self.assertRaises(ValueError):
            study.configure(settings())
        study.cancel()
        self.assertEqual(Study(self.store).status()["state"], "cancelled")

    def test_calendar_clamping_and_dst(self):
        zone = ZoneInfo("Europe/Ljubljana")
        start = datetime(2026, 1, 31, tzinfo=zone)
        self.assertEqual(add_months(start, 1).day, 28)
        self.assertEqual(add_months(start, 2).day, 31)
        self.assertEqual(add_months(start, 3).utcoffset().total_seconds(), 7200)

    def test_reports_are_created_once_and_resume_from_private_state(self):
        study = Study(self.store)
        study.configure(settings())
        now = datetime(2026, 1, 30, 12, tzinfo=ZoneInfo("Europe/Ljubljana")).timestamp()
        with patch(
            "energy_cost_monitor.study.quality",
            return_value={"ready": True, "coverage": 1},
        ):
            state = study.advance(self.engine, now)
        self.assertEqual(state["state"], "running")
        self.assertEqual(
            datetime.fromtimestamp(
                state["windows"][0], ZoneInfo("Europe/Ljubljana")
            ).day,
            31,
        )
        with patch.object(
            self.store, "freeze", side_effect=["one", "two", "three", "final"]
        ) as freeze:
            state = study.advance(self.engine, state["windows"][-1] + 1)
            self.assertEqual(freeze.call_count, 4)
            self.assertEqual(state["state"], "complete")
            study.advance(self.engine, state["windows"][-1] + 2)
            self.assertEqual(freeze.call_count, 4)
        self.assertEqual(Study(self.store).status()["reports"]["final"], "final")

    def test_daily_crosscheck_is_derived_from_stored_measurements(self):
        zone = ZoneInfo("Europe/Ljubljana")
        end = int(datetime(2026, 3, 30, tzinfo=zone).timestamp())
        start = int(datetime(2026, 3, 29, tzinfo=zone).timestamp())
        with self.engine._db(write=True) as db:
            for t in range(end - 48 * 3600, end, 900):
                for role in self.engine.roles:
                    db.execute(
                        "INSERT OR REPLACE INTO intervals VALUES(?,?,?,?)",
                        (t, role, 0.1, 900),
                    )
            reference = {
                "house_daily_reference": {
                    "quality": "estimated",
                    "value": (end - start) / 900 * 0.1,
                }
            }
            db.execute(
                "INSERT OR REPLACE INTO samples VALUES(?,?)",
                (end - 60, json.dumps(reference)),
            )
        result = quality(self.engine, settings(), end)
        self.assertEqual(result["daily"]["status"], "ok")
        self.assertAlmostEqual(result["daily"]["measured_kwh"], 9.2)

    def test_limits_refuse_invalid_configuration(self):
        value = settings()
        value["minimum_coverage"] = float("nan")
        with self.assertRaises(ValueError):
            validate_study(value)
