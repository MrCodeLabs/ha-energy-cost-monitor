"""HA lifecycle for the private application store and optional public prices."""

import asyncio
from datetime import datetime, timedelta, timezone
from functools import partial
import json
import time
import sqlite3
import urllib.error
import urllib.parse
import urllib.request

from homeassistant.core import callback

from ._core.collector import drain_on_cancel
from ._core.application import ApplicationStore
from .const import DOMAIN


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_market(zone, day):
    """Fixed public endpoint; never send household states or accept arbitrary URLs."""
    params = urllib.parse.urlencode({"bzn": zone, "start": day, "end": day})
    request = urllib.request.Request("https://api.energy-charts.info/v2/price?" + params,
                                     headers={"User-Agent": "EnergyCostMonitor-development/0.1"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
        data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("market_response_too_large")
        return json.loads(data)


class Application:
    def __init__(self, runtime, store):
        self.runtime, self.store = runtime, store
        self.lock = asyncio.Lock()
        self.stopped = False
        self.market_task = None
        self.next_fetch = 0
        self.price_error = None
        self.cursor = 0

    async def call(self, function, *args, **kwargs):
        async with self.lock:
            if self.stopped or self.runtime.hass.data.get(f"{DOMAIN}_backup_in_progress"):
                raise ValueError("application_temporarily_unavailable")
            return await drain_on_cancel(self.runtime.hass.async_add_executor_job(partial(function, *args, **kwargs)))

    async def pause(self):
        # Backup flag is set before entry; drain every in-flight application job.
        async with self.lock:
            pass

    async def stop(self):
        self.stopped = True
        if self.market_task is not None:
            await drain_on_cancel(self.market_task)
        async with self.lock:
            pass

    @callback
    def tick(self, _now=None):
        if not self.stopped and time.time() >= self.next_fetch and (self.market_task is None or self.market_task.done()):
            self.market_task = asyncio.create_task(self.refresh_prices())

    async def refresh_prices(self):
        self.next_fetch = time.time() + 3600
        try:
            zones = await self.call(self.store.market_bindings)
            if not zones:
                return
            # A bounded rotation backfills seven days, today and tomorrow. At
            # most one request per hour per integration, independent of meters.
            slots = [(zone, offset) for zone in zones for offset in [0, 1, -1, -2, -3, -4, -5, -6, -7]]
            zone, offset = slots[self.cursor % len(slots)]
            self.cursor += 1
            day = (datetime.now(timezone.utc).date() + timedelta(days=offset)).isoformat()
            payload = await self.call(fetch_market, zone, day)
            await self.call(self.store.store_market, zone, payload, time.time())
            self.price_error = None
        except urllib.error.HTTPError as error:
            retry = error.headers.get("Retry-After", "") if error.headers else ""
            if retry.isdigit():
                self.next_fetch = max(self.next_fetch, time.time() + min(int(retry), 86400))
            self.price_error = "market_http_error"
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
            self.price_error = "market_unavailable_or_invalid"


def application_store(hass):
    return ApplicationStore(hass.config.path(".storage", "energy_cost_monitor_application.sqlite3"))
