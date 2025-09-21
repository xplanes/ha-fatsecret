"""Sensor platform for the FatSecret custom component.

This module sets up the FatSecret sensor platform and integrates it with Home Assistant.
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .FatSecretCoordinator import FatSecretCoordinator
from .FatSecretSensor import FatSecretSensor
from .const import FATSECRET_FIELDS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the FatSecret sensor platform from a config entry."""
    _LOGGER.debug("Setting up FatSecret sensor platform")

    # Retrieve the coordinator from hass.data
    coordinator: FatSecretCoordinator = hass.data[DOMAIN].get(entry.entry_id)

    if coordinator:
        sensors = [FatSecretSensor(coordinator, field) for field in FATSECRET_FIELDS]
        async_add_entities(sensors)
