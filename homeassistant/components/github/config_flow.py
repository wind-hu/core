"""Config flow for GitHub integration."""
from __future__ import annotations

import asyncio
from typing import Any

from aiogithubapi import (
    GitHubAPI,
    GitHubDeviceAPI,
    GitHubException,
    GitHubLoginDeviceModel,
    GitHubLoginOauthModel,
)
from aiogithubapi.const import OAUTH_USER_LOGIN
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import (
    SERVER_SOFTWARE,
    async_get_clientsession,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_call_later

from .const import CLIENT_ID, DOMAIN, LOGGER


async def _stared_repositories(
    hass: HomeAssistant,
    access_token: str,
) -> list[str]:
    """Return a list of repositories that the user has starred."""
    client = GitHubAPI(token=access_token, session=async_get_clientsession(hass))

    async def _get_starred():
        response = await client.user.starred(**{"params": {"per_page": 100}})
        if not response.is_last_page:
            results = await asyncio.gather(
                *(
                    client.user.starred(
                        **{"params": {"per_page": 100, "page": page_number}},
                    )
                    for page_number in range(
                        response.next_page_number, response.last_page_number + 1
                    )
                )
            )
            for result in results:
                response.data.extend(result.data)

        return response.data

    try:
        result = await _get_starred()
        return sorted((repo.full_name for repo in result), key=str.casefold)
    except GitHubException:
        pass

    return ["home-assistant/core"]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GitHub."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self._device: GitHubDeviceAPI | None = None
        self._activation: GitHubLoginOauthModel | None = None
        self._login_device: GitHubLoginDeviceModel | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        self._errors = {}
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        return await self.async_step_device(user_input)

    async def async_step_device(self, _user_input):
        """Handle device steps."""

        async def _wait_for_activation(_=None):
            if self._login_device is None or self._login_device.expires_in is None:
                async_call_later(self.hass, 0, _wait_for_activation)
                return

            response = await self._device.activation(
                device_code=self._login_device.device_code
            )
            self._activation = response.data
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
            )

        if not self._activation:
            if not self._device:
                self._device = GitHubDeviceAPI(
                    client_id=CLIENT_ID,
                    session=async_get_clientsession(self.hass),
                    **{"client_name": SERVER_SOFTWARE},
                )
            async_call_later(self.hass, 0, _wait_for_activation)
            try:
                response = await self._device.register()
                self._login_device = response.data
            except GitHubException as exception:
                LOGGER.exception(exception)
                return self.async_abort(reason="could_not_register")

            return self.async_show_progress(
                step_id="device",
                progress_action="wait_for_device",
                description_placeholders={
                    "url": OAUTH_USER_LOGIN,
                    "code": self._login_device.user_code,
                },
            )

        return self.async_show_progress_done(next_step_id="repositories")

    async def async_step_repositories(self, user_input):
        """Handle repositories step."""

        if not user_input:
            repositories = await _stared_repositories(
                self.hass, self._activation.access_token
            )
            return self.async_show_form(
                step_id="repositories",
                data_schema=vol.Schema(
                    {
                        vol.Required("repositories"): cv.multi_select(repositories),
                    }
                ),
                errors=self._errors,
            )

        return self.async_create_entry(
            title="",
            data={
                "access_token": self._activation.access_token,
                "scope": self._activation.scope,
                "repositories": user_input["repositories"],
            },
        )
