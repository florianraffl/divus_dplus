from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .api import DivusDplusApi
from .coordinator import DivusCoordinator

import logging
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data["host"]
    username = entry.data.get("username")
    password = entry.data.get("password")

    api = DivusDplusApi(host, username, password)

    devices = await api.get_devices()
    
    _LOGGER.debug(f"Found devices: {devices}")

    return True


async def async_unload_entry(hass, entry):
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload
