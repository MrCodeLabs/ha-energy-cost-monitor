"""Validated single-instance setup and conservative reconfiguration."""

import json

import probatio as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import storage_path
from ._core.accounting import AccountingEngine
from ._core.collector import drain_on_cancel, validate_settings
from .const import DOMAIN


def configuration_form(data=None):
    data = data or {}
    return vol.Schema({
        vol.Required("source_config", default=json.dumps(data.get("source_config", {}), indent=2)):
            selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        vol.Required("max_gap_seconds", default=data.get("max_gap_seconds", 300)):
            vol.All(vol.Coerce(int), vol.Range(min=30, max=900)),
    })


async def validate_input(hass, user_input, options):
    data = {"source_config": json.loads(user_input["source_config"]),
            "max_gap_seconds": user_input["max_gap_seconds"]}
    config, gap, _poll = validate_settings(data, options)

    def check_existing():
        path = storage_path(hass)
        if path.exists():
            # Validation only: the engine never modifies a compatible existing
            # database and refuses a different identity/schema.
            AccountingEngine(path, config, max_gap_seconds=gap, sampling_mode="report")

    await drain_on_cancel(hass.async_add_executor_job(check_existing))
    return data


class EnergyCostMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return await self._configure(user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._configure(user_input, self._get_reconfigure_entry())

    async def _configure(self, user_input, entry=None):
        errors = {}
        if user_input is not None:
            try:
                data = await validate_input(self.hass, user_input, dict(entry.options) if entry else {})
            except (ValueError, KeyError, TypeError):
                errors["base"] = "invalid_configuration"
            except OSError:
                errors["base"] = "storage_unavailable"
            else:
                if entry:
                    # An active entry has an update listener which owns reload;
                    # a failed setup has none and needs an explicit reload.
                    if entry.update_listeners:
                        self.hass.config_entries.async_update_entry(entry, data=data)
                        return self.async_abort(reason="reconfigure_successful")
                    return self.async_update_reload_and_abort(entry, data=data)
                return self.async_create_entry(title="Energy Cost Monitor", data=data)
        return self.async_show_form(step_id="reconfigure" if entry else "user",
                                    data_schema=configuration_form(dict(entry.data) if entry else None),
                                    errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EnergyCostMonitorOptionsFlow()


class EnergyCostMonitorOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                validate_settings(dict(self.config_entry.data), user_input)
            except ValueError:
                errors["base"] = "invalid_poll_interval"
            else:
                return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", errors=errors, data_schema=vol.Schema({
            vol.Required("poll_seconds", default=self.config_entry.options.get("poll_seconds", 30)):
                vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
        }))
