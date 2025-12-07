import logging
from custom_components.divus_dplus.coordinator import DivusCoordinator
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto
from custom_components.divus_dplus.const import DOMAIN
from homeassistant.components.climate import ClimateEntity, HVACAction, HVACMode, UnitOfTemperature, ClimateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:

    _LOGGER.info("Setting up DIVUS D+ climates for entry %s", entry.entry_id)

    devices = hass.data[DOMAIN][entry.entry_id]["coordinator"].devices
    devices = [dev for dev in devices if isinstance(dev, DivusClimateEntity)]
    async_add_entities(devices)

class DivusClimateEntity(ClimateEntity, CoordinatorEntity):

    def __init__(self, coordinator: DivusCoordinator, device: DeviceDto):
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.entry.entry_id + "_" + device.id
        self._attr_name = device.json['NAME']

        currentTemperatureDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "34"), None)
        self.currentTemperatureDeviceId: str = currentTemperatureDevice['ID'] if currentTemperatureDevice else None
        self._attr_current_temperature: float = float(currentTemperatureDevice['CURRENT_VALUE']) if currentTemperatureDevice else None

        targetTemperatureDevice = next((dev for dev in device.subElements if dev['RENDERING_ID'] == "35"), None)
        self.targetTemperatureDeviceId: str = targetTemperatureDevice['ID'] if targetTemperatureDevice else None
        self._attr_target_temperature: float = float(targetTemperatureDevice['CURRENT_VALUE']) if targetTemperatureDevice else None
            
        self.updateDeviceIds = [self.currentTemperatureDeviceId, self.targetTemperatureDeviceId]
        _LOGGER.debug("Adding climate device: %s", self._attr_name)

    @property
    def supported_features(self) -> int:
        return ClimateEntityFeature.TARGET_TEMPERATURE
    
    @property
    def hvac_action(self):
        return HVACAction.OFF
    
    @property
    def hvac_mode(self):
        return HVACMode.OFF
    
    @property
    def hvac_modes(self):
        return [HVACMode.HEAT, HVACMode.OFF]
    
    @property
    def target_temperature_high(self):
        return 30.0
    
    @property
    def target_temperature_low(self):
        return 15.0
    
    @property
    def target_temperature_step(self):
        return 0.1
    
    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is not None:
            await self.coordinator.api.set_value(self.targetTemperatureDeviceId, str(int(temperature)))
            _LOGGER.debug("Set target temperature of %s to %s", self._attr_name, temperature)

    async def updateState(self, state: DeviceStateDto):
        float_current_value = float(state.current_value)
        if(state.id == self.currentTemperatureDeviceId and float_current_value != self._attr_current_temperature):
            self._attr_current_temperature = float_current_value
            _LOGGER.debug("Updated current temperature of %s to %s", self._attr_name, float_current_value)
        elif(state.id == self.targetTemperatureDeviceId and float_current_value != self._attr_target_temperature):
            self._attr_target_temperature = float_current_value
            _LOGGER.debug("Updated target temperature of %s to %s", self._attr_name, float_current_value)