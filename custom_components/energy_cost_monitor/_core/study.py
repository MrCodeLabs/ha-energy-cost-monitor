"""Persisted study warm-up and calendar report windows; no device control."""

import calendar
from datetime import datetime, time, timedelta
import json
import math
from zoneinfo import ZoneInfo


def validate_study(value):
    if not isinstance(value, dict) or set(value) != {
        "timezone",
        "months",
        "warmup_hours",
        "minimum_coverage",
        "require_daily_check",
        "daily_absolute_kwh",
        "daily_relative",
        "reference_age_seconds",
    }:
        raise ValueError("invalid_study_configuration")
    ZoneInfo(value["timezone"])
    if type(value["months"]) is not int or not 1 <= value["months"] <= 12:
        raise ValueError("invalid_study_months")
    if type(value["require_daily_check"]) is not bool:
        raise ValueError("invalid_daily_check_setting")
    for key, low, high in [
        ("warmup_hours", 1, 168),
        ("minimum_coverage", 0.5, 1),
        ("daily_absolute_kwh", 0, 100),
        ("daily_relative", 0, 1),
        ("reference_age_seconds", 1, 900),
    ]:
        v = value[key]
        if type(v) not in (float, int) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError("invalid_study_limit")
    return value


def add_months(local, months):
    index = local.year * 12 + local.month - 1 + months
    year, month = index // 12, index % 12 + 1
    return local.replace(
        year=year, month=month, day=min(local.day, calendar.monthrange(year, month)[1])
    )


def quality(engine, settings, now):
    stop = int(now // 900) * 900
    start = int((stop - settings["warmup_hours"] * 3600) // 900) * 900
    zone = ZoneInfo(settings["timezone"])
    today = datetime.fromtimestamp(now, zone).date()
    day_end = datetime.combine(today, time.min, zone).timestamp()
    day_start = datetime.combine(today - timedelta(days=1), time.min, zone).timestamp()
    with engine._db() as db:
        first = db.execute("SELECT MIN(ts) FROM samples").fetchone()[0]
        rows = {
            (t, r): s
            for t, r, s in db.execute(
                "SELECT start,role,seconds FROM intervals WHERE start>=? AND start<?",
                (start, stop),
            )
        }
        complete = sum(
            all(
                math.isclose(rows.get((t, r), 0), 900, abs_tol=1e-6)
                for r in engine.roles
            )
            for t in range(start, stop, 900)
        )
        daily = db.execute(
            "SELECT kwh,seconds FROM intervals WHERE role='house' AND start>=? AND start<?",
            (day_start, day_end),
        ).fetchall()
        candidates = db.execute(
            "SELECT body FROM samples WHERE ts>=? AND ts<? ORDER BY ts DESC LIMIT 3",
            (day_end - settings["reference_age_seconds"], day_end),
        ).fetchall()
    reference = None
    for (body,) in candidates:
        reading = json.loads(body).get("house_daily_reference", {})
        if reading.get("quality") in ("valid", "estimated") and type(
            reading.get("value")
        ) in (int, float):
            reference = reading["value"]
            break
    full = len(daily) == int((day_end - day_start) / 900) and all(
        math.isclose(s, 900, abs_tol=1e-6) for _, s in daily
    )
    measured = sum(k for k, _ in daily)
    difference = None if reference is None else measured - reference
    tolerance = (
        None
        if reference is None
        else max(settings["daily_absolute_kwh"], reference * settings["daily_relative"])
    )
    daily_status = (
        "insufficient"
        if not full or reference is None
        else "ok"
        if abs(difference) <= tolerance
        else "review"
    )
    coverage = complete / len(range(start, stop, 900))
    ready = (
        first is not None
        and stop - first >= settings["warmup_hours"] * 3600
        and coverage >= settings["minimum_coverage"]
        and (not settings["require_daily_check"] or daily_status == "ok")
    )
    return {
        "ready": ready,
        "coverage": coverage,
        "window_start": start,
        "window_end": stop,
        "daily": {
            "status": daily_status,
            "measured_kwh": measured,
            "reference_kwh": reference,
            "difference_kwh": difference,
            "tolerance_kwh": tolerance,
        },
        "daily_check_required": settings["require_daily_check"],
    }


class Study:
    def __init__(self, store):
        self.store = store

    def status(self):
        with self.store.db() as db:
            row = db.execute("SELECT value FROM settings WHERE key='study'").fetchone()
        return json.loads(row[0]) if row else {"state": "not_configured"}

    def save(self, state):
        from .application import encoded

        with self.store.db(True) as db:
            db.execute(
                "INSERT OR REPLACE INTO settings VALUES('study',?)", (encoded(state),)
            )
        return state

    def configure(self, settings):
        validate_study(settings)
        if self.status()["state"] in ("warmup", "running"):
            raise ValueError("study_already_running_cancel_first")
        return self.save({"state": "warmup", "settings": settings, "reports": {}})

    def cancel(self):
        state = self.status()
        state["state"] = "cancelled"
        return self.save(state)

    def advance(self, engine, now):
        state = self.status()
        if state["state"] not in ("warmup", "running"):
            return state
        settings = state["settings"]
        if state["state"] == "warmup":
            state["quality"] = quality(engine, settings, now)
            if not state["quality"]["ready"]:
                return self.save(state)
            zone = ZoneInfo(settings["timezone"])
            start = datetime.combine(
                datetime.fromtimestamp(now, zone).date() + timedelta(days=1),
                time.min,
                zone,
            )
            state.update(
                state="running",
                validated_at=now,
                windows=[
                    int(add_months(start, n).timestamp())
                    for n in range(settings["months"] + 1)
                ],
            )
            self.save(state)
        for index, (start, end) in enumerate(
            zip(state["windows"], state["windows"][1:])
        ):
            key = f"month-{index + 1}"
            if now >= end and key not in state["reports"]:
                state["reports"][key] = self.store.freeze(engine, start, end, now=now)
                self.save(state)
        if now >= state["windows"][-1] and "final" not in state["reports"]:
            state["reports"]["final"] = self.store.freeze(
                engine,
                state["windows"][0],
                state["windows"][-1],
                now=now,
                include_sessions=False,
            )
            state["state"] = "complete"
            self.save(state)
        return state
