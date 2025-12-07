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

    def __init__(self, coordinator: DivusCoordinator):
        super().__init__(coordinator)
        self.coordinator = coordinator

        self._attr_device_class = CoverDeviceClass.SHUTTER
        self._attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.OPEN_TILT | CoverEntityFeature.CLOSE_TILT

class DivusDeviceCoverEntity(DivusCoverEntity):

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.entry.entry_id + "_" + device.id
        self._attr_name = device.json['NAME']

        shutterLongDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "25"), None)
        self.shutterLongId: str = shutterLongDevice['ID'] if shutterLongDevice else None
        self._attr_is_closed: bool | None = None

        shutterShortDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "27"), None)
        self.shutterShortId: str = shutterShortDevice['ID'] if shutterShortDevice else None
            
        self.updateDeviceIds = [self.shutterLongId, self.shutterShortId]
        _LOGGER.debug("Adding cover device: %s", self._attr_name)

    async def async_open_cover(self):
        """Open the cover."""
        await self.coordinator.api.set_value(self.shutterLongId, "0")
        _LOGGER.debug("Opened cover device: %s", self._attr_name)

    async def async_close_cover(self):
        """Close the cover."""
        await self.coordinator.api.set_value(self.shutterLongId, "1")
        _LOGGER.debug("Closed cover device: %s", self._attr_name)
    async def async_stop_cover(self):
        """Stop the cover."""
        await self.coordinator.api.set_value(self.shutterShortId, "1")
        _LOGGER.debug("Stopped cover device: %s", self._attr_name)

    async def async_open_cover_tilt(self):
        """Tilt open the cover."""
        await self.coordinator.api.set_value(self.shutterShortId, "0")
        _LOGGER.debug("Tilt opened cover device: %s", self._attr_name)

    async def async_close_cover_tilt(self):
        """Tilt close the cover."""
        await self.coordinator.api.set_value(self.shutterShortId, "1")
        _LOGGER.debug("Tilt closed cover device: %s", self._attr_name)
        
    async def updateState(self, state: DeviceStateDto):
        # Nothing to do here for now
        pass


class DivusRoomCoverEntity(DivusCoverEntity):

    def __init__(self, coordinator: DivusCoordinator,
        deviceId: str,
        name: str,
        shutterLongIds: list[str],
        shutterShortIds: list[str]):
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.entry.entry_id + "_" + deviceId
        self._attr_name = name
        self.shutterLongIds = shutterLongIds
        self._attr_is_closed: bool | None = None
        self.shutterShortIds = shutterShortIds
        self.updateDeviceIds = [*self.shutterLongIds, *self.shutterShortIds]
        _LOGGER.debug("Adding room cover: %s", self._attr_name)

    async def async_open_cover(self):
        """Open the cover."""
        for shutterId in self.shutterLongIds:
            await self.coordinator.api.set_value(shutterId, "0")
        _LOGGER.debug("Opened room cover: %s", self._attr_name)

    async def async_close_cover(self):
        """Close the cover."""
        for shutterId in self.shutterLongIds:
            await self.coordinator.api.set_value(shutterId, "1")
        _LOGGER.debug("Closed room cover: %s", self._attr_name)

    async def async_stop_cover(self):
        """Stop the cover."""
        for shutterId in self.shutterShortIds:
            await self.coordinator.api.set_value(shutterId, "1")
        _LOGGER.debug("Stopped room cover: %s", self._attr_name)

    async def async_open_cover_tilt(self):
        """Tilt open the cover."""
        for shutterId in self.shutterShortIds:
            await self.coordinator.api.set_value(shutterId, "0")
        _LOGGER.debug("Tilt opened room cover: %s", self._attr_name)

    async def async_close_cover_tilt(self):
        """Tilt close the cover."""
        for shutterId in self.shutterShortIds:
            await self.coordinator.api.set_value(shutterId, "1")
        _LOGGER.debug("Tilt closed room cover: %s", self._attr_name)

    async def updateState(self, state: DeviceStateDto):
        # Nothing to do here for now
        pass
        