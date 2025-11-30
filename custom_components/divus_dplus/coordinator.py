from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta

class DivusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api):
        super().__init__(
            hass,
            name="divus_dplus",
            update_interval=timedelta(seconds=2),
        )
        self.api = api

    async def _async_update_data(self):
        return await self.api.get_all_states()
