from homeassistant.components import bluetooth

import logging
import base64

_LOGGER = logging.getLogger(__name__)

class CompanionBLEScanner(bluetooth.BaseHaRemoteScanner):

    def __init__(self, hass, entry):
        self._connector = bluetooth.HaBluetoothConnector(client=None, source=entry.entry_id, can_connect=lambda: False)
        super().__init__(entry.entry_id, entry.title, self._connector, False)
        self._sensors = []

    async def async_process_json(self, data: dict):
        service_data = {key: base64.b64decode(value) for (key, value) in data.get("service_data", {}).items()}
        m_data = {int(key, 10): base64.b64decode(value) for (key, value) in data.get("manufacturer_data", {}).items()}
        _LOGGER.debug(f"async_process_json: {data}, {service_data}, {m_data}")
        self._async_on_advertisement(
            address=data["address"],
            rssi=data.get("rssi", 0),
            local_name=data.get("name"),
            service_uuids=data.get("service_uuids", []),
            service_data=service_data,
            manufacturer_data=m_data,
            tx_power=data.get("tx_power", 0),
            details=dict(),
            advertisement_monotonic_time=data.get("timestamp"),
        )

    async def async_update_sensors(self):
        for s in self._sensors:
            await s.async_on_scanner_update(self)

    async def async_load(self, hass):
        self._unload_callback = bluetooth.async_register_scanner(hass, self, False)

    async def async_unload(self, hass):
        self._unload_callback()
        self._sensors = []