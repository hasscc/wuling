import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from . import DOMAIN, TITLE


def get_schemas(defaults):
    return vol.Schema({
        vol.Required(CONF_ACCESS_TOKEN, default=defaults.get(CONF_ACCESS_TOKEN)): str,
    })


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input):
        if user_input is None:
            user_input = {}
        if user_input.get(CONF_ACCESS_TOKEN):
            return self.async_create_entry(title=TITLE, data=user_input)

        return self.async_show_form(
            step_id='user',
            data_schema=get_schemas(user_input),
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is None:
            user_input = {}
        if user_input.get(CONF_ACCESS_TOKEN):
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title='', data={})
        defaults = {
            **self.config_entry.data,
            **self.config_entry.options,
            **user_input,
        }
        return self.async_show_form(
            step_id='init',
            data_schema=get_schemas(defaults),
            description_placeholders={'tip': self.context.pop('last_error', '')},
        )
