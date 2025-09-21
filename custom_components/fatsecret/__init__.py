"""FatSecret component for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.loader import IntegrationNotLoaded
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .FatSecretCoordinator import FatSecretCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""

    # Initialize the FatSecret and store it in hass.data
    # with the entry ID as the key
    coordinator = FatSecretCoordinator(hass, entry)

    # Ensure first refresh happens
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward to platforms (e.g., sensor)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the coordinator and its entities."""

    # Unload the platforms (e.g., sensor)
    try:
        await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    except IntegrationNotLoaded:
        pass

    # Optionally remove the domain if empty
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True
