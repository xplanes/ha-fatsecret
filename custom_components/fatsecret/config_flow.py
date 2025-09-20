"""Config flow for the FatSecret integration."""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

import aiohttp
import urllib.parse
import time
import random


from .oauth_helpers import (
    oauth_build_base_string,
    oauth_generate_signature,
)

from .const import (
    DOMAIN,
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    CONF_TOKEN,
    CONF_TOKEN_SECRET,
    REQUEST_TOKEN_URL,
    AUTHORIZE_URL,
    ACCESS_TOKEN_URL,
    OAUTH_SIGNATURE_METHOD,
    OAUTH_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class FatsecretConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FatSecret."""

    VERSION = 1

    def __init__(self):
        self.consumer_key: str = ""
        self.consumer_secret: str = ""
        self.request_token: str = ""
        self.request_token_secret: str = ""

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.consumer_key = user_input["consumer_key"]
            self.consumer_secret = user_input["consumer_secret"]

            # Step 1: request token
            try:
                await self._get_request_token()
                return await self.async_step_authorize()
            except Exception as e:
                _LOGGER.exception("Failed to obtain request token")
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
        auth_url = f"{AUTHORIZE_URL}?oauth_token={self.request_token}"
        # Wrap URL in HTML <a> tag
        auth_link_html = f'<a href="{auth_url}" target="_blank">Click here to authorize FatSecret</a>'

        """Show the user a link to authorize."""
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
            except Exception:
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
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": str(random.randint(0, 100000000)),
            "oauth_timestamp": str(int(time.time())),
            "oauth_signature_method": OAUTH_SIGNATURE_METHOD,
            "oauth_version": OAUTH_VERSION,
            "oauth_callback": "oob",
        }

        base_string = oauth_build_base_string("GET", REQUEST_TOKEN_URL, oauth_params)
        oauth_params["oauth_signature"] = oauth_generate_signature(
            base_string, self.consumer_secret, ""
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(REQUEST_TOKEN_URL, params=oauth_params) as resp:
                resp.raise_for_status()
                resp_text = await resp.text()
                _LOGGER.debug("Request token response: %s", resp_text)

        qs = dict(urllib.parse.parse_qsl(resp_text))

        if "oauth_token" not in qs:
            raise Exception(f"Failed to obtain request token: {qs}")

        self.request_token = qs["oauth_token"]
        self.request_token_secret = qs["oauth_token_secret"]

    async def _get_access_token(self, verifier: str):
        """Exchange the request token for an access token."""
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": str(random.randint(0, 100000000)),
            "oauth_timestamp": str(int(time.time())),
            "oauth_signature_method": OAUTH_SIGNATURE_METHOD,
            "oauth_version": OAUTH_VERSION,
            "oauth_token": self.request_token,
            "oauth_verifier": verifier,
        }

        base_string = oauth_build_base_string("GET", ACCESS_TOKEN_URL, oauth_params)
        oauth_params["oauth_signature"] = oauth_generate_signature(
            base_string,
            self.consumer_secret,
            self.request_token_secret,
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(ACCESS_TOKEN_URL, params=oauth_params) as resp:
                text = await resp.text()
                _LOGGER.debug("Access token response: %s", text)
                qs = dict(urllib.parse.parse_qsl(text))
                return qs["oauth_token"], qs["oauth_token_secret"]
