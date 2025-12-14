import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
)
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.divus_dplus.const import DOMAIN
from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from custom_components.divus_dplus.entity import DivusEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.info("Setting up DIVUS D+ climates for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusClimateEntity)]
    async_add_entities(devices)


class DivusClimateEntity(ClimateEntity, CoordinatorEntity, DivusEntity):
    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.entry.entry_id + "_" + device.id
        self._attr_name = device.json["NAME"]

        current_temperature_device = next(
            (dev for dev in device.sub_elements if dev["RENDERING_ID"] == "34"), None
        )
        self.current_temperature_device_id: str = (
            current_temperature_device["ID"] if current_temperature_device else ""
        )
        self._attr_current_temperature: float = (
            float(current_temperature_device["CURRENT_VALUE"])
            if current_temperature_device
            else 0
        )

        target_temperature_device = next(
            (dev for dev in device.sub_elements if dev["RENDERING_ID"] == "35"), None
        )
        self.target_temperature_device_id: str = (
            target_temperature_device["ID"] if target_temperature_device else ""
        )
        self._attr_target_temperature: float = (
            float(target_temperature_device["CURRENT_VALUE"])
            if target_temperature_device
            else 0
        )

        self.update_device_ids = {
            self.current_temperature_device_id,
            self.target_temperature_device_id,
        }

        self.coordinator = coordinator
        _LOGGER.debug("Adding climate device: %s", self._attr_name)

    @property
    def supported_features(self) -> int:
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def hvac_action(self) -> HVACAction:
        return HVACAction.OFF

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.OFF

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return [HVACMode.HEAT, HVACMode.OFF]

    @property
    def target_temperature_high(self) -> float:
        return 30.0

    @property
    def target_temperature_low(self) -> float:
        return 15.0

    @property
    def target_temperature_step(self) -> float:
        return 0.1

    @property
    def temperature_unit(self) -> str:
        return UnitOfTemperature.CELSIUS

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is not None:
            await self.coordinator.api.set_value(
                self.target_temperature_device_id, str(int(temperature))
            )
            _LOGGER.debug(
                "Set target temperature of %s to %s", self._attr_name, temperature
            )

    def update_state(self, state: DeviceStateDto) -> None:
        float_current_value = float(state.current_value)
        if (
            state.id == self.current_temperature_device_id
            and float_current_value != self._attr_current_temperature
        ):
            self._attr_current_temperature = float_current_value
            _LOGGER.debug(
                "Updated current temperature of %s to %s",
                self._attr_name,
                float_current_value,
            )
        elif (
            state.id == self.target_temperature_device_id
            and float_current_value != self._attr_target_temperature
        ):
            self._attr_target_temperature = float_current_value
            _LOGGER.debug(
                "Updated target temperature of %s to %s",
                self._attr_name,
                float_current_value,
            )
