import voluptuous as vol
from homeassistant import config_entries

from custom_components.divus_dplus.const import DOMAIN


class DivusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        errors = {}

        if user_input:
            # you can add test-connection here
            return self.async_create_entry(title="DIVUS D+", data=user_input)

        schema = vol.Schema(
            {
                vol.Required("host"): str,
                vol.Optional("username"): str,
                vol.Optional("password"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
