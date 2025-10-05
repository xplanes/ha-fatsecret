import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from homeassistant.core import HomeAssistant
from custom_components.fatsecret import config_flow

CONF_CONSUMER_KEY = config_flow.CONF_CONSUMER_KEY
CONF_CONSUMER_SECRET = config_flow.CONF_CONSUMER_SECRET
CONF_TOKEN = config_flow.CONF_TOKEN
CONF_TOKEN_SECRET = config_flow.CONF_TOKEN_SECRET


@pytest.mark.asyncio
async def test_is_matching():
    flow = config_flow.FatSecretConfigFlow()

    # Creamos un mock de otro flow con el mismo DOMAIN
    class OtherFlow(config_flow.FatSecretConfigFlow):
        DOMAIN = config_flow.DOMAIN

    # Y otro con un DOMAIN distinto
    class DifferentFlow(config_flow.FatSecretConfigFlow):
        DOMAIN = "different"

    assert flow.is_matching(OtherFlow()) is True
    assert flow.is_matching(DifferentFlow()) is False


@pytest.mark.asyncio
async def test_step_user_no_input(hass: HomeAssistant):
    flow = config_flow.FatSecretConfigFlow()
    result = await flow.async_step_user()
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert "data_schema" in result
    assert result["errors"] == {}


@pytest.mark.asyncio
async def test_step_user_with_input_success(hass: HomeAssistant):
    flow = config_flow.FatSecretConfigFlow()
    user_input = {
        CONF_CONSUMER_KEY: "my_key",
        CONF_CONSUMER_SECRET: "my_secret",
    }

    with patch.object(
        flow, "_get_request_token", return_value=asyncio.Future()
    ) as mock_get_token:
        mock_get_token.return_value.set_result(None)
        result = await flow.async_step_user(user_input)

    assert "step_id" in result or "type" in result
    assert flow.consumer_key == "my_key"
    assert flow.consumer_secret == "my_secret"


@pytest.mark.asyncio
async def test_step_user_with_input_error(hass: HomeAssistant):
    flow = config_flow.FatSecretConfigFlow()
    user_input = {
        CONF_CONSUMER_KEY: "my_key",
        CONF_CONSUMER_SECRET: "my_secret",
    }

    with patch.object(flow, "_get_request_token", side_effect=ValueError("fail")):
        result = await flow.async_step_user(user_input)

    assert result["type"] == "form"
    assert result["errors"]["base"] == "auth_failed"
    assert flow.consumer_key == "my_key"
    assert flow.consumer_secret == "my_secret"


# -----------------------------
# Tests para async_step_authorize
# -----------------------------
@pytest.mark.asyncio
async def test_step_authorize_no_input():
    flow = config_flow.FatSecretConfigFlow()
    flow.request_token = "req_token_123"
    result = await flow.async_step_authorize()
    assert result["type"] == "form"
    assert result["step_id"] == "authorize"
    assert "verifier" in str(result["data_schema"])


@pytest.mark.asyncio
async def test_step_authorize_with_input_success():
    flow = config_flow.FatSecretConfigFlow()
    flow.consumer_key = "my_key"
    flow.consumer_secret = "my_secret"
    flow.request_token = "req_token"
    flow.request_token_secret = "req_secret"

    user_input = {"verifier": "verif123"}

    # Mock _get_access_token para devolver tokens de prueba
    flow._get_access_token = AsyncMock(return_value=("access_token", "access_secret"))

    result = await flow.async_step_authorize(user_input)

    # async_create_entry devuelve dict con type=create_entry
    assert result["type"] == "create_entry"
    assert result["data"][CONF_TOKEN] == "access_token"
    assert result["data"][CONF_TOKEN_SECRET] == "access_secret"


@pytest.mark.asyncio
async def test_step_authorize_with_input_error():
    flow = config_flow.FatSecretConfigFlow()
    flow.consumer_key = "my_key"
    flow.consumer_secret = "my_secret"
    flow.request_token = "req_token"
    flow.request_token_secret = "req_secret"

    user_input = {"verifier": "verif123"}

    # Mock _get_access_token para lanzar error
    with patch.object(flow, "_get_access_token", side_effect=ValueError("fail")):
        result = await flow.async_step_authorize(user_input)

    assert result["type"] == "form"
    assert result["errors"]["base"] == "auth_failed"
    assert "verifier" in str(result["data_schema"])


# -----------------------------
# Tests para _get_request_token
# -----------------------------
@pytest.mark.asyncio
async def test_get_request_token_success():
    flow = config_flow.FatSecretConfigFlow()
    flow.consumer_key = "my_key"
    flow.consumer_secret = "my_secret"

    # Mock de la respuesta de session.get
    class MockResponse:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def raise_for_status(self):
            pass

        async def text(self):
            return "oauth_token=req_token&oauth_token_secret=req_secret"

    # Mock de ClientSession
    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url, params=None):
            return MockResponse()

    # Patch aiohttp.ClientSession para que devuelva nuestro mock
    with patch("aiohttp.ClientSession", return_value=MockSession()):
        await flow._get_request_token()

    assert flow.request_token == "req_token"
    assert flow.request_token_secret == "req_secret"


@pytest.mark.asyncio
async def test_get_request_token_failure():
    flow = config_flow.FatSecretConfigFlow()
    flow.consumer_key = "my_key"
    flow.consumer_secret = "my_secret"

    # Mock de la respuesta de session.get
    class MockResponse:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def raise_for_status(self):
            pass

        async def text(self):
            return "invalid_response"

    # Mock de ClientSession
    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url, params=None):
            return MockResponse()

    # Patch aiohttp.ClientSession para que devuelva nuestro mock
    try:
        with patch("aiohttp.ClientSession", return_value=MockSession()):
            await flow._get_request_token()
    except ValueError as e:
        assert str(e) == "Failed to obtain request token: {}"
    else:
        assert False, "ValueError no fue lanzado"


# -----------------------------
# Tests para _get_access_token
# -----------------------------
@pytest.mark.asyncio
async def test_get_access_token():
    flow = config_flow.FatSecretConfigFlow()
    flow.consumer_key = "my_key"
    flow.consumer_secret = "my_secret"
    flow.request_token = "req_token"
    flow.request_token_secret = "req_secret"

    # Mock de la respuesta de session.get
    class MockResponse:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def raise_for_status(self):
            pass

        async def text(self):
            return "oauth_token=access_token&oauth_token_secret=access_secret"

    # Mock de ClientSession
    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url, params=None):
            return MockResponse()

    with patch("aiohttp.ClientSession", return_value=MockSession()):
        token, secret = await flow._get_access_token("verif123")

    assert token == "access_token"
    assert secret == "access_secret"
