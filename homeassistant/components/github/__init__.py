"""The GitHub integration."""
from __future__ import annotations

import asyncio

from aiogithubapi import GitHubAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    SERVER_SOFTWARE,
    async_get_clientsession,
)

from .const import DOMAIN
from .coordinator import (
    DataUpdateCoordinators,
    RepositoryInformationDataUpdateCoordinator,
    RepositoryIssueDataUpdateCoordinator,
    RepositoryReleaseDataUpdateCoordinator,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GitHub from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = GitHubAPI(
        token=entry.data["access_token"],
        session=async_get_clientsession(hass),
        **{"client_name": SERVER_SOFTWARE},
    )

    repositories: list[str] = entry.data["repositories"]

    for repository in repositories:
        coordinators = DataUpdateCoordinators(
            information=RepositoryInformationDataUpdateCoordinator(
                hass=hass, entry=entry, client=client, repository=repository
            ),
            release=RepositoryReleaseDataUpdateCoordinator(
                hass=hass, entry=entry, client=client, repository=repository
            ),
            issue=RepositoryIssueDataUpdateCoordinator(
                hass=hass, entry=entry, client=client, repository=repository
            ),
        )
        hass.data[DOMAIN][repository] = coordinators

        await asyncio.gather(
            *(
                coordinator.async_config_entry_first_refresh()
                for coordinator in coordinators.list
            )
        )

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN)
    return unload_ok
