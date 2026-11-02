"""Guided setup contracts, synthetic sensors only; not a frontend test."""

from copy import deepcopy
import tempfile
import unittest

from ha_contract import Entry, Hass, install_doubles
from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.sources import parse_config
from test_accounting import START


class GuidedSetupTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher, self.adapter, flow, sensor = install_doubles(lambda: START)
        self.addCleanup(patcher.stop)
        self.hass = Hass(self.temp.name, self.adapter, sensor)
        self.hass.report("1")
        self.flow = flow.EnergyCostMonitorConfigFlow()
        self.flow.hass = self.hass
        self.assertEqual((await self.flow.async_step_user())["step_id"], "user")
        self.assertEqual((await self.flow.async_step_user({"setup_mode": "guided"}))["step_id"], "sources")

    def source(self, role="import", **changes):
        return {"entity_id": "sensor.example_" + role + "_energy", "measurement": "cumulative_energy_kwh",
                "max_age_seconds": 180, "max_power_kw": 12, **changes}

    async def test_minimal_alias_without_json_and_no_database_creation(self):
        await self.flow.async_step_sources({"roles": [], "max_gap_seconds": 300})
        await self.flow.async_step_source(self.source())
        result = await self.flow.async_step_source(self.source())
        self.assertEqual(result["step_id"], "review")
        self.assertNotIn("source_config", result["data_schema"].schema)
        result = await self.flow.async_step_review({"action": "save"})
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"]["source_config"]["sources"]["house"], result["data"]["source_config"]["sources"]["import"])
        self.assertFalse(self.adapter.storage_path(self.hass).exists())

    async def test_optional_capabilities_add_required_meters_and_daily_type(self):
        await self.flow.async_step_sources({"roles": ["ev_connected", "battery_soc", "pv_power", "water"], "max_gap_seconds": 300})
        self.assertEqual(set(self.flow._draft["source_config"]["capabilities"]), {"ev","battery","solar","heat_pump"})
        self.assertTrue({"ev","charge","discharge","pv","water"} <= set(self.flow._roles))
        for role in self.flow._roles:
            if role == "ev_connected":
                data = {"entity_id":"binary_sensor.example_plug", "measurement":"binary_state", "max_age_seconds":180}
            elif role in {"battery_soc", "pv_power"}:
                data = {"entity_id":"sensor.example_"+role, "measurement":"percentage_percent" if role=="battery_soc" else "power_w", "max_age_seconds":180}
            else:
                data = self.source(role, measurement="daily_energy_estimate_kwh" if role=="water" else "cumulative_energy_kwh")
            await self.flow.async_step_source(data)
        result = await self.flow.async_step_review({"action":"save"})
        self.assertEqual(result["type"], "create_entry", result)
        self.assertEqual(result["data"]["source_config"]["sources"]["water"]["kind"], "daily_energy_estimate")

    async def test_wrong_unit_rejected_without_advancing(self):
        await self.flow.async_step_sources({"roles": [], "max_gap_seconds":300})
        result = await self.flow.async_step_source(self.source(measurement="cumulative_energy_wh"))
        self.assertEqual(result["errors"], {"base":"invalid_source"})
        self.assertEqual(self.flow._role_index, 0)

    async def test_alias_conflict_rejected_and_restart_clears_draft(self):
        await self.flow.async_step_sources({"roles": [], "max_gap_seconds":300})
        await self.flow.async_step_source(self.source())
        await self.flow.async_step_source(self.source(max_power_kw=20))
        result = await self.flow.async_step_review({"action":"save"})
        self.assertEqual(result["errors"], {"base":"invalid_configuration"})
        await self.flow.async_step_review({"action":"restart"})
        await self.flow.async_step_sources({"roles": [], "max_gap_seconds":300})
        self.assertEqual(self.flow._draft["source_config"]["sources"], {})

    async def begin_reconfigure(self, entry):
        self.flow.config_entry = entry
        self.hass.entries.append(entry)
        form = await self.flow.async_step_reconfigure()
        self.assertEqual(form["data_schema"]({}), {"setup_mode": "guided"})
        return await self.flow.async_step_reconfigure({"setup_mode": "guided"})

    async def fill_existing_sources(self, form, **changes):
        choice = form["data_schema"]({})
        result = await self.flow.async_step_sources(choice)
        for _role in self.flow._roles:
            row = result["data_schema"]({})
            row.update(changes)
            result = await self.flow.async_step_source(row)
        self.assertEqual(result["step_id"], "review")

    async def test_existing_defaults_preserve_history_and_noop_does_not_reload(self):
        entry = Entry()
        entry.options = {"poll_seconds": 5}
        entry.data["max_gap_seconds"] = 300.5
        for row in entry.data["source_config"]["sources"].values():
            row["max_age_seconds"] = 15.5
        entry.update_listeners.append(object())
        before = deepcopy(entry.data)
        engine = AccountingEngine(self.adapter.storage_path(self.hass), parse_config(before["source_config"]),
                                  max_gap_seconds=300.5, sampling_mode="report")
        original = engine.path.read_bytes()
        await self.fill_existing_sources(await self.begin_reconfigure(entry))
        self.assertEqual(entry.data, before)  # No writes while reviewing/cancelling.
        result = await self.flow.async_step_review({"action": "save"})
        self.assertEqual(result["reason"], "reconfigure_successful")
        self.assertEqual(engine.path.read_bytes(), original)
        self.assertEqual(entry.data, before)
        self.assertEqual(entry.options, {"poll_seconds": 5})
        self.assertEqual(self.hass.reload_requests, 0)

    async def test_guided_identity_change_refused_and_restart_prefills_draft(self):
        entry = Entry()
        before = deepcopy(entry.data)
        engine = AccountingEngine(self.adapter.storage_path(self.hass), parse_config(before["source_config"]),
                                  max_gap_seconds=300, sampling_mode="report")
        original = engine.path.read_bytes()
        await self.fill_existing_sources(await self.begin_reconfigure(entry), entity_id="sensor.example_replacement")
        result = await self.flow.async_step_review({"action": "save"})
        self.assertEqual(result["errors"], {"base": "incompatible_history"})
        self.assertEqual(engine.path.read_bytes(), original)
        self.assertEqual(entry.data, before)
        self.assertEqual(self.hass.reload_requests, 0)
        result = await self.flow.async_step_review({"action": "restart"})
        result = await self.flow.async_step_sources(result["data_schema"]({}))
        self.assertEqual(result["data_schema"]({})["entity_id"], "sensor.example_replacement")

    async def test_guided_repair_before_store_exists_updates_only_on_save(self):
        entry = Entry()
        await self.fill_existing_sources(await self.begin_reconfigure(entry), entity_id="sensor.example_replacement")
        self.assertNotEqual(entry.data["source_config"]["sources"]["house"]["entity_id"], "sensor.example_replacement")
        result = await self.flow.async_step_review({"action": "save"})
        self.assertEqual(result["reason"], "reconfigure_successful")
        self.assertEqual(entry.data["source_config"]["sources"]["house"]["entity_id"], "sensor.example_replacement")
        self.assertEqual(len(self.hass.entries), 1)
        self.assertEqual(self.hass.reload_requests, 1)
        self.assertFalse(self.adapter.storage_path(self.hass).exists())

    async def test_guided_reconfigure_checks_current_polling_options(self):
        entry = Entry()
        entry.options = {"poll_seconds": 120}
        before = deepcopy(entry.data)
        await self.fill_existing_sources(await self.begin_reconfigure(entry), max_age_seconds=60)
        result = await self.flow.async_step_review({"action": "save"})
        self.assertEqual(result["errors"], {"base": "invalid_configuration"})
        self.assertEqual(entry.data, before)
        self.assertEqual(self.hass.reload_requests, 0)

    async def test_concurrent_edit_is_not_overwritten(self):
        entry = Entry()
        await self.fill_existing_sources(await self.begin_reconfigure(entry))
        entry.data = {**entry.data, "max_gap_seconds": 400}
        result = await self.flow.async_step_review({"action": "save"})
        self.assertEqual(result["reason"], "configuration_changed")
        self.assertEqual(entry.data["max_gap_seconds"], 400)
