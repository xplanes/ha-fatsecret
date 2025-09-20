"""Module for managing the FatSecret component."""

import base64
import hashlib
import hmac
import logging
import random
import time
import urllib.parse
from datetime import datetime

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .oauth_helpers import oauth1_request

from .const import (
    DOMAIN,
    SENSOR_TYPES,
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    CONF_TOKEN,
    CONF_TOKEN_SECRET,
)
from .FatSecretSensor import FatSecretSensor

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

        for metric in SENSOR_TYPES:
            sensor = FatSecretSensor(metric)
            self.entities[metric] = sensor

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

    async def fetch_fatsecret_data2(self) -> dict:
        """Fetch latest FatSecret food entries and return summed metrics.

        Returns a dict:
        calories, carbs, protein, fat, fiber, sugar
        """
        # Implement actual API call here
        # For demonstration, returning dummy data
        return {
            "calories": 2000,
            "carbs": 250,
            "protein": 150,
            "fat": 70,
            "fiber": 30,
            "sugar": 90,
        }

    async def fetch_fatsecret_data(self) -> dict:
        """Fetch latest FatSecret food entries and return summed metrics.

        Returns a dict:
        calories, carbs, protein, fat, fiber, sugar
        """

        url = "https://platform.fatsecret.com/rest/food-entries/v2"
        query_params = {"format": "json"}  # API params

        data = await oauth1_request(
            method="GET",
            url=url,
            consumer_key=self.entry.data[CONF_CONSUMER_KEY],
            consumer_secret=self.entry.data[CONF_CONSUMER_SECRET],
            token=self.entry.data[CONF_TOKEN],
            token_secret=self.entry.data[CONF_TOKEN_SECRET],
            params=query_params,
            use_headers=True,
        )

        # Sum up metrics
        totals = dict.fromkeys(SENSOR_TYPES, 0.0)
        for entry in data.get("food_entries", {}).get("food_entry", []):
            totals["calories"] += float(entry.get("calories", 0))
            totals["carbs"] += float(entry.get("carbohydrate", 0))
            totals["protein"] += float(entry.get("protein", 0))
            totals["fat"] += float(entry.get("fat", 0))
            totals["fiber"] += float(entry.get("fiber", 0))
            totals["sugar"] += float(entry.get("sugar", 0))

        return totals
