"""Synthetic supply comparisons: invented offers, counters and calendar cases."""

import copy
from dataclasses import FrozenInstanceError
from datetime import datetime
from decimal import Decimal, Inexact, localcontext
import json
from pathlib import Path
import tempfile
import unittest

from energy_cost_monitor.accounting import AccountingEngine, Interval
from energy_cost_monitor.observations import Observation
from energy_cost_monitor.pricing import compare_scenarios, parse_scenario
from energy_cost_monitor.sources import ConfigurationError, parse_config


ROOT = Path(__file__).resolve().parents[1]


def ts(text):
    return int(datetime.fromisoformat(text).timestamp())


START = ts("2026-01-01T00:00:00Z")
UNTIL = ts("2026-02-01T00:00:00Z")


def raw_offer(index=0):
    return json.loads((ROOT / "examples/supply-scenarios.json").read_text())[index]


def offer(**changes):
    raw = raw_offer()
    version = raw["versions"][0]
    for direction in ("import", "export"):
        version[direction][0]["status"] = "confirmed"
    version["subscription"]["status"] = "confirmed"
    for key, value in changes.items():
        quote = version["subscription"] if key == "subscription" else version[key][0]
        quote["value"] = value
        quote["status"] = "unknown" if value is None else "confirmed"
    return parse_scenario(raw)


def row(start=START, imported=1.0, exported=0.0, seconds=900):
    energy = {"import": imported, "export": exported, "house": 1000.0, "ev": 1000.0}
    covered = {role: seconds if value is not None else 0 for role, value in energy.items()}
    return Interval(start, energy, covered, {role: value == 900 for role, value in covered.items()})


def compare(rows, scenarios=None, *, start=START, end=START + 900, scope="import_export"):
    return compare_scenarios(rows, scenarios or (offer(subscription="0"),), start=start, end=end, scope=scope)


class ScenarioConfigurationTests(unittest.TestCase):
    def test_examples_are_detached_immutable_reference_scenarios(self):
        raw = raw_offer()
        scenario = parse_scenario(raw)
        raw["versions"][0]["import"][0]["value"] = "999"
        self.assertEqual(scenario.versions[0].import_prices[0].quote.value, Decimal("0.20"))
        self.assertEqual(scenario.versions[0].import_prices[0].quote.status, "reference")
        with self.assertRaises(FrozenInstanceError):
            scenario.identifier = "changed"
        self.assertNotIn("Invented", repr(scenario))

    def test_strict_fields_currency_tax_basis_timezone_and_identifiers(self):
        for key, value in (("schema_version", True), ("schema_version", 2), ("id", "Bad name"),
                           ("currency", "USD"), ("tax_basis", "including_vat"),
                           ("timezone", "Missing/Zone"), ("versions", []), ("extra", 1)):
            raw = raw_offer()
            raw[key] = value
            with self.subTest(key=key), self.assertRaises(ConfigurationError):
                parse_scenario(raw)
        for value in (None, [], {"schema_version": 1}):
            with self.assertRaises(ConfigurationError):
                parse_scenario(value)

    def test_bad_quotes_fail_without_echoing_source_values(self):
        for field, value in (("value", True), ("value", 0.2), ("value", "NaN"),
                             ("value", "Infinity"), ("value", "1e1000"),
                             ("value", "0.0000000000001"), ("unit", "USD/kWh"),
                             ("source", ""), ("status", "trusted"), ("value", None)):
            raw = raw_offer()
            raw["versions"][0]["import"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ConfigurationError) as error:
                parse_scenario(raw)
            self.assertNotIn("Invented", str(error.exception))
        raw = raw_offer()
        raw["versions"][0]["subscription"]["value"] = "-1"
        with self.assertRaises(ConfigurationError):
            parse_scenario(raw)

    def test_offset_and_alignment_are_required_for_all_validities(self):
        for value in ("2026-01-01", "2026-01-01T00:00:00", "2026-01-01T00:01:00Z",
                      "invalid", None, "2026-02-01T00:00:00Z"):
            raw = raw_offer()
            raw["versions"][0]["from"] = value
            with self.subTest(value=value), self.assertRaises(ConfigurationError):
                parse_scenario(raw)

    def test_overlapping_prices_versions_and_duplicate_ids_are_rejected(self):
        raw = raw_offer()
        raw["versions"][0]["import"] *= 2
        with self.assertRaises(ConfigurationError):
            parse_scenario(raw)
        raw = raw_offer()
        raw["versions"].append(copy.deepcopy(raw["versions"][0]))
        with self.assertRaises(ConfigurationError):
            parse_scenario(raw)
        raw["versions"][1]["id"] = "other"
        with self.assertRaises(ConfigurationError):
            parse_scenario(raw)

    def test_rate_cannot_outlive_contract_and_empty_prices_mean_unknown(self):
        raw = raw_offer()
        raw["versions"][0]["import"][0]["until"] = "2026-02-02T00:00:00Z"
        with self.assertRaises(ConfigurationError):
            parse_scenario(raw)
        raw = raw_offer()
        raw["versions"][0]["import"] = []
        result = compare([row()], [parse_scenario(raw)]).results[0]
        self.assertIsNone(result.total)
        self.assertIn("missing_import_price", result.intervals[0].reasons)


class SupplyComparisonTests(unittest.TestCase):
    def test_two_offers_include_import_export_and_local_daily_subscription(self):
        rows = [row(START + i * 900, imported=1, exported=0.5) for i in range(96)]
        scenarios = [parse_scenario(raw_offer(i)) for i in range(2)]
        result = compare(rows, scenarios, end=START + 86400)
        # A: 19.20 - 2.40 + 0.10; B: 14.40 - 1.92 + 0.20.
        self.assertEqual([r.total for r in result.results], [Decimal("16.90"), Decimal("12.68")])
        self.assertEqual(result.savings_vs_first["offer-b"], Decimal("4.22"))
        self.assertEqual(result.common_coverage, 1)
        self.assertFalse(result.results[0].confirmed)
        self.assertIn("reference_import_price", result.results[0].intervals[0].reasons)
        self.assertEqual(result.results[0].intervals[0].import_quote.source,
                         "Invented offer A for development tests")

    def test_negative_import_and_export_prices_preserve_direction(self):
        result = compare([row(imported=2, exported=1)], [offer(**{"import": "-0.10", "export": "-0.04", "subscription": "0"})])
        self.assertEqual(result.results[0].total, Decimal("-0.16"))
        self.assertEqual(result.results[0].export_subtotal, Decimal("-0.04"))
        self.assertTrue(result.results[0].confirmed)

    def test_zero_energy_and_zero_price_are_known(self):
        result = compare([row(imported=0, exported=0)]).results[0]
        self.assertEqual(result.total, Decimal("0.00"))
        self.assertEqual(result.coverage, 1)
        result = compare([row()], [offer(**{"import": "0", "export": "0", "subscription": "0"})]).results[0]
        self.assertEqual(result.total, Decimal("0.00"))

    def test_coverage_tolerates_the_ledgers_fractional_second_rounding(self):
        measured = Interval(START, {"import": 1}, {"import": 900.0000001}, {"import": True})
        self.assertEqual(compare([measured], scope="import_only").results[0].total, Decimal("0.20"))

    def test_missing_price_is_not_zero_even_with_zero_energy(self):
        result = compare([row(imported=0)], [offer(**{"import": None, "subscription": "0"})]).results[0]
        self.assertIsNone(result.total)
        self.assertIsNone(result.import_subtotal)
        self.assertEqual(result.export_subtotal, Decimal("0.00"))
        self.assertEqual(result.import_coverage, 0)
        self.assertIn("missing_import_price", result.intervals[0].reasons)

    def test_incomplete_energy_has_no_cost_or_full_total(self):
        result = compare([row(imported=1, seconds=450)]).results[0]
        self.assertIsNone(result.total)
        self.assertIsNone(result.known_net_subtotal)
        self.assertEqual(result.subscription_subtotal, Decimal("0.00"))
        self.assertIn("incomplete_import_energy", result.intervals[0].reasons)

    def test_missing_intervals_remain_in_denominator(self):
        result = compare([row()], end=START + 1800)
        self.assertEqual(result.results[0].coverage, 0.5)
        self.assertEqual(result.results[0].known_net_subtotal, Decimal("0.20"))
        self.assertIsNone(result.results[0].total)
        self.assertEqual(result.common_intervals, 1)
        self.assertEqual(result.common_coverage, 0.5)

    def test_import_only_scope_does_not_fabricate_export(self):
        rows = [row(exported=None)]
        self.assertIsNone(compare(rows).results[0].total)
        result = compare(rows, scope="import_only").results[0]
        self.assertEqual(result.total, Decimal("0.20"))
        self.assertIsNone(result.export_subtotal)
        self.assertIsNone(result.export_coverage)
        self.assertIsNone(result.intervals[0].export_credit)

    def test_subscription_unknown_blocks_total_but_preserves_energy_subtotals(self):
        result = compare([row()], [offer(subscription=None)]).results[0]
        self.assertEqual(result.import_subtotal, Decimal("0.20"))
        self.assertIsNone(result.subscription_subtotal)
        self.assertIsNone(result.total)
        self.assertIn("missing_subscription", result.intervals[0].reasons)

    def test_comparison_uses_common_buckets_not_unmatched_totals(self):
        raw = raw_offer(1)
        raw["versions"][0]["import"][0]["from"] = "2026-01-01T00:15:00Z"
        raw["versions"][0]["subscription"]["value"] = "0"
        result = compare([row(imported=100), row(START + 900, imported=1)],
                         [offer(subscription="0"), parse_scenario(raw)], end=START + 1800)
        self.assertEqual(result.results[0].total, Decimal("20.20"))
        self.assertIsNone(result.results[1].total)
        self.assertEqual(result.common_totals["offer-a"], Decimal("0.20"))
        self.assertEqual(result.common_totals["offer-b"], Decimal("0.15"))
        self.assertEqual(result.savings_vs_first["offer-b"], Decimal("0.05"))
        self.assertEqual(result.common_coverage, 0.5)
        with self.assertRaises(TypeError):
            result.common_totals["offer-a"] = Decimal(1)

    def test_no_common_evidence_produces_unknown_difference(self):
        result = compare([], end=START + 1800)
        self.assertEqual(result.common_intervals, 0)
        self.assertIsNone(result.common_totals["offer-a"])
        self.assertIsNone(result.savings_vs_first["offer-a"])

    def test_hourly_prices_repeat_only_inside_explicit_validity(self):
        raw = raw_offer()
        period = raw["versions"][0]["import"][0]
        period["until"] = "2026-01-01T01:00:00Z"
        raw["versions"][0]["subscription"]["value"] = "0"
        result = compare([row(START + i * 900) for i in range(5)], [parse_scenario(raw)], end=START + 4500).results[0]
        self.assertEqual(result.import_subtotal, Decimal("0.80"))
        self.assertEqual(result.import_coverage, 0.8)
        self.assertIsNone(result.intervals[4].import_cost)

    def test_quarter_hour_prices_are_not_averaged(self):
        raw = raw_offer()
        original = raw["versions"][0]["import"][0]
        periods = []
        for index, value in enumerate(("0.10", "0.30")):
            period = copy.deepcopy(original)
            period.update({"from": f"2026-01-01T00:{index * 15:02d}:00Z",
                           "until": f"2026-01-01T00:{(index + 1) * 15:02d}:00Z", "value": value})
            periods.append(period)
        raw["versions"][0]["import"] = list(reversed(periods))
        raw["versions"][0]["subscription"]["value"] = "0"
        result = compare([row(imported=1), row(START + 900, imported=3)],
                         [parse_scenario(raw)], end=START + 1800).results[0]
        self.assertEqual(result.total, Decimal("1.00"))

    def test_contract_switch_and_expiry_have_exclusive_end(self):
        raw = raw_offer()
        first = raw["versions"][0]
        first["until"] = "2026-01-01T00:15:00Z"
        for direction in ("import", "export"):
            first[direction][0]["until"] = first["until"]
        first["subscription"]["value"] = "0"
        second = copy.deepcopy(first)
        second.update(id="second", **{"from": first["until"], "until": "2026-01-01T00:30:00Z"})
        for direction in ("import", "export"):
            second[direction][0].update({key: second[key] for key in ("from", "until")})
        second["import"][0]["value"] = "0.40"
        raw["versions"] = [second, first]
        result = compare([row(START + i * 900) for i in range(3)], [parse_scenario(raw)], end=START + 2700).results[0]
        self.assertEqual([r.version_id for r in result.intervals], ["january", "second", None])
        self.assertEqual(result.import_subtotal, Decimal("0.60"))
        self.assertIn("missing_contract", result.intervals[2].reasons)
        self.assertIsNone(result.total)

    def test_round_once_not_each_quarter_and_isolate_decimal_context(self):
        scenarios = [offer(**{"import": "0.005", "subscription": "0"})]
        with localcontext() as context:
            context.prec = 2
            context.traps[Inexact] = True
            result = compare([row(), row(START + 900)], scenarios, end=START + 1800).results[0]
        self.assertEqual(result.total, Decimal("0.01"))
        self.assertEqual(result.intervals[0].net_cost, Decimal("0.005"))

    def test_rejects_ambiguous_or_inconsistent_interval_input(self):
        for rows in ([row(), row()], [row(START - 900)], [row(START + 1)],
                     [row(imported=-1)], [row(imported=float("nan"))],
                     [row(imported=float("inf"))], [row(seconds=901)],
                     [Interval(START, {"import": 1}, {"import": 450}, {"import": True})]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                compare(rows)
        with self.assertRaises(ValueError):
            compare([row()], [offer(), offer()])
        with self.assertRaises(ValueError):
            compare([row()], scope="automatic")

    def test_ledger_collection_is_independent_of_missing_prices_and_repricing(self):
        config = parse_config(json.loads((ROOT / "examples/minimal.json").read_text()))
        with tempfile.TemporaryDirectory(prefix="ecm-supply-") as folder:
            engine = AccountingEngine(Path(folder) / "synthetic.sqlite3", config, max_gap_seconds=120)
            entity = config.sources["import"].entity_id
            for minute in range(16):
                timestamp = START + minute * 60
                engine.ingest(timestamp, {entity: Observation(minute / 10, "kWh", timestamp)})
            before = engine.path.read_bytes()
            intervals = engine.intervals(START, START + 900)
            missing = compare(intervals, [offer(**{"import": None})], scope="import_only")
            self.assertIsNone(missing.results[0].total)
            complete = compare(intervals, [offer(subscription="0")], scope="import_only")
            self.assertEqual(complete.results[0].total, Decimal("0.30"))
            self.assertEqual(before, engine.path.read_bytes())


class SubscriptionCalendarTests(unittest.TestCase):
    def calendar_offer(self, start, end, monthly, zone="Europe/Ljubljana"):
        raw = raw_offer()
        raw["timezone"] = zone
        version = raw["versions"][0]
        version.update({"from": start, "until": end})
        for direction in ("import", "export"):
            version[direction][0].update({"from": start, "until": end, "value": "0"})
        version["subscription"]["value"] = monthly
        return parse_scenario(raw)

    def test_dst_days_have_equal_daily_share_with_92_and_100_intervals(self):
        for start, end, count in (
            ("2026-03-29T00:00:00+01:00", "2026-03-30T00:00:00+02:00", 92),
            ("2026-10-25T00:00:00+02:00", "2026-10-26T00:00:00+01:00", 100),
        ):
            scenario = self.calendar_offer(start, end, "31")
            rows = [row(timestamp, imported=0) for timestamp in range(ts(start), ts(end), 900)]
            result = compare(rows, [scenario], start=ts(start), end=ts(end)).results[0]
            self.assertEqual(len(result.intervals), count)
            self.assertEqual(result.total, Decimal("1.00"))

    def test_month_length_leap_february_and_full_month(self):
        for start, end, monthly, expected in (
            ("2028-02-29T00:00:00Z", "2028-03-01T00:00:00Z", "29", "1.00"),
            ("2026-01-31T00:00:00Z", "2026-02-02T00:00:00Z", "31", "2.11"),
            ("2026-02-01T00:00:00Z", "2026-03-01T00:00:00Z", "7.99", "7.99"),
        ):
            scenario = self.calendar_offer(start, end, monthly, "UTC")
            rows = [row(timestamp, imported=0) for timestamp in range(ts(start), ts(end), 900)]
            result = compare(rows, [scenario], start=ts(start), end=ts(end)).results[0]
            self.assertEqual(result.subscription_subtotal, Decimal(expected))

    def test_partial_local_day_uses_elapsed_share_without_full_day_charge(self):
        start, end = "2026-01-01T12:00:00+01:00", "2026-01-02T00:00:00+01:00"
        scenario = self.calendar_offer(start, end, "31")
        rows = [row(timestamp, imported=0) for timestamp in range(ts(start), ts(end), 900)]
        result = compare(rows, [scenario], start=ts(start), end=ts(end)).results[0]
        self.assertEqual(result.total, Decimal("0.50"))

    def test_subscription_changes_at_contract_boundary_and_accrues_without_energy(self):
        raw = raw_offer()
        first = raw["versions"][0]
        first["until"] = "2026-01-01T12:00:00Z"
        for direction in ("import", "export"):
            first[direction][0]["until"] = first["until"]
        first["subscription"]["value"] = "31"
        second = copy.deepcopy(first)
        second.update(id="second", **{"from": first["until"], "until": "2026-01-02T00:00:00Z"})
        for direction in ("import", "export"):
            second[direction][0].update({key: second[key] for key in ("from", "until")})
        second["subscription"]["value"] = "62"
        raw["versions"] = [first, second]
        result = compare([], [parse_scenario(raw)], end=START + 86400).results[0]
        self.assertEqual(result.subscription_subtotal, Decimal("1.50"))
        self.assertEqual(result.subscription_coverage, 1)
        self.assertIsNone(result.total)


if __name__ == "__main__":
    unittest.main()
