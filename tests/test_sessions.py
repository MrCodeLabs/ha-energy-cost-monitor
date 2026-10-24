"""Conservative EV session accounting, without counter replay."""

import unittest

from energy_cost_monitor.sessions import reconstruct_sessions


def reading(plug, power=1):
    return {"ev_connected": {"value": plug, "quality": "valid" if plug is not None else "unavailable"},
            "ev_power": {"value": power, "quality": "valid" if power is not None else "unavailable"}}


class SessionTests(unittest.TestCase):
    def test_complete_interval_uses_ledger_energy_with_charging_and_pause(self):
        samples = [(-60, reading(False)), (0, reading(True)), (300, reading(True, 0)),
                   (600, reading(True, 0)), (900, reading(False, 0))]
        session, = reconstruct_sessions(samples, [(0, .25, 900)], stop=1800)
        self.assertEqual(session["body"]["kwh"], .25)
        self.assertEqual(session["body"]["charging_seconds"], 300)
        self.assertEqual(session["body"]["pause_seconds"], 600)
        self.assertFalse(session["body"]["partial"])

    def test_unknown_does_not_disconnect_and_gap_is_not_charging(self):
        samples = [(0, reading(True)), (60, reading(None)), (120, reading(True)), (900, reading(False))]
        session, = reconstruct_sessions(samples, [(0, .3, 120)], stop=1800)
        self.assertTrue(session["body"]["partial"])
        self.assertEqual(session["end"], 900)
        self.assertEqual(session["body"]["charging_seconds"], 0)

    def test_edge_interval_not_counted_twice_for_two_connections(self):
        samples = [(60, reading(True)), (120, reading(False)), (180, reading(True)), (240, reading(False))]
        sessions = reconstruct_sessions(samples, [(0, .4, 240)], stop=900)
        self.assertEqual(len(sessions), 2)
        self.assertTrue(all(s["body"]["kwh"] is None for s in sessions))
        self.assertTrue(all(s["body"]["partial"] for s in sessions))

    def test_unclosed_session_ends_at_explicit_boundary_as_partial(self):
        session, = reconstruct_sessions([(0, reading(True))], [], stop=900)
        self.assertEqual(session["end"], 900)
        self.assertTrue(session["body"]["partial"])
        self.assertEqual(session["body"]["events"][-1]["state"], "gap")
