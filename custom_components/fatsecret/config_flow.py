"""Config flow for the FatSecret integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    CONF_TOKEN,
    CONF_TOKEN_SECRET,
)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONSUMER_KEY): str,
        vol.Required(CONF_CONSUMER_SECRET): str,
        vol.Required(CONF_TOKEN): str,
        vol.Required(CONF_TOKEN_SECRET): str,
    }
)


class FatSecretConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FatSecret."""

    VERSION = 1

    def is_matching(self, other_flow) -> bool:
        """Return True if other_flow is matching this flow."""
        # Implement logic to determine if this flow matches the other flow.
        # For most custom integrations, returning True is sufficient.
        return True

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="FatSecret",
                data={
                    CONF_CONSUMER_KEY: user_input[CONF_CONSUMER_KEY],
                    CONF_CONSUMER_SECRET: user_input[CONF_CONSUMER_SECRET],
                    CONF_TOKEN: user_input[CONF_TOKEN],
                    CONF_TOKEN_SECRET: user_input[CONF_TOKEN_SECRET],
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CONSUMER_KEY): str,
                vol.Required(CONF_CONSUMER_SECRET): str,
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_TOKEN_SECRET): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONSUMER_KEY): str,
                    vol.Required(CONF_CONSUMER_SECRET): str,
                    vol.Required(CONF_TOKEN): str,
                    vol.Required(CONF_TOKEN_SECRET): str,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return FatSecretOptionsFlow(config_entry)


class FatSecretOptionsFlow(config_entries.OptionsFlow):
    """Handle FatSecret options."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Example: allow changing the name in options
        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NAME,
                    default=self.config_entry.data.get(CONF_NAME, "FatSecret"),
                ): str
            }
        )
        return self.async_show_form(step_id="init", data_schema=options_schema)
