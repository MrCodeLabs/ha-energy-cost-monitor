"""Validated single-instance setup and conservative reconfiguration."""

import json

import probatio as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import storage_path
from ._core.accounting import AccountingEngine
from ._core.collector import drain_on_cancel, validate_settings
from ._core.sources import ROLE_RULES, ENERGY_UNITS, POWER_UNITS, ENERGY_KINDS
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
        if user_input is not None:
            if user_input.get("setup_mode") == "advanced":
                return await self.async_step_advanced()
            if user_input.get("setup_mode") == "guided":
                return await self.async_step_sources()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("setup_mode", default="guided"): selector.SelectSelector(selector.SelectSelectorConfig(
                options=["guided", "advanced"], translation_key="setup_mode")),
        }))

    async def async_step_advanced(self, user_input=None):
        return await self._configure(user_input)

    async def async_step_sources(self, user_input=None):
        """Choose supported roles; core capability requirements are added together."""
        schema = vol.Schema({
            vol.Optional("roles", default=[]): selector.SelectSelector(selector.SelectSelectorConfig(
                options=[r for r in ROLE_RULES if r not in {"house", "import"}],
                multiple=True, translation_key="source_roles")),
            vol.Required("max_gap_seconds", default=300): vol.All(vol.Coerce(int), vol.Range(min=30, max=900)),
        })
        errors = {}
        if user_input is not None:
            try:
                choice = schema(user_input)
                roles = {"house", "import", *choice["roles"]}
                caps = {ROLE_RULES[r][0] for r in roles} - {None}
                for cap, required in (("solar", {"pv"}), ("battery", {"charge", "discharge"}), ("ev", {"ev"})):
                    if cap in caps:
                        roles.update(required)
                self._roles = [r for r in ROLE_RULES if r in roles]
                self._draft = {"source_config": {"schema_version": 1, "capabilities": sorted(caps), "sources": {}},
                               "max_gap_seconds": choice["max_gap_seconds"]}
                self._role_index = 0
            except (vol.Invalid, ValueError, TypeError, KeyError):
                errors["base"] = "invalid_configuration"
            else:
                return await self.async_step_source()
        return self.async_show_form(step_id="sources", data_schema=schema, errors=errors)

    async def async_step_source(self, user_input=None):
        if not hasattr(self, "_draft"):
            return await self.async_step_sources()
        role = self._roles[self._role_index]
        kinds = ROLE_RULES[role][1]
        measurements = {(kind + "_" + (unit.lower() or "state")).replace("%", "percent"): (kind, unit)
                        for kind in sorted(kinds)
                        for unit in (ENERGY_UNITS if kind in ENERGY_KINDS else
                                     POWER_UNITS if kind == "power" else ["%"] if kind == "percentage" else [""])}
        fields = {
            vol.Required("entity_id"): selector.EntitySelector(selector.EntitySelectorConfig(
                domain="binary_sensor" if kinds == {"binary"} else "sensor")),
            vol.Required("measurement"): selector.SelectSelector(selector.SelectSelectorConfig(
                options=list(measurements), translation_key="measurement")),
            vol.Required("max_age_seconds", default=180): vol.All(vol.Coerce(int), vol.Range(min=30, max=86400)),
        }
        if kinds & ENERGY_KINDS:
            fields[vol.Required("max_power_kw")] = vol.All(vol.Coerce(float), vol.Range(min=0.001, max=1000000))
            signals = [r for r in self._roles if not ROLE_RULES[r][1] & ENERGY_KINDS]
            if signals:
                fields[vol.Optional("freshness_sources", default=[])] = selector.SelectSelector(
                    selector.SelectSelectorConfig(options=signals, multiple=True, translation_key="source_roles"))
        schema = vol.Schema(fields)
        errors = {}
        if user_input is not None:
            try:
                row = schema(user_input)
                kind, unit = measurements[row.pop("measurement")]
                row["kind"] = kind
                if unit:
                    row["unit"] = unit
                state = self.hass.states.get(row["entity_id"])
                reported_unit = state.attributes.get("unit_of_measurement") if state else None
                if unit and reported_unit is not None and reported_unit != unit:
                    raise ValueError("unit_mismatch")
                self._draft["source_config"]["sources"][role] = row
            except (vol.Invalid, ValueError, TypeError, KeyError):
                errors["base"] = "invalid_source"
            else:
                if self._role_index + 1 < len(self._roles):
                    self._role_index += 1
                    return await self.async_step_source()
                return await self.async_step_review()
        return self.async_show_form(step_id="source", data_schema=schema, errors=errors,
                                    description_placeholders={"role": role})

    async def async_step_review(self, user_input=None):
        if not hasattr(self, "_draft"):
            return await self.async_step_sources()
        errors = {}
        if user_input is not None:
            if user_input.get("action") == "restart":
                return await self.async_step_sources()
            if user_input.get("action") == "save":
                try:
                    data = await validate_input(self.hass, {
                        "source_config": json.dumps(self._draft["source_config"]),
                        "max_gap_seconds": self._draft["max_gap_seconds"]}, {})
                except (ValueError, KeyError, TypeError):
                    errors["base"] = "invalid_configuration"
                except OSError:
                    errors["base"] = "storage_unavailable"
                else:
                    if self._async_current_entries():
                        return self.async_abort(reason="single_instance_allowed")
                    return self.async_create_entry(title="Energy Cost Monitor", data=data)
        summary = "\n".join(f"{role}: {row['entity_id']} ({row.get('unit', 'on/off')})"
                            for role, row in self._draft["source_config"]["sources"].items())
        return self.async_show_form(step_id="review", errors=errors,
            description_placeholders={"sources": summary},
            data_schema=vol.Schema({vol.Required("action", default="save"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["save", "restart"], translation_key="review_action"))}))

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
        return self.async_show_form(step_id="reconfigure" if entry else "advanced",
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
