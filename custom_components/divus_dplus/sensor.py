import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
    _LOGGER.info("Setting up DIVUS D+ sensors for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusSensorEntity)]
    async_add_entities(devices)


class DivusSensorEntity(SensorEntity, CoordinatorEntity, DivusEntity):
    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto) -> None:
        super().__init__(coordinator)

        self._attr_name = device.json["NAME"]

        current_temperature_device = next(
            (dev for dev in device.sub_elements if dev["RENDERING_ID"] == "34"), None
        )
        self.current_temperature_device_id: str = (
            current_temperature_device["ID"] if current_temperature_device else ""
        )
        self._attr_unique_id = (
            coordinator.entry.entry_id + "_" + self.current_temperature_device_id
        )
        self._attr_native_value: float = (
            float(current_temperature_device["CURRENT_VALUE"])
            if current_temperature_device
            else 0
        )

        self.update_device_ids = {self.current_temperature_device_id}
        _LOGGER.debug("Adding sensor device: %s", self._attr_name)

    @property
    def device_class(self) -> SensorDeviceClass:
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> UnitOfTemperature:
        return UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> float:
        return self._attr_native_value

    @property
    def suggested_display_precision(self) -> int | None:
        return 2

    def update_state(self, state: DeviceStateDto) -> None:
        if state.id == self.current_temperature_device_id:
            self._attr_native_value = float(state.current_value)
