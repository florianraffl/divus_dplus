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
            _LOGGER,
            name="divus_dplus",
            update_interval=timedelta(seconds=2),
            always_update=True,
        )
        self.hass = hass
        self.api = api
        self.entry = entry

    async def _async_update_data(self):
        _LOGGER.debug("Updating DIVUS D+ data for entry %s", self.entry.entry_id)

        from homeassistant.helpers.entity import Entity
        devices: list[Entity] = self.hass.data[DOMAIN][self.entry.entry_id]["devices"]

        device_ids = [dev.device.id for dev in devices]
        states = await self.api.get_states(device_ids)

        for state in states:
            device = next((dev for dev in devices if dev.device.id == state.id), None)
            if device:
                await device.updateState(state)
    
    async def async_config_entry_first_refresh(self):
        # Import here to avoid circular import
        from custom_components.divus_dplus.switch import DivusSwitchEntity
        from custom_components.divus_dplus.light import DivusDimLightEntity, DivusSwitchLightEntity

        api_devices = await self.api.get_devices()

        devices = []
        for device in api_devices:
            optionalP = device.json['OPTIONALP'].split('|')
            _LOGGER.debug("Device %s optionalP: %s", device.json['NAME'], optionalP)
            category = next((x for x in optionalP if x.startswith('category=')), None).replace('category=', '').strip("'")

            match (device.json["TYPE"], category):
                case ("EIBOBJECT", "lighting"):
                    devices.append(DivusSwitchLightEntity(self, device))
                case ("CONTAINER", "lighting"):
                    devices.append(DivusDimLightEntity(self, device))
                case ("EIBOBJECT", _):
                    devices.append(DivusSwitchEntity(self, device))

        self.hass.data.setdefault(DOMAIN, {})[self.entry.entry_id] = {
            "api": self.api,
            "coordinator": self,
            "devices": devices,
        }

