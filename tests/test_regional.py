"""Synthetic dated network/levy arithmetic, never a household bill."""

import unittest
from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo
from energy_cost_monitor.regional import block_2026, regional_bill, validate_regional
from energy_cost_monitor.accounting import Interval


def config():
    return [
        {
            "from": "2026-01-01",
            "until": "2027-01-01",
            "source": "Invented test schedule",
            "confirmed": True,
            "calendar": "si_2026",
            "energy": dict.fromkeys("12345", "0.01"),
            "power": dict.fromkeys("12345", "1"),
            "agreed_kw": dict.fromkeys("12345", "2"),
            "excess_mode": "informative",
            "vat": "0.2",
            "export_vat": "0",
            "operator_kwh": "0.001",
            "efficiency_kwh": "0.002",
            "excise_kwh": "0.003",
            "renewables_kw": "2",
            "renewables_kw_month": "1",
            "excess_factor": "1.2",
        }
    ]


def window(first, last, energy=1):
    zone = ZoneInfo("Europe/Ljubljana")
    start = int(datetime.fromisoformat(first).replace(tzinfo=zone).timestamp())
    end = int(datetime.fromisoformat(last).replace(tzinfo=zone).timestamp())
    rows = [
        Interval(t, {"import": energy}, {"import": 900}, {"import": True})
        for t in range(start, end, 900)
    ]
    supply = {
        "intervals": [
            {
                "start": r.start,
                "import_cost": "0.2",
                "export_credit": None,
                "subscription_cost": "0",
                "reference": False,
            }
            for r in rows
        ]
    }
    return rows, supply, start, end


class RegionalTests(unittest.TestCase):
    def test_malformed_versions_fail_as_configuration_errors(self):
        for invalid in ([None], [5], [{"from": 5, "until": "2027-01-01"}]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_regional(invalid)

    def bill(self, first="2026-03-01", last="2026-04-01", settings=None):
        rows, supply, start, end = window(first, last)
        return regional_bill(
            rows,
            supply,
            settings or config(),
            start=start,
            end=end,
            export_enabled=False,
        )

    def test_dst_month_fixed_fees_are_one_month_and_energy_uses_actual_quarters(self):
        result = self.bill()
        self.assertEqual(result["components"]["network_power_net"], "8.00")
        self.assertEqual(result["components"]["network_energy_net"], "29.72")
        self.assertEqual(result["components"]["levies_net"], "10.92")
        self.assertIsNotNone(result["total_gross"])
        self.assertIsNone(result["payment"])

    def test_unknown_is_not_zero_and_no_current_rates_carried_into_future(self):
        settings = config()
        settings[0]["energy"]["3"] = None
        result = self.bill(settings=settings)
        self.assertIsNone(result["total_gross"])
        self.assertIn("network_energy_net", result["missing"])
        result = self.bill("2027-01-01", "2027-01-02")
        self.assertIsNone(result["total_gross"])
        self.assertIn("regional_validity", result["missing"])
        settings = config()
        settings[0]["until"] = "2028-01-01"
        with self.assertRaises(ValueError):
            validate_regional(settings)

    def test_net_excise_offsets_export_across_intervals_and_leaves_other_levies(self):
        settings = config()
        settings[0].update(
            {"from": "2026-03-28", "until": "2026-03-30", "excise_basis": "net_import"}
        )
        rows, supply, start, end = window("2026-03-28", "2026-03-30", energy=2)
        rows = [
            replace(
                row,
                energy_kwh={"import": 2, "export": 3 if i % 2 else 0},
                complete={"import": True, "export": True},
            )
            for i, row in enumerate(rows)
        ]
        for price in supply["intervals"]:
            price["export_credit"] = "0"
        def bill():
            return regional_bill(rows, supply, settings, start=start, end=end, export_enabled=True)

        net = bill()
        self.assertEqual(len(rows), 188)  # Spring clock change.
        self.assertEqual(net["components"]["excise_net"], "0.28")
        self.assertIsNotNone(net["total_gross"])
        settings[0].pop("excise_basis")
        gross = bill()
        self.assertEqual(gross["components"]["excise_net"], "1.13")
        self.assertEqual(net["components"]["levies_net"], gross["components"]["levies_net"])
        self.assertEqual(net["components"]["network_energy_net"], gross["components"]["network_energy_net"])
        self.assertAlmostEqual(
            float(gross["components"]["vat_import"]) - float(net["components"]["vat_import"]),
            0.17,
        )

        settings[0]["excise_basis"] = "net_import"
        rows[:] = [replace(row, energy_kwh={"import": 2, "export": 3}) for row in rows]
        self.assertEqual(bill()["components"]["excise_net"], "0.00")

    def test_net_excise_requires_the_whole_period_and_both_measurements(self):
        settings = config()
        settings[0]["excise_basis"] = "net_import"
        rows, supply, start, end = window("2026-10-02", "2026-10-03")
        partial = regional_bill(rows, supply, settings, start=start, end=end, export_enabled=True)
        self.assertIn("excise_partial_period", partial["missing"])
        self.assertIsNone(partial["components"]["excise_net"])
        settings[0].update({"from": "2026-10-02", "until": "2026-10-03"})
        for data, enabled in [(rows, False), (rows, True), (rows[1:], True)]:
            with self.subTest(rows=len(data), export_enabled=enabled):
                incomplete = regional_bill(data, supply, settings, start=start, end=end, export_enabled=enabled)
                self.assertIn("excise_coverage", incomplete["missing"])
                self.assertIsNone(incomplete["components"]["excise_net"])
                self.assertIsNone(incomplete["total_gross"])
        settings[0]["excise_basis"] = "invalid"
        with self.assertRaisesRegex(ValueError, "invalid_excise_basis"):
            validate_regional(settings)

    def test_excess_is_monthly_root_sum_square_and_partial_month_is_flagged(self):
        settings = config()
        settings[0]["excess_mode"] = "charged"
        result = self.bill("2026-03-02", "2026-03-03", settings)
        self.assertIn("excess_partial_month", result["missing"])
        self.assertIsNone(result["total_gross"])
        # 96 quarters at 4kW vs 2kW, grouped into the three daily blocks.
        expected = round(1.2 * 2 * ((44**0.5) + (20**0.5) + (32**0.5)), 2)
        self.assertAlmostEqual(
            float(result["components"]["excess_power_net"]), expected
        )

    def test_calendar_weekend_holiday_and_hour_edges(self):
        self.assertEqual(block_2026(datetime(2026, 11, 2, 7)), "1")
        self.assertEqual(block_2026(datetime(2026, 11, 2, 14)), "2")
        self.assertEqual(block_2026(datetime(2026, 11, 1, 7)), "2")
        self.assertEqual(block_2026(datetime(2026, 4, 6, 7)), "3")
        self.assertEqual(block_2026(datetime(2026, 6, 8, 7)), "2")
