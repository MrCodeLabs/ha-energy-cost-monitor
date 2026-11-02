"""Conservative session reconstruction from normalized snapshots and ledger rows.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
"""

import math


MODE_FIELDS = ("mode", "amp_limit", "pv_enabled", "night_enabled", "night_owned", "grid_limit",
               "current_cap", "status", "deadline_status", "deadline", "target_soc",
               "requested_current", "maximum_current", "cable_current")


def counter_sessions(samples, *, stop, max_gap_seconds, max_power_kw,
                     tolerance_kwh=0, charging_kw=0.1, charging_delta_kwh=0,
                     close_open=False):
    """Session-only counter deltas; never write/reallocate ledger energy.

    Both endpoints must be usable, ordered and within configured physical/time
    limits. This recovers session edges while keeping gaps, resets and unknown
    connection states explicit. Mode values are observations, never commands.
    """
    for value in (stop, max_gap_seconds, max_power_kw, tolerance_kwh, charging_kw, charging_delta_kwh):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("invalid_session_limit")
    if not max_gap_seconds or not max_power_kw:
        raise ValueError("invalid_session_limit")
    sessions, active, prior = [], None, None

    def value(readings, role):
        item = readings.get(role, {})
        return item.get("value") if item.get("quality") == "valid" else None

    def numeric(value):
        return type(value) in (int, float) and math.isfinite(value) and value >= 0

    def mode(readings):
        return {key: value(readings, "ev_" + key) for key in MODE_FIELDS}

    for ts, readings in samples:
        if not math.isfinite(ts) or ts > stop or (prior and ts <= prior[0]):
            raise ValueError("unordered_session_samples")
        plug, power, energy = (value(readings, role) for role in ("ev_connected", "ev_power", "ev"))
        if plug is True and active is None:
            active = {"start": ts, "end": None, "body": {
                "kwh": 0., "covered_seconds": 0., "charging_seconds": 0., "pause_seconds": 0.,
                "max_w": 0., "partial": not (prior and prior[1] is False and ts-prior[0] <= max_gap_seconds),
                "events": [{"ts": ts, "state": "connected", "mode": mode(readings)}],
                "ecm_semantics": "bounded_sample_counter_deltas", "mode_totals": {},
            }}
            sessions.append(active)
        if active is not None:
            body = active["body"]
            if numeric(power):
                body["max_w"] = max(body["max_w"], power*1000)
            if prior and prior[0] >= active["start"]:
                previous_ts, previous_plug, previous_power, previous_energy, previous_readings = prior
                dt = ts-previous_ts
                valid = (dt <= max_gap_seconds and previous_plug is True and type(plug) is bool
                         and numeric(energy) and numeric(previous_energy)
                         and 0 <= energy-previous_energy <= max_power_kw*dt/3600+tolerance_kwh)
                if valid:
                    delta = energy-previous_energy
                    state = "charging" if (delta > charging_delta_kwh or
                                           (numeric(previous_power) and previous_power > charging_kw)) else "pause"
                    body["kwh"] += delta
                    body["covered_seconds"] += dt
                    body[state + "_seconds" if state == "pause" else "charging_seconds"] += dt
                    observed_mode = mode(previous_readings)
                    label = observed_mode["mode"] or "unknown"
                    total = body["mode_totals"].setdefault(str(label), {"kwh": 0., "seconds": 0.})
                    total["kwh"] += delta
                    total["seconds"] += dt
                else:
                    state, observed_mode, body["partial"] = "gap", mode(readings), True
                last = body["events"][-1]
                if last["state"] != state or (state != "gap" and last["mode"] != observed_mode):
                    body["events"].append({"ts": previous_ts, "state": state, "mode": observed_mode})
            if plug is False:
                active["end"] = ts
                body["events"].append({"ts": ts, "state": "disconnected", "mode": mode(readings)})
                active = None
        prior = ts, plug, power, energy, readings
    if active:
        active["body"]["partial"] = True
        if close_open:
            active["end"] = stop
            active["body"]["events"].append({"ts": stop, "state": "gap", "mode": {}})
    for session in sessions:
        body = session["body"]
        duration = (session["end"] if session["end"] is not None else stop) - session["start"]
        body["partial"] |= body["covered_seconds"] < duration
        body["ecm_energy_status"] = "partial" if body["partial"] else "complete"
        if not body["covered_seconds"]:
            body["kwh"], body["ecm_energy_status"] = None, "unknown"
        body["average_charging_kw"] = (body["kwh"]*3600/body["charging_seconds"]
                                         if body["kwh"] is not None and body["charging_seconds"] else None)
        body["average_connected_kw"] = (body["kwh"]*3600/body["covered_seconds"]
                                         if body["kwh"] is not None and body["covered_seconds"] else None)
    return sessions


def reconstruct_sessions(samples, intervals, *, stop, max_gap_seconds=300, charging_kw=0.1, close_open=True):
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
        if close_open:
            finish(stop, False)
        else:
            active["body"]["partial"] = True
            sessions.append(active)
    # Inputs are native EV allocations, never legacy session totals.
    for start, kwh, seconds in intervals:
        for session in sessions:
            session_end = stop if session["end"] is None else session["end"]
            if start < session_end and start + 900 > session["start"]:
                body = session["body"]
                if start >= session["start"] and start + 900 <= session_end:
                    body["kwh"] += kwh
                    body["covered_seconds"] += seconds
                else:
                    body["ecm_excluded_edge_intervals"] += 1
                    body["partial"] = True
    for session in sessions:
        body = session["body"]
        if body["covered_seconds"] < (stop if session["end"] is None else session["end"]) - session["start"]:
            body["partial"] = True
        body["ecm_energy_status"] = "partial" if body["partial"] else "complete"
        if body["covered_seconds"] == 0:
            body["kwh"], body["ecm_energy_status"] = None, "unknown"
    return sessions
