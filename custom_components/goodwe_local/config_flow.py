import goodwe
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT


class GoodWeFlow(config_entries.ConfigFlow, domain="goodwe_local"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            try:
                inv = await goodwe.connect(user_input[CONF_HOST], port=user_input[CONF_PORT])
                await self.async_set_unique_id(inv.serial_number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"GoodWe {inv.model_name}", data=user_input)
            except config_entries.data_entry_flow.AbortFlow:
                raise
            except Exception:
                errors["base"] = "cannot_connect"
        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=8899): vol.In([8899, 502]),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
