"""Test the GitHub config flow."""
import datetime
import json

from homeassistant import config_entries
from homeassistant.components.github.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import (
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_SHOW_PROGRESS,
)

from tests.common import async_fire_time_changed, load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_full_user_flow_implementation(
    hass: HomeAssistant,
    mock_setup_entry: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the full manual user flow from start to finish."""
    oauth_access_token_fixture = json.loads(
        load_fixture("oauth_access_token.json", DOMAIN)
    )
    aioclient_mock.post(
        "https://github.com/login/device/code",
        json=json.loads(load_fixture("oauth_device_code.json", DOMAIN)),
        headers={"Content-Type": "application/json"},
    )
    aioclient_mock.post(
        "https://github.com/login/oauth/access_token",
        json=oauth_access_token_fixture,
        headers={"Content-Type": "application/json"},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["step_id"] == "device"
    assert result["type"] == RESULT_TYPE_SHOW_PROGRESS
    assert "flow_id" in result

    async_fire_time_changed(
        hass, datetime.datetime.now() + datetime.timedelta(seconds=1)
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "repositories": ["home-assistant/core"],
        },
    )

    assert result["title"] == ""
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert "data" in result
    assert result["data"]["access_token"] == oauth_access_token_fixture["access_token"]
    assert result["data"]["scope"] == ""
    assert "options" in result
    assert result["options"]["repositories"] == ["home-assistant/core"]
