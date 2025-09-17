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

from .const import DOMAIN, SENSOR_TYPES
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

        # Extract credentials from config entry
        consumer_key = self.entry.data["consumer_key"]
        consumer_secret = self.entry.data["consumer_secret"]
        oauth_token = self.entry.data["oauth_token"]
        token_secret = self.entry.data["token_secret"]

        url = "https://platform.fatsecret.com/rest/food-entries/v2"
        query_params = {"format": "json"}  # API params

        # OAuth1 params
        oauth_params = {
            "oauth_consumer_key": consumer_key,
            "oauth_token": oauth_token,
            "oauth_nonce": str(random.randint(0, 100000000)),
            "oauth_timestamp": str(int(time.time())),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_version": "1.0",
        }

        # Merge API + OAuth params for signing
        all_params = {**query_params, **oauth_params}
        sorted_items = sorted(all_params.items())
        encoded_params = "&".join(
            f"{urllib.parse.quote(str(k), safe='')}={urllib.parse.quote(str(v), safe='')}"
            for k, v in sorted_items
        )

        # Signature base string
        base_string = f"GET&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(encoded_params, safe='')}"
        signing_key = f"{urllib.parse.quote(consumer_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"

        # Create signature
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()

        oauth_params["oauth_signature"] = signature

        # Build Authorization header
        auth_header = "OAuth " + ", ".join(
            f'{k}="{urllib.parse.quote(str(v), safe="")}"'
            for k, v in oauth_params.items()
        )

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                url, headers={"Authorization": auth_header}, params=query_params
            ) as resp,
        ):
            resp.raise_for_status()
            data = await resp.json()

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
