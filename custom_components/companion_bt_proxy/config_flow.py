from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector
from homeassistant.helpers import device_registry, network
from homeassistant.components import webhook

from .constants import DOMAIN

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

def _create_webhook(hass) -> str:
    id = webhook.async_generate_id()
    url = webhook.async_generate_url(hass, id)
    return id, url

def _create_schema(hass):
    hook_id, hook_url = _create_webhook(hass)
    schema = vol.Schema({
        vol.Required("name"): selector({
            "text": {}
        }),
        vol.Required("webhook", default=hook_id): selector({
            "text": {}
        }),
        vol.Optional("webhook_url", default=hook_url): selector({
            "text": { "type": "url" }
        }),
    })
    return schema


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_create_schema(self.hass))
        else:
            _LOGGER.debug(f"Input: {user_input}")
            await self.async_set_unique_id(user_input["name"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], options={}, data={"webhook": user_input["webhook"],})
