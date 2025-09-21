"""Config flow for the FatSecret integration."""

import logging
import random
import time
import urllib.parse

import aiohttp
import voluptuous as vol
from homeassistant import config_entries

from .const import (
    ACCESS_TOKEN_URL,
    AUTHORIZE_URL,
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    CONF_TOKEN,
    CONF_TOKEN_SECRET,
    DOMAIN,
    OAUTH_PARAM_CONSUMER_KEY,
    OAUTH_PARAM_NONCE,
    OAUTH_PARAM_TIMESTAMP,
    OAUTH_PARAM_TOKEN,
    OAUTH_PARAM_VERSION,
    OAUTH_PARAM_SIGNATURE,
    OAUTH_PARAM_SIGNATURE_METHOD,
    OAUTH_PARAM_CALLBACK,
    OAUTH_PARAM_VERIFIER,
    OAUTH_PARAM_TOKEN_SECRET,
    OAUTH_SIGNATURE_METHOD,
    OAUTH_VERSION,
    OAUTH_CALLBACK,
    REQUEST_TOKEN_URL,
)
from .oauth_helpers import (
    oauth_build_base_string,
    oauth_generate_signature,
)

_LOGGER = logging.getLogger(__name__)


class FatsecretConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FatSecret."""

    def is_matching(self, other_flow: config_entries.ConfigFlow) -> bool:
        """Check if the other flow matches this config flow."""
        return getattr(other_flow, "DOMAIN", None) == DOMAIN

    def __init__(self):
        self.consumer_key: str = ""
        self.consumer_secret: str = ""
        self.request_token: str = ""
        self.request_token_secret: str = ""

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.consumer_key = user_input[CONF_CONSUMER_KEY]
            self.consumer_secret = user_input[CONF_CONSUMER_SECRET]

            # Step 1: request token
            try:
                await self._get_request_token()
                return await self.async_step_authorize()
            except (aiohttp.ClientError, ValueError) as err:
                _LOGGER.exception("Failed to obtain request token: %s", err)
                errors["base"] = "auth_failed"

        schema = vol.Schema(
            {
                vol.Required(CONF_CONSUMER_KEY): str,
                vol.Required(CONF_CONSUMER_SECRET): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_authorize(self, user_input=None):
        """Show the user a link to authorize."""
        auth_url = f"{AUTHORIZE_URL}?{OAUTH_PARAM_TOKEN}={self.request_token}"

        if user_input is not None:
            # user entered oauth_verifier
            verifier = user_input["verifier"]
            try:
                access_token, access_token_secret = await self._get_access_token(
                    verifier
                )
                data = {
                    CONF_CONSUMER_KEY: self.consumer_key,
                    CONF_CONSUMER_SECRET: self.consumer_secret,
                    CONF_TOKEN: access_token,
                    CONF_TOKEN_SECRET: access_token_secret,
                }
                return self.async_create_entry(title="FatSecret", data=data)
            except (aiohttp.ClientError, ValueError) as err:
                _LOGGER.exception("Failed to obtain access token: %s", err)
                return self.async_show_form(
                    step_id="authorize",
                    data_schema=vol.Schema({vol.Required("verifier"): str}),
                    errors={"base": "auth_failed"},
                    description_placeholders={"auth_url": auth_url},
                )

        return self.async_show_form(
            step_id="authorize",
            data_schema=vol.Schema({vol.Required("verifier"): str}),
            description_placeholders={"auth_url": auth_url},
        )

    async def _get_request_token(self):
        """Request a temporary request token."""

        oauth_params = {
            OAUTH_PARAM_CONSUMER_KEY: self.consumer_key,
            OAUTH_PARAM_NONCE: str(random.randint(0, 100000000)),
            OAUTH_PARAM_TIMESTAMP: str(int(time.time())),
            OAUTH_PARAM_SIGNATURE_METHOD: OAUTH_SIGNATURE_METHOD,
            OAUTH_PARAM_VERSION: OAUTH_VERSION,
            OAUTH_PARAM_CALLBACK: OAUTH_CALLBACK,
        }

        base_string = oauth_build_base_string("GET", REQUEST_TOKEN_URL, oauth_params)
        oauth_params[OAUTH_PARAM_SIGNATURE] = oauth_generate_signature(
            base_string, self.consumer_secret, ""
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(REQUEST_TOKEN_URL, params=oauth_params) as resp:
                resp.raise_for_status()
                resp_text = await resp.text()
                _LOGGER.debug("Request token response: %s", resp_text)

        qs = dict(urllib.parse.parse_qsl(resp_text))

        if OAUTH_PARAM_TOKEN not in qs:
            raise ValueError(f"Failed to obtain request token: {qs}")

        self.request_token = qs[OAUTH_PARAM_TOKEN]
        self.request_token_secret = qs[OAUTH_PARAM_TOKEN_SECRET]

    async def _get_access_token(self, verifier: str):
        """Exchange the request token for an access token."""
        oauth_params = {
            OAUTH_PARAM_CONSUMER_KEY: self.consumer_key,
            OAUTH_PARAM_NONCE: str(random.randint(0, 100000000)),
            OAUTH_PARAM_TIMESTAMP: str(int(time.time())),
            OAUTH_PARAM_SIGNATURE_METHOD: OAUTH_SIGNATURE_METHOD,
            OAUTH_PARAM_VERSION: OAUTH_VERSION,
            OAUTH_PARAM_TOKEN: self.request_token,
            OAUTH_PARAM_VERIFIER: verifier,
        }

        base_string = oauth_build_base_string("GET", ACCESS_TOKEN_URL, oauth_params)
        oauth_params[OAUTH_PARAM_SIGNATURE] = oauth_generate_signature(
            base_string,
            self.consumer_secret,
            self.request_token_secret,
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(ACCESS_TOKEN_URL, params=oauth_params) as resp:
                text = await resp.text()
                _LOGGER.debug("Access token response: %s", text)
                qs = dict(urllib.parse.parse_qsl(text))
                return qs[OAUTH_PARAM_TOKEN], qs[OAUTH_PARAM_TOKEN_SECRET]
