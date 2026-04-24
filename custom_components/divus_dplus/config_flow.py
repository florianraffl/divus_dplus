import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from custom_components.divus_dplus.const import (
    CONF_ADD_GLOBAL_COVER,
    CONF_ADD_ROOM_COVERS,
    DOMAIN,
)


def _covers_schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_ADD_ROOM_COVERS,
                default=defaults.get(CONF_ADD_ROOM_COVERS, True),
            ): bool,
            vol.Required(
                CONF_ADD_GLOBAL_COVER,
                default=defaults.get(CONF_ADD_GLOBAL_COVER, True),
            ): bool,
        }
    )


class DivusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors = {}

        if user_input is not None:
            self._data = user_input
            return await self.async_step_covers()

        schema = vol.Schema(
            {
                vol.Required("host"): str,
                vol.Optional("username"): str,
                vol.Optional("password"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_covers(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="DIVUS D+",
                data=self._data,
                options=user_input,
            )

        return self.async_show_form(
            step_id="covers",
            data_schema=_covers_schema({}),
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return DivusOptionsFlow()


class DivusOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_covers_schema(self.config_entry.options),
        )
