"""Private application store and reproducible supply reports, independent of HA.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
"""

from collections.abc import Mapping
from contextlib import closing, contextmanager
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
import csv
import hashlib
import html
import io
import json
import math
from pathlib import Path
import re
import sqlite3
import time

from .accounting import Interval, _bounds, _timestamp
from .pricing import compare_scenarios, parse_scenario, _money
from .sessions import reconstruct_sessions, counter_sessions
from .regional import validate_regional, regional_bill

APP_ID = 0x45434D41
ZONES = {"SI", "AT", "DE-LU", "HR", "IT-North", "HU"}
MAX_SAMPLES = 250000


def plain(value):
    if is_dataclass(value):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    return value


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def validate_profile(profile):
    if (not isinstance(profile, dict) or not {"name", "scenarios", "indexed_import"} <= set(profile)
            or set(profile) - {"name", "scenarios", "indexed_import", "session_charging_kw", "session", "regional"}):
        raise ValueError("invalid_profile_fields")
    if not isinstance(profile["name"], str) or not 1 <= len(profile["name"].strip()) <= 100:
        raise ValueError("invalid_profile_name")
    if not isinstance(profile["scenarios"], list) or not 1 <= len(profile["scenarios"]) <= 8:
        raise ValueError("expected_one_to_eight_scenarios")
    threshold = profile.get("session_charging_kw", 0.1)
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 1000:
        raise ValueError("invalid_session_charging_threshold")
    if "session" in profile:
        limits = profile["session"]
        if not isinstance(limits, dict) or set(limits) != {"max_gap_seconds", "max_power_kw", "tolerance_kwh", "charging_kw", "charging_delta_kwh"}:
            raise ValueError("invalid_session_configuration")
        counter_sessions([], stop=0, **limits)
    if "regional" in profile:
        validate_regional(profile["regional"])
    scenarios = [parse_scenario(value) for value in profile["scenarios"]]
    ids = {s.identifier for s in scenarios}
    if len(ids) != len(scenarios):
        raise ValueError("duplicate_scenario")
    indexed = profile["indexed_import"]
    if not isinstance(indexed, dict) or not set(indexed) <= ids:
        raise ValueError("invalid_indexed_scenarios")
    for data in indexed.values():
        if not isinstance(data, dict) or set(data) != {"zone", "markup_eur_kwh"} or data["zone"] not in ZONES:
            raise ValueError("invalid_market_binding")
        if _money(data["markup_eur_kwh"], "markup") is None:
            raise ValueError("unknown_market_markup")
    # Offline legacy imports may include saved historical price periods. The
    # HTTP write limit remains 256 KB; larger imports are read-only in the card.
    if len(encoded(profile).encode()) > 2000000:
        raise ValueError("profile_too_large")
    return profile


def parse_market(payload, zone):
    """Energy-Charts v2 explicit resolution, never infer duration across gaps."""
    if (not isinstance(payload, dict) or payload.get("schema_version") != "2.0"
            or payload.get("endpoint") != "price" or payload.get("bidding_zone") != zone
            or payload.get("unit") != "EUR / MWh" or payload.get("interval_minutes") not in (15, 60)):
        raise ValueError("unsupported_market_response")
    if not isinstance(payload.get("data"), list) or len(payload["data"]) > 400:
        raise ValueError("invalid_market_size")
    rows, seen = [], set()
    for row in payload["data"]:
        if (not isinstance(row, dict) or not isinstance(row.get("timestamp"), str)
                or not isinstance(row.get("values"), dict)):
            raise ValueError("invalid_market_row")
        timestamp = datetime.fromisoformat(row["timestamp"])
        if timestamp.utcoffset() is None:
            raise ValueError("market_timestamp_without_offset")
        ts = _timestamp(timestamp.timestamp())
        if ts % 900:
            raise ValueError("unaligned_market_timestamp")
        value = row["values"]["day_ahead_price"]
        if isinstance(value, bool) or (value is not None and not isinstance(value, (int, float))):
            raise ValueError("invalid_market_price")
        price = None if value is None else _money(str(value), "market") / Decimal(1000)
        for offset in range(0, payload["interval_minutes"] * 60, 900):
            key = int(ts + offset)
            if key in seen:
                raise ValueError("overlapping_market_periods")
            seen.add(key)
            rows.append((key, None if price is None else str(price)))
    return rows


class ApplicationStore:
    """Separate schema, no automatic mutation of the metering database."""
    def __init__(self, path):
        self.path = Path(path).absolute()
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("xb"):
                pass
            with self.db(write=True) as db:
                db.execute(f"PRAGMA application_id={APP_ID}")
                db.execute("PRAGMA user_version=1")
                db.execute("CREATE TABLE profiles(id TEXT PRIMARY KEY,created REAL NOT NULL,body TEXT NOT NULL)")
                db.execute("CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
                db.execute("CREATE TABLE fetches(id TEXT PRIMARY KEY,captured REAL NOT NULL,zone TEXT NOT NULL,body TEXT NOT NULL)")
                db.execute("CREATE TABLE prices(zone TEXT,ts INTEGER,price TEXT,fetch_id TEXT,PRIMARY KEY(zone,ts))")
                db.execute("CREATE TABLE reports(id TEXT PRIMARY KEY,created REAL NOT NULL,body TEXT NOT NULL)")
            self.path.chmod(0o600)
        with self.db() as db:
            if (db.execute("PRAGMA application_id").fetchone()[0] != APP_ID
                    or db.execute("PRAGMA user_version").fetchone()[0] != 1):
                raise ValueError("unsupported_application_store")
            for query in ("SELECT id,created,body FROM profiles", "SELECT key,value FROM settings",
                          "SELECT id,captured,zone,body FROM fetches", "SELECT zone,ts,price,fetch_id FROM prices",
                          "SELECT id,created,body FROM reports"):
                db.execute(query + " LIMIT 0")

    @contextmanager
    def db(self, write=False):
        with closing(sqlite3.connect(self.path.as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True)) as db:
            db.execute("PRAGMA trusted_schema=OFF")
            if not write:
                db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            with db:
                yield db

    def save_profile(self, profile, now=None):
        body = encoded(validate_profile(profile))
        ident = hashlib.sha256(body.encode()).hexdigest()
        with self.db(True) as db:
            db.execute("INSERT OR IGNORE INTO profiles VALUES(?,?,?)", (ident, time.time() if now is None else now, body))
            db.execute("INSERT OR REPLACE INTO settings VALUES('active_profile',?)", (ident,))
        return ident

    def profiles(self):
        with self.db() as db:
            active = db.execute("SELECT value FROM settings WHERE key='active_profile'").fetchone()
            return {"active": active[0] if active else None,
                    "versions": [{"id": i, "created": t, "profile": json.loads(b)}
                                 for i, t, b in db.execute("SELECT * FROM profiles ORDER BY created DESC LIMIT 100")]}

    def activate(self, ident):
        with self.db(True) as db:
            if not db.execute("SELECT 1 FROM profiles WHERE id=?", (ident,)).fetchone():
                raise ValueError("unknown_profile")
            db.execute("INSERT OR REPLACE INTO settings VALUES('active_profile',?)", (ident,))

    def active_profile(self, db):
        row = db.execute("SELECT p.id,p.body FROM profiles p JOIN settings s ON s.value=p.id WHERE s.key='active_profile'").fetchone()
        return (row[0], json.loads(row[1])) if row else (None, None)

    def market_bindings(self):
        with self.db() as db:
            _, profile = self.active_profile(db)
            return sorted({v["zone"] for v in profile["indexed_import"].values()}) if profile else []

    def store_market(self, zone, payload, captured):
        if zone not in ZONES:
            raise ValueError("unsupported_zone")
        rows = parse_market(payload, zone)
        if not rows:
            raise ValueError("empty_market_response")
        body = encoded(payload)
        ident = hashlib.sha256(body.encode()).hexdigest()
        with self.db(True) as db:
            db.execute("INSERT OR IGNORE INTO fetches VALUES(?,?,?,?)", (ident, captured, zone, body))
            for ts, price in rows:
                # A null retry cannot erase an earlier usable published quote.
                db.execute("INSERT INTO prices VALUES(?,?,?,?) ON CONFLICT(zone,ts) DO UPDATE SET "
                           "price=excluded.price,fetch_id=excluded.fetch_id WHERE excluded.price IS NOT NULL OR prices.price IS NULL",
                           (zone, ts, price, ident))
        return len(rows)

    def market_status(self):
        with self.db() as db:
            return [{"zone": z, "last_fetch": c} for z, c in db.execute("SELECT zone,MAX(captured) FROM fetches GROUP BY zone")]

    def view(self, engine, start, end, *, now=None, include_sessions=True):
        start, end = _bounds(start, end)
        if include_sessions and end - start > 32 * 86400:
            raise ValueError("window_exceeds_32_days")
        now = _timestamp(time.time() if now is None else now)
        if end > now:
            raise ValueError("window_not_closed")
        session_stop = now if now - end < 900 else end
        # One ledger read transaction freezes samples and allocations together.
        with engine._db() as ledger:
            stored = {(ts, role): (energy, seconds) for ts, role, energy, seconds in ledger.execute(
                "SELECT start,role,kwh,seconds FROM intervals WHERE start>=? AND start<?", (start, end))}
            sample_rows = ledger.execute("SELECT ts,body FROM samples WHERE ts>=? AND ts<=? ORDER BY ts LIMIT ?",
                                         (start, session_stop, MAX_SAMPLES + 1)).fetchall() if include_sessions else []
            if len(sample_rows) > MAX_SAMPLES:
                raise ValueError("too_many_samples_choose_shorter_window")
            ev_rows = ledger.execute("SELECT start,kwh,seconds FROM intervals WHERE role='ev' AND start>=? AND start+900<=?",
                                     (start, session_stop)).fetchall()
            latest = ledger.execute("SELECT MAX(ts) FROM samples").fetchone()[0]
            archived_sessions = []
            migration = ledger.execute("SELECT value FROM meta WHERE key='migration'").fetchone()
            if migration and include_sessions:
                cutover = json.loads(migration[0])["cutover"]
                for ident, begin, stop, body in ledger.execute(
                    "SELECT * FROM legacy_sessions WHERE start<? AND (end IS NULL OR end>?) ORDER BY start",
                    (min(session_stop, cutover), start)
                ):
                    if start >= cutover:
                        continue
                    data = json.loads(body)
                    data["ecm_semantics"] = "legacy_archived_not_recomputed"
                    if stop is None or stop > cutover:
                        data["partial"] = True
                    archived_sessions.append({"id": ident, "start": begin, "end": min(stop, cutover) if stop is not None else cutover,
                                              "original_end": stop, "body": data, "legacy": True})
        intervals = []
        for ts in range(start, end, 900):
            energy, seconds, complete = {}, {}, {}
            for role in engine.roles:
                energy[role], seconds[role] = stored.get((ts, role), (None, 0))
                complete[role] = math.isclose(seconds[role], 900, abs_tol=1e-6)
            intervals.append(Interval(ts, energy, seconds, complete))
        with self.db() as db:
            profile_id, profile = self.active_profile(db)
            scenarios, provenance = [], {}
            if profile:
                for original in profile["scenarios"]:
                    scenario = json.loads(encoded(original))
                    binding = profile["indexed_import"].get(scenario["id"])
                    if binding:
                        quotes = db.execute("SELECT ts,price,fetch_id FROM prices WHERE zone=? AND ts>=? AND ts<? ORDER BY ts",
                                            (binding["zone"], start, end)).fetchall()
                        for version in scenario["versions"]:
                            first = datetime.fromisoformat(version["from"]).timestamp()
                            last = datetime.fromisoformat(version["until"]).timestamp()
                            version["import"] = []
                            for ts, price, fetch_id in quotes:
                                if first <= ts and ts + 900 <= last:
                                    value = None if price is None else str(Decimal(price) + Decimal(binding["markup_eur_kwh"]))
                                    version["import"].append({"from": datetime.fromtimestamp(ts, timezone.utc).isoformat(),
                                        "until": datetime.fromtimestamp(ts+900, timezone.utc).isoformat(),
                                        "value": value, "unit": "EUR/kWh", "source": "Energy-Charts.info " + binding["zone"],
                                        "status": "unknown" if value is None else "reference"})
                                    if fetch_id not in provenance:
                                        raw = json.loads(db.execute("SELECT body FROM fetches WHERE id=?", (fetch_id,)).fetchone()[0])
                                        provenance[fetch_id] = {"source": "Energy-Charts.info", "license": raw.get("license", "See provider publishing notes"),
                                                                "interval_minutes": raw["interval_minutes"]}
                    scenarios.append(parse_scenario(scenario))
            scope = "import_export" if "export" in engine.roles else "import_only"
            comparison = plain(compare_scenarios(intervals, scenarios, start=start, end=end, scope=scope)) if scenarios else None
        if profile and "session" in profile:
            sessions = counter_sessions(((ts, json.loads(body)) for ts, body in sample_rows),
                                        stop=session_stop, **profile["session"])
        else:
            sessions = reconstruct_sessions(((ts, json.loads(body)) for ts, body in sample_rows), ev_rows,
                                            stop=session_stop, max_gap_seconds=engine.max_gap_seconds, close_open=False,
                                            charging_kw=profile.get("session_charging_kw", 0.1) if profile else 0.1)
        sessions = sorted(archived_sessions + sessions, key=lambda item: item["start"])
        bills = ({result["scenario"]["identifier"]: regional_bill(intervals, result, profile["regional"],
                    start=start, end=end, export_enabled="export" in engine.roles)
                  for result in comparison["results"]} if profile and "regional" in profile and comparison else {})
        return {"schema_version": 1, "start": start, "end": end, "as_of": now, "latest_sample": latest,
                "profile_id": profile_id, "profile": profile, "comparison": comparison,
                "regional_bills": bills,
                "sessions_included": include_sessions,
                "intervals": plain(intervals), "sessions": sessions, "market_provenance": provenance,
                "limits": ["Supply comparison excludes regional components; configured regional estimates are separate and are not an invoice or payment balance", "Session edge energy may be unknown",
                           "Energy-Charts is a reference, not a confirmed supplier billing index"]}

    def freeze(self, engine, start, end, now=None, *, include_sessions=True):
        captured = time.time() if now is None else now
        if end > captured:
            raise ValueError("window_not_closed")
        data = self.view(engine, start, end, now=end, include_sessions=include_sessions)
        data["frozen_at"] = captured
        body = encoded(data)
        ident = hashlib.sha256(body.encode()).hexdigest()
        with self.db(True) as db:
            db.execute("INSERT OR IGNORE INTO reports VALUES(?,?,?)", (ident, captured, body))
        return ident

    def reports(self):
        with self.db() as db:
            return [{"id": i, "created": t, "start": json.loads(b)["start"], "end": json.loads(b)["end"],
                     "legacy": json.loads(b).get("kind") == "legacy_frozen"}
                    for i, t, b in db.execute("SELECT * FROM reports ORDER BY created DESC LIMIT 100")]

    def report(self, ident):
        if not isinstance(ident, str) or not re.fullmatch(r"[0-9a-f]{64}", ident):
            raise ValueError("invalid_report_id")
        with self.db() as db:
            row = db.execute("SELECT body FROM reports WHERE id=?", (ident,)).fetchone()
            if row is None:
                raise ValueError("unknown_report")
            return json.loads(row[0])


def render_report(data, format):
    if data.get("kind") == "legacy_frozen":
        original = data["original_body"]
        if hashlib.sha256(original.encode()).hexdigest() != data["original_sha256"]:
            raise ValueError("legacy_report_changed")
        if format == "csv":
            return json.loads(original)["csv"]
        if format != "html":
            raise ValueError("unsupported_report_format")
        # Never execute saved legacy HTML. Retain all original evidence as text.
        return ("<!doctype html><meta charset=utf-8><title>Archived Energy Cost Monitor report</title>"
                "<h1>Archived legacy report</h1><p>Historical calculation, not recalculated; "
                "not validated as a current bill.</p><pre>" + html.escape(original) + "</pre>")
    if format == "html":
        def esc(value):
            return html.escape("unknown" if value is None else str(value))
        rows = "".join("<tr>" + "".join("<td>" + esc(value) + "</td>" for value in (
            result["scenario"]["identifier"], result["total"], result["known_net_subtotal"],
            result["coverage"], result["confirmed"])) + "</tr>"
            for result in (data.get("comparison") or {}).get("results", []))
        return ("<!doctype html><meta charset=utf-8><title>Energy Cost Monitor</title>"
                "<h1>Energy Cost Monitor — frozen evidence</h1><p>The supply table excludes regional charges. Any configured regional estimates are retained in the frozen data below. This report is not an invoice or a payment balance.</p>"
                "<p>Profile version: " + esc(data["profile_id"]) + "</p>"
                "<table border=1><tr><th>Scenario</th><th>Full covered total EUR</th><th>Known subtotal EUR</th><th>Coverage</th><th>Confirmed</th></tr>"
                + rows + "</table><h2>Frozen data, sources and assumptions</h2><pre>"
                + html.escape(json.dumps(data, ensure_ascii=False, indent=2)) + "</pre>")
    if format != "csv":
        raise ValueError("unsupported_report_format")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    attribution = "; ".join("Energy-Charts.info: " + str(source["license"]) for source in data["market_provenance"].values())
    writer.writerow(["record", "start_utc", "role_or_scenario", "energy_kwh", "covered_seconds", "complete",
                     "import_cost_eur", "export_credit_eur", "subscription_eur", "net_eur", "reference", "profile_version", "market_attribution"])
    for row in data["intervals"]:
        for role, energy in row["energy_kwh"].items():
            writer.writerow(["energy", datetime.fromtimestamp(row["start"], timezone.utc).isoformat(), role,
                             "" if energy is None else energy, row["covered_seconds"][role],
                             row["complete"][role], "", "", "", "", "", data["profile_id"] or "", attribution])
    for result in (data.get("comparison") or {}).get("results", []):
        for row in result["intervals"]:
            writer.writerow(["supply", datetime.fromtimestamp(row["start"], timezone.utc).isoformat(),
                             result["scenario"]["identifier"], "", "", row["net_cost"] is not None,
                             row["import_cost"], row["export_credit"], row["subscription_cost"], row["net_cost"],
                             row["reference"], data["profile_id"] or "", attribution])
    return output.getvalue()
