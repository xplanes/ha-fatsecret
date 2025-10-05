import pytest
from unittest.mock import Mock, AsyncMock

from custom_components.fatsecret.sensor import async_setup_entry
from custom_components.fatsecret.const import DOMAIN, FATSECRET_FIELDS
from custom_components.fatsecret.FatSecretSensor import FatSecretSensor
from custom_components.fatsecret.FatSecretCoordinator import FatSecretCoordinator


@pytest.mark.asyncio
async def test_async_setup_entry_creates_sensors(hass):
    """Test that async_setup_entry adds one sensor per field."""
    entry = Mock()
    entry.entry_id = "test_entry"

    # Create a mock coordinator and store in hass.data
    mock_coordinator = Mock(spec=FatSecretCoordinator)
    hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

    # Use a mock for async_add_entities
    async_add_entities = Mock()

    await async_setup_entry(hass, entry, async_add_entities)

    # Check that async_add_entities was called once
    async_add_entities.assert_called_once()
    sensors_added = async_add_entities.call_args[0][0]

    # There should be one sensor per field
    assert len(sensors_added) == len(FATSECRET_FIELDS)

    # All sensors should be instances of FatSecretSensor
    for sensor in sensors_added:
        assert isinstance(sensor, FatSecretSensor)
        # Each sensor should reference the mock coordinator
        assert sensor.coordinator == mock_coordinator


@pytest.mark.asyncio
async def test_async_setup_entry_no_coordinator(hass):
    """Test that async_setup_entry does nothing if coordinator is missing."""
    entry = Mock()
    entry.entry_id = "missing_entry"

    # hass.data is empty
    hass.data[DOMAIN] = {}

    async_add_entities = Mock()

    await async_setup_entry(hass, entry, async_add_entities)

    # async_add_entities should not be called
    async_add_entities.assert_not_called()
