"""C411 integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import InvalidKey, ProfileError, fetch_profile
from .dashboard import async_register_dashboard_action

DOMAIN = "c411"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the dashboard action."""
    async_register_dashboard_action(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Fetch one shared profile for all entities."""
    session = async_get_clientsession(hass)

    async def update_profile():
        try:
            profile = await fetch_profile(session, entry.data[CONF_API_KEY])
        except InvalidKey as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ProfileError as err:
            raise UpdateFailed(str(err)) from err

        return {**profile, "_last_success": dt_util.utcnow()}

    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        config_entry=entry,
        name=DOMAIN,
        update_interval=timedelta(minutes=5),
        update_method=update_profile,
        always_update=False,
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
