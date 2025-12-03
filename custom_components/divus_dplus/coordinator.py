import logging
from custom_components.divus_dplus.api import DivusDplusApi
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
from custom_components.divus_dplus.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class DivusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: DivusDplusApi, entry, logger: logging.Logger):
        super().__init__(
            hass,
            name="divus_dplus",
            update_interval=timedelta(seconds=2),
            logger=logger,
        )
        self.hass = hass
        self.api = api
        self.entry = entry

    async def _async_update_data(self):
        _LOGGER.debug("Updating DIVUS D+ data for entry %s", self.entry.entry_id)
        devices = self.hass.data[DOMAIN][self.entry.entry_id]["devices"]

        device_ids = [dev["id"] for dev in devices]
        states = await self.api.get_states(device_ids)

        for state in states:
            device = next((dev for dev in devices if dev["id"] == state.id), None)
            if device:
                await device.updateState(state)
    
    async def async_config_entry_first_refresh(self):
        # Import here to avoid circular import
        from custom_components.divus_dplus.switch import DivusSwitchEntity

        api_devices = await self.api.get_devices()

        devices = []
        for device in api_devices:
            match device.json["TYPE"]:
                case "EIBOBJECT":
                    devices.append(DivusSwitchEntity(self, device))

        self.hass.data.setdefault(DOMAIN, {})[self.entry.entry_id] = {
            "api": self.api,
            "coordinator": self,
            "devices": devices,
        }

