from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature 
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:

    _LOGGER.info("Setting up DIVUS D+ covers for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusCoverEntity)]
    async_add_entities(devices)

class DivusCoverEntity(CoverEntity, CoordinatorEntity):

    _is_on: bool = False

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = device.id
        self._attr_name = device.json['NAME']
        self._attr_device_class = CoverDeviceClass.SHUTTER
        self._attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.OPEN_TILT | CoverEntityFeature.CLOSE_TILT

        shutterLongDeviceId = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "25"), None)
        self.shutterLongId = shutterLongDeviceId['ID'] if shutterLongDeviceId else None

        shutterShortDeviceId = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "27"), None)
        self.shutterShortId = shutterShortDeviceId['ID'] if shutterShortDeviceId else None
        _LOGGER.debug("Adding cover device: %s", self._attr_name)

        self.updateDeviceIds = [self.shutterLongId, self.shutterShortId]

    async def async_open_cover(self):
        """Open the cover."""
        await self.coordinator.api.set_value(self.shutterLongId, "0")

    async def async_close_cover(self):
        """Close the cover."""
        await self.coordinator.api.set_value(self.shutterLongId, "1")

    async def async_stop_cover(self):
        """Stop the cover."""
        await self.coordinator.api.set_value(self.shutterShortId, "1")

    async def async_tilt_open_cover(self):
        """Tilt open the cover."""
        await self.coordinator.api.set_value(self.shutterShortId, "0")

    async def async_tilt_close_cover(self):
        """Tilt close the cover."""
        await self.coordinator.api.set_value(self.shutterShortId, "1")