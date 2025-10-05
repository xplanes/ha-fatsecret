"""Module for managing the FatSecret component."""

import logging
import random
import time
from datetime import timedelta
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant, ServiceCall

from .oauth_helpers import (
    oauth_build_authorization_header,
    oauth_build_base_string,
    oauth_generate_signature,
)

from .const import (
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    CONF_TOKEN,
    CONF_TOKEN_SECRET,
    OAUTH_PARAM_CONSUMER_KEY,
    OAUTH_PARAM_NONCE,
    OAUTH_PARAM_TIMESTAMP,
    OAUTH_PARAM_TOKEN,
    OAUTH_PARAM_VERSION,
    OAUTH_PARAM_SIGNATURE,
    OAUTH_PARAM_SIGNATURE_METHOD,
    OAUTH_SIGNATURE_METHOD,
    OAUTH_VERSION,
    API_FOOD_ENTRIES_URL,
    FATSECRET_FOOD_ENTRIES,
    FATSECRET_FOOD_ENTRY,
    FATSECRET_FIELDS,
    DOMAIN,
    FATSECRET_UPDATE_INTERVAL,
    FATSECRET_FOOD_ENTRIES_ERRORS,
)

_LOGGER = logging.getLogger(__name__)


class FatSecretCoordinator(DataUpdateCoordinator):
    """Class to handle FatSecret API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="FatSecret",
            update_interval=timedelta(
                minutes=FATSECRET_UPDATE_INTERVAL
            ),  # periodic update interval
        )
        self.entry = config_entry
        self.latest_data = {}

        async def handle_update_fatsecret(_call: ServiceCall):
            await self.async_refresh()

        self.hass.services.async_register(
            DOMAIN, "update_fatsecret", handle_update_fatsecret
        )

    async def _async_update_data(self):
        """Fetch data from FatSecret API."""
        try:
            # Call your API client once
            data = await self.fetch_fatsecret_data()
            self.latest_data = data
            return data
        except Exception as err:
            raise UpdateFailed(f"FatSecret update failed: {err}") from err

    async def fetch_fatsecret_data(self) -> dict:
        """Fetch latest FatSecret food entries and return summed metrics.

        Returns a dict with all fields in FATSECRET_FIELDS as keys and their summed
        values as floats.
        """

        query_params = {"format": "json"}  # API params

        oauth_params = {
            OAUTH_PARAM_CONSUMER_KEY: self.entry.data[CONF_CONSUMER_KEY],
            OAUTH_PARAM_NONCE: str(random.randint(0, 100000000)),
            OAUTH_PARAM_TIMESTAMP: str(int(time.time())),
            OAUTH_PARAM_SIGNATURE_METHOD: OAUTH_SIGNATURE_METHOD,
            OAUTH_PARAM_VERSION: OAUTH_VERSION,
            OAUTH_PARAM_TOKEN: self.entry.data[CONF_TOKEN],
        }
        all_params = {**oauth_params, **query_params}
        base_string = oauth_build_base_string("GET", API_FOOD_ENTRIES_URL, all_params)
        oauth_params[OAUTH_PARAM_SIGNATURE] = oauth_generate_signature(
            base_string,
            self.entry.data[CONF_CONSUMER_SECRET],
            self.entry.data[CONF_TOKEN_SECRET],
        )
        auth_header = oauth_build_authorization_header(oauth_params)

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                API_FOOD_ENTRIES_URL,
                headers={"Authorization": auth_header},
                params=query_params,
            ) as resp,
        ):
            # 1️⃣ Network-level errors
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                raise UpdateFailed(f"HTTP error {resp.status}: {e.message}") from e

            # 2️⃣ Parse JSON
            try:
                data = await resp.json()
            except aiohttp.ContentTypeError as exc:
                raise UpdateFailed("FatSecret response is not valid JSON") from exc

        # 3️⃣ API-level error handling (OAuth or API error codes)
        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            code = err.get("code")
            message = err.get("message", "No message provided")

            # Known OAuth errors
            if code in FATSECRET_FOOD_ENTRIES_ERRORS:
                explanation = FATSECRET_FOOD_ENTRIES_ERRORS[code]
                _LOGGER.error(
                    "FatSecret API error %s: %s — %s", code, explanation, message
                )
                raise UpdateFailed(f"OAuth error {code}: {explanation}")
            else:
                # Unknown error code — still raise
                raise UpdateFailed(f"FatSecret returned error {code}: {message}")

        # 4️⃣ Normal data processing
        totals = dict.fromkeys(FATSECRET_FIELDS, 0.0)
        food_entries = (
            (data.get(FATSECRET_FOOD_ENTRIES) or {}).get(FATSECRET_FOOD_ENTRY, [])
            if isinstance(data, dict)
            else []
        )

        for entry in food_entries:
            for field in FATSECRET_FIELDS:
                try:
                    totals[field] += float(entry.get(field, 0) or 0)
                except (TypeError, ValueError):
                    _LOGGER.debug(
                        "Invalid value for field %s: %s",
                        field,
                        entry.get(field),
                    )

        return totals
