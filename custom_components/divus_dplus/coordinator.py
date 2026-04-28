import logging
from datetime import timedelta
from itertools import groupby
from typing import TYPE_CHECKING, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.divus_dplus.api import DivusDplusApi
from custom_components.divus_dplus.const import DOMAIN

if TYPE_CHECKING:
    from custom_components.divus_dplus.entity import DivusEntity

_LOGGER = logging.getLogger(__name__)


class DivusCoordinator(DataUpdateCoordinator):
    def __init__(
        self, hass: HomeAssistant, api: DivusDplusApi, entry: ConfigEntry
    ) -> None:
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
        self.devices: list[DivusEntity]

    async def _async_update_data(self) -> None:
        device_ids = [dev.update_device_ids for dev in self.devices]
        device_ids = [x for xs in device_ids for x in xs]
        device_ids = [x for x in device_ids if x != ""]
        states = await self.api.get_states(device_ids)

        for state in states:
            devices = [dev for dev in self.devices if state.id in dev.update_device_ids]
            for device in devices:
                device.update_state(state)

    async def async_config_entry_first_refresh(self) -> None:
        # Dynamic imports to avoid circular dependencies
        from custom_components.divus_dplus.climate import (  # noqa: PLC0415
            DivusClimateEntity,
        )
        from custom_components.divus_dplus.cover import (  # noqa: PLC0415
            DivusDeviceCoverEntity,
            DivusGlobalCoverEntity,
            DivusRoomCoverEntity,
        )
        from custom_components.divus_dplus.light import (  # noqa: PLC0415
            DivusColorTempLightEntity,
            DivusDimLightEntity,
            DivusSwitchLightEntity,
        )
        from custom_components.divus_dplus.sensor import (  # noqa: PLC0415
            DivusSensorEntity,
        )
        from custom_components.divus_dplus.switch import (  # noqa: PLC0415
            DivusSwitchEntity,
        )

        api_devices = await self.api.get_devices()

        self.devices = []
        for room_name, devices_list in groupby(api_devices, lambda d: d.parentName):
            devices = list(devices_list)
            _LOGGER.info("Room '%s' has %d devices.", room_name, len(devices))

            room_entities: set[DivusEntity] = set()
            for device in devices:
                optional_p = device.json["OPTIONALP"].split("|")
                category = next(
                    (x for x in optional_p if x.startswith("category=")), None
                )
                if category:
                    category = category.replace("category=", "").strip("'")

                match (device.json["TYPE"], category):
                    case ("EIBOBJECT", "lighting"):
                        room_entities.add(DivusSwitchLightEntity(self, device))
                    case ("CONTAINER", "lighting"):
                        if device.sub_elements and any(
                            sub_dev["RENDERING_ID"] == "418"
                            for sub_dev in device.sub_elements
                        ):
                            room_entities.add(DivusColorTempLightEntity(self, device))
                        elif device.sub_elements and any(
                            sub_dev["RENDERING_ID"] == "11"
                            for sub_dev in device.sub_elements
                        ):
                            room_entities.add(DivusDimLightEntity(self, device))
                    case ("EIBOBJECT", _):
                        room_entities.add(DivusSwitchEntity(self, device))
                    case ("CONTAINER", "shutters"):
                        room_entities.add(DivusDeviceCoverEntity(self, device))
                    case ("CONTAINER", "climate"):
                        room_entities.add(DivusClimateEntity(self, device))
                        room_entities.add(DivusSensorEntity(self, device))
                    case _:
                        _LOGGER.debug(
                            "Device '%s' of type '%s' with category '%s' is not supported.",
                            device.json["NAME"],
                            device.json["TYPE"],
                            category,
                        )

            cover_entities: list[DivusDeviceCoverEntity] = [
                cast("DivusDeviceCoverEntity", dev)
                for dev in room_entities
                if isinstance(dev, DivusDeviceCoverEntity)
            ]
            if len(cover_entities) > 1:
                shutter_long_ids = [
                    dev.shutter_long_id for dev in cover_entities if dev.shutter_long_id
                ]
                shutter_short_ids = [
                    dev.shutter_short_id
                    for dev in cover_entities
                    if dev.shutter_short_id
                ]
                room_entities.add(
                    DivusRoomCoverEntity(
                        self,
                        devices[0].parentId,
                        f"{room_name} Alle",
                        shutter_long_ids,
                        shutter_short_ids,
                    )
                )
            self.devices.extend(room_entities)

        all_cover_entities: list[DivusDeviceCoverEntity] = [
            dev for dev in self.devices if isinstance(dev, DivusDeviceCoverEntity)
        ]
        if all_cover_entities:
            shutter_long_ids = [
                dev.shutter_long_id for dev in all_cover_entities if dev.shutter_long_id
            ]
            shutter_short_ids = [
                dev.shutter_short_id
                for dev in all_cover_entities
                if dev.shutter_short_id
            ]
            self.devices.append(
                DivusGlobalCoverEntity(
                    self,
                    self.entry.entry_id,
                    shutter_long_ids,
                    shutter_short_ids,
                )
            )

        self.hass.data.setdefault(DOMAIN, {})[self.entry.entry_id] = {
            "api": self.api,
            "coordinator": self,
        }
