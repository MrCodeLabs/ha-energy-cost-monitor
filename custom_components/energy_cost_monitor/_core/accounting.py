"""Cumulative-meter ledger, adapted from the owner's private prototype.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
See docs/provenance.md for the reviewed extraction boundary.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from types import MappingProxyType

from .observations import Observation, normalize_snapshot
from .sources import SourceConfig


INTERVAL_SECONDS = 900
MAX_QUERY_INTERVALS = 400 * 96
APPLICATION_ID = 0x45434D31
SCHEMA_VERSION = 1
MIGRATED_SCHEMA_VERSION = 2


def _timestamp(value: float) -> float:
    if type(value) not in (int, float):
        raise ValueError("invalid_timestamp")
    try:
        value = float(value)
    except OverflowError:
        raise ValueError("invalid_timestamp") from None
    if not math.isfinite(value) or not 0 <= value <= 253402300799:
        raise ValueError("invalid_timestamp")
    return value


def _bounds(start: float, end: float) -> tuple[int, int]:
    start, end = _timestamp(start), _timestamp(end)
    if (start % INTERVAL_SECONDS or end % INTERVAL_SECONDS or start >= end
            or (end - start) / INTERVAL_SECONDS > MAX_QUERY_INTERVALS):
        raise ValueError("expected_aligned_window_of_at_most_400_days")
    return int(start), int(end)


@dataclass(frozen=True)
class Interval:
    start: int
    energy_kwh: Mapping[str, float | None]
    covered_seconds: Mapping[str, float]
    complete: Mapping[str, bool]

    @property
    def ready(self) -> bool:
        """All configured cumulative meters cover this interval."""
        return all(self.complete.values())


@dataclass(frozen=True)
class Summary:
    start: int
    end: int
    expected_intervals: int
    energy_kwh: Mapping[str, float | None]
    coverage: Mapping[str, float]
    joint_coverage: float


class AccountingEngine:
    """Synchronous SQLite ledger; call from a serialized executor in a future HA adapter.

    Each operation opens and closes its own connection. A fresh path creates a
    dedicated database. Existing files must match both schema and configuration;
    this class never upgrades, clears or replaces an existing database.
    """

    def __init__(self, path: Path | str, config: SourceConfig, *, max_gap_seconds: float,
                 sampling_mode: str = "collection"):
        if sampling_mode not in {"collection", "report"}:
            raise ValueError("unsupported_sampling_mode")
        self.sampling_mode = sampling_mode
        max_gap_seconds = _timestamp(max_gap_seconds)
        if not 0 < max_gap_seconds <= INTERVAL_SECONDS:
            raise ValueError("max_gap_seconds_must_be_between_zero_and_900")
        self.path = Path(path).absolute()
        self.config = config
        self.max_gap_seconds = max_gap_seconds
        self.roles = tuple(sorted(config.required_roles))
        if not self.roles:
            raise ValueError("no_cumulative_meters")
        identity = {
            "capabilities": sorted(config.capabilities),
            "sources": {role: asdict(source) for role, source in config.sources.items()},
            "max_gap_seconds": max_gap_seconds,
        }
        # Preserve the identity of existing collection-time databases. Report
        # time ledgers cannot silently reopen them with different semantics.
        if sampling_mode != "collection":
            identity["sampling_mode"] = sampling_mode
        self._identity = hashlib.sha256(
            json.dumps(identity, sort_keys=True, allow_nan=False).encode("utf-8")
        ).hexdigest()
        if self.path.exists():
            self._validate_database()
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation prevents a race from opening somebody else's DB.
            with self.path.open("xb"):
                pass
            self._initialize()

    @contextmanager
    def _db(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        mode = "rw" if write else "ro"
        db = sqlite3.connect(self.path.as_uri() + f"?mode={mode}", uri=True, timeout=15)
        try:
            if write:
                db.execute("PRAGMA synchronous=FULL")
                db.execute("BEGIN IMMEDIATE")
            with db:
                yield db
        finally:
            db.close()

    def _initialize(self) -> None:
        with self._db(write=True) as db:
            db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("CREATE TABLE samples(ts REAL PRIMARY KEY, body TEXT NOT NULL)")
            db.execute("CREATE TABLE baselines(role TEXT PRIMARY KEY, ts REAL NOT NULL, "
                       "value REAL NOT NULL, continuous INTEGER NOT NULL)")
            db.execute("CREATE TABLE intervals(start INTEGER NOT NULL, role TEXT NOT NULL, "
                       "kwh REAL NOT NULL, seconds REAL NOT NULL, PRIMARY KEY(start, role))")
            db.execute("CREATE TABLE anomalies(id INTEGER PRIMARY KEY, ts REAL NOT NULL, "
                       "role TEXT NOT NULL, reason TEXT NOT NULL, delta_kwh REAL, unassigned_kwh REAL)")
            db.execute("INSERT INTO meta VALUES('identity', ?)", (self._identity,))
            db.execute(f"PRAGMA application_id={APPLICATION_ID}")
            db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    def _validate_database(self) -> None:
        try:
            with self._db() as db:
                version = db.execute("PRAGMA user_version").fetchone()[0]
                if (db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                        or version not in {SCHEMA_VERSION, MIGRATED_SCHEMA_VERSION}):
                    raise ValueError("unsupported_database")
                if version == MIGRATED_SCHEMA_VERSION:
                    migration = db.execute("SELECT value FROM meta WHERE key='migration'").fetchone()
                    cutover = db.execute("SELECT value FROM meta WHERE key='collection_not_before'").fetchone()
                    if migration is None or cutover is None:
                        raise ValueError("missing_migration_boundary")
                    try:
                        record = json.loads(migration[0])
                        boundary = _timestamp(float(cutover[0]))
                        if record["version"] != 1 or record["cutover"] != boundary or boundary % INTERVAL_SECONDS:
                            raise ValueError("invalid_migration_boundary")
                    except (ValueError, TypeError, KeyError):
                        raise ValueError("invalid_migration_boundary") from None
                identity = db.execute("SELECT value FROM meta WHERE key='identity'").fetchone()
                if identity is None or identity[0] != self._identity:
                    raise ValueError("database_configuration_mismatch")
                # Fail on missing tables/columns before any attempt to collect.
                db.execute("SELECT ts, body FROM samples LIMIT 0")
                db.execute("SELECT role, ts, value, continuous FROM baselines LIMIT 0")
                db.execute("SELECT start, role, kwh, seconds FROM intervals LIMIT 0")
                db.execute("SELECT ts, role, reason, delta_kwh, unassigned_kwh FROM anomalies LIMIT 0")
        except sqlite3.DatabaseError:
            raise ValueError("unsupported_database") from None

    def ingest(self, timestamp: float, observations: Mapping[str, Observation]) -> bool:
        """Atomically collect a snapshot; ignore duplicate or older collection times.

        Report mode uses each meter's report time and ignores repeated reads of
        the same report. Neither mode makes uniform allocation a measurement.
        Daily estimates are stored but never differenced.
        """
        timestamp = _timestamp(timestamp)
        with self._db(write=True) as db:
            cutover = db.execute("SELECT value FROM meta WHERE key='collection_not_before'").fetchone()
            if cutover is not None and timestamp < float(cutover[0]):
                raise ValueError("sample_precedes_migration_cutover")
            latest = db.execute("SELECT MAX(ts) FROM samples").fetchone()[0]
            if latest is not None and timestamp <= latest:
                return False
            snapshot = normalize_snapshot(self.config, observations, now=timestamp)
            body = json.dumps({role: asdict(reading) for role, reading in snapshot.readings.items()},
                              allow_nan=False)
            db.execute("INSERT INTO samples VALUES(?, ?)", (timestamp, body))
            for role in self.roles:
                reading = snapshot.readings[role]
                previous = db.execute(
                    "SELECT ts, value, continuous FROM baselines WHERE role=?", (role,)
                ).fetchone()
                if not reading.usable:
                    db.execute("UPDATE baselines SET continuous=0 WHERE role=?", (role,))
                    self._anomaly(db, timestamp, role, reading.quality)
                    continue
                value = reading.value
                sample_time = timestamp
                if self.sampling_mode == "report":
                    sample_time = _timestamp(observations[self.config.sources[role].entity_id].reported_at)
                    if cutover is not None and sample_time < float(cutover[0]):
                        self._anomaly(db, timestamp, role, "report_precedes_migration_cutover")
                        continue
                    if previous is not None and sample_time <= previous[0]:
                        if sample_time < previous[0] or value != previous[1]:
                            db.execute("UPDATE baselines SET continuous=0 WHERE role=?", (role,))
                            self._anomaly(db, timestamp, role, "non_monotonic_report")
                        continue
                if previous is not None:
                    start, before, continuous = previous
                    elapsed = sample_time - start
                    delta = value - before
                    limit = self.config.sources[role].max_power_kw * (elapsed / 3600)
                    if delta < 0:
                        self._anomaly(db, timestamp, role, "counter_reset", delta)
                    elif delta > limit and not math.isclose(delta, limit, rel_tol=1e-9, abs_tol=1e-12):
                        self._anomaly(db, timestamp, role, "counter_jump", delta)
                    elif not continuous or elapsed > self.max_gap_seconds:
                        self._anomaly(db, timestamp, role, "gap", delta, delta)
                    else:
                        self._allocate(db, role, start, sample_time, delta)
                # A reset/jump starts a new baseline; its delta is never charged.
                db.execute("INSERT INTO baselines VALUES(?, ?, ?, 1) ON CONFLICT(role) "
                           "DO UPDATE SET ts=excluded.ts, value=excluded.value, continuous=1",
                           (role, sample_time, value))
        return True

    def break_continuity(self) -> None:
        """Do not bridge an adapter restart or collection failure with estimates."""
        with self._db(write=True) as db:
            db.execute("UPDATE baselines SET continuous=0")

    @staticmethod
    def _anomaly(db, timestamp, role, reason, delta=None, unassigned=None) -> None:
        db.execute("INSERT INTO anomalies(ts, role, reason, delta_kwh, unassigned_kwh) "
                   "VALUES(?, ?, ?, ?, ?)", (timestamp, role, reason, delta, unassigned))

    @staticmethod
    def _allocate(db, role: str, start: float, end: float, delta: float) -> None:
        cursor = start
        while cursor < end:
            bucket = int(cursor // INTERVAL_SECONDS) * INTERVAL_SECONDS
            stop = min(end, bucket + INTERVAL_SECONDS)
            seconds = stop - cursor
            db.execute("INSERT INTO intervals VALUES(?, ?, ?, ?) ON CONFLICT(start, role) "
                       "DO UPDATE SET kwh=kwh+excluded.kwh, seconds=seconds+excluded.seconds",
                       (bucket, role, delta * (seconds / (end - start)), seconds))
            cursor = stop

    def intervals(self, start: float, end: float) -> tuple[Interval, ...]:
        """Return every UTC bucket in [start, end), including entirely missing ones."""
        start, end = _bounds(start, end)
        with self._db() as db:
            rows = {(ts, role): (kwh, seconds) for ts, role, kwh, seconds in db.execute(
                "SELECT start, role, kwh, seconds FROM intervals WHERE start>=? AND start<?",
                (start, end),
            )}
        result = []
        for timestamp in range(start, end, INTERVAL_SECONDS):
            energy, covered, complete = {}, {}, {}
            for role in self.roles:
                energy[role], covered[role] = rows.get((timestamp, role), (None, 0.0))
                complete[role] = math.isclose(covered[role], INTERVAL_SECONDS, rel_tol=0, abs_tol=1e-6)
            result.append(Interval(timestamp, MappingProxyType(energy), MappingProxyType(covered),
                                   MappingProxyType(complete)))
        return tuple(result)

    def summary(self, start: float, end: float) -> Summary:
        """Totals are per role and may be partial; coverage always accompanies them."""
        start, end = _bounds(start, end)
        rows = self.intervals(start, end)
        energy, coverage = {}, {}
        for role in self.roles:
            values = [row.energy_kwh[role] for row in rows if row.energy_kwh[role] is not None]
            energy[role] = math.fsum(values) if values else None
            coverage[role] = sum(row.complete[role] for row in rows) / len(rows)
        return Summary(start, end, len(rows), MappingProxyType(energy), MappingProxyType(coverage),
                       sum(row.ready for row in rows) / len(rows))

    def anomalies(self) -> tuple[dict, ...]:
        """Diagnostics in collection order; rejected deltas are not measured energy."""
        with self._db() as db:
            rows = db.execute("SELECT ts, role, reason, delta_kwh, unassigned_kwh "
                              "FROM anomalies ORDER BY id").fetchall()
        return tuple(dict(zip(("timestamp", "role", "reason", "delta_kwh", "unassigned_kwh"), row))
                     for row in rows)

    def latest_observations(self) -> dict | None:
        """Return a detached snapshot, including daily estimates and signal quality."""
        with self._db() as db:
            row = db.execute("SELECT ts, body FROM samples ORDER BY ts DESC LIMIT 1").fetchone()
        return None if row is None else {"timestamp": row[0], "readings": json.loads(row[1])}
