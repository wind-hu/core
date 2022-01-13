"""Custom data update coordinators for the GitHub integration."""
from __future__ import annotations

from dataclasses import dataclass

from aiogithubapi import GitHubAPI, GitHubException
from aiogithubapi.models.release import GitHubReleaseModel
from aiogithubapi.models.repository import GitHubRepositoryModel

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, T
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN, LOGGER


@dataclass
class DataUpdateCoordinators:
    """Custom data update coordinators for the GitHub integration."""

    information: RepositoryInformationDataUpdateCoordinator
    release: RepositoryReleasesDataUpdateCoordinator


class GitHubBaseDataUpdateCoordinator(DataUpdateCoordinator[T]):
    """Base class for GitHub data update coordinators."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        client: GitHubAPI,
        entry: ConfigEntry,
    ) -> None:
        """Initialize base GitHub data updater."""
        self.repository: str = entry.data["repository"]
        self._client = client

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )


class RepositoryInformationDataUpdateCoordinator(
    GitHubBaseDataUpdateCoordinator[GitHubRepositoryModel]
):
    """Data update coordinator for repository information."""

    async def _async_update_data(self) -> GitHubRepositoryModel | None:
        """Get the latest data from GitHub."""
        try:
            result = await self._client.repos.get(self.repository)
            return result.data
        except GitHubException as exception:
            raise UpdateFailed(exception) from exception


class RepositoryReleasesDataUpdateCoordinator(
    GitHubBaseDataUpdateCoordinator[GitHubReleaseModel]
):
    """Data update coordinator for repository releases."""

    async def _async_update_data(self) -> GitHubReleaseModel | None:
        """Get the latest data from GitHub."""
        try:
            result = await self._client.repos.releases.list(self.repository)
            return next(result.data, None)
        except GitHubException as exception:
            raise UpdateFailed(exception) from exception
