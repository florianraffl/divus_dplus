from abc import ABC, abstractmethod

from custom_components.divus_dplus.dtos import DeviceStateDto


class DivusEntity(ABC):
    """Abstract base class for Divus D+ entities."""

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
