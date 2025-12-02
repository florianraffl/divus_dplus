from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]

    entities = [
        DivusSwitchEntity(coordinator, dev)
        for dev in devices if type(dev) is DivusSwitchEntity
    ]
    async_add_entities(entities)

class DivusSwitchEntity(SwitchEntity):

    _is_on: bool = False

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = device.id
        self._attr_name = device.json['NAME']
        self._is_on = device.json['CURRENT_VALUE'] == "1"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self):
        await self.coordinator.api.set_value(self.device.id, "1")
    async def async_turn_off(self):
        await self.coordinator.api.set_value(self.device.id, "0")
    
    async def updateState(self, state: DeviceStateDto):
        self._is_on = state.current_value == "1"