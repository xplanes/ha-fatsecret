"""Module for managing the FatSecret component."""

import logging
import random
import time
from datetime import datetime
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .FatSecretSensor import FatSecretSensor

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
    DOMAIN,
    FATSECRET_FIELDS,
)

_LOGGER = logging.getLogger(__name__)


class FatSecretManager:
    """Class to handle FatSecret API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the FatSecretManager with Home Assistant instance and config entry."""
        self.hass = hass
        self.entry = config_entry
        self.entities = {}
        self._async_add_entities = None
        self._midnight_listener = None
        self.latest_data = None  # add in __init__

    async def async_init(self):
        """Initialize the FatSecretManager by registering services."""
        # Initialize API client here (using entry.data for credentials)
        await self.async_register_services()

    async def async_unload(self):
        """Unload the manager and remove all entities."""

        if self._async_add_entities:
            self._async_add_entities = None

    async def restore_and_add_entities(self, async_add_entities: AddEntitiesCallback):
        """Restore entities from config entry and add them to Home Assistant."""
        self._async_add_entities = async_add_entities

        for field in FATSECRET_FIELDS:
            sensor = FatSecretSensor(field)
            self.entities[field] = sensor

        self._async_add_entities(list(self.entities.values()), True)

    async def async_register_services(self):
        """Register Home Assistant services for plant management."""

        async def handle_update_fatsecret(_call: ServiceCall):
            await self.async_update_fatsecret()

        self.hass.services.async_register(
            DOMAIN, "update_fatsecret", handle_update_fatsecret
        )

        self._midnight_listener = async_track_time_change(
            self.hass,
            self.async_update_fatsecret,
            hour=0,
            minute=0,
            second=1,
        )

    async def async_update_fatsecret(self, _now: datetime | None = None):
        """Update the sensors."""

        # Example: call your API or fetch from Node-RED
        data = await self.fetch_fatsecret_data()

        self.latest_data = data

        for metric, entity in self.entities.items():
            entity.update_value(data.get(metric, 0))

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
