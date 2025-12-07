from itertools import groupby
import logging
from custom_components.divus_dplus.api import DivusDplusApi
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
from custom_components.divus_dplus.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class DivusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: DivusDplusApi, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name="divus_dplus",
            update_interval=timedelta(seconds=2),
            always_update=True,
        )
        from homeassistant.helpers.entity import Entity

        self.hass = hass
        self.api = api
        self.entry = entry
        self.devices: list[Entity]

    async def _async_update_data(self):
        _LOGGER.debug("Updating DIVUS D+ data for entry %s", self.entry.entry_id)

        device_ids = [dev.updateDeviceIds for dev in self.devices]
        device_ids = [
            x
            for xs in device_ids
            for x in xs
        ]
        states = await self.api.get_states(device_ids)

        for state in states:
            device = next((dev for dev in self.devices if state.id in dev.updateDeviceIds), None)
            if device:
                await device.updateState(state)
    
    async def async_config_entry_first_refresh(self):
        # Import here to avoid circular import
        from custom_components.divus_dplus.switch import DivusSwitchEntity
        from custom_components.divus_dplus.light import DivusDimLightEntity, DivusSwitchLightEntity
        from custom_components.divus_dplus.cover import DivusDeviceCoverEntity, DivusRoomCoverEntity
        from custom_components.divus_dplus.climate import DivusClimateEntity
        from custom_components.divus_dplus.sensor import DivusSensorEntity

        api_devices = await self.api.get_devices()

        self.devices = []
        for roomName, devices in groupby(api_devices, lambda d: d.parentName):
            devices = list(devices)
            _LOGGER.info(f"Room '{roomName}' has {len(devices)} devices.")

            roomEntities = []
            for device in devices:
                optionalP = device.json['OPTIONALP'].split('|')
                category = next((x for x in optionalP if x.startswith('category=')), None)
                if category:
                    category = category.replace('category=', '').strip("'")

                match (device.json["TYPE"], category):
                    case ("EIBOBJECT", "lighting"):
                        roomEntities.append(DivusSwitchLightEntity(self, device))
                    case ("CONTAINER", "lighting"):
                        roomEntities.append(DivusDimLightEntity(self, device))
                    case ("EIBOBJECT", _):
                        roomEntities.append(DivusSwitchEntity(self, device))
                    case ("CONTAINER", "shutters"):
                        roomEntities.append(DivusDeviceCoverEntity(self, device))
                    case ("CONTAINER", "climate"):
                        roomEntities.append(DivusClimateEntity(self, device))
                        roomEntities.append(DivusSensorEntity(self, device))

            coverEntities: list[DivusDeviceCoverEntity] = list(filter(lambda d: isinstance(d, DivusDeviceCoverEntity), roomEntities))
            if(len(coverEntities) > 1):
                shutterLongIds = [dev.shutterLongId for dev in coverEntities if dev.shutterLongId]
                shutterShortIds = [dev.shutterShortId for dev in coverEntities if dev.shutterShortId]
                roomEntities.append(DivusRoomCoverEntity(self, devices[0].parentId, f'{roomName} Alle', shutterLongIds, shutterShortIds, 
                    "1" if all(dev._attr_is_closed for dev in coverEntities) else "0"))
            self.devices.extend(roomEntities)
            

        self.hass.data.setdefault(DOMAIN, {})[self.entry.entry_id] = {
            "api": self.api,
            "coordinator": self,
        }

