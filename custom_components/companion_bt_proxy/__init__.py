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
    hass.data[DOMAIN]["scanners"][entry.entry_id] = scanner
    webhook.async_register(hass, DOMAIN, "Companion BT Proxy", hook_id, _async_handle_webhook)
    _LOGGER.debug(f"async_setup_entry() Webhook: {hook_id}")

    for p in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, p)
        )
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    # coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    data = entry.as_dict()["data"]
    hook_id = data["webhook"]
    webhook.async_unregister(hass, hook_id)
    for p in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, p)
    hass.data[DOMAIN]["webhooks"].pop(hook_id)
    scanner = hass.data[DOMAIN]["scanners"][entry.entry_id]
    await scanner.async_unload(hass)
    hass.data[DOMAIN]["scanners"].pop(entry.entry_id)
    return True

# http://192.168.0.22:7123/api/webhook/e4e7fa2bfe90edcb7c9b601005b2df38c3bf357b6b8223dbc4bb26aa97e469a9
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data[DOMAIN] = {"scanners": {}, "webhooks": {}}
    return True
