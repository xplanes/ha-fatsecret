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

        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_FOOD_ENTRIES_URL,
                headers={"Authorization": auth_header},
                params=query_params,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

        # Sum up metrics
        totals = dict.fromkeys(FATSECRET_FIELDS, 0.0)
        for entry in data.get(FATSECRET_FOOD_ENTRIES, {}).get(FATSECRET_FOOD_ENTRY, []):
            for field in FATSECRET_FIELDS:
                totals[field] += float(entry.get(field, 0))

        return totals
