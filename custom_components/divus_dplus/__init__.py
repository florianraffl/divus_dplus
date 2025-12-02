from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.divus_dplus.const import DOMAIN, PLATFORMS
from custom_components.divus_dplus.api import DivusDplusApi
from custom_components.divus_dplus.coordinator import DivusCoordinator

import logging
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data["host"]
    username = entry.data.get("username")
    password = entry.data.get("password")

    api = DivusDplusApi(host, username, password, _LOGGER)
    
    api_devices = await api.get_devices()
    coordinator = DivusCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()
    
    _LOGGER.debug(f"Found devices: {api_devices}")

    return True


async def async_unload_entry(hass, entry):
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload
