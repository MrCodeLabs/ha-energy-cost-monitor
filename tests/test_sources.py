"""Synthetic source-boundary behaviors; no HA, network, or production files."""

import copy
import json
from pathlib import Path
import unittest

from energy_cost_monitor.observations import Observation, normalize_snapshot
from energy_cost_monitor.sources import ConfigurationError, parse_config


ROOT = Path(__file__).resolve().parents[1]
NOW = 1_800_000_000.0


def example(name="minimal"):
    return json.loads((ROOT / "examples" / f"{name}.json").read_text(encoding="utf-8"))


def observations(config):
    return {source.entity_id: Observation("off" if source.kind == "binary" else "0", source.unit, NOW)
            for source in config.sources.values()}


class SourceConfigurationTests(unittest.TestCase):
    def assert_invalid(self, raw, code):
        with self.assertRaises(ConfigurationError) as caught:
            parse_config(raw)
        self.assertEqual(caught.exception.code, code)

    def test_minimal_import_only_household_needs_no_optional_equipment(self):
        config = parse_config(example())
        self.assertEqual(config.capabilities, frozenset())
        self.assertEqual(config.required_roles, {"house", "import"})
        result = normalize_snapshot(config, observations(config), now=NOW)
        self.assertTrue(result.ready)
        self.assertEqual(set(result.readings), {"house", "import"})
        self.assertEqual(result.readings["house"].value, 0)

    def test_enabled_capability_requires_its_meters(self):
        for capability in ("solar", "battery", "ev", "heat_pump"):
            with self.subTest(capability=capability):
                raw = example()
                raw["capabilities"] = [capability]
                self.assert_invalid(raw, "missing_heat_pump_source" if capability == "heat_pump" else "missing_required_meter")

    def test_each_capability_works_independently(self):
        complete = example("optional-capabilities")
        role_sets = {"solar": {"pv", "pv_power"}, "battery": {"charge", "discharge", "battery_soc"},
                     "ev": {"ev", "ev_power", "ev_connected"}, "heat_pump": {"heating", "water"}}
        for capability, roles in role_sets.items():
            with self.subTest(capability=capability):
                raw = copy.deepcopy(complete)
                raw["capabilities"] = [capability]
                raw["sources"] = {role: source for role, source in raw["sources"].items()
                                  if role in {"house", "import"} | roles}
                config = parse_config(raw)
                self.assertTrue(normalize_snapshot(config, observations(config), now=NOW).ready)

    def test_daily_heat_pump_estimates_do_not_block_meter_readiness(self):
        config = parse_config(example("optional-capabilities"))
        states = observations(config)
        del states[config.sources["heating"].entity_id]
        del states[config.sources["water"].entity_id]
        result = normalize_snapshot(config, states, now=NOW)
        self.assertTrue(result.ready)
        self.assertNotIn("heating", result.required_roles)
        self.assertEqual(result.readings["heating"].quality, "missing")

    def test_cumulative_heat_pump_meter_participates_in_quality_gate(self):
        raw = example("optional-capabilities")
        raw["sources"]["heating"]["kind"] = "cumulative_energy"
        config = parse_config(raw)
        states = observations(config)
        del states[config.sources["heating"].entity_id]
        self.assertFalse(normalize_snapshot(config, states, now=NOW).ready)

    def test_disabled_capability_cannot_have_leftover_sources(self):
        raw = example("optional-capabilities")
        raw["capabilities"].remove("ev")
        self.assert_invalid(raw, "capability_disabled")

    def test_battery_requires_both_directions(self):
        raw = example("optional-capabilities")
        del raw["sources"]["discharge"]
        self.assert_invalid(raw, "missing_required_meter")

    def test_reject_typos_unknown_capabilities_and_schema_versions(self):
        for patch, code in (({"schema_version": True}, "unsupported_version"),
                            ({"schema_version": 2}, "unsupported_version"),
                            ({"capabilities": ["storage"]}, "invalid_capability"),
                            ({"capabilities": ["ev", "ev"]}, "duplicate_capability"),
                            ({"capabilities": [None]}, "invalid_capability"),
                            ({"capabilities": "ev"}, "invalid_capability"),
                            ({"source": {}}, "unknown_field")):
            with self.subTest(patch=patch):
                raw = example()
                raw.update(patch)
                self.assert_invalid(raw, code)
        raw = example()
        raw["sources"]["unrecognized_role"] = {}
        self.assert_invalid(raw, "unknown_field")

    def test_reject_malformed_shapes_and_source_fields(self):
        for raw in (None, [], "configuration"):
            self.assert_invalid(raw, "expected_object")
        for sources in (None, []):
            raw = example()
            raw["sources"] = sources
            self.assert_invalid(raw, "expected_object")
        raw = example()
        raw["sources"]["house"]["max_age_second"] = 10
        self.assert_invalid(raw, "unknown_field")

    def test_reject_wrong_entity_domain_kind_and_unit(self):
        for patch, code in (({"entity_id": "switch.example_device"}, "invalid_entity_id"),
                            ({"entity_id": "sensor.example invalid"}, "invalid_entity_id"),
                            ({"entity_id": "sensor.example\n"}, "invalid_entity_id"),
                            ({"kind": "daily_energy_estimate"}, "invalid_kind"),
                            ({"kind": []}, "invalid_kind"),
                            ({"unit": "W"}, "unsupported_unit"),
                            ({"unit": None}, "unsupported_unit"),
                            ({"unit": []}, "unsupported_unit")):
            with self.subTest(patch=patch):
                raw = example()
                raw["sources"]["house"].update(patch)
                self.assert_invalid(raw, code)

    def test_thresholds_are_explicit_positive_finite_numbers(self):
        for field in ("max_power_kw", "max_age_seconds"):
            for value in (None, 0, -1, True, "20", float("nan"), float("inf"), 10**1000):
                with self.subTest(field=field, value=str(value)[:30]):
                    raw = example()
                    raw["sources"]["house"][field] = value
                    self.assert_invalid(raw, "expected_positive_number")
            raw = example()
            del raw["sources"]["house"][field]
            self.assert_invalid(raw, "expected_positive_number")

    def test_dependencies_are_configured_signals_without_cycles(self):
        for dependencies, code in ((["ev_power"], "expected_configured_signal"),
                                   (["house"], "expected_configured_signal"),
                                   (["import"], "expected_configured_signal"),
                                   (["missing_signal"], "invalid_dependencies"),
                                   (["house_power", "house_power"], "invalid_dependencies"),
                                   ([{}], "invalid_dependencies")):
            with self.subTest(dependencies=dependencies):
                raw = example()
                raw["sources"]["house"]["freshness_sources"] = dependencies
                self.assert_invalid(raw, code)
        raw = example("optional-capabilities")
        raw["sources"]["pv_power"]["freshness_sources"] = ["ev_connected"]
        self.assert_invalid(raw, "energy_only")

    def test_reject_ambiguous_reuse_of_one_meter(self):
        for capability in ("solar", "battery"):
            raw = example()
            raw["capabilities"] = [capability]
            complete = example("optional-capabilities")["sources"]
            for role in ({"pv"} if capability == "solar" else {"charge", "discharge"}):
                raw["sources"][role] = complete[role]
                raw["sources"][role].pop("freshness_sources", None)
            self.assert_invalid(raw, "conflicting_entity_mapping")
        raw = example("optional-capabilities")
        raw["sources"]["export"]["entity_id"] = raw["sources"]["import"]["entity_id"]
        self.assert_invalid(raw, "conflicting_entity_mapping")
        raw = example()
        raw["sources"]["house"]["max_power_kw"] = 13
        self.assert_invalid(raw, "conflicting_entity_mapping")

    def test_configuration_is_detached_and_read_only(self):
        raw = example("optional-capabilities")
        config = parse_config(raw)
        raw["sources"]["ev"]["freshness_sources"].clear()
        raw["sources"]["ev"]["entity_id"] = "sensor.example_changed"
        self.assertEqual(config.sources["ev"].freshness_sources, ("ev_power", "ev_connected"))
        self.assertEqual(config.sources["ev"].entity_id, "sensor.example_ev_energy")
        with self.assertRaises(TypeError):
            config.sources["house"] = config.sources["import"]

    def test_error_and_source_repr_do_not_echo_private_values(self):
        raw = example()
        raw["sources"]["house"]["entity_id"] = "secret.example_invalid_entity"
        with self.assertRaises(ConfigurationError) as caught:
            parse_config(raw)
        self.assertNotIn("secret", str(caught.exception))
        self.assertNotIn("example_import_energy", repr(parse_config(example())))


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.config = parse_config(example("optional-capabilities"))
        self.states = observations(self.config)

    def read(self, role, value, unit=None, timestamp=NOW):
        source = self.config.sources[role]
        self.states[source.entity_id] = Observation(value, source.unit if unit is None else unit, timestamp)
        return normalize_snapshot(self.config, self.states, now=NOW).readings[role]

    def test_energy_and_power_units_normalize_with_known_values(self):
        for unit, value in (("Wh", "1250"), ("kWh", "1.25"), ("MWh", "0.00125")):
            raw = example("optional-capabilities")
            raw["sources"]["import"]["unit"] = unit
            config = parse_config(raw)
            states = observations(config)
            states[config.sources["import"].entity_id] = Observation(value, unit, NOW)
            result = normalize_snapshot(config, states, now=NOW).readings["import"]
            self.assertAlmostEqual(result.value, 1.25)
            self.assertEqual(result.unit, "kWh")
        self.assertEqual(self.read("ev_power", "2500").value, 2.5)
        self.assertEqual(self.read("ev_power", "2500").unit, "kW")

    def test_missing_unavailable_and_invalid_values_remain_unknown(self):
        for value in (None, "unknown", "unavailable", "", " UNKNOWN "):
            with self.subTest(value=value):
                reading = self.read("import", value)
                self.assertIsNone(reading.value)
                self.assertEqual(reading.quality, "unavailable")
        for value in ("nan", float("inf"), "-inf", True, [], "broken", 10**1000):
            with self.subTest(value=str(value)[:30]):
                reading = self.read("import", value)
                self.assertIsNone(reading.value)
                self.assertEqual(reading.quality, "invalid_value")
        del self.states[self.config.sources["import"].entity_id]
        result = normalize_snapshot(self.config, self.states, now=NOW)
        self.assertFalse(result.ready)
        self.assertEqual(result.readings["import"].quality, "missing")

    def test_missing_or_changed_units_are_not_assumed_to_be_kwh(self):
        for unit in (None, "W", "kWh", "wh"):
            self.states[self.config.sources["import"].entity_id] = Observation("1000", unit, NOW)
            reading = normalize_snapshot(self.config, self.states, now=NOW).readings["import"]
            self.assertEqual(reading.quality, "unit_mismatch")
            self.assertIsNone(reading.value)

    def test_zero_is_valid_and_negative_energy_is_rejected(self):
        self.assertEqual(self.read("import", "0").value, 0)
        self.assertEqual(self.read("import", "-1").quality, "out_of_range")
        self.assertEqual(self.read("ev_power", "-1").quality, "out_of_range")

    def test_signed_grid_and_battery_power_and_soc_limits(self):
        raw = example("optional-capabilities")
        for role in ("grid_power", "battery_power"):
            raw["sources"][role] = {"entity_id": f"sensor.example_{role}", "kind": "power", "unit": "kW", "max_age_seconds": 60}
        self.config = parse_config(raw)
        for role in ("grid_power", "battery_power"):
            self.assertEqual(self.read(role, "-2").value, -2)
        self.assertEqual(self.read("battery_soc", "100").value, 100)
        self.assertEqual(self.read("battery_soc", "100.01").quality, "out_of_range")
        self.assertEqual(self.read("battery_soc", "-0.01").quality, "out_of_range")

    def test_freshness_boundary_future_and_invalid_timestamps(self):
        self.assertTrue(self.read("house", "1", timestamp=NOW - 180).usable)
        self.assertEqual(self.read("house", "1", timestamp=NOW - 180.001).quality, "stale")
        self.assertEqual(self.read("house", "1", timestamp=NOW + 0.001).quality, "future_timestamp")
        for timestamp in (None, "1800000000", float("nan"), float("inf"), True):
            self.assertEqual(self.read("house", "1", timestamp=timestamp).quality, "invalid_timestamp")
        for timestamp in (None, "1800000000", float("nan"), True):
            with self.assertRaisesRegex(ValueError, "invalid_observation_time"):
                normalize_snapshot(self.config, self.states, now=timestamp)

    def test_stale_ev_signal_invalidates_only_its_dependent_meter(self):
        self.read("ev_power", "0", timestamp=NOW - 61)
        result = normalize_snapshot(self.config, self.states, now=NOW)
        self.assertFalse(result.ready)
        self.assertIsNone(result.readings["ev"].value)
        self.assertEqual(result.readings["ev"].quality, "dependency_unavailable")
        for role in ("house", "import", "export", "pv", "charge", "discharge"):
            self.assertTrue(result.readings[role].usable)

    def test_unknown_connection_is_not_disconnect_and_signal_recovery_restores_meter(self):
        self.read("ev_connected", "unknown")
        result = normalize_snapshot(self.config, self.states, now=NOW)
        self.assertIsNone(result.readings["ev_connected"].value)
        self.assertFalse(result.readings["ev"].usable)
        self.assertIs(self.read("ev_connected", "off").value, False)
        self.assertTrue(normalize_snapshot(self.config, self.states, now=NOW).ready)
        self.assertIs(self.read("ev_connected", "on").value, True)
        self.assertEqual(self.read("ev_connected", "disconnected").quality, "invalid_value")

    def test_estimate_is_labeled_and_kept_separate_from_counters(self):
        reading = self.read("heating", "2.5")
        self.assertEqual(reading.value, 2.5)
        self.assertEqual(reading.quality, "estimated")
        self.assertTrue(reading.usable)

    def test_unconfigured_inputs_are_ignored_and_snapshots_are_detached(self):
        self.states["sensor.example_unconfigured"] = Observation("9999", "kWh", NOW)
        result = normalize_snapshot(self.config, self.states, now=NOW)
        self.states.clear()
        self.assertEqual(set(result.readings), set(self.config.sources))
        self.assertTrue(result.ready)
        with self.assertRaises(TypeError):
            result.readings["house"] = None


if __name__ == "__main__":
    unittest.main()
