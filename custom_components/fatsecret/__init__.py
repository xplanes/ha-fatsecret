"""FatSecret component for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.loader import IntegrationNotLoaded
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .FatSecretManager import FatSecretManager

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from a config entry."""

    # Initialize the DOMAIN in hass.data if it doesn't exist
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Initialize the FatSecret and store it in hass.data
    # with the entry ID as the key
    fatsecret = FatSecretManager(hass, entry)
    await fatsecret.async_init()

    hass.data[DOMAIN][entry.entry_id] = fatsecret

    # Set up the sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the plant diary manager and its entities."""

    # Unload the platforms (e.g., sensor)
    try:
        await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    except IntegrationNotLoaded:
        pass

    # Cleanup manager
    manager: FatSecretManager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        await manager.async_unload()

    # Optionally remove the domain if empty
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle reloads of the config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
