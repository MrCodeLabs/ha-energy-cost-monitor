"""Small HA API doubles for adapter contract tests, NOT an HA installation.

The adapter and sensor modules execute unchanged; schema validation uses the
real probatio package. These doubles do not validate HA's loader or frontend.
"""

import asyncio
from datetime import datetime, timezone
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from test_accounting import START, configuration

DOMAIN = "energy_cost_monitor"


class ConfigEntryError(Exception):
    pass


class ConfigEntryNotReady(Exception):
    pass


class Flow:
    def __init_subclass__(cls, **kwargs):
        pass

    def _async_current_entries(self):
        return self.hass.entries

    async def async_set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def _abort_if_unique_id_configured(self):
        if any(e.unique_id == self.unique_id for e in self.hass.entries):
            raise AssertionError("duplicate flow was not aborted")

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    def async_abort(self, **kwargs):
        return {"type": "abort", **kwargs}

    def _get_reconfigure_entry(self):
        return self.config_entry

    def async_update_reload_and_abort(self, entry, *, data):
        self.hass.config_entries.async_update_entry(entry, data=data)
        self.hass.reload_requests += 1
        return self.async_abort(reason="reconfigure_successful")


class SensorEntity:
    def async_on_remove(self, callback):
        self.remove_callback = callback

    def async_write_ha_state(self):
        self.writes = getattr(self, "writes", 0) + 1


class TextSelector:
    def __init__(self, config):
        self.config = config

    def __call__(self, value):
        if not isinstance(value, str):
            raise ValueError("expected text")
        return value


class SelectSelector:
    def __init__(self, config):
        self.config = config

    def __call__(self, value):
        values = value if self.config.get("multiple") else [value]
        if not isinstance(values, list) or any(v not in self.config["options"] for v in values):
            raise ValueError("invalid_choice")
        return value


def install_doubles(now):
    modules = {}

    def module(name, **attrs):
        value = ModuleType(name)
        value.__dict__.update(attrs)
        modules[name] = value
        if "." in name:
            parent, child = name.rsplit(".", 1)
            setattr(modules[parent], child, value)
        return value

    module("homeassistant")
    module("homeassistant.config_entries", ConfigFlow=Flow, OptionsFlow=Flow)
    module("homeassistant.const", EVENT_HOMEASSISTANT_STOP="stop",
           Platform=SimpleNamespace(SENSOR="sensor"), EntityCategory=SimpleNamespace(DIAGNOSTIC="diagnostic"))
    module("homeassistant.core", callback=lambda function: function)
    module("homeassistant.exceptions", ConfigEntryError=ConfigEntryError, ConfigEntryNotReady=ConfigEntryNotReady)
    module("homeassistant.helpers")
    module("homeassistant.helpers.event", async_track_time_interval=lambda hass, action, interval: hass.listen(action))
    module("homeassistant.helpers.selector", TextSelector=TextSelector, TextSelectorConfig=dict,
           EntitySelector=TextSelector, EntitySelectorConfig=dict,
           SelectSelector=SelectSelector, SelectSelectorConfig=dict)
    module("homeassistant.util")
    module("homeassistant.util.dt", utcnow=lambda: datetime.fromtimestamp(now(), timezone.utc))
    module("homeassistant.components")
    module("homeassistant.components.http", HomeAssistantView=object)
    module("homeassistant.components.sensor", SensorEntity=SensorEntity, SensorDeviceClass=SimpleNamespace(ENUM="enum"))
    patcher = patch.dict(sys.modules, modules)
    patcher.start()
    # Avoid retaining an adapter bound to a previous test's fake clock/modules.
    for key in list(sys.modules):
        if key == "custom_components" or key.startswith("custom_components."):
            del sys.modules[key]
    adapter = importlib.import_module("custom_components.energy_cost_monitor")
    flow = importlib.import_module("custom_components.energy_cost_monitor.config_flow")
    sensor = importlib.import_module("custom_components.energy_cost_monitor.sensor")
    return patcher, adapter, flow, sensor


class Entry:
    def __init__(self, entry_id="synthetic-entry"):
        self.entry_id = entry_id
        self.unique_id = DOMAIN
        self.data = {"source_config": configuration(), "max_gap_seconds": 300}
        self.options = {}
        self.update_listeners = []

    def add_update_listener(self, listener):
        self.update_listeners.append(listener)
        return lambda: self.update_listeners.remove(listener)


class Hass:
    def __init__(self, directory, adapter, sensor):
        self.data = {}
        self.views = []
        self.http = SimpleNamespace(register_view=self.views.append)
        self.adapter, self.sensor = adapter, sensor
        self.config = SimpleNamespace(path=lambda *parts: str(Path(directory).joinpath(*parts)))
        self.state_values = {}
        self.states = SimpleNamespace(get=self.state_values.get)
        self.listeners = []
        self.bus = SimpleNamespace(async_listen_once=lambda event, action: self.listen(action))
        self.entries = []
        self.entities = []
        self.reload_requests = 0
        self.unload_ok = True
        self.config_entries = SimpleNamespace(
            async_forward_entry_setups=self.forward,
            async_unload_platforms=self.unload,
            async_reload=self.reload,
            async_update_entry=self.update,
        )

    def listen(self, callback):
        self.listeners.append(callback)
        return lambda: self.listeners.remove(callback)

    async def async_add_executor_job(self, function):
        return await asyncio.to_thread(function)

    async def forward(self, entry, platforms):
        await self.sensor.async_setup_entry(self, entry, self.entities.extend)
        for entity in self.entities:
            await entity.async_added_to_hass()

    async def unload(self, entry, platforms):
        if not self.unload_ok:
            return False
        for entity in self.entities:
            entity.remove_callback()
        self.entities.clear()
        return True

    async def reload(self, entry_id):
        self.reload_requests += 1
        entry = next(e for e in self.entries if e.entry_id == entry_id)
        if await self.adapter.async_unload_entry(self, entry):
            return await self.adapter.async_setup_entry(self, entry)
        return False

    def update(self, entry, *, data):
        entry.data = data
        return True

    def report(self, value, seconds=0, *, restored=False, timestamp=True):
        self.state_values["sensor.example_import_energy"] = SimpleNamespace(
            state=value, attributes={"unit_of_measurement": "kWh", "restored": restored},
            last_reported=datetime.fromtimestamp(START + seconds, timezone.utc) if timestamp else None,
        )
