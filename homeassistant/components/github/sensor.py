"""Sensor platform for the GitHub integratiom."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import (
    DataUpdateCoordinators,
    GitHubBaseDataUpdateCoordinator,
    RepositoryIssueDataUpdateCoordinator,
    RepositoryReleaseDataUpdateCoordinator,
)
from .entity import GitHubEntity


@dataclass
class GitHubSensorEntityDescriptionMixin:
    """Mixin for required GitHub description keys."""

    state_fn: Callable[[Any], StateType | datetime]


@dataclass
class GitHubSensorEntityDescription(
    SensorEntityDescription, GitHubSensorEntityDescriptionMixin
):
    """Describes GitHub sensor entity."""


INFORMATION_DESCRIPTIONS: tuple[GitHubSensorEntityDescription, ...] = (
    GitHubSensorEntityDescription(
        key="stargazers_count",
        name="Stars",
        icon="mdi:star",
        native_unit_of_measurement="Stars",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        state_fn=lambda data: data.stargazers_count,
    ),
    GitHubSensorEntityDescription(
        key="watchers_count",
        name="Watchers",
        icon="mdi:glasses",
        native_unit_of_measurement="Watchers",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        state_fn=lambda data: data.watchers_count,
    ),
    GitHubSensorEntityDescription(
        key="forks_count",
        name="Forks",
        icon="mdi:source-fork",
        native_unit_of_measurement="Forks",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        state_fn=lambda data: data.forks_count,
    ),
    GitHubSensorEntityDescription(
        key="default_branch",
        name="Default branch",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        state_fn=lambda data: data.default_branch,
    ),
)

ISSUES_DESCRIPTIONS: tuple[GitHubSensorEntityDescription, ...] = (
    GitHubSensorEntityDescription(
        key="issues_count",
        name="Issues",
        native_unit_of_measurement="Issues",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        state_fn=lambda data: len(data.issues),
    ),
)

PULLS_DESCRIPTIONS: tuple[GitHubSensorEntityDescription, ...] = (
    GitHubSensorEntityDescription(
        key="pulls_count",
        name="Pull Requests",
        native_unit_of_measurement="Pull Requests",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        state_fn=lambda data: len(data.pulls),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GitHub sensor based on a config entry."""
    repositories: dict[str, DataUpdateCoordinators] = hass.data[DOMAIN]
    entities: list[GitHubSensorBaseEntity] = []

    for coordinators in repositories.values():
        for description in INFORMATION_DESCRIPTIONS:
            entities.append(
                GitHubSensorInformationEntity(coordinators.information, description)
            )

        if coordinators.release.data is not None:
            entities.append(GitHubSensorLastReleaseEntity(coordinators.release))

        entities.append(GitHubSensorLastPullEntity(coordinators.issue))
        for description in PULLS_DESCRIPTIONS:
            entities.append(
                GitHubSensorInformationEntity(coordinators.issue, description)
            )

        if coordinators.information.data.has_issues:
            entities.append(GitHubSensorLastIssueEntity(coordinators.issue))
            for description in ISSUES_DESCRIPTIONS:
                entities.append(
                    GitHubSensorInformationEntity(coordinators.issue, description)
                )

    async_add_entities(entities)


class GitHubSensorBaseEntity(GitHubEntity, SensorEntity):
    """Defines a base GitHub sensor entity."""

    _attr_icon = "mdi:github"
    _attr_entity_registry_enabled_default = False


class GitHubSensorInformationEntity(GitHubSensorBaseEntity):
    """Defines a GitHub information sensor entity."""

    entity_description: GitHubSensorEntityDescription
    coordinator: GitHubBaseDataUpdateCoordinator

    def __init__(
        self,
        coordinator: GitHubBaseDataUpdateCoordinator,
        description: GitHubSensorEntityDescription,
    ) -> None:
        """Initialize a GitHub sensor entity."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self._attr_name = f"{coordinator.repository} {description.name}"
        self._attr_unique_id = f"{coordinator.repository}_{description.key}"

    @property
    def native_value(self) -> datetime | StateType:
        """Return the state of the sensor."""
        return self.entity_description.state_fn(self.coordinator.data)


class GitHubSensorLastReleaseEntity(GitHubSensorBaseEntity):
    """Defines a GitHub release sensor entity."""

    _attr_entity_registry_enabled_default = True

    coordinator: RepositoryReleaseDataUpdateCoordinator

    def __init__(self, coordinator: GitHubBaseDataUpdateCoordinator) -> None:
        """Initialize a GitHub sensor entity."""
        super().__init__(coordinator=coordinator)
        self._attr_name = f"{coordinator.repository} Last Release"
        self._attr_unique_id = f"{coordinator.repository}_last_release"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data.name

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the extra state attributes."""
        return {
            "url": self.coordinator.data.html_url,
            "tag": self.coordinator.data.tag_name,
        }


class GitHubSensorLastIssueEntity(GitHubSensorBaseEntity):
    """Defines a GitHub issue sensor entity."""

    coordinator: RepositoryIssueDataUpdateCoordinator

    def __init__(self, coordinator: GitHubBaseDataUpdateCoordinator) -> None:
        """Initialize a GitHub sensor entity."""
        super().__init__(coordinator=coordinator)
        self._attr_name = f"{coordinator.repository} Last Issue"
        self._attr_unique_id = f"{coordinator.repository}_last_issue"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and len(self.coordinator.data.issues) != 0

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data.issues[0].title

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the extra state attributes."""
        issue = self.coordinator.data.issues[0]
        return {
            "url": issue.html_url,
            "number": issue.number,
        }


class GitHubSensorLastPullEntity(GitHubSensorBaseEntity):
    """Defines a GitHub pull sensor entity."""

    coordinator: RepositoryIssueDataUpdateCoordinator

    def __init__(self, coordinator: GitHubBaseDataUpdateCoordinator) -> None:
        """Initialize a GitHub sensor entity."""
        super().__init__(coordinator=coordinator)
        self._attr_name = f"{coordinator.repository} Last Pull Request"
        self._attr_unique_id = f"{coordinator.repository}_last_pull_request"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and len(self.coordinator.data.pulls) != 0

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data.pulls[0].title

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the extra state attributes."""
        pull = self.coordinator.data.pulls[0]
        return {
            "url": pull.html_url,
            "number": pull.number,
        }
