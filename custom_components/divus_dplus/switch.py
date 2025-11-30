from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]

    entities = [
        DivusSwitchEntity(coordinator, dev)
        for dev in devices if dev["type"] == "switch"
    ]
    async_add_entities(entities)

class DivusSwitchEntity(SwitchEntity):
    def __init__(self, coordinator, device):
        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = device["id"]
        self._attr_name = device["name"]

    @property
    def is_on(self):
        state = self.coordinator.data[self.device["id"]]
        return state["value"] == 1

    async def async_turn_on(self):
        await self.coordinator.api.set_state(self.device["id"], {"value": 1})

    async def async_turn_off(self):
        await self.coordinator.api.set_state(self.device["id"], {"value": 0})
