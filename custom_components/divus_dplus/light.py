import logging
import math
from enum import Enum
from typing import Any

from homeassistant.components.light import LightEntity
from homeassistant.components.light.const import ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import brightness_to_value, value_to_brightness

from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from custom_components.divus_dplus.entity import DivusEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.info("Setting up DIVUS D+ lights for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusLightEntity)]
    async_add_entities(devices)


class DivusLightEntity(LightEntity, CoordinatorEntity, DivusEntity):
    _is_on: bool = False

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto) -> None:
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = coordinator.entry.entry_id + "_" + device.id
        self._attr_name = device.json["NAME"]
        _LOGGER.debug("Adding light device: %s of type %s", self._attr_name, type(self))

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self) -> None:
        await self.coordinator.api.set_value(self.device.id, "1")
        _LOGGER.debug("Turned on light device: %s", self._attr_name)

    async def async_turn_off(self) -> None:
        await self.coordinator.api.set_value(self.device.id, "0")
        _LOGGER.debug("Turned off light device: %s", self._attr_name)


class TypeEnum(Enum):
    DIMABLE = "dimable"
    SWITCH = "switch"


class DivusDimLightEntity(DivusLightEntity):
    @property
    def supported_color_modes(self) -> set[ColorMode]:
        return {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto) -> None:
        super().__init__(coordinator, device)
        self.type = TypeEnum.DIMABLE
        current_dim_value_device = next(
            (dev for dev in device.sub_elements if dev["RENDERING_ID"] == "11"), None
        )
        self.dim_device_id = (
            current_dim_value_device["ID"] if current_dim_value_device else ""
        )
        self.dim_value = (
            current_dim_value_device["CURRENT_VALUE"]
            if current_dim_value_device
            else "0"
        )

        current_switch_value_device = next(
            (dev for dev in device.sub_elements if dev["RENDERING_ID"] == "10"), None
        )
        self.switch_device_id = (
            current_switch_value_device["ID"] if current_switch_value_device else ""
        )
        self._is_on = (
            current_switch_value_device["CURRENT_VALUE"] != "0"
            if current_switch_value_device
            else False
        )

        self.update_device_ids = {self.dim_device_id, self.switch_device_id}
        _LOGGER.debug(
            "Adding update IDs for dim light %s: %s",
            self._attr_name,
            self.update_device_ids,
        )

    def update_state(self, state: DeviceStateDto) -> None:
        if state.id == self.switch_device_id:
            new_value = state.current_value != "0"
            if new_value != self._is_on:
                self._is_on = new_value
                _LOGGER.debug(
                    "Updated state of %s to is_on=%s", self._attr_name, self._is_on
                )
        elif state.id == self.dim_device_id:
            new_value = state.current_value
            if new_value != self.dim_value:
                self.dim_value = new_value
                _LOGGER.debug(
                    "Updated dim value of %s to dim_value=%s",
                    self._attr_name,
                    self.dim_value,
                )

    @property
    def brightness(self) -> int | None:
        return value_to_brightness((1, 100), int(self.dim_value))

    async def async_turn_on(self, **kwargs: Any) -> None:
        if self.switch_device_id is None or self.dim_device_id is None:
            _LOGGER.error("Dim light device %s is missing device IDs", self._attr_name)
            return

        await self.coordinator.api.set_value(self.switch_device_id, "1")
        if "brightness" in kwargs:
            value_in_range = math.ceil(
                brightness_to_value((1, 100), kwargs["brightness"])
            )
            await self.coordinator.api.set_value(
                self.dim_device_id, str(value_in_range)
            )
            _LOGGER.debug(
                "Tured on and set brightness of %s to %s",
                self._attr_name,
                kwargs["brightness"],
            )
        else:
            _LOGGER.debug("Turned on light device: %s", self._attr_name)

    async def async_turn_off(self) -> None:
        if self.switch_device_id is None:
            _LOGGER.error(
                "Dim light device %s is missing switch device ID", self._attr_name
            )
            return
        await self.coordinator.api.set_value(self.switch_device_id, "0")
        _LOGGER.debug("Turned off light device: %s", self._attr_name)


class DivusSwitchLightEntity(DivusLightEntity):
    @property
    def supported_color_modes(self) -> set[ColorMode]:
        return {ColorMode.ONOFF}

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto) -> None:
        super().__init__(coordinator, device)
        self.type = TypeEnum.SWITCH
        self._is_on = device.json["CURRENT_VALUE"] == "1"

        self.update_device_ids = {device.id}

    def update_state(self, state: DeviceStateDto) -> None:
        new_is_on = state.current_value == "1"
        if state.id == self.device.id and new_is_on != self._is_on:
            self._is_on = new_is_on
            _LOGGER.debug(
                "Updated state of %s to is_on=%s", self._attr_name, self._is_on
            )
