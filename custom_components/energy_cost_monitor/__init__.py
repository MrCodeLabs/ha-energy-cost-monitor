"""Read-only, single-instance Home Assistant development adapter."""

from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path
import sqlite3

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from ._core.accounting import AccountingEngine
from ._core.collector import Collector, drain_on_cancel, validate_settings
from ._core.observations import Observation
from .const import DOMAIN, STORAGE_FILE

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


def storage_path(hass):
    """A fixed private path also preserves history across entry removal/re-add."""
    return Path(hass.config.path(".storage", STORAGE_FILE))


class Runtime:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.collector = None
        self.unsubscribers = []
        self.listeners = set()
        self.reported_failure = False

    @callback
    def updated(self):
        failed = self.collector.failed
        if failed and not self.reported_failure:
            _LOGGER.warning("Energy collection failed; history is retained and collection will retry")
        self.reported_failure = failed
        for listener in tuple(self.listeners):
            listener()

    @callback
    def read_snapshot(self):
        observations = {}
        for source in self.collector.engine.config.sources.values():
            state = self.hass.states.get(source.entity_id)
            if state is None:
                continue
            # last_changed is not a freshness signal. Restored states cannot
            # establish a new measured baseline before a live source report.
            if state.attributes.get("restored"):
                continue
            reported = getattr(state, "last_reported", None)
            observations[source.entity_id] = Observation(
                state.state, state.attributes.get("unit_of_measurement"),
                reported.timestamp() if reported is not None else None,
            )
        return dt_util.utcnow().timestamp(), observations

    @callback
    def tick(self, _now=None):
        self.collector.request()

    async def stop(self, _event=None):
        for unsubscribe in self.unsubscribers:
            unsubscribe()
        self.unsubscribers.clear()
        if self.collector is not None:
            await self.collector.stop()


async def async_setup_entry(hass, entry):
    """Reserve the sole runtime before the first await; never replace a DB."""
    if DOMAIN in hass.data:
        raise ConfigEntryError("Only one Energy Cost Monitor instance is supported")
    runtime = Runtime(hass, entry)
    hass.data[DOMAIN] = runtime
    try:
        try:
            config, gap, poll = validate_settings(dict(entry.data), dict(entry.options))
        except ValueError:
            raise ConfigEntryError("Invalid Energy Cost Monitor configuration; reconfigure the entry") from None

        def open_engine():
            engine = AccountingEngine(storage_path(hass), config, max_gap_seconds=gap,
                                      sampling_mode="report")
            engine.break_continuity()
            return engine

        try:
            engine = await drain_on_cancel(hass.async_add_executor_job(open_engine))
        except ValueError:
            raise ConfigEntryError("Existing ledger is incompatible; retained without replacement") from None
        except (OSError, sqlite3.Error):
            raise ConfigEntryNotReady("Ledger unavailable; retrying without replacement") from None
        runtime.collector = Collector(engine, runtime.read_snapshot,
                                      hass.async_add_executor_job, runtime.updated)
        await drain_on_cancel(runtime.collector.request())
        if runtime.collector.failed:
            raise ConfigEntryNotReady("Initial collection failed; retrying without replacement")
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        runtime.unsubscribers.append(async_track_time_interval(hass, runtime.tick, timedelta(seconds=poll)))
        runtime.unsubscribers.append(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, runtime.stop))
        runtime.unsubscribers.append(entry.add_update_listener(async_reload_entry))
    except BaseException:
        # Shield rollback so setup cancellation cannot leave a reserved runtime,
        # active listener or executor write behind.
        async def rollback():
            try:
                await runtime.stop()
                await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
            finally:
                hass.data.pop(DOMAIN, None)
        await drain_on_cancel(rollback())
        raise
    return True


async def async_reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    runtime = hass.data.get(DOMAIN)
    if runtime is None or runtime.entry.entry_id != entry.entry_id:
        return True

    async def unload():
        if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
            return False
        await runtime.stop()
        hass.data.pop(DOMAIN, None)
        return True

    return await drain_on_cancel(unload())
