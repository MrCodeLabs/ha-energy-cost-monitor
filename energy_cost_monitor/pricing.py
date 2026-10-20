"""Supply-only scenario comparison; no collection, network access or bill rules.

Copyright (c) 2026 MrCodeLabs
SPDX-License-Identifier: MIT
The owner's prototype informed validity and daily subscription allocation.
See docs/provenance.md. All configuration and fixtures are independently written.
"""

from __future__ import annotations

from bisect import bisect_right
import calendar
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import math
import re
from types import MappingProxyType
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .accounting import INTERVAL_SECONDS, Interval, _bounds
from .sources import ConfigurationError


ZERO = Decimal(0)
CENT = Decimal("0.01")


def _object(value, keys, path):
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise ConfigurationError(path, "expected_exact_fields")
    return value


def _identifier(value, path):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", value):
        raise ConfigurationError(path, "invalid_identifier")
    return value


def _instant(value, path):
    if not isinstance(value, str):
        raise ConfigurationError(path, "expected_offset_datetime")
    try:
        parsed = datetime.fromisoformat(value)
        timestamp = parsed.timestamp() if parsed.utcoffset() is not None else -1
    except (ValueError, OverflowError, OSError):
        timestamp = -1
    # Leave room for calendar arithmetic around either endpoint.
    if not 86400 <= timestamp <= 253370764800 or timestamp % INTERVAL_SECONDS:
        raise ConfigurationError(path, "expected_aligned_offset_datetime")
    return int(timestamp)


def _span(value, path):
    start, end = (_instant(value[key], f"{path}.{key}") for key in ("from", "until"))
    if start >= end:
        raise ConfigurationError(path, "empty_validity")
    return start, end


def _money(value, path):
    if value is None:
        return None
    if type(value) not in (str, int) or len(str(value)) > 48:
        raise ConfigurationError(path, "expected_decimal_string_or_integer")
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ConfigurationError(path, "invalid_decimal") from None
    if not result.is_finite() or result.copy_abs() > Decimal("1000000000") or result.as_tuple().exponent < -12:
        raise ConfigurationError(path, "decimal_out_of_range")
    return result


@dataclass(frozen=True)
class Quote:
    value: Decimal | None
    unit: str
    source: str = field(repr=False)
    status: str


def _quote(value, path, *, monthly=False):
    units = ("EUR/month",) if monthly else ("EUR/kWh", "EUR/MWh")
    if value["unit"] not in units:
        raise ConfigurationError(path, "unsupported_unit")
    source = value["source"]
    if not isinstance(source, str) or not source.strip() or len(source) > 1024:
        raise ConfigurationError(path, "expected_source")
    status = value["status"]
    if status not in ("confirmed", "reference", "unknown"):
        raise ConfigurationError(path, "invalid_status")
    amount = _money(value["value"], path)
    if (amount is None) != (status == "unknown"):
        raise ConfigurationError(path, "value_status_mismatch")
    if monthly and amount is not None and amount < 0:
        raise ConfigurationError(path, "negative_subscription")
    return Quote(amount, value["unit"], source, status)


@dataclass(frozen=True)
class PricePeriod:
    start: int
    end: int
    quote: Quote


def _ordered(periods, path):
    periods = tuple(sorted(periods, key=lambda p: p.start))
    if any(left.end > right.start for left, right in zip(periods, periods[1:])):
        raise ConfigurationError(path, "overlapping_validity")
    return periods


def _prices(value, start, end, path):
    if not isinstance(value, list):
        raise ConfigurationError(path, "expected_price_list")
    periods = []
    for index, item in enumerate(value):
        location = f"{path}[{index}]"
        item = _object(item, ("from", "until", "value", "unit", "source", "status"), location)
        first, last = _span(item, location)
        if first < start or last > end:
            raise ConfigurationError(location, "outside_contract_validity")
        periods.append(PricePeriod(first, last, _quote(item, location)))
    return _ordered(periods, path)


@dataclass(frozen=True)
class ContractVersion:
    identifier: str
    start: int
    end: int
    import_prices: tuple[PricePeriod, ...]
    export_prices: tuple[PricePeriod, ...]
    subscription: Quote


@dataclass(frozen=True)
class Scenario:
    identifier: str
    currency: str
    tax_basis: str
    timezone: str
    versions: tuple[ContractVersion, ...]


def parse_scenario(value: object) -> Scenario:
    """Detach and validate a EUR, excluding-VAT, versioned supply scenario."""
    value = _object(value, ("schema_version", "id", "currency", "tax_basis", "timezone", "versions"), "scenario")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ConfigurationError("scenario", "unsupported_version")
    identifier = _identifier(value["id"], "scenario.id")
    if value["currency"] != "EUR" or value["tax_basis"] != "excluding_vat":
        raise ConfigurationError("scenario", "expected_eur_excluding_vat")
    zone = value["timezone"]
    try:
        if not isinstance(zone, str):
            raise ValueError
        ZoneInfo(zone)
    except (ValueError, ZoneInfoNotFoundError):
        raise ConfigurationError("scenario.timezone", "unknown_timezone") from None
    if not isinstance(value["versions"], list) or not value["versions"]:
        raise ConfigurationError("scenario.versions", "expected_nonempty_versions")
    versions = []
    for index, item in enumerate(value["versions"]):
        path = f"scenario.versions[{index}]"
        item = _object(item, ("id", "from", "until", "import", "export", "subscription"), path)
        version_id = _identifier(item["id"], path)
        start, end = _span(item, path)
        subscription = _object(item["subscription"], ("value", "unit", "source", "status"), path + ".subscription")
        versions.append(ContractVersion(
            version_id, start, end,
            _prices(item["import"], start, end, path + ".import"),
            _prices(item["export"], start, end, path + ".export"),
            _quote(subscription, path + ".subscription", monthly=True),
        ))
    if len({v.identifier for v in versions}) != len(versions):
        raise ConfigurationError("scenario.versions", "duplicate_identifier")
    return Scenario(identifier, "EUR", "excluding_vat", zone, _ordered(versions, "scenario.versions"))


@dataclass(frozen=True)
class PricedInterval:
    start: int
    version_id: str | None
    import_cost: Decimal | None
    export_credit: Decimal | None
    subscription_cost: Decimal | None
    net_cost: Decimal | None
    import_quote: Quote | None
    export_quote: Quote | None
    subscription_quote: Quote | None
    reasons: tuple[str, ...]
    reference: bool


@dataclass(frozen=True)
class ScenarioResult:
    scenario: Scenario
    intervals: tuple[PricedInterval, ...]
    import_subtotal: Decimal | None
    export_subtotal: Decimal | None
    subscription_subtotal: Decimal | None
    known_net_subtotal: Decimal | None
    total: Decimal | None
    coverage: float
    import_coverage: float
    export_coverage: float | None
    subscription_coverage: float
    confirmed: bool


@dataclass(frozen=True)
class Comparison:
    start: int
    end: int
    scope: str
    results: tuple[ScenarioResult, ...]
    common_intervals: int
    common_coverage: float
    common_totals: Mapping[str, Decimal | None]
    savings_vs_first: Mapping[str, Decimal | None]


def _lookup(periods, starts, timestamp):
    index = bisect_right(starts, timestamp) - 1
    if index >= 0 and periods[index].end >= timestamp + INTERVAL_SECONDS:
        return periods[index]
    return None


def _subscription(amount, timestamp, zone):
    """Uniform share of a local calendar day, then of that day's calendar month."""
    if amount is None:
        return None
    cursor, end, result = timestamp, timestamp + INTERVAL_SECONDS, ZERO
    while cursor < end:
        local = datetime.fromtimestamp(cursor, zone)
        midnight = datetime.combine(local.date(), time.min, zone).timestamp()
        next_midnight = datetime.combine(local.date() + timedelta(days=1), time.min, zone).timestamp()
        stop = min(end, next_midnight)
        if stop <= cursor or next_midnight <= midnight:
            raise ValueError("unsupported_calendar_day")
        result += (amount * Decimal(str(stop - cursor)) / Decimal(str(next_midnight - midnight))
                   / Decimal(calendar.monthrange(local.year, local.month)[1]))
        cursor = stop
    return result


def _energy_rows(intervals, start, end, roles):
    rows = {}
    for row in intervals:
        if not isinstance(row, Interval):
            raise ValueError("expected_ledger_intervals")
        if (type(row.start) not in (int, float) or not start <= row.start < end
                or row.start % INTERVAL_SECONDS or row.start in rows):
            raise ValueError("duplicate_or_invalid_interval")
        for role in roles:
            value = row.energy_kwh.get(role)
            seconds = row.covered_seconds.get(role, 0)
            complete = row.complete.get(role, False)
            if (type(seconds) not in (int, float) or not 0 <= seconds <= INTERVAL_SECONDS + 1e-6
                    or type(complete) is not bool
                    or complete != math.isclose(seconds, INTERVAL_SECONDS, rel_tol=0, abs_tol=1e-6)):
                raise ValueError("inconsistent_interval_coverage")
            if value is None:
                if seconds != 0:
                    raise ValueError("missing_covered_energy")
            elif (type(value) not in (int, float) or not 0 <= value <= 1e15
                  or seconds <= 0):
                raise ValueError("invalid_interval_energy")
        rows[row.start] = row
    return rows


def _sum(values):
    known = [value for value in values if value is not None]
    return sum(known, ZERO) if known else None


def _rounded(value):
    return None if value is None else value.quantize(CENT, rounding=ROUND_HALF_UP)


def _evaluate(scenario, rows, start, end, roles):
    zone = ZoneInfo(scenario.timezone)
    version_starts = tuple(version.start for version in scenario.versions)
    price_indices = {
        (version.identifier, role): (prices, tuple(price.start for price in prices))
        for version in scenario.versions
        for role, prices in (("import", version.import_prices), ("export", version.export_prices))
    }
    priced = []
    for timestamp in range(start, end, INTERVAL_SECONDS):
        version = _lookup(scenario.versions, version_starts, timestamp)
        row = rows.get(timestamp)
        reasons, costs, quotes = [], {}, {}
        if version is None:
            reasons.append("missing_contract")
        for role in roles:
            period = _lookup(*price_indices[(version.identifier, role)], timestamp) if version else None
            quote = period.quote if period else None
            quotes[role] = quote
            complete = row is not None and row.complete.get(role, False)
            if not complete:
                reasons.append(f"incomplete_{role}_energy")
            rate = quote.value if quote else None
            if rate is None:
                reasons.append(f"missing_{role}_price")
            elif quote.unit == "EUR/MWh":
                rate /= 1000
            if quote and quote.status == "reference":
                reasons.append(f"reference_{role}_price")
            costs[role] = Decimal(str(row.energy_kwh[role])) * rate if complete and rate is not None else None
        fee_quote = version.subscription if version else None
        fee = _subscription(fee_quote.value, timestamp, zone) if fee_quote else None
        if fee is None:
            reasons.append("missing_subscription")
        if fee_quote and fee_quote.status == "reference":
            reasons.append("reference_subscription")
        net = None
        if fee is not None and all(costs[role] is not None for role in roles):
            net = costs["import"] - (costs["export"] if "export" in roles else ZERO) + fee
        priced.append(PricedInterval(
            timestamp, version.identifier if version else None, costs["import"], costs.get("export"),
            fee, net, quotes["import"], quotes.get("export"), fee_quote, tuple(reasons),
            any(reason.startswith("reference_") for reason in reasons),
        ))
    priced = tuple(priced)
    coverage = sum(row.net_cost is not None for row in priced) / len(priced)
    known = _sum(row.net_cost for row in priced)
    return ScenarioResult(
        scenario, priced,
        _rounded(_sum(row.import_cost for row in priced)),
        _rounded(_sum(row.export_credit for row in priced)),
        _rounded(_sum(row.subscription_cost for row in priced)),
        _rounded(known), _rounded(known) if coverage == 1 else None, coverage,
        sum(row.import_cost is not None for row in priced) / len(priced),
        sum(row.export_credit is not None for row in priced) / len(priced) if "export" in roles else None,
        sum(row.subscription_cost is not None for row in priced) / len(priced),
        coverage == 1 and not any(row.reference for row in priced),
    )


def compare_scenarios(intervals: Iterable[Interval], scenarios: Iterable[Scenario], *,
                      start: float, end: float, scope: str) -> Comparison:
    """Compare identical UTC buckets, returning partial evidence without extrapolation.

    Scope must explicitly select import_only or import_export. Summary money uses
    decimal arithmetic and rounds once to cents; interval amounts stay unrounded.
    Supply totals exclude VAT, network charges, levies, credits and settlement.
    """
    start, end = _bounds(start, end)
    if scope not in ("import_only", "import_export"):
        raise ValueError("expected_explicit_supply_scope")
    scenarios = tuple(scenarios)
    if not scenarios or any(not isinstance(scenario, Scenario) for scenario in scenarios):
        raise ValueError("expected_scenarios")
    if len({scenario.identifier for scenario in scenarios}) != len(scenarios):
        raise ValueError("duplicate_scenario_identifier")
    roles = ("import",) if scope == "import_only" else ("import", "export")
    rows = _energy_rows(intervals, start, end, roles)
    # Caller decimal context must not change calculation or rounding policy.
    with localcontext(Context(prec=40, rounding=ROUND_HALF_UP)):
        results = tuple(_evaluate(scenario, rows, start, end, roles) for scenario in scenarios)
        common = tuple(index for index in range((end - start) // INTERVAL_SECONDS)
                       if all(result.intervals[index].net_cost is not None for result in results))
        raw_totals = [_sum(result.intervals[index].net_cost for index in common) for result in results]
        totals = {result.scenario.identifier: _rounded(total) for result, total in zip(results, raw_totals)}
        savings = {
            result.scenario.identifier: _rounded(raw_totals[0] - total) if common else None
            for result, total in zip(results, raw_totals)
        }
    return Comparison(start, end, scope, results, len(common),
                      len(common) / ((end - start) // INTERVAL_SECONDS),
                      MappingProxyType(totals), MappingProxyType(savings))
