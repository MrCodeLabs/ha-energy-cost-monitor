"""Collection health only; no unverified bill totals are exposed."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([CollectionStatus(hass.data[DOMAIN])])


class CollectionStatus(SensorEntity):
    _attr_should_poll = False
    _attr_name = "Energy Cost Monitor collection"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_options = ["collecting", "incomplete", "storage_error"]

    def __init__(self, runtime):
        self.runtime = runtime
        self._attr_unique_id = f"{runtime.entry.entry_id}_collection"

    async def async_added_to_hass(self):
        self.runtime.listeners.add(self.async_write_ha_state)
        self.async_on_remove(lambda: self.runtime.listeners.discard(self.async_write_ha_state))

    @property
    def native_value(self):
        collector = self.runtime.collector
        if collector.failed:
            return "storage_error"
        latest = collector.latest
        if latest is None or any(latest["readings"][role]["quality"] != "valid"
                                 for role in collector.engine.roles):
            return "incomplete"
        return "collecting"

    @property
    def extra_state_attributes(self):
        latest = self.runtime.collector.latest
        return {"last_collection_utc": latest["timestamp"] if latest else None,
                "quality": {role: reading["quality"] for role, reading in latest["readings"].items()}
                if latest else {}}
