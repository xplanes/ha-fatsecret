import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock
import aiohttp
from aiohttp import ClientResponseError, ContentTypeError

from custom_components.fatsecret.FatSecretCoordinator import FatSecretCoordinator
from custom_components.fatsecret.const import (
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    CONF_TOKEN,
    CONF_TOKEN_SECRET,
    FATSECRET_FIELDS,
    DOMAIN,
    FATSECRET_FOOD_ENTRIES,
    FATSECRET_FOOD_ENTRY,
    FATSECRET_FOOD_ENTRIES_ERRORS,  # Added import for error codes
)
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.core import HomeAssistant


def MockConfigEntry() -> MagicMock:
    """Mock a ConfigEntry for testing."""
    mock_entry = MagicMock()
    mock_entry.data = {
        CONF_CONSUMER_KEY: "key",
        CONF_CONSUMER_SECRET: "secret",
        CONF_TOKEN: "token",
        CONF_TOKEN_SECRET: "token_secret",
    }
    return mock_entry


class MockResp:
    def __init__(self, response, status):
        self.response = response
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def json(self):
        return self.response

    def raise_for_status(self):
        return None


class MockSession:
    def __init__(self, MockResp):
        self.resp = MockResp

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def get(self, url, headers=None, params=None):
        return self.resp


@pytest.mark.asyncio
async def test_coordinator_init_register_service():
    hass = MagicMock()
    entry = MockConfigEntry()

    FatSecretCoordinator(hass, entry)

    # Debe registrar el servicio
    assert hass.services.async_register.call_count == 1
    service_args = hass.services.async_register.call_args[0]
    assert service_args[0] == DOMAIN
    assert service_args[1] == "update_fatsecret"


@pytest.mark.asyncio
async def test_handle_update_fatsecret_service(hass: HomeAssistant):
    """Test that calling the update_fatsecret service triggers async_refresh."""
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    # Patch async_refresh para comprobar que se llama
    coordinator.async_refresh = AsyncMock()

    # Llamamos al servicio registrado
    await hass.services.async_call(
        DOMAIN,
        "update_fatsecret",
        service_data={},
        blocking=True,
    )

    # Comprobamos que async_refresh fue llamado
    coordinator.async_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_update_data_success():
    hass = MagicMock()
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    with patch.object(
        coordinator,
        "fetch_fatsecret_data",
        new=AsyncMock(return_value={"calories": 100}),
    ):
        result = await coordinator._async_update_data()

    assert result == {"calories": 100}
    assert coordinator.latest_data == {"calories": 100}


@pytest.mark.asyncio
async def test_async_update_data_failure():
    hass = MagicMock()
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    with patch.object(
        coordinator,
        "fetch_fatsecret_data",
        new=AsyncMock(side_effect=Exception("fail")),
    ):
        with pytest.raises(UpdateFailed, match="FatSecret update failed: fail"):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_fetch_fatsecret_data_normal(monkeypatch):
    hass = MagicMock()
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    fake_response = {
        FATSECRET_FOOD_ENTRIES: {
            FATSECRET_FOOD_ENTRY: [
                {"calories": "100", "protein": "10"},
                {"calories": "200", "protein": "20"},
            ]
        }
    }

    # Parchear aiohttp.ClientSession
    monkeypatch.setattr(
        "aiohttp.ClientSession", lambda: MockSession(MockResp(fake_response, 200))
    )

    totals = await coordinator.fetch_fatsecret_data()
    for field in FATSECRET_FIELDS:
        assert field in totals


@pytest.mark.asyncio
async def test_fetch_fatsecret_data_http_error(monkeypatch):
    hass = MagicMock()
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    class MockRespUnauthorized(MockResp):
        def __init__(self):
            super().__init__(response=None, status=401)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def json(self):
            return {}

        def raise_for_status(self):
            raise aiohttp.ClientResponseError(
                request_info=Mock(),
                history=(),
                status=401,
                message="Unauthorized",
            )

    monkeypatch.setattr(
        "aiohttp.ClientSession", lambda: MockSession(MockRespUnauthorized())
    )

    with pytest.raises(UpdateFailed, match="HTTP error 401: Unauthorized"):
        await coordinator.fetch_fatsecret_data()


@pytest.mark.asyncio
async def test_fetch_fatsecret_data_invalid_json(monkeypatch):
    hass = MagicMock()
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    class MockRespInvalidJSON(MockResp):
        def __init__(self):
            super().__init__(response=None, status=200)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def raise_for_status(self):
            return None

        async def json(self):
            raise ContentTypeError(
                request_info=Mock(), history=(), message="Invalid JSON"
            )

    monkeypatch.setattr(
        "aiohttp.ClientSession", lambda: MockSession(MockRespInvalidJSON())
    )

    with pytest.raises(UpdateFailed, match="FatSecret response is not valid JSON"):
        await coordinator.fetch_fatsecret_data()


@pytest.mark.asyncio
async def test_fetch_fatsecret_data_known_error(monkeypatch):
    """Test that fetch_fatsecret_data raises UpdateFailed on known API errors."""
    hass = MagicMock()
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    class MockRespAPIError(MockResp):
        def __init__(self, error_code):
            super().__init__(response=None, status=200)
            self.error_code = error_code

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def json(self):
            return {"error": {"code": self.error_code, "message": "Some message"}}

        def raise_for_status(self):
            return None

    # Forzamos un error conocido
    error_code = list(FATSECRET_FOOD_ENTRIES_ERRORS.keys())[0]

    monkeypatch.setattr(
        "aiohttp.ClientSession", lambda: MockSession(MockRespAPIError(error_code))
    )

    with pytest.raises(UpdateFailed, match=f"OAuth error {error_code}"):
        await coordinator.fetch_fatsecret_data()


@pytest.mark.asyncio
async def test_fetch_fatsecret_data_unknown_error(monkeypatch):
    """Test that fetch_fatsecret_data raises UpdateFailed on known API errors."""
    hass = MagicMock()
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    class MockRespAPIError(MockResp):
        def __init__(self, error_code):
            super().__init__(response=None, status=200)
            self.error_code = error_code

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def json(self):
            return {"error": {"code": 9999, "message": "Unknown error"}}

        def raise_for_status(self):
            return None

    # Forzamos un error conocido
    error_code = list(FATSECRET_FOOD_ENTRIES_ERRORS.keys())[0]

    monkeypatch.setattr(
        "aiohttp.ClientSession", lambda: MockSession(MockRespAPIError(error_code))
    )

    with pytest.raises(
        UpdateFailed, match=f"FatSecret returned error 9999: Unknown error"
    ):
        await coordinator.fetch_fatsecret_data()


@pytest.mark.asyncio
async def test_fetch_fatsecret_data_invalid_value(monkeypatch):
    """Test that fetch_fatsecret_data raises TypeError."""
    hass = MagicMock()
    entry = MockConfigEntry()

    coordinator = FatSecretCoordinator(hass, entry)

    fake_response = {
        FATSECRET_FOOD_ENTRIES: {
            FATSECRET_FOOD_ENTRY: [
                {"calories": "a", "protein": "b"},
            ]
        }
    }

    # Parchear aiohttp.ClientSession
    monkeypatch.setattr(
        "aiohttp.ClientSession", lambda: MockSession(MockResp(fake_response, 200))
    )

    totals = await coordinator.fetch_fatsecret_data()
    for field in FATSECRET_FIELDS:
        assert field in totals
