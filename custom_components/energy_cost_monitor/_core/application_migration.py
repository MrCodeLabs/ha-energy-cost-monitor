"""Offline conversion of legacy supply profiles and frozen report evidence.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
No network requests, automatic activation in HA or regional billing conversion.
"""

from contextlib import closing
from datetime import date, datetime, time, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import math
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo

from .application import ApplicationStore, encoded, validate_profile
from .migration import _publish, _ro, _validate_legacy
from .pricing import _money


def _amount(value):
    if isinstance(value, bool):
        raise ValueError("invalid_legacy_amount")
    if isinstance(value, float) and math.isfinite(value) and abs(value) <= 1000000000:
        # Legacy SQLite REAL values have binary tails. The original stays in the
        # archive; conversion explicitly rounds to the price model's 12 places.
        value = Decimal(str(value)).quantize(Decimal("0.000000000001"), rounding=ROUND_HALF_UP)
    return _money(None if value is None else str(value), "legacy")


def _quote(value, source, monthly=False):
    if value is not None:
        value = value.quantize(Decimal("0.000000000001"), rounding=ROUND_HALF_UP).normalize()
    return {"value": None if value is None else str(value),
            "unit": "EUR/month" if monthly else "EUR/kWh", "source": source,
            "status": "unknown" if value is None else "reference"}


def _price_periods(prices, basis):
    if basis not in {"quarter_hour", "hourly_reference"}:
        raise ValueError("unsupported_legacy_market_basis")
    previous = None
    hours = {}
    result = []
    for ts, duration, value, captured in prices:
        if duration not in (900, 3600) or ts % 900 or (duration == 3600 and ts % 3600):
            raise ValueError("unsupported_legacy_price_period")
        if previous is not None and ts < previous:
            raise ValueError("overlapping_legacy_prices")
        previous = ts + duration
        amount = _amount(value)
        result.append((ts, duration, amount, captured))
        hours.setdefault(ts // 3600 * 3600, []).append((duration, amount))
    if basis == "quarter_hour":
        return result
    # Real UTC hours preserve repeated local DST hours. An incomplete hour is
    # unknown, even if a subset of its quarter-hour prices is available.
    return [(ts, 3600, sum((Decimal(d)*p for d, p in rows), Decimal(0))/3600
             if sum(d for d, _ in rows) == 3600 and all(p is not None for _, p in rows) else None, None)
            for ts, rows in sorted(hours.items())]


def convert_profile(legacy, prices, *, horizon):
    """Convert supply only, bounded by an explicit exclusive local-date horizon.

    Indexed imports AND exports use the saved reference quotes. No live binding
    is enabled. Missing quotes and unsupported averaging must not become zero.
    The complete original profile remains in the archived legacy ledger.
    """
    if legacy.get("schema_version") != 1:
        raise ValueError("unsupported_legacy_profile")
    zone = ZoneInfo(legacy["timezone"])
    limit = date.fromisoformat(horizon)
    def instant(day):
        return datetime.combine(date.fromisoformat(day), time.min, zone).isoformat()
    result = {"name": "Imported legacy supply (reference)", "scenarios": [], "indexed_import": {}}
    for index, (name, versions) in enumerate(legacy["suppliers"].items()):
        scenario = {"schema_version": 1, "id": f"legacy-{index+1}", "currency": "EUR",
                    "tax_basis": "excluding_vat", "timezone": legacy["timezone"], "versions": []}
        for number, original in enumerate(versions):
            first = date.fromisoformat(original["from"])
            last = min(date.fromisoformat(original["until"]), limit) if original.get("until") else limit
            if first >= limit:
                continue
            if last <= first:
                raise ValueError("invalid_legacy_validity")
            start, end = instant(first.isoformat()), instant(last.isoformat())
            source = f"Legacy {name}: {original.get('source') or 'unverified source'}"
            monthly, discount = _amount(original.get("monthly_net")), _amount(original.get("discount_net"))
            version = {"id": f"version-{number+1}", "from": start, "until": end,
                       "subscription": _quote(None if monthly is None or discount is None else monthly-discount,
                                              source, True)}
            for side in ("import", "export"):
                direct, indexed = side + "_net", side + "_markup_net"
                if direct in original and indexed in original:
                    raise ValueError("ambiguous_legacy_price")
                if indexed not in original:
                    version[side] = [{"from": start, "until": end, **_quote(_amount(original.get(direct)), source)}]
                    continue
                periods_source = _price_periods(prices, legacy.get("market", {}).get("basis"))
                markup = _amount(original[indexed])
                low, high = datetime.fromisoformat(start).timestamp(), datetime.fromisoformat(end).timestamp()
                periods = []
                for ts, duration, amount, _captured in periods_source:
                    begin, stop = max(ts, low), min(ts + duration, high)
                    if begin >= stop:
                        continue
                    quote = _quote(None if amount is None or markup is None else amount + markup, source)
                    periods.append({"from": datetime.fromtimestamp(begin, timezone.utc).isoformat(),
                                    "until": datetime.fromtimestamp(stop, timezone.utc).isoformat(), **quote})
                version[side] = periods
            scenario["versions"].append(version)
        if scenario["versions"]:
            result["scenarios"].append(scenario)
    return validate_profile(result)


def migrate_application(source, destination, *, horizon, active_profile):
    """Build a fresh app store; publish only after every source row is processed.

    Caller supplies an offline legacy snapshot and the chosen original profile
    hash. Existing destinations and the original database are never modified.
    """
    destination = Path(destination).absolute()
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(_ro(source)) as original, tempfile.TemporaryDirectory(
        prefix="ecm-app-migrate-", dir=destination.parent
    ) as temporary:
        original.execute("BEGIN")
        _validate_legacy(original)
        profiles = original.execute("SELECT hash,captured,body FROM profiles ORDER BY rowid").fetchall()
        if active_profile not in {row[0] for row in profiles}:
            raise ValueError("explicit_active_legacy_profile_required")
        prices = original.execute("SELECT ts,duration,eur_kwh,captured FROM prices ORDER BY ts").fetchall()
        store = ApplicationStore(Path(temporary) / "application.sqlite3")
        mapping = {}
        for ident, captured, body in profiles:
            profile = convert_profile(json.loads(body), prices, horizon=horizon)
            mapping[ident] = store.save_profile(profile, now=captured)
        store.activate(mapping[active_profile])
        reports = {}
        with store.db(True) as target:
            for ident, start, end, generated, body in original.execute("SELECT * FROM reports ORDER BY rowid"):
                data = json.loads(body)
                if not isinstance(data, dict) or not isinstance(data.get("csv"), str):
                    raise ValueError("unsupported_legacy_report")
                if not start < end <= generated:
                    raise ValueError("invalid_legacy_report_window")
                frozen = {"kind": "legacy_frozen", "legacy_id": ident, "start": start, "end": end,
                          "frozen_at": generated, "original_body": body,
                          "original_sha256": hashlib.sha256(body.encode()).hexdigest(),
                          "limits": ["Historical legacy calculation; not recalculated or validated as a current bill"]}
                serialized = encoded(frozen)
                key = hashlib.sha256(serialized.encode()).hexdigest()
                target.execute("INSERT INTO reports VALUES(?,?,?)", (key, generated, serialized))
                reports[ident] = key
        evidence = {"version": 1, "horizon_exclusive_local_date": horizon, "profiles": mapping, "reports": reports,
                    "price_rounding": "12 decimal places, ROUND_HALF_UP; original REAL values retained in archive",
                    "live_price_fetch_enabled": False, "regional_bill_converted": False,
                    "original_archive_required": True}
        with store.db(True) as target:
            target.execute("INSERT INTO settings VALUES('legacy_conversion',?)", (encoded(evidence),))
        _publish(store.path, destination)
        return evidence


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--horizon", required=True, help="Exclusive local YYYY-MM-DD; not a new contract expiry")
    parser.add_argument("--active-profile", required=True, help="Original profile hash to select explicitly")
    args = parser.parse_args()
    evidence = migrate_application(args.source, args.destination, horizon=args.horizon, active_profile=args.active_profile)
    print(json.dumps({"result": "PASS", "profiles": len(evidence["profiles"]), "reports": len(evidence["reports"])}))


if __name__ == "__main__":
    main()
