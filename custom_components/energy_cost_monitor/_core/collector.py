"""Bounded asynchronous collection, with no Home Assistant dependency."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import partial
import sqlite3

from .accounting import AccountingEngine
from .sources import parse_config


def validate_settings(data, options):
    """Return validated immutable sources, gap and collection interval."""
    if not isinstance(data, dict) or set(data) != {"source_config", "max_gap_seconds"}:
        raise ValueError("invalid_configuration")
    config = parse_config(data["source_config"])
    gap = data["max_gap_seconds"]
    if type(gap) not in (int, float) or not 30 <= gap <= 900:
        raise ValueError("invalid_max_gap")
    if not isinstance(options, dict) or set(options) - {"poll_seconds"}:
        raise ValueError("invalid_options")
    poll = options.get("poll_seconds", 30)
    if (type(poll) is not int or not 5 <= poll <= 300
            or poll > min(gap, *(source.max_age_seconds for source in config.sources.values()))):
        raise ValueError("invalid_poll_interval")
    return config, gap, poll


async def drain_on_cancel(awaitable):
    """Finish executor/cleanup work before propagating cancellation.

    Cancelling an asyncio waiter cannot stop a SQLite thread. Shield and drain
    the owned operation, even if shutdown cancels the waiter more than once.
    """
    task = asyncio.ensure_future(awaitable)
    cancelled = False
    while True:
        try:
            result = await asyncio.shield(task)
            break
        except asyncio.CancelledError:
            if task.cancelled():
                raise
            cancelled = True
        except Exception:
            if cancelled:
                raise asyncio.CancelledError from None
            raise
    if cancelled:
        raise asyncio.CancelledError
    return result


class Collector:
    """One in-flight snapshot, no backlog; all database calls are serialized.

    read_snapshot runs on the event loop and returns detached observations.
    execute accepts a zero-argument callable and returns an awaitable.
    """

    def __init__(self, engine: AccountingEngine, read_snapshot: Callable,
                 execute: Callable, on_update: Callable = lambda: None):
        self.engine = engine
        self.read_snapshot = read_snapshot
        self.execute = execute
        self.on_update = on_update
        self.task = None
        self.stopped = False
        self.failed = False
        self.latest = None
        self._needs_break = False

    def request(self):
        if self.stopped:
            return None
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._collect())
        return self.task

    def _write(self, now, observations):
        if self._needs_break:
            self.engine.break_continuity()
        self.engine.ingest(now, observations)
        return self.engine.latest_observations()

    async def _collect(self):
        try:
            now, observations = self.read_snapshot()
            self.latest = await drain_on_cancel(self.execute(partial(self._write, now, observations)))
        except (OSError, sqlite3.Error, ValueError):
            self.failed = True
            self._needs_break = True
        except asyncio.CancelledError:
            self._needs_break = True
            raise
        else:
            self.failed = False
            self._needs_break = False
        finally:
            self.on_update()

    async def stop(self):
        self.stopped = True
        if self.task is not None:
            # Do not cancel a writer. A reload may open its database only after
            # this operation has finished and closed every SQLite connection.
            try:
                await drain_on_cancel(self.task)
            except asyncio.CancelledError:
                if not self.task.cancelled():
                    raise
