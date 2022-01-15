"""Test the GitHub config flow."""
import datetime

from homeassistant import config_entries
from homeassistant.components.github.const import DEFAULT_REPOSITORIES, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_SHOW_PROGRESS,
)

from .common import MOCK_ACCESS_TOKEN, load_json_fixture

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_full_user_flow_implementation(
    hass: HomeAssistant,
    mock_setup_entry: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the full manual user flow from start to finish."""
    aioclient_mock.post(
        "https://github.com/login/device/code",
        json=load_json_fixture("oauth_device_code"),
        headers={"Content-Type": "application/json"},
    )
    aioclient_mock.post(
        "https://github.com/login/oauth/access_token",
        json={
            **load_json_fixture("oauth_access_token"),
            "access_token": MOCK_ACCESS_TOKEN,
        },
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
            "repositories": DEFAULT_REPOSITORIES,
        },
    )

    assert result["title"] == ""
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert "data" in result
    assert result["data"]["access_token"] == MOCK_ACCESS_TOKEN
    assert result["data"]["scope"] == ""
    assert "options" in result
    assert result["options"]["repositories"] == DEFAULT_REPOSITORIES


async def test_already_configured(
    hass: HomeAssistant,
    mock_setup_entry: None,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test we abort if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result.get("reason") == "already_configured"
