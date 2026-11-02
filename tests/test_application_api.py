"""API authorization, recovery and backup lifecycle with HA doubles."""

import asyncio
import importlib
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from aiohttp import web
from ha_contract import DOMAIN, Entry, Hass, install_doubles
from test_accounting import START
from test_application import profile, market


class Request(dict):
    def __init__(self, admin, method="GET"):
        super().__init__()
        if admin is not None:
            self["hass_user"] = SimpleNamespace(is_admin=admin)
        self.method = method


class ApplicationApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher, self.adapter, _, sensor = install_doubles(lambda: START)
        self.addCleanup(patcher.stop)
        self.hass = Hass(self.temp.name, self.adapter, sensor)
        self.entry = Entry()
        self.hass.entries.append(self.entry)
        self.hass.report("10")
        await self.adapter.async_setup_entry(self.hass, self.entry)
        self.runtime = self.hass.data[DOMAIN]
        self.api_module = importlib.import_module("custom_components.energy_cost_monitor.api")
        self.view = self.hass.views[0]
        self.addAsyncCleanup(self.adapter.async_unload_entry, self.hass, self.entry)

    async def test_non_admin_and_unauthenticated_cannot_read_or_write(self):
        for admin in (False, None):
            for action in ("view", "profiles", "reports", "report", "study", "history"):
                with self.assertRaises(web.HTTPForbidden):
                    await self.view.dispatch(Request(admin, "POST"), action, {})
        self.assertEqual(self.runtime.application.store.profiles()["versions"], [])

    async def test_study_settings_persist_and_background_error_is_visible(self):
        from test_study import settings

        response = await self.view.dispatch(Request(True, "POST"), "study", settings())
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.text)["state"], "warmup")
        self.runtime.application.study_error = "study_unavailable"
        response = await self.view.dispatch(Request(True), "study", {})
        self.assertEqual(json.loads(response.text)["error"], "study_unavailable")
        await self.adapter.async_unload_entry(self.hass, self.entry)
        await self.adapter.async_setup_entry(self.hass, self.entry)
        response = await self.view.dispatch(Request(True), "study", {})
        self.assertEqual(json.loads(response.text)["state"], "warmup")
        response = await self.view.dispatch(Request(True, "POST"), "study", {"cancel": True})
        self.assertEqual(json.loads(response.text)["state"], "cancelled")

    async def test_admin_profile_report_and_download_survive_reload(self):
        response = await self.view.dispatch(Request(True, "POST"), "profiles", profile())
        self.assertEqual(response.status, 200)
        with patch("custom_components.energy_cost_monitor._core.application.time.time", return_value=START+900):
            response = await self.view.dispatch(Request(True, "POST"), "reports", {"start": START-900, "end": START})
        self.assertEqual(response.status, 200, response.text)
        ident = json.loads(response.text)["id"]
        await self.adapter.async_unload_entry(self.hass, self.entry)
        await self.adapter.async_setup_entry(self.hass, self.entry)
        response = await self.view.dispatch(Request(True), "report", {"id": ident, "format": "html"})
        self.assertEqual(response.status, 200)
        self.assertIn("sandbox", response.headers["Content-Security-Policy"])
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertEqual(len(self.hass.views), 2)

    async def test_backup_drains_application_writer_and_rejects_new_writes(self):
        app = self.runtime.application
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def slow():
            entered.set()
            release.wait(5)
            return app.store.save_profile(profile())
        job = asyncio.create_task(app.call(slow))
        await asyncio.to_thread(entered.wait, 2)
        backup = importlib.import_module("custom_components.energy_cost_monitor.backup")
        task = asyncio.create_task(backup.async_pre_backup(self.hass))
        await asyncio.sleep(.02)
        self.assertFalse(task.done())
        release.set()
        await job
        await task
        with self.assertRaisesRegex(ValueError, "temporarily"):
            await app.call(app.store.save_profile, profile())
        await backup.async_post_backup(self.hass)
        await app.call(app.store.save_profile, profile())

    async def test_backup_waiting_for_import_keeps_collection_paused(self):
        history = importlib.import_module("custom_components.energy_cost_monitor.history")
        backup = importlib.import_module("custom_components.energy_cost_monitor.backup")
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def slow(*args, **kwargs):
            entered.set()
            release.wait(5)
            return {"imported": True}
        data = {"confirm": True, "id": "synthetic", "sha256": "synthetic",
                "mapping": {}, "horizon": "2027-01-01", "profile": "synthetic"}
        with patch.object(history, "staged_path", return_value=Path(self.temp.name) / "synthetic"), patch.object(history, "import_history", side_effect=slow):
            task = asyncio.create_task(history.apply_import(self.runtime, data))
            await asyncio.to_thread(entered.wait, 2)
            saving = asyncio.create_task(backup.async_pre_backup(self.hass))
            await asyncio.sleep(.02)
            self.assertFalse(saving.done())
            release.set()
            await task
            await saving
            self.assertTrue(self.runtime.collector.paused)
            self.assertIsNone(self.runtime.collector.request())
            await backup.async_post_backup(self.hass)

    async def test_price_failure_does_not_stop_collection_and_later_recovers(self):
        app = self.runtime.application
        p = profile()
        p["indexed_import"] = {"offer-a": {"zone": "SI", "markup_eur_kwh": "0"}}
        await app.call(app.store.save_profile, p)
        module = importlib.import_module("custom_components.energy_cost_monitor.application")
        with patch.object(module, "fetch_market", side_effect=OSError("synthetic")):
            await app.refresh_prices()
        self.assertIsNotNone(app.price_error)
        await self.runtime.collector.request()
        self.assertFalse(self.runtime.collector.failed)
        with patch.object(module, "fetch_market", return_value=market()):
            await app.refresh_prices()
        self.assertIsNone(app.price_error)
        self.assertTrue(app.store.market_status())

    async def test_card_resource_has_code_but_no_private_state(self):
        response = await self.hass.views[1].get(Request(None))
        self.assertEqual(response.content_type, "application/javascript")
        self.assertNotIn(str(Path(self.temp.name)), response.text)
        self.assertNotIn("sensor.example_import_energy", response.text)

    async def test_cancel_backup_while_application_busy_resumes_collector(self):
        app = self.runtime.application
        await app.lock.acquire()
        backup = importlib.import_module("custom_components.energy_cost_monitor.backup")
        task = asyncio.create_task(backup.async_pre_backup(self.hass))
        try:
            for _ in range(100):
                if self.runtime.collector.paused:
                    break
                await asyncio.sleep(.001)
            self.assertTrue(self.runtime.collector.paused)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertFalse(self.runtime.collector.paused)
            self.assertNotIn(f"{DOMAIN}_backup_in_progress", self.hass.data)
        finally:
            app.lock.release()
