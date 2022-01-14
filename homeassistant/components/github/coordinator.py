"""Custom data update coordinators for the GitHub integration."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from aiogithubapi import (
    GitHubAPI,
    GitHubException,
    GitHubIssueModel,
    GitHubReleaseModel,
    GitHubRepositoryModel,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, T
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN, LOGGER, IssuesPulls


class GitHubBaseDataUpdateCoordinator(DataUpdateCoordinator[T]):
    """Base class for GitHub data update coordinators."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: GitHubAPI,
        repository: str,
    ) -> None:
        """Initialize base GitHub data updater."""
        self.config_entry = entry
        self.repository = repository
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


class RepositoryReleaseDataUpdateCoordinator(
    GitHubBaseDataUpdateCoordinator[GitHubReleaseModel]
):
    """Data update coordinator for repository releases."""

    async def _async_update_data(self) -> GitHubReleaseModel | None:
        """Get the latest data from GitHub."""
        try:
            result = await self._client.repos.releases.list(
                self.repository, **{"params": {"per_page": 1}}
            )
            return result.data[0] if result.data else None
        except GitHubException as exception:
            raise UpdateFailed(exception) from exception


class RepositoryIssueDataUpdateCoordinator(
    GitHubBaseDataUpdateCoordinator[IssuesPulls]
):
    """Data update coordinator for repository issues."""

    async def _async_update_data(self) -> IssuesPulls:
        """Get the latest data from GitHub."""

        async def _get_issues():
            response = await self._client.repos.issues.list(
                self.repository, **{"params": {"per_page": 100}}
            )
            if not response.is_last_page:
                results = await asyncio.gather(
                    *(
                        self._client.repos.issues.list(
                            self.repository,
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
            all_issues = await _get_issues()
        except GitHubException as exception:
            raise UpdateFailed(exception) from exception
        else:
            issues: list[GitHubIssueModel] = [
                issue for issue in all_issues or [] if issue.pull_request is None
            ]
            pulls: list[GitHubIssueModel] = [
                issue for issue in all_issues or [] if issue.pull_request is not None
            ]

            return IssuesPulls(issues=issues, pulls=pulls)


@dataclass
class DataUpdateCoordinators:
    """Custom data update coordinators for the GitHub integration."""

    information: RepositoryInformationDataUpdateCoordinator
    release: RepositoryReleaseDataUpdateCoordinator
    issue: RepositoryIssueDataUpdateCoordinator

    @property
    def list(self) -> list[GitHubBaseDataUpdateCoordinator]:
        """Return a list of all coordinators."""
        return [self.information, self.release, self.issue]
