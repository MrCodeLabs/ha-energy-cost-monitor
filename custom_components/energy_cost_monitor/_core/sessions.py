"""Conservative session reconstruction from normalized snapshots and ledger rows.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
"""


def reconstruct_sessions(samples, intervals, *, stop, max_gap_seconds=300, charging_kw=0.1):
    """Return observed connection sessions, without re-differencing EV counters.

    Only EV intervals fully inside a session contribute energy. Edge allocations
    are excluded, not guessed. Charging/pause times use sampled power, so they
    remain estimates. Unknown connection state never means disconnected.
    """
    sessions, active, prior = [], None, None

    def value(readings, role):
        reading = readings.get(role, {})
        return reading.get("value") if reading.get("quality") == "valid" else None

    def finish(end, observed):
        nonlocal active
        active["end"] = end
        active["body"]["partial"] |= not observed
        active["body"]["events"].append({"ts": end, "state": "disconnected" if observed else "gap", "mode": {}})
        sessions.append(active)
        active = None

    for ts, readings in samples:
        plug, power = value(readings, "ev_connected"), value(readings, "ev_power")
        if active is None and plug is True:
            known_start = prior is not None and prior[1] is False and ts - prior[0] <= max_gap_seconds
            active = {"start": ts, "end": None, "body": {
                "kwh": 0.0, "covered_seconds": 0.0, "charging_seconds": 0.0, "pause_seconds": 0.0,
                "max_w": 0.0, "partial": not known_start,
                "events": [{"ts": ts, "state": "connected", "mode": {}}],
                "ecm_semantics": "whole_ledger_intervals_and_sampled_power",
                "ecm_excluded_edge_intervals": 0,
            }}
        if active is not None:
            body = active["body"]
            if power is not None:
                body["max_w"] = max(body["max_w"], power * 1000)
            if prior is not None and prior[0] >= active["start"]:
                elapsed = ts - prior[0]
                if 0 < elapsed <= max_gap_seconds and prior[1] is True and plug in (True, False) and prior[2] is not None:
                    state = "charging" if prior[2] > charging_kw else "pause"
                    body["charging_seconds" if state == "charging" else "pause_seconds"] += elapsed
                else:
                    body["partial"], state = True, "gap"
                if body["events"][-1]["state"] != state:
                    body["events"].append({"ts": prior[0], "state": state, "mode": {}})
            if plug is False:
                finish(ts, True)
        prior = ts, plug, power
    if active is not None:
        finish(stop, False)
    # Inputs are native EV allocations, never legacy session totals.
    for start, kwh, seconds in intervals:
        for session in sessions:
            if start < session["end"] and start + 900 > session["start"]:
                body = session["body"]
                if start >= session["start"] and start + 900 <= session["end"]:
                    body["kwh"] += kwh
                    body["covered_seconds"] += seconds
                else:
                    body["ecm_excluded_edge_intervals"] += 1
                    body["partial"] = True
    for session in sessions:
        body = session["body"]
        if body["covered_seconds"] < session["end"] - session["start"]:
            body["partial"] = True
        body["ecm_energy_status"] = "partial" if body["partial"] else "complete"
        if body["covered_seconds"] == 0:
            body["kwh"], body["ecm_energy_status"] = None, "unknown"
    return sessions
