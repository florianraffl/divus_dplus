import logging
from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from custom_components.divus_dplus.const import DOMAIN
from homeassistant.components.sensor import SensorEntity, UnitOfTemperature, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:

    _LOGGER.info("Setting up DIVUS D+ sensors for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusSensorEntity)]
    async_add_entities(devices)

class DivusSensorEntity(SensorEntity, CoordinatorEntity):

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator)

        self._attr_name = device.json['NAME']

        currentTemperatureDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "34"), None)
        self.currentTemperatureDeviceId: str = currentTemperatureDevice['ID'] if currentTemperatureDevice else None
        self._attr_unique_id = coordinator.entry.entry_id + "_" + self.currentTemperatureDeviceId
        self._attr_native_value: float = float(currentTemperatureDevice['CURRENT_VALUE']) if currentTemperatureDevice else None
  
        self.updateDeviceIds = [self.currentTemperatureDeviceId]
        _LOGGER.debug("Adding sensor device: %s", self._attr_name)
    
    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE
    
    @property
    def native_unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS
    
    @property
    def native_value(self):
        return self._attr_native_value
    
    @property
    def suggested_display_precision(self) -> int | None:
        return 2

    async def updateState(self, state: DeviceStateDto):
        if(state.id == self.currentTemperatureDeviceId):
            self._attr_native_value = float(state.current_value)