import voluptuous as vol
from homeassistant import config_entries
from . import DOMAIN, TITLE, CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, callback


def get_schemas(defaults):
    return vol.Schema({
        vol.Required(CONF_ACCESS_TOKEN, default=defaults.get(CONF_ACCESS_TOKEN)): str,
        vol.Required(CONF_CLIENT_ID, default=defaults.get(CONF_CLIENT_ID)): str,
        vol.Required(CONF_CLIENT_SECRET, default=defaults.get(CONF_CLIENT_SECRET)): str,
    })


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return OptionsFlowHandler(entry)

    async def async_step_user(self, user_input):
        if user_input is None:
            user_input = {}
        if user_input.get(CONF_ACCESS_TOKEN):
            return self.async_create_entry(title=TITLE, data=user_input)

        self.context['tip'] = '请抓包获取以下参数'
        return self.async_show_form(
            step_id='user',
            data_schema=get_schemas(user_input),
            description_placeholders={'tip': self.context.pop('tip', '')},
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
            description_placeholders={'tip': self.context.pop('tip', '')},
        )
