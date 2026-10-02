import goodwe
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

CONF_ADVANCED = "advanced_write"


class GoodWeFlow(config_entries.ConfigFlow, domain="goodwe_local"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            try:
                inv = await goodwe.connect(user_input[CONF_HOST], port=user_input[CONF_PORT])
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(inv.serial_number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"GoodWe {inv.model_name}", data=user_input)
        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=8899): vol.In([8899, 502]),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return GoodWeOptions()


class GoodWeOptions(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Optional(CONF_ADVANCED,
                         default=self.config_entry.options.get(CONF_ADVANCED, False)): bool,
        }))
