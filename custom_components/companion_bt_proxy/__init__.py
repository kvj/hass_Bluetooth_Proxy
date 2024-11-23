from __future__ import annotations
from .constants import DOMAIN, PLATFORMS
from .scanner import CompanionBLEScanner

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import webhook

import voluptuous as vol
import logging

from aiohttp.web import json_response

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
    }, extra=vol.ALLOW_EXTRA),
}, extra=vol.ALLOW_EXTRA)

async def _async_handle_webhook(hass, webhook_id, request):
    try:
        message = await request.json()
    except ValueError:
        _LOGGER.warning(f"Invalid JSON in Webhook")
        return json_response([])
    _LOGGER.debug(f"JSON: {message}")
    if scanner := hass.data[DOMAIN]["scanners"].get(hass.data[DOMAIN]["webhooks"].get(webhook_id)):
        for item in message:
            await scanner.async_process_json(item)
        await scanner.async_update_sensors()
    else:
        _LOGGER.warning(f"No scanner registered for webhook {webhook_id}")
    return json_response([])

async def async_setup_entry(hass: HomeAssistant, entry):
    data = entry.as_dict()["data"]
    hook_id = data["webhook"]
    hass.data[DOMAIN]["webhooks"][hook_id] = entry.entry_id
    scanner = CompanionBLEScanner(hass, entry)
    await scanner.async_load(hass)
    entry.runtime_data = scanner
    hass.data[DOMAIN]["scanners"][entry.entry_id] = scanner
    webhook.async_register(hass, DOMAIN, "Companion BT Proxy", hook_id, _async_handle_webhook)
    _LOGGER.debug(f"async_setup_entry() Webhook: {hook_id}")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    scanner = entry.runtime_data
    data = entry.as_dict()["data"]
    hook_id = data["webhook"]
    webhook.async_unregister(hass, hook_id)

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data[DOMAIN]["webhooks"].pop(hook_id)
    await scanner.async_unload(hass)
    hass.data[DOMAIN]["scanners"].pop(entry.entry_id)
    entry.runtime_data = None
    return True

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data[DOMAIN] = {"scanners": {}, "webhooks": {}}
    return True
