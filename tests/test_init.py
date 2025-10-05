import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import custom_components.fatsecret.__init__ as fatsecret_init
from custom_components.fatsecret.const import DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry():
    # Mock ConfigEntry
    entry = MagicMock()
    entry.entry_id = "entry_123"

    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    # Mock FatSecretCoordinator
    with patch(
        "custom_components.fatsecret.__init__.FatSecretCoordinator"
    ) as MockCoordinator:
        mock_coordinator = AsyncMock()
        MockCoordinator.return_value = mock_coordinator

        # Simular refresh inicial
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        result = await fatsecret_init.async_setup_entry(hass, entry)

    # Comprobaciones
    assert result is True
    MockCoordinator.assert_called_once_with(hass, entry)
    mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()
    assert DOMAIN in hass.data
    assert hass.data[DOMAIN][entry.entry_id] == mock_coordinator
    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry, ["sensor"]
    )


@pytest.mark.asyncio
async def test_async_unload_entry():
    entry = MagicMock()
    entry.entry_id = "entry_123"

    hass = MagicMock()
    coordinator_mock = MagicMock()
    hass.data = {DOMAIN: {entry.entry_id: coordinator_mock}}
    hass.config_entries.async_unload_platforms = AsyncMock(
        side_effect=lambda e, p: hass.data[DOMAIN].pop(entry.entry_id)
    )

    result = await fatsecret_init.async_unload_entry(hass, entry)

    assert result is True
    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry, ["sensor"]
    )
    assert DOMAIN not in hass.data  # Debe eliminarse si estaba vacío


@pytest.mark.asyncio
async def test_async_unload_entry_integration_not_loaded():
    entry = MagicMock()
    entry.entry_id = "entry_123"

    hass = MagicMock()
    hass.data = {DOMAIN: {entry.entry_id: MagicMock()}}

    # El side_effect debe ser un callable que devuelva la excepción con el dominio
    def raise_integration_not_loaded(*args, **kwargs):
        raise fatsecret_init.IntegrationNotLoaded(domain=DOMAIN)

    # Simular IntegrationNotLoaded
    hass.config_entries.async_unload_platforms = AsyncMock(
        side_effect=raise_integration_not_loaded
    )

    # No debe lanzar excepción
    result = await fatsecret_init.async_unload_entry(hass, entry)
    assert result is True
