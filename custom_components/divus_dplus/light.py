from enum import Enum
import math
from typing import Optional
from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import value_to_brightness, brightness_to_value
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:

    _LOGGER.info("Setting up DIVUS D+ lights for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusLightEntity)]
    async_add_entities(devices)

class DivusLightEntity(LightEntity, CoordinatorEntity):

    _is_on: bool = False

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = coordinator.entry.entry_id + "_" + device.id
        self._attr_name = device.json['NAME']
        _LOGGER.debug("Adding light device: %s of type %s", self._attr_name, type(self))

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self):
        await self.coordinator.api.set_value(self.device.id, "1")
    async def async_turn_off(self):
        await self.coordinator.api.set_value(self.device.id, "0")

class TypeEnum(Enum):
    DIMABLE = "dimable"
    SWITCH = "switch"

class DivusDimLightEntity(DivusLightEntity):

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        return [ColorMode.BRIGHTNESS]
    
    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator, device)
        self.type = TypeEnum.DIMABLE
        currentDimValueDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "11"), None)
        self.dimDeviceId = currentDimValueDevice['ID'] if currentDimValueDevice else None
        self.dimValue = currentDimValueDevice['CURRENT_VALUE'] if currentDimValueDevice else "0"

        currentSwitchValueDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "10"), None)
        self.switchDeviceId = currentSwitchValueDevice['ID'] if currentSwitchValueDevice else None
        self._is_on = currentSwitchValueDevice['CURRENT_VALUE'] != "0" if currentSwitchValueDevice else False

        self.updateDeviceIds = [self.dimDeviceId, self.switchDeviceId]
    
    async def updateState(self, state: DeviceStateDto):
        if state.id == self.switchDeviceId:
            self._is_on = state.current_value != "0"
        elif state.id == self.dimDeviceId:
            self.dimValue = state.current_value
        return
    
    @property
    def brightness(self) -> Optional[int]:
        """Return the current brightness."""
        _LOGGER.debug("Getting brightness for light %s with dimValue %s", self._attr_name, self.dimValue)
        return value_to_brightness((1, 100), int(self.dimValue))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api.set_value(self.switchDeviceId, "1")
        _LOGGER.debug("Turning on light %s with brightness %s", self._attr_name, kwargs)
        value_in_range = math.ceil(brightness_to_value((1, 100), kwargs['brightness']))
        _LOGGER.debug("Setting dim value for light %s to %s", self._attr_name, value_in_range)
        await self.coordinator.api.set_value(self.dimDeviceId, str(value_in_range))
    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.set_value(self.switchDeviceId, "0")

class DivusSwitchLightEntity(DivusLightEntity):

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        return [ColorMode.ONOFF]
    
    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator, device)
        self.type = TypeEnum.SWITCH
        self._is_on = device.json['CURRENT_VALUE'] == "1"

        self.updateDeviceIds = [self._attr_unique_id]
    
    async def updateState(self, state: DeviceStateDto):
        self._is_on = state.current_value == "1"
