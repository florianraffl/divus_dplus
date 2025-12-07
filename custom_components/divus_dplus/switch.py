from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:

    _LOGGER.info("Setting up DIVUS D+ switches for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusSwitchEntity)]
    async_add_entities(devices)

class DivusSwitchEntity(SwitchEntity, CoordinatorEntity):

    _is_on: bool = False

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = coordinator.entry.entry_id + "_" + device.id
        self._attr_name = device.json['NAME']
        self._is_on = device.json['CURRENT_VALUE'] == "1"
        _LOGGER.debug("Adding switch device: %s", self._attr_name)

        self.updateDeviceIds = [self._attr_unique_id]

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self):
        await self.coordinator.api.set_value(self.device.id, "1")
    async def async_turn_off(self):
        await self.coordinator.api.set_value(self.device.id, "0")
    
    async def updateState(self, state: DeviceStateDto):
        self._is_on = state.current_value == "1"