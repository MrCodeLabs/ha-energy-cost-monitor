"""Profiles, reference prices, live sessions and immutable reports on synthetic data."""

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.application import ApplicationStore, parse_market, render_report
from energy_cost_monitor.sources import parse_config
from test_accounting import START, configuration, sample


def profile():
    scenario = json.loads((Path(__file__).resolve().parents[1] / "examples/supply-scenarios.json").read_text())[0]
    version = scenario["versions"][0]
    for row in [version, *version["import"], *version["export"]]:
        row["from"], row["until"] = "2020-01-01T00:00:00Z", "2030-01-01T00:00:00Z"
    return {"name": "Invented supply example", "scenarios": [scenario], "indexed_import": {}}


def market(price=100, ts=START):
    return {"schema_version": "2.0", "endpoint": "price", "bidding_zone": "SI", "unit": "EUR / MWh",
            "interval_minutes": 15, "license": "Synthetic fixture",
            "data": [{"timestamp": datetime.fromtimestamp(ts, timezone.utc).isoformat(),
                      "values": {"day_ahead_price": price}}]}


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = parse_config(configuration())
        self.engine = AccountingEngine(self.root / "ledger.sqlite3", self.config, max_gap_seconds=300, sampling_mode="report")
        for offset in range(0, 901, 60):
            self.engine.ingest(START+offset, sample(self.config, START+offset, 10+offset/6000))
        self.store = ApplicationStore(self.root / "application.sqlite3")

    def test_profile_versions_are_immutable_reactivatable_and_persist_after_restart(self):
        first = profile()
        a = self.store.save_profile(first)
        first["name"] = "Revised"
        b = self.store.save_profile(first)
        reopened = ApplicationStore(self.store.path)
        self.assertNotEqual(a, b)
        self.assertEqual(len(reopened.profiles()["versions"]), 2)
        reopened.activate(a)
        self.assertEqual(reopened.profiles()["active"], a)
        self.assertEqual(next(x["profile"]["name"] for x in reopened.profiles()["versions"] if x["id"] == a), "Invented supply example")

    def test_supply_view_preserves_coverage_and_no_profile_is_explicit(self):
        result = self.store.view(self.engine, START, START+900, now=START+901)
        self.assertIsNone(result["comparison"])
        self.store.save_profile(profile())
        result = self.store.view(self.engine, START, START+900, now=START+901)
        self.assertEqual(result["comparison"]["common_coverage"], 1)
        self.assertIsNotNone(result["comparison"]["results"][0]["total"])

    def test_market_negative_missing_units_dst_and_atomic_refusal(self):
        self.assertEqual(parse_market(market(-10), "SI"), [(START, "-0.01")])
        self.store.store_market("SI", market(100), START+900)
        invalid = market(90)
        invalid["data"].append(copy.deepcopy(invalid["data"][0]))
        with self.assertRaises(ValueError):
            self.store.store_market("SI", invalid, START+901)
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT price FROM prices").fetchone()[0], "0.1")
        self.store.store_market("SI", market(None), START+902)
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT price FROM prices").fetchone()[0], "0.1")
        payload = market()
        payload["data"] = [{"timestamp": t, "values": {"day_ahead_price": 5}} for t in
                           ["2026-10-25T02:00:00+02:00", "2026-10-25T02:00:00+01:00"]]
        rows = parse_market(payload, "SI")
        self.assertEqual(rows[1][0]-rows[0][0], 3600)
        payload["unit"] = "USD / MWh"
        with self.assertRaises(ValueError):
            parse_market(payload, "SI")

    def test_frozen_report_does_not_change_after_profile_and_market_updates(self):
        value = profile()
        value["indexed_import"] = {"offer-a": {"zone": "SI", "markup_eur_kwh": "0.02"}}
        self.store.save_profile(value)
        self.store.store_market("SI", market(100), START+900)
        ident = self.store.freeze(self.engine, START, START+900, now=START+901)
        frozen = self.store.report(ident)
        self.assertFalse(frozen["comparison"]["results"][0]["confirmed"])
        self.store.store_market("SI", market(300), START+902)
        value["name"] = "Changed profile"
        self.store.save_profile(value)
        self.assertEqual(self.store.report(ident), frozen)
        self.assertNotEqual(self.store.freeze(self.engine, START, START+900, now=START+903), ident)
        self.assertTrue(frozen["market_provenance"])
        self.assertIn("energy_kwh", render_report(frozen, "csv"))

    def test_missing_market_price_does_not_become_zero_or_stop_metering(self):
        value = profile()
        value["indexed_import"] = {"offer-a": {"zone": "SI", "markup_eur_kwh": "0"}}
        self.store.save_profile(value)
        result = self.store.view(self.engine, START, START+900, now=START+901)
        self.assertIsNone(result["comparison"]["results"][0]["total"])
        self.assertEqual(result["comparison"]["common_coverage"], 0)
        self.assertTrue(self.engine.ingest(START+960, sample(self.config, START+960, 10.16)))

    def test_report_html_escapes_profile_markup_and_future_window_is_rejected(self):
        value = profile()
        value["name"] = "<script>alert(1)</script>"
        self.store.save_profile(value)
        ident = self.store.freeze(self.engine, START, START+900, now=START+901)
        output = render_report(self.store.report(ident), "html")
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)
        with self.assertRaises(ValueError):
            self.store.freeze(self.engine, START, START+1800, now=START+1000)

    def test_open_ev_session_remains_open_in_live_view(self):
        from energy_cost_monitor.observations import Observation
        config = parse_config(configuration("optional-capabilities"))
        engine = AccountingEngine(self.root / "ev.sqlite3", config, max_gap_seconds=300, sampling_mode="report")
        states = sample(config, START, 10)
        states[config.sources["ev_connected"].entity_id] = Observation("on", None, START)
        states[config.sources["ev_power"].entity_id] = Observation(1000, "W", START)
        engine.ingest(START, states)
        result = self.store.view(engine, START-900, START, now=START+10)
        self.assertIsNone(result["sessions"][0]["end"])
        self.assertIsNone(result["sessions"][0]["body"]["kwh"])

    def test_threshold_validation_and_csv_matches_frozen_interval_cost(self):
        import csv
        import io
        value = profile()
        value["session_charging_kw"] = -1
        with self.assertRaises(ValueError):
            self.store.save_profile(value)
        value["session_charging_kw"] = 0.25
        self.store.save_profile(value)
        ident = self.store.freeze(self.engine, START, START+900, now=START+901)
        frozen = self.store.report(ident)
        rows = list(csv.DictReader(io.StringIO(render_report(frozen, "csv"))))
        supply = next(row for row in rows if row["record"] == "supply")
        self.assertEqual(supply["net_eur"], frozen["comparison"]["results"][0]["intervals"][0]["net_cost"])
        self.assertEqual(frozen["frozen_at"], START+901)
        for malformed in (None, {}, {"timestamp": 0, "values": {}}):
            payload = market()
            payload["data"] = [malformed]
            with self.assertRaises(ValueError):
                parse_market(payload, "SI")
