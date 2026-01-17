import logging

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from custom_components.divus_dplus.entity import DivusEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.info("Setting up DIVUS D+ covers for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusCoverEntity)]
    async_add_entities(devices)


class DivusCoverEntity(CoverEntity, CoordinatorEntity):
    def __init__(self, coordinator: DivusCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator

        self._attr_assumed_state = True
        self._attr_device_class = CoverDeviceClass.SHUTTER
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.OPEN_TILT
            | CoverEntityFeature.CLOSE_TILT
        )


class DivusDeviceCoverEntity(DivusCoverEntity, DivusEntity):
    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.entry.entry_id + "_" + device.id
        self._attr_name = device.json["NAME"]

        shutter_long_device = next(
            (dev for dev in device.sub_elements if dev["RENDERING_ID"] == "25"), None
        )
        self.shutter_long_id: str = (
            shutter_long_device["ID"] if shutter_long_device else ""
        )
        self._attr_is_closed: bool | None = (
            shutter_long_device["CURRENT_VALUE"] == "1" if shutter_long_device else None
        )

        shutter_short_device = next(
            (dev for dev in device.sub_elements if dev["RENDERING_ID"] == "27"), None
        )
        self.shutter_short_id: str = (
            shutter_short_device["ID"] if shutter_short_device else ""
        )

        self.update_device_ids = {self.shutter_long_id, self.shutter_short_id}
        _LOGGER.debug("Adding cover device: %s", self._attr_name)

    async def async_open_cover(self) -> None:
        """Open the cover."""
        await self.coordinator.api.set_value(self.shutter_long_id, "0")
        _LOGGER.debug("Opened cover device: %s", self._attr_name)

    async def async_close_cover(self) -> None:
        """Close the cover."""
        await self.coordinator.api.set_value(self.shutter_long_id, "1")
        _LOGGER.debug("Closed cover device: %s", self._attr_name)

    async def async_stop_cover(self) -> None:
        """Stop the cover."""
        await self.coordinator.api.set_value(self.shutter_short_id, "1")
        _LOGGER.debug("Stopped cover device: %s", self._attr_name)

    async def async_open_cover_tilt(self) -> None:
        """Tilt open the cover."""
        await self.coordinator.api.set_value(self.shutter_short_id, "0")
        _LOGGER.debug("Tilt opened cover device: %s", self._attr_name)

    async def async_close_cover_tilt(self) -> None:
        """Tilt close the cover."""
        await self.coordinator.api.set_value(self.shutter_short_id, "1")
        _LOGGER.debug("Tilt closed cover device: %s", self._attr_name)

    def update_state(self, state: DeviceStateDto) -> None:
        if state.id == self.shutter_long_id:
            self._attr_is_closed = state.current_value == "1"


class DivusRoomCoverEntity(DivusCoverEntity):
    def __init__(
        self,
        coordinator: DivusCoordinator,
        device_id: str,
        name: str,
        shutter_long_ids: list[str],
        shutter_short_ids: list[str],
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.entry.entry_id + "_" + device_id
        self._attr_name = name
        self.shutter_long_ids = shutter_long_ids
        self._attr_is_closed: bool | None = None
        self.shutter_short_ids = shutter_short_ids
        self.update_device_ids = [*self.shutter_long_ids, *self.shutter_short_ids]
        _LOGGER.debug("Adding room cover: %s", self._attr_name)

    async def async_open_cover(self) -> None:
        """Open the cover."""
        for shutter_id in self.shutter_long_ids:
            await self.coordinator.api.set_value(shutter_id, "0")
        _LOGGER.debug("Opened room cover: %s", self._attr_name)

    async def async_close_cover(self) -> None:
        """Close the cover."""
        for shutter_id in self.shutter_long_ids:
            await self.coordinator.api.set_value(shutter_id, "1")
        _LOGGER.debug("Closed room cover: %s", self._attr_name)

    async def async_stop_cover(self) -> None:
        """Stop the cover."""
        for shutter_id in self.shutter_short_ids:
            await self.coordinator.api.set_value(shutter_id, "1")
        _LOGGER.debug("Stopped room cover: %s", self._attr_name)

    async def async_open_cover_tilt(self) -> None:
        """Tilt open the cover."""
        for shutter_id in self.shutter_short_ids:
            await self.coordinator.api.set_value(shutter_id, "0")
        _LOGGER.debug("Tilt opened room cover: %s", self._attr_name)

    async def async_close_cover_tilt(self) -> None:
        """Tilt close the cover."""
        for shutter_id in self.shutter_short_ids:
            await self.coordinator.api.set_value(shutter_id, "1")
        _LOGGER.debug("Tilt closed room cover: %s", self._attr_name)

    def update_state(self, state: DeviceStateDto) -> None:
        # Nothing to do here for now
        pass
