"""Offline compatibility export; preserve allocations, never replay counters.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
"""

from contextlib import closing
import json
import math
from pathlib import Path
import sqlite3
import tempfile

from .accounting import INTERVAL_SECONDS, _timestamp
from .migration import _publish, _ro, export_legacy, restore_bundle
from .sessions import reconstruct_sessions


def reconcile_legacy(bundle, destination, config, *, resume_at, signal_mapping=None, max_gap_seconds=300):
    """Produce a legacy-format database from a verified recovery bundle.

    The bundle is retained as the authoritative record of both eras. Stop the
    new writer before taking it. Resume time is aligned and strictly follows
    captured samples; the old application's first sample cannot bridge eras.
    """
    resume_at = _timestamp(resume_at)
    if resume_at % INTERVAL_SECONDS:
        raise ValueError("unaligned_resume")
    destination = Path(destination).absolute()
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ecm-reconcile-", dir=destination.parent) as temporary:
        work = Path(temporary)
        ledger, output = work / "ledger.sqlite3", work / "legacy.sqlite3"
        report = restore_bundle(bundle, ledger, config, max_gap_seconds=max_gap_seconds)
        if (resume_at <= report["cutover"] or (report["latest_native_sample"] is not None
                                              and resume_at <= report["latest_native_sample"])):
            raise ValueError("resume_overlaps_native_history")
        export_legacy(ledger, output)
        with closing(_ro(ledger)) as source, closing(sqlite3.connect(output)) as target, target:
            manifest = json.loads(source.execute("SELECT value FROM meta WHERE key='migration'").fetchone()[0])
            mapping = dict(manifest["role_mapping"])
            signals = {} if signal_mapping is None else dict(signal_mapping)
            if set(signals) != set(config.sources) - set(config.required_roles):
                raise ValueError("explicit_signal_mapping_required")
            mapping.update(signals)
            if (any(not isinstance(value, str) or not value or value.startswith("ecm_") for value in mapping.values())
                    or len(set(mapping.values())) != len(mapping)):
                raise ValueError("ambiguous_legacy_mapping")
            count = 0
            with closing(source.execute("SELECT start,role,kwh,seconds FROM intervals WHERE start>=? "
                                        "ORDER BY start,role", (report["cutover"],))) as rows:
                for ts, role, kwh, seconds in rows:
                    if (ts % INTERVAL_SECONDS or ts + INTERVAL_SECONDS > resume_at
                            or role not in config.required_roles or not math.isfinite(kwh) or kwh < 0
                            or not math.isfinite(seconds) or not 0 < seconds <= INTERVAL_SECONDS):
                        raise ValueError("invalid_native_interval")
                    existing = target.execute("SELECT body FROM intervals WHERE ts=?", (ts,)).fetchone()
                    body = json.loads(existing[0]) if existing else {
                        "energy": {}, "seconds": {}, "flags": ["ecm:report_time_allocation"],
                        "signals": {}, "signal_seconds": {},
                    }
                    metric = mapping[role]
                    if metric in body["energy"]:
                        raise ValueError("legacy_interval_collision")
                    body["energy"][metric], body["seconds"][metric] = kwh, seconds
                    target.execute("INSERT OR REPLACE INTO intervals VALUES(?,?)", (ts, json.dumps(body)))
                    count += 1
            with closing(source.execute("SELECT ts,body FROM samples ORDER BY ts")) as rows:
                for ts, raw in rows:
                    readings, flat = json.loads(raw), {}
                    for role, metric in mapping.items():
                        reading = readings.get(role)
                        value = reading.get("value") if reading and reading.get("quality") in {"valid", "estimated"} else None
                        kind = config.sources[role].kind
                        if value is not None and kind == "binary":
                            value = "on" if value else "off"
                        elif value is not None and kind == "power":
                            value *= 1000  # Public normalized kW -> legacy W.
                        flat[metric] = value
                    flat["ecm_semantics"] = "normalized_snapshot_not_replayed"
                    target.execute("INSERT INTO samples VALUES(?,?)", (ts, json.dumps(flat, allow_nan=False)))
            # Keep anomalies as unallocated evidence, never as energy intervals.
            with closing(source.execute("SELECT ts,role,reason,unassigned_kwh FROM anomalies ORDER BY id")) as rows:
                for ts, role, reason, unassigned in rows:
                    target.execute("INSERT INTO anomalies(ts,metric,reason,kwh) VALUES(?,?,?,?)",
                                   (ts, mapping.get(role, role), "ecm:" + reason, unassigned))
            # An open pre-migration session cannot describe the unobserved era.
            active = target.execute("SELECT id,start,body FROM sessions WHERE end IS NULL").fetchall()
            for ident, start, raw in active:
                if start > report["cutover"]:
                    raise ValueError("legacy_session_overlaps_cutover")
                body = json.loads(raw)
                body["partial"] = True
                body.setdefault("events", []).append({"ts": report["cutover"], "state": "gap", "mode": {}})
                body["ecm_end_reason"] = "migration_boundary_not_observed_disconnect"
                target.execute("UPDATE sessions SET end=?,body=? WHERE id=?",
                               (report["cutover"], json.dumps(body), ident))
            reconstructed = []
            if {"ev", "ev_connected"} <= set(config.sources):
                # No native session is silently joined to an archived session.
                with (closing(source.execute("SELECT ts,body FROM samples ORDER BY ts")) as samples,
                      closing(source.execute("SELECT start,kwh,seconds FROM intervals WHERE role='ev' "
                                             "AND start>=? ORDER BY start", (report["cutover"],))) as ev_rows):
                    reconstructed = reconstruct_sessions(((ts, json.loads(raw)) for ts, raw in samples),
                                                         ev_rows, stop=resume_at, max_gap_seconds=max_gap_seconds)
                for session in reconstructed:
                    target.execute("INSERT INTO sessions(start,end,body) VALUES(?,?,?)",
                                   (session["start"], session["end"], json.dumps(session["body"])))
            # Empty synthetic barrier prevents old aggregation/session code from
            # bridging its next real sample to a report-time counter baseline.
            target.execute("INSERT INTO samples VALUES(?,?)",
                           (resume_at, '{"ecm_semantics":"resume_barrier_not_measurement"}'))
            evidence = {"version": 1, "cutover": report["cutover"], "resume_at": resume_at,
                        "native_role_intervals": count, "native_samples": report["native_samples"],
                        "closed_partial_sessions": len(active), "full_application_parity": False,
                        "reconstructed_sessions": len(reconstructed),
                        "missing_workflows": ["live_session_workflow", "signal_integrals", "new_frozen_reports"]}
            for key, value in {"meter_baselines": {}, "last_sample": resume_at,
                               "ecm_reconciliation": evidence}.items():
                target.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (key, json.dumps(value)))
        _publish(output, destination)
        return evidence


def main():
    import argparse
    from .sources import parse_config
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--resume-at", type=float, required=True)
    parser.add_argument("--signal-mapping", type=Path)
    parser.add_argument("--max-gap-seconds", type=float, default=300)
    args = parser.parse_args()
    config = parse_config(json.loads(args.config.read_text(encoding="utf-8")))
    signals = json.loads(args.signal_mapping.read_text(encoding="utf-8")) if args.signal_mapping else None
    reconcile_legacy(args.bundle, args.destination, config, resume_at=args.resume_at,
                     signal_mapping=signals, max_gap_seconds=args.max_gap_seconds)
    print("Compatibility export created. Bundle retained; no application activated.")


if __name__ == "__main__":
    main()
