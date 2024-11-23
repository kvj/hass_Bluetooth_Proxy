from homeassistant.components import sensor
from homeassistant.util import dt
from homeassistant.helpers.entity import EntityCategory

from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    scanner = entry.runtime_data
    async_setup_entities([_LastUpdate(scanner, entry)])

class _LastUpdate(sensor.SensorEntity):

    def __init__(self, scanner, entry):

        self._attr_has_entity_name = True
        self._attr_unique_id = f"bt_proxy_{entry.entry_id}_last_update"
        self._attr_name = "Last Update"

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = sensor.SensorDeviceClass.TIMESTAMP

        scanner._sensors.append(self)

        self._value = None
        self._entry_id = entry.entry_id
        self._device_name = entry.title

    async def async_on_scanner_update(self, scanner):
        self._value = dt.now()
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        return self._value

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("entry_id", self._entry_id), 
            },
            "name": self._device_name,
        }
