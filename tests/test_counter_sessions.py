"""Counter-based EV boundaries, physical limits and observed modes."""

import unittest

from energy_cost_monitor.sessions import counter_sessions


def sample(plug, energy, mode="solar", power=0):
    return {
        key: {
            "value": value,
            "quality": "valid" if value is not None else "unavailable",
        }
        for key, value in {
            "ev_connected": plug,
            "ev": energy,
            "ev_mode": mode,
            "ev_power": power,
        }.items()
    }


class CounterSessionsTests(unittest.TestCase):
    def run_sessions(self, rows, **settings):
        return counter_sessions(
            rows, stop=600, max_gap_seconds=90, max_power_kw=12, **settings
        )

    def test_edges_modes_and_two_sessions_do_not_duplicate_energy(self):
        rows = [
            (0, sample(False, 1)),
            (60, sample(True, 1)),
            (120, sample(True, 1.1, "night")),
            (180, sample(False, 1.2)),
            (240, sample(True, 1.2)),
            (300, sample(False, 1.25)),
        ]
        sessions = self.run_sessions(rows)
        self.assertAlmostEqual(sum(s["body"]["kwh"] for s in sessions), 0.25)
        self.assertAlmostEqual(sessions[0]["body"]["mode_totals"]["night"]["kwh"], 0.1)
        self.assertFalse(any(s["body"]["partial"] for s in sessions))
        self.assertEqual(sessions[0]["body"]["charging_seconds"], 120)

    def test_reset_jump_gap_and_unknown_are_not_energy(self):
        for end, reading in [
            (120, sample(False, 0.5)),
            (120, sample(False, 8)),
            (180, sample(False, 1.1)),
            (120, sample(None, 1.1)),
        ]:
            (session,) = self.run_sessions(
                [(0, sample(False, 1)), (60, sample(True, 1)), (end, reading)]
            )
            self.assertIsNone(session["body"]["kwh"])
            self.assertTrue(session["body"]["partial"])

    def test_zero_energy_is_known_pause_not_unknown(self):
        (session,) = self.run_sessions(
            [(0, sample(False, 1)), (60, sample(True, 1)), (120, sample(False, 1))]
        )
        self.assertEqual(session["body"]["kwh"], 0)
        self.assertEqual(session["body"]["pause_seconds"], 60)
        self.assertEqual(session["body"]["ecm_energy_status"], "complete")

    def test_tolerance_and_delta_threshold_are_explicit(self):
        (session,) = self.run_sessions(
            [(0, sample(False, 1)), (60, sample(True, 1)), (120, sample(False, 1.21))],
            tolerance_kwh=0.02,
            charging_delta_kwh=0.3,
        )
        self.assertAlmostEqual(session["body"]["kwh"], 0.21)
        self.assertEqual(session["body"]["pause_seconds"], 60)
        with self.assertRaises(ValueError):
            self.run_sessions([], tolerance_kwh=float("nan"))
