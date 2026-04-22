from abc import ABC, abstractmethod

from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.divus_dplus.const import DOMAIN
from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto


class DivusEntity(ABC):
    """Abstract base class for Divus D+ entities."""

    def __init__(self, device: DeviceDto) -> None:
        """Store the device and register it in the HA device registry."""
        self.device = device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            name=device.json["NAME"],
            manufacturer="DIVUS",
        )

    @property
    def update_device_ids(self) -> set[str]:
        """Return a list of update IDs that this entity listens to."""
        return self._update_device_ids

    @update_device_ids.setter
    def update_device_ids(self, value: set[str]) -> None:
        """Set the update IDs that this entity listens to."""
        self._update_device_ids = value

    @abstractmethod
    def update_state(self, state: DeviceStateDto) -> None:
        """Update the entity's state."""
