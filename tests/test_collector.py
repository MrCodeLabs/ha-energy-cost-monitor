"""Cancellation and failures use real SQLite in background executor threads."""

import asyncio
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from energy_cost_monitor.accounting import AccountingEngine
from energy_cost_monitor.collector import Collector, validate_settings
from energy_cost_monitor.sources import parse_config
from test_accounting import START, configuration, sample


class CollectorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ecm-collector-")
        self.addCleanup(self.temp.cleanup)
        self.config = parse_config(configuration())
        self.engine = AccountingEngine(Path(self.temp.name) / "ledger.sqlite3", self.config,
                                      max_gap_seconds=300, sampling_mode="report")
        self.offset = 0
        self.collector = Collector(self.engine, self.read, asyncio.to_thread)
        self.addAsyncCleanup(self.collector.stop)

    def read(self):
        timestamp = START + self.offset
        return timestamp, sample(self.config, timestamp, 10 + self.offset / 6000)

    async def gate(self):
        started, release = threading.Event(), threading.Event()
        original = self.engine.ingest

        def slow(*args):
            started.set()
            if not release.wait(5):
                raise AssertionError("test failed to release writer")
            return original(*args)

        self.addCleanup(release.set)
        patcher = patch.object(self.engine, "ingest", slow)
        patcher.start()
        self.addCleanup(patcher.stop)
        task = self.collector.request()
        self.assertTrue(await asyncio.to_thread(started.wait, 2))
        return task, release

    async def test_busy_ticks_are_coalesced_without_a_backlog(self):
        task, release = await self.gate()
        for _ in range(20):
            self.assertIs(self.collector.request(), task)
        release.set()
        await task
        self.assertEqual(self.collector.latest["timestamp"], START)

    async def test_backup_pause_drains_writer_blocks_ticks_and_breaks_continuity(self):
        task, release = await self.gate()
        paused = asyncio.create_task(self.collector.pause())
        await asyncio.sleep(0)
        self.assertFalse(paused.done())
        self.assertIsNone(self.collector.request())
        release.set()
        await paused
        self.assertTrue(task.done())
        self.offset = 60
        await self.collector.resume()
        self.assertIsNone(self.engine.summary(START, START + 900).energy_kwh["house"])
        self.offset = 120
        await self.collector.request()
        self.assertAlmostEqual(self.engine.summary(START, START + 900).energy_kwh["house"], 0.01)

    async def test_cancelled_backup_pause_does_not_leave_collector_frozen(self):
        task, release = await self.gate()
        paused = asyncio.create_task(self.collector.pause())
        await asyncio.sleep(0)
        paused.cancel()
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await paused
        self.assertTrue(task.done())
        self.assertFalse(self.collector.paused)

    async def test_post_backup_cannot_resurrect_an_unloaded_collector(self):
        await self.collector.pause()
        await self.collector.stop()
        self.assertIsNone(self.collector.resume())

    async def test_unload_drains_writer_and_rejects_new_ticks(self):
        task, release = await self.gate()
        stop = asyncio.create_task(self.collector.stop())
        await asyncio.sleep(0)
        self.assertFalse(stop.done())
        self.assertIsNone(self.collector.request())
        release.set()
        await stop
        self.assertTrue(task.done())
        self.assertEqual(self.engine.latest_observations()["timestamp"], START)

    async def test_repeated_cancellation_waits_for_executor_before_propagating(self):
        task, release = await self.gate()
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        self.assertFalse(task.done())
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(self.engine.latest_observations()["timestamp"], START)
        await self.collector.stop()

    async def test_cancelled_stop_does_not_cancel_the_writer(self):
        task, release = await self.gate()
        stop = asyncio.create_task(self.collector.stop())
        await asyncio.sleep(0)
        stop.cancel()
        await asyncio.sleep(0)
        self.assertFalse(stop.done())
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await stop
        self.assertFalse(task.cancelled())

    async def test_io_failure_recovers_without_bridging_the_failed_period(self):
        await self.collector.request()
        self.offset = 60
        with patch.object(self.engine, "ingest", side_effect=OSError("synthetic failure")):
            await self.collector.request()
        self.assertTrue(self.collector.failed)
        self.offset = 120
        await self.collector.request()
        self.assertFalse(self.collector.failed)
        self.assertIsNone(self.engine.summary(START, START + 900).energy_kwh["house"])
        self.offset = 180
        await self.collector.request()
        self.assertAlmostEqual(self.engine.summary(START, START + 900).energy_kwh["house"], 0.01)

    async def test_deleted_database_is_not_replaced_by_retry(self):
        await self.collector.request()
        self.engine.path.unlink()
        self.offset = 60
        await self.collector.request()
        self.assertTrue(self.collector.failed)
        self.assertFalse(self.engine.path.exists())

    def test_options_reject_unsafe_cadence_and_extra_storage_parameters(self):
        data = {"source_config": configuration(), "max_gap_seconds": 300}
        self.assertEqual(validate_settings(data, {"poll_seconds": 60})[2], 60)
        for options in ({"poll_seconds": True}, {"poll_seconds": 301}, {"poll_seconds": 0},
                        {"poll_seconds": 200}, {"database_path": "ignored"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                validate_settings(data, options)
