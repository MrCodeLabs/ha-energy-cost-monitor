"""Guided setup contracts, synthetic sensors only; not a frontend test."""

import tempfile
import unittest

from ha_contract import Hass, install_doubles
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
