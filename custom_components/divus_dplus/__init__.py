import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.divus_dplus.api import DivusDplusApi
from custom_components.divus_dplus.const import DOMAIN, PLATFORMS
from custom_components.divus_dplus.coordinator import DivusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data["host"]
    username: str = entry.data.get("username", "")
    password: str = entry.data.get("password", "")

    api = DivusDplusApi(host, username, password)

    coordinator = DivusCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    _LOGGER.debug("Set up DIVUS D+ entry for host %s", host)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload
