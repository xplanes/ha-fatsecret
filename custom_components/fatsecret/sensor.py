"""Sensor platform for the FatSecret custom component.

This module sets up the FatSecret sensor platform and integrates it with Home Assistant.
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .FatSecretManager import FatSecretManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the FatSecret sensor platform from a config entry."""
    _LOGGER.debug("Setting up FatSecret sensor platform")

    # Retrieve the manager from hass.data
    manager: FatSecretManager = hass.data[DOMAIN].get(entry.entry_id)

    if manager:
        await manager.restore_and_add_entities(async_add_entities)
    else:
        _LOGGER.error("FatSecret not found in hass.data")
