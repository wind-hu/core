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
    RepositoryReleasesDataUpdateCoordinator,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GitHub from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = GitHubAPI(
        token=entry.data["token"],
        session=async_get_clientsession(hass),
        **{"client_name": SERVER_SOFTWARE},
    )

    coordinators = DataUpdateCoordinators(
        information=RepositoryInformationDataUpdateCoordinator(
            hass=hass, client=client, entry=entry
        ),
        release=RepositoryReleasesDataUpdateCoordinator(
            hass=hass, client=client, entry=entry
        ),
    )

    await asyncio.gather(
        *[
            coordinators.information.async_config_entry_first_refresh(),
            coordinators.release.async_config_entry_first_refresh(),
        ]
    )

    hass.data[DOMAIN][entry.entry_id] = coordinators

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
