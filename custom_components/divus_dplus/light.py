from enum import Enum
from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:

    _LOGGER.info("Setting up DIVUS D+ lights for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["devices"]
    devices = [dev for dev in devices if isinstance(dev, DivusLightEntity)]
    async_add_entities(devices)

class DivusLightEntity(LightEntity, CoordinatorEntity):

    _is_on: bool = False

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = device.id
        self._attr_name = device.json['NAME']
        _LOGGER.debug("Adding switch device: %s", self._attr_name)

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
    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator, device)
        self.type = TypeEnum.DIMABLE
        currentDimValueDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "11"), None)
        self.dimDeviceId = currentDimValueDevice['ID'] if currentDimValueDevice else None
        self.dimValue = currentDimValueDevice['CURRENT_VALUE'] if currentDimValueDevice else "0"

        currentSwitchValueDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "10"), None)
        self.switchDeviceId = currentSwitchValueDevice['ID'] if currentSwitchValueDevice else None
        self._is_on = currentSwitchValueDevice['CURRENT_VALUE'] != "0" if currentSwitchValueDevice else False
    
    async def updateState(self, state: DeviceStateDto):
        currentDimValueDevice = next((dev for dev in state.subElements if dev['RENDERING_ID'] == "11"), None)

class DivusSwitchLightEntity(DivusLightEntity):
    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator, device)
        self.type = TypeEnum.SWITCH
        self._is_on = device['CURRENT_VALUE']
    
    async def updateState(self, state: DeviceStateDto):
        self._is_on = state.current_value == "1"
