"""Adapter lifecycle contracts with HA doubles and real SQLite/executor work."""

import asyncio
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from ha_contract import ConfigEntryError, ConfigEntryNotReady, DOMAIN, Entry, Hass, install_doubles
from test_accounting import START


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ecm-ha-contract-")
        self.addCleanup(self.temp.cleanup)
        self.offset = 0
        patcher, self.adapter, self.flow_module, sensor = install_doubles(lambda: START + self.offset)
        self.addCleanup(patcher.stop)
        self.hass = Hass(self.temp.name, self.adapter, sensor)
        self.entry = Entry()
        self.hass.entries.append(self.entry)
        self.hass.report("10")
        self.addAsyncCleanup(self.cleanup_runtime)

    async def cleanup_runtime(self):
        self.hass.unload_ok = True
        await self.adapter.async_unload_entry(self.hass, self.entry)

    async def setup(self):
        self.assertTrue(await self.adapter.async_setup_entry(self.hass, self.entry))
        return self.hass.data[DOMAIN]

    async def test_setup_collects_and_exposes_only_quality_metadata(self):
        runtime = await self.setup()
        self.assertEqual(self.hass.entities[0].native_value, "collecting")
        self.assertEqual(self.hass.entities[0]._attr_unique_id, "synthetic-entry_collection")
        self.assertNotIn("sensor.example_import_energy", json.dumps(self.hass.entities[0].extra_state_attributes))
        self.assertEqual(runtime.collector.latest["readings"]["house"]["value"], 10)
        self.assertEqual(len(self.hass.listeners), 3)
        self.assertEqual(len(self.entry.update_listeners), 1)
        self.assertTrue(self.adapter.storage_path(self.hass).is_relative_to(Path(self.temp.name) / ".storage"))

    async def test_duplicate_instance_rejected_before_storage_changes(self):
        runtime = await self.setup()
        with self.assertRaises(ConfigEntryError):
            await self.adapter.async_setup_entry(self.hass, Entry("another-entry"))
        self.assertIs(self.hass.data[DOMAIN], runtime)

    async def test_backup_blocks_a_new_writer_until_post_backup(self):
        self.hass.data[f"{DOMAIN}_backup_in_progress"] = True
        with self.assertRaises(ConfigEntryNotReady):
            await self.setup()
        self.assertNotIn(DOMAIN, self.hass.data)
        self.hass.data.pop(f"{DOMAIN}_backup_in_progress")
        await self.setup()

    async def test_missing_source_sets_incomplete_then_recovers(self):
        self.hass.state_values.clear()
        runtime = await self.setup()
        self.assertEqual(self.hass.entities[0].native_value, "incomplete")
        self.offset = 60
        self.hass.report("10", 60)
        await runtime.collector.request()
        self.assertEqual(self.hass.entities[0].native_value, "collecting")

    async def test_restored_or_timestamp_missing_state_is_not_a_live_baseline(self):
        self.hass.report("10", restored=True)
        runtime = await self.setup()
        self.assertEqual(self.hass.entities[0].native_value, "incomplete")
        self.offset = 60
        self.hass.report("10", 60, timestamp=False)
        await runtime.collector.request()
        self.assertEqual(runtime.collector.latest["readings"]["house"]["quality"], "invalid_timestamp")

    async def test_options_reload_removes_old_tasks_and_retains_history(self):
        runtime = await self.setup()
        self.offset = 60
        self.hass.report("10.1", 60)
        await runtime.collector.request()
        self.entry.options = {"poll_seconds": 60}
        await self.entry.update_listeners[0](self.hass, self.entry)
        new = self.hass.data[DOMAIN]
        self.assertIsNot(new, runtime)
        self.assertTrue(runtime.collector.stopped)
        self.assertEqual(len(self.hass.listeners), 3)
        self.assertEqual(len(self.entry.update_listeners), 1)
        self.assertAlmostEqual(new.collector.engine.summary(START, START + 900).energy_kwh["house"], 0.1)
        self.offset = 120
        self.hass.report("10.2", 120)
        await new.collector.request()
        self.assertAlmostEqual(new.collector.engine.summary(START, START + 900).energy_kwh["house"], 0.1)

    async def test_unload_retains_database_and_unsubscribes_every_listener(self):
        runtime = await self.setup()
        path = runtime.collector.engine.path
        before = path.read_bytes()
        self.assertTrue(await self.adapter.async_unload_entry(self.hass, self.entry))
        self.assertNotIn(DOMAIN, self.hass.data)
        self.assertFalse(self.hass.listeners)
        self.assertFalse(self.entry.update_listeners)
        self.assertFalse(runtime.listeners)
        self.assertIsNone(runtime.collector.request())
        self.assertEqual(path.read_bytes(), before)

    async def test_platform_refusal_preserves_running_collector(self):
        runtime = await self.setup()
        self.hass.unload_ok = False
        self.assertFalse(await self.adapter.async_unload_entry(self.hass, self.entry))
        self.assertIs(self.hass.data[DOMAIN], runtime)
        self.assertFalse(runtime.collector.stopped)

    async def test_bad_configuration_fails_without_files_and_can_be_corrected(self):
        valid = self.entry.data
        self.entry.data = {"source_config": {}}
        with self.assertRaises(ConfigEntryError):
            await self.setup()
        self.assertNotIn(DOMAIN, self.hass.data)
        self.assertFalse(self.adapter.storage_path(self.hass).exists())
        self.entry.data = valid
        await self.setup()

    async def test_foreign_database_is_preserved_on_setup_failure(self):
        path = self.adapter.storage_path(self.hass)
        path.parent.mkdir()
        path.write_bytes(b"synthetic foreign database")
        before = path.read_bytes()
        with self.assertRaises(ConfigEntryError):
            await self.setup()
        self.assertEqual(path.read_bytes(), before)
        self.assertNotIn(DOMAIN, self.hass.data)
        self.assertFalse(self.hass.listeners)

    async def test_storage_access_failure_retries_and_releases_reservation(self):
        with patch.object(self.adapter, "AccountingEngine", side_effect=OSError("synthetic access failure")):
            with self.assertRaises(ConfigEntryNotReady):
                await self.setup()
        self.assertNotIn(DOMAIN, self.hass.data)
        await self.setup()

    async def test_forwarding_failure_rolls_back_runtime_and_listeners(self):
        async def partial_setup(entry, platforms):
            await self.hass.forward(entry, platforms)
            raise RuntimeError("synthetic partial platform failure")

        with patch.object(self.hass.config_entries, "async_forward_entry_setups", partial_setup):
            with self.assertRaises(RuntimeError):
                await self.setup()
        self.assertNotIn(DOMAIN, self.hass.data)
        self.assertFalse(self.hass.listeners)
        self.assertFalse(self.hass.entities)
        await self.setup()

    async def test_cancelled_unload_drains_writer_before_releasing_singleton(self):
        runtime = await self.setup()
        started, release = threading.Event(), threading.Event()
        original = runtime.collector.engine.ingest

        def slow(*args):
            started.set()
            if not release.wait(5):
                raise AssertionError("writer not released")
            return original(*args)

        with patch.object(runtime.collector.engine, "ingest", slow):
            self.offset = 60
            self.hass.report("10.1", 60)
            runtime.collector.request()
            self.assertTrue(await asyncio.to_thread(started.wait, 2))
            unload = asyncio.create_task(self.adapter.async_unload_entry(self.hass, self.entry))
            # Wait until unload reaches the draining writer, without time sleeps.
            while not runtime.collector.stopped:
                await asyncio.sleep(0)
            unload.cancel()
            await asyncio.sleep(0)
            self.assertIn(DOMAIN, self.hass.data)
            self.assertFalse(unload.done())
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await unload
        self.assertNotIn(DOMAIN, self.hass.data)
        self.assertFalse(self.hass.listeners)
        self.assertAlmostEqual(runtime.collector.engine.summary(START, START + 900).energy_kwh["house"], 0.1)

    async def test_cancelled_setup_drains_database_open_then_releases_runtime(self):
        started, release = threading.Event(), threading.Event()
        original = self.adapter.AccountingEngine

        def slow(*args, **kwargs):
            started.set()
            if not release.wait(5):
                raise AssertionError("setup not released")
            return original(*args, **kwargs)

        with patch.object(self.adapter, "AccountingEngine", slow):
            setup = asyncio.create_task(self.adapter.async_setup_entry(self.hass, self.entry))
            self.assertTrue(await asyncio.to_thread(started.wait, 2))
            setup.cancel()
            await asyncio.sleep(0)
            self.assertIn(DOMAIN, self.hass.data)
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await setup
        self.assertNotIn(DOMAIN, self.hass.data)
        await self.setup()

    async def test_shutdown_unsubscribes_and_stops_future_collection(self):
        runtime = await self.setup()
        await runtime.stop()
        self.assertFalse(self.hass.listeners)
        self.assertIsNone(runtime.collector.request())

    async def test_flow_validates_json_and_single_instance(self):
        flow = self.flow_module.EnergyCostMonitorConfigFlow()
        flow.hass = self.hass
        self.assertEqual((await flow.async_step_user())["reason"], "single_instance_allowed")
        self.hass.entries.clear()
        self.assertEqual((await flow.async_step_user({"source_config": "invalid", "max_gap_seconds": 300}))["errors"],
                         {"base": "invalid_configuration"})
        form = await flow.async_step_user()
        data = form["data_schema"]({"source_config": json.dumps(self.entry.data["source_config"]), "max_gap_seconds": 300})
        result = await flow.async_step_user(data)
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"], self.entry.data)
        self.assertFalse(self.adapter.storage_path(self.hass).exists())

    async def test_options_validate_without_changing_measurement_identity(self):
        flow = self.flow_module.EnergyCostMonitorOptionsFlow()
        flow.config_entry = self.entry
        self.assertEqual((await flow.async_step_init({"poll_seconds": 200}))["errors"],
                         {"base": "invalid_poll_interval"})
        result = await flow.async_step_init({"poll_seconds": 60})
        self.assertEqual(result["data"], {"poll_seconds": 60})

    async def test_reconfiguration_rejects_source_change_without_touching_ledger(self):
        runtime = await self.setup()
        path = runtime.collector.engine.path
        before = path.read_bytes()
        flow = self.flow_module.EnergyCostMonitorConfigFlow()
        flow.hass, flow.config_entry = self.hass, self.entry
        raw = json.loads(json.dumps(self.entry.data["source_config"]))
        for source in raw["sources"].values():
            source["entity_id"] = "sensor.example_different_meter"
        result = await flow.async_step_reconfigure({"source_config": json.dumps(raw), "max_gap_seconds": 300})
        self.assertEqual(result["errors"], {"base": "invalid_configuration"})
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.hass.reload_requests, 0)

    async def test_reconfigure_recovers_invalid_entry_before_storage_exists(self):
        valid = self.entry.data
        self.entry.data = {"source_config": {}, "max_gap_seconds": 300}
        with self.assertRaises(ConfigEntryError):
            await self.setup()
        flow = self.flow_module.EnergyCostMonitorConfigFlow()
        flow.hass, flow.config_entry = self.hass, self.entry
        result = await flow.async_step_reconfigure({"source_config": json.dumps(valid["source_config"]),
                                                    "max_gap_seconds": 300})
        self.assertEqual(result["reason"], "reconfigure_successful")
        self.assertEqual(self.hass.reload_requests, 1)
        self.assertEqual(self.entry.data, valid)
        await self.setup()

    async def test_storage_failure_is_visible_and_recovery_clears_error(self):
        runtime = await self.setup()
        self.offset = 60
        with patch.object(runtime.collector.engine, "ingest", side_effect=OSError("synthetic")):
            with self.assertLogs(self.adapter.__name__, level="WARNING") as messages:
                await runtime.collector.request()
            self.assertNotIn("sensor.example", " ".join(messages.output))
        self.assertEqual(self.hass.entities[0].native_value, "storage_error")
        self.offset = 120
        self.hass.report("10.1", 120)
        await runtime.collector.request()
        self.assertEqual(self.hass.entities[0].native_value, "collecting")
        self.assertIsNone(runtime.collector.engine.summary(START, START + 900).energy_kwh["house"])

    def test_package_manifest_and_translation_keys_are_consistent(self):
        component = Path(self.adapter.__file__).parent
        manifest = json.loads((component / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["single_config_entry"])
        self.assertTrue(manifest["config_flow"])
        self.assertEqual(manifest["requirements"], [])

        def keys(value, prefix=""):
            result = set()
            for key, child in value.items():
                path = f"{prefix}.{key}"
                result.add(path)
                if isinstance(child, dict):
                    result.update(keys(child, path))
            return result

        expected = json.loads((component / "strings.json").read_text(encoding="utf-8"))
        for language in ("en", "sl"):
            actual = json.loads((component / "translations" / f"{language}.json").read_text(encoding="utf-8"))
            self.assertEqual(keys(expected), keys(actual))
