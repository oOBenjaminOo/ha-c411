"""Configure C411 from the Home Assistant interface."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from . import DOMAIN
from .api import InvalidKey, MissingScope, ProfileError, RateLimited, UnexpectedResponse, fetch_profile

SCHEMA = vol.Schema(
    {vol.Required(CONF_API_KEY): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))}
)


class C411ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Validate the API key before storing it."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self._async_profile_step("user", user_input)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        return await self._async_profile_step("reauth_confirm", user_input)

    async def _async_profile_step(self, step, user_input):
        errors = {}
        if user_input is not None:
            key = user_input[CONF_API_KEY].strip()
            try:
                if not key or any(char.isspace() for char in key):
                    raise InvalidKey
                profile = await fetch_profile(async_get_clientsession(self.hass), key)
            except MissingScope:
                errors["base"] = "missing_scope"
            except InvalidKey:
                errors["base"] = "invalid_auth"
            except RateLimited:
                errors["base"] = "rate_limited"
            except UnexpectedResponse:
                errors["base"] = "unexpected_response"
            except ProfileError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(str(profile["id"]))
                data = {CONF_API_KEY: key}
                if step == "reauth_confirm":
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data_updates=data
                    )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=profile["username"], data=data)
        return self.async_show_form(step_id=step, data_schema=SCHEMA, errors=errors)
