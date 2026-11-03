"""Dated regional reference components. No household tariffs or implied zeroes."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
import calendar
from zoneinfo import ZoneInfo

from .pricing import _money

BLOCKS = ("1", "2", "3", "4", "5")
SCALARS = (
    "vat",
    "export_vat",
    "operator_kwh",
    "efficiency_kwh",
    "excise_kwh",
    "renewables_kw",
    "renewables_kw_month",
    "excess_factor",
)
ZERO = Decimal(0)


def validate_regional(config):
    if not isinstance(config, list) or not 1 <= len(config) <= 50:
        raise ValueError("invalid_regional_versions")
    if any(
        not isinstance(version, dict)
        or not isinstance(version.get("from"), str)
        or not isinstance(version.get("until"), str)
        for version in config
    ):
        raise ValueError("invalid_regional_dates")
    previous = None
    for version in sorted(config, key=lambda v: v.get("from", "")):
        if not isinstance(version, dict) or set(version) != {
            "from",
            "until",
            "source",
            "confirmed",
            "calendar",
            "energy",
            "power",
            "agreed_kw",
            "excess_mode",
            *SCALARS,
        }:
            raise ValueError("invalid_regional_fields")
        first, last = (
            date.fromisoformat(version["from"]),
            date.fromisoformat(version["until"]),
        )
        if first >= last or (previous and first < previous):
            raise ValueError("overlapping_regional_versions")
        previous = last
        if (
            version["calendar"] != "si_2026"
            or first < date(2026, 1, 1)
            or last > date(2027, 1, 1)
        ):
            raise ValueError("unsupported_regional_calendar_validity")
        if (
            type(version["confirmed"]) is not bool
            or not isinstance(version["source"], str)
            or not 1 <= len(version["source"]) <= 1024
        ):
            raise ValueError("invalid_regional_provenance")
        if version["excess_mode"] not in ("unknown", "informative", "charged"):
            raise ValueError("invalid_excess_mode")
        for key in ("energy", "power", "agreed_kw"):
            if not isinstance(version[key], dict) or set(version[key]) != set(BLOCKS):
                raise ValueError("expected_five_blocks")
            for value in version[key].values():
                number = _money(value, key)
                if number is not None and number < 0:
                    raise ValueError("negative_regional_value")
        for key in SCALARS:
            number = _money(version[key], key)
            if number is not None and (
                number < 0 or (key in ("vat", "export_vat") and number > 1)
            ):
                raise ValueError("invalid_regional_rate")
    return config


def block_2026(local):
    if local.year != 2026:
        raise ValueError("unsupported_calendar_year")
    # Official 2026 work-free calendar. Easter Monday is 6 April in this year.
    holidays = {
        (1, 1),
        (1, 2),
        (2, 8),
        (4, 6),
        (4, 27),
        (5, 1),
        (5, 2),
        (6, 25),
        (8, 15),
        (10, 31),
        (11, 1),
        (12, 25),
        (12, 26),
    }
    working = local.weekday() < 5 and (local.month, local.day) not in holidays
    hour = local.hour
    rank = 0 if 7 <= hour < 14 or 16 <= hour < 20 else 1 if 6 <= hour < 22 else 2
    return str(
        (1 if local.month in (11, 12, 1, 2) else 2) + (0 if working else 1) + rank
    )


def regional_bill(intervals, supply, versions, *, start, end, export_enabled):
    """Reference sum, not payment. Partial month excess stays explicitly partial."""
    validate_regional(versions)
    zone = ZoneInfo("Europe/Ljubljana")
    components, known, missing, exceedances = {}, set(), set(), {}

    def add(key, value):
        if value is None:
            missing.add(key)
        else:
            known.add(key)
            components[key] = components.get(key, ZERO) + Decimal(str(value))

    def product(*values):
        result = Decimal(1)
        for value in values:
            if value is None:
                return None
            result *= Decimal(str(value))
        return result

    def num(version, key):
        return _money(version[key], key)

    def taxed(key, value, rate):
        add(key, value)
        add("vat_import", product(value, rate))

    priced = {row["start"]: row for row in supply["intervals"]}
    for interval in intervals:
        local = datetime.fromtimestamp(interval.start, zone)
        day = local.date().isoformat()
        version = next((v for v in versions if v["from"] <= day < v["until"]), None)
        if version is None:
            missing.add("regional_validity")
            continue
        if not version["confirmed"]:
            missing.add("unconfirmed_regional_settings")
        b = block_2026(local)
        row = priced[interval.start]
        vat = num(version, "vat")
        taxed("supply_net", row["import_cost"], vat)
        taxed("subscription_net", row["subscription_cost"], vat)
        if row["reference"]:
            missing.add("unconfirmed_supply")
        if export_enabled:
            add("export_net", row["export_credit"])
            add("vat_export", product(row["export_credit"], num(version, "export_vat")))
        else:
            add("export_net", ZERO)
            add("vat_export", ZERO)
        energy = (
            interval.energy_kwh.get("import")
            if interval.complete.get("import")
            else None
        )
        taxed(
            "network_energy_net",
            product(energy, _money(version["energy"][b], "energy")),
            vat,
        )
        taxed("levies_net", product(energy, num(version, "operator_kwh")), vat)
        taxed("levies_net", product(energy, num(version, "efficiency_kwh")), vat)
        taxed("excise_net", product(energy, num(version, "excise_kwh")), vat)
        # Same local-day accrual as supply subscriptions, including DST days.
        midnight = datetime.combine(local.date(), time.min, zone)
        tomorrow = datetime.combine(local.date() + timedelta(days=1), time.min, zone)
        share = (
            Decimal(900)
            / Decimal(str(tomorrow.timestamp() - midnight.timestamp()))
            / Decimal(calendar.monthrange(local.year, local.month)[1])
        )
        active = (
            ("1", "2", "3", "4")
            if local.month in (11, 12, 1, 2)
            else ("2", "3", "4", "5")
        )
        for active_block in active:
            taxed(
                "network_power_net",
                product(
                    _money(version["power"][active_block], "power"),
                    _money(version["agreed_kw"][active_block], "agreed_kw"),
                    share,
                ),
                vat,
            )
        taxed(
            "levies_net",
            product(
                num(version, "renewables_kw"),
                num(version, "renewables_kw_month"),
                share,
            ),
            vat,
        )
        if version["excess_mode"] == "informative":
            add("excess_power_net", ZERO)
        elif version["excess_mode"] == "unknown":
            missing.add("excess_mode")
        else:
            key = (local.year, local.month, b, version["from"])
            agreed = _money(version["agreed_kw"][b], "agreed_kw")
            if energy is None or agreed is None:
                missing.add("excess_coverage")
            else:
                delta = max(ZERO, Decimal(str(energy)) * 4 - agreed)
                item = exceedances.setdefault(key, [ZERO, version])
                item[0] += delta * delta
            first = datetime(local.year, local.month, 1, tzinfo=zone)
            next_month = datetime(
                local.year + local.month // 12, local.month % 12 + 1, 1, tzinfo=zone
            )
            if start > first.timestamp() or end < next_month.timestamp():
                missing.add("excess_partial_month")
            if (
                version["from"] > first.date().isoformat()
                or version["until"] < next_month.date().isoformat()
            ):
                missing.add("excess_midmonth_configuration_change")
    for (_, _, b, _), (squares, version) in exceedances.items():
        taxed(
            "excess_power_net",
            product(
                squares.sqrt(),
                _money(version["power"][b], "power"),
                num(version, "excess_factor"),
            ),
            num(version, "vat"),
        )
    keys = (
        "supply_net",
        "export_net",
        "subscription_net",
        "network_energy_net",
        "network_power_net",
        "excess_power_net",
        "levies_net",
        "excise_net",
        "vat_import",
        "vat_export",
    )
    result = {
        key: str(components[key].quantize(Decimal(".01"), rounding=ROUND_HALF_UP))
        if key in known
        else None
        for key in keys
    }
    total = sum(
        (
            value * (-1 if key in ("export_net", "vat_export") else 1)
            for key, value in components.items()
        ),
        ZERO,
    )
    subtotal = (
        str(total.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)) if known else None
    )
    return {
        "components": result,
        "known_reference_gross": subtotal,
        "total_gross": subtotal
        if not missing and all(k in known for k in keys)
        else None,
        "missing": sorted(missing),
        "payment": None,
        "status": "reference estimate from HA measurements",
        "calendar": "si_2026",
        "source_versions": versions,
    }
