import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.divus_dplus.api import DivusDplusApi
from custom_components.divus_dplus.const import DOMAIN, PLATFORMS
from custom_components.divus_dplus.coordinator import DivusCoordinator

_LOGGER = logging.getLogger(__name__)


async def _async_migrate_entity_areas_to_devices(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Migrate area assignments from entities to their devices (runs once).

    Before device_info was introduced, users could assign areas directly to
    entities. Now that every entity belongs to a device, the area should live
    on the device so all its entities inherit it automatically. This one-time
    migration moves the area from each entity to its device (when the device
    has no area yet) and then clears the entity-level area so HA uses the
    inherited value.

    A flag is persisted in the config entry options after the first run so
    the scan is skipped entirely on all subsequent startups.
    """
    if entry.options.get("area_migration_done"):
        return

    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)

    migrated = 0
    for entity_entry in er.async_entries_for_config_entry(entity_reg, entry.entry_id):
        if not entity_entry.area_id or not entity_entry.device_id:
            continue

        device = device_reg.async_get(entity_entry.device_id)
        if device is None:
            continue

        if not device.area_id:
            device_reg.async_update_device(
                entity_entry.device_id,
                area_id=entity_entry.area_id,
            )
            _LOGGER.debug(
                "Migrated area '%s' from entity '%s' to device '%s'",
                entity_entry.area_id,
                entity_entry.entity_id,
                device.name,
            )

        # Clear the entity-level area so it inherits from the device
        entity_reg.async_update_entity(entity_entry.entity_id, area_id=None)
        migrated += 1

    if migrated:
        _LOGGER.info(
            "DIVUS D+: migrated area assignments from %d entities to their devices",
            migrated,
        )

    # Mark as done so this block never runs again
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "area_migration_done": True}
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data["host"]
    username: str = entry.data.get("username", "")
    password: str = entry.data.get("password", "")

    api = DivusDplusApi(host, username, password)

    coordinator = DivusCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    _LOGGER.debug("Set up DIVUS D+ entry for host %s", host)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await _async_migrate_entity_areas_to_devices(hass, entry)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload
