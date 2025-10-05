"""Tests for Plant Diary integration."""

import pathlib
import types
from unittest import mock

import pytest
from homeassistant import config_entries
from homeassistant.loader import Integration
from homeassistant.setup import async_setup_component
from homeassistant.core import HomeAssistant

from custom_components.fatsecret import (
    config_flow,
)

DEFAULT_NAME = "My FatSecret"


@pytest.mark.asyncio
async def test_flow_user_init(hass: HomeAssistant) -> None:
    """Test the initialization of the form in the first step of the config flow."""

    # Registramos manualmente el flujo
    config_entries.HANDLERS[config_flow.DOMAIN] = config_flow.FatSecretConfigFlow

    mock_integration = Integration(
        hass=hass,
        pkg_path="custom_components.fatsecret",
        file_path=pathlib.Path("custom_components/fatsecret/__init__.py"),
        manifest={
            "domain": config_flow.DOMAIN,
            "name": "FatSecret",
            "version": "1.0.0",
            "requirements": [],
            "dependencies": [],
            "after_dependencies": [],
            "is_built_in": False,
        },
        top_level_files={
            "custom_components/fatsecret/manifest.json",
            "custom_components/fatsecret/config_flow.py",
            "custom_components/fatsecret/const.py",
            "custom_components/fatsecret/FatSecretEntity.py",
            "custom_components/fatsecret/FatSecretManager.py",
            "custom_components/fatsecret/services.yaml",
        },
    )

    mock_config_flow_module = types.SimpleNamespace()
    mock_config_flow_module.FatSecretConfigFlow = config_flow.FatSecretConfigFlow
    mock_integration.async_get_platform = mock.AsyncMock(
        return_value=mock_config_flow_module
    )

    # Carga componentes necesarios (sensor, etc)
    assert await async_setup_component(hass, "sensor", {})

    with (
        mock.patch(
            "homeassistant.loader.async_get_integration",
            return_value=mock_integration,
        ),
        mock.patch(
            "homeassistant.loader.async_get_integrations",
            return_value={config_flow.DOMAIN: mock_integration},
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN, context={"source": "user"}
        )

    expected = {
        "flow_id": mock.ANY,
        "type": mock.ANY,
        "description_placeholders": None,
        "handler": "fatsecret",
        "errors": {},
        "last_step": None,
        "preview": None,
        "step_id": "user",
        "data_schema": mock.ANY,
    }
    assert expected == result
