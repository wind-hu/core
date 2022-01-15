"""Sensor platform for the GitHub integratiom."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
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
    CoordinatorKeyType,
    DataUpdateCoordinators,
    GitHubBaseDataUpdateCoordinator,
    RepositoryCommitDataUpdateCoordinator,
    RepositoryIssueDataUpdateCoordinator,
    RepositoryReleaseDataUpdateCoordinator,
)
from .entity import GitHubEntity


@dataclass
class GitHubSensorEntityDescriptionMixin:
    """Mixin for required GitHub description keys."""

    coordinator_key: CoordinatorKeyType
    value_fn: Callable[[Any], StateType]


@dataclass
class GitHubSensorEntityDescription(
    SensorEntityDescription, GitHubSensorEntityDescriptionMixin
):
    """Describes GitHub sensor entity."""

    icon: str = "mdi:github"
    entity_registry_enabled_default: bool = False


SENSOR_DESCRIPTIONS: tuple[GitHubSensorEntityDescription, ...] = (
    GitHubSensorEntityDescription(
        key="stargazers_count",
        name="Stars",
        icon="mdi:star",
        native_unit_of_measurement="Stars",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.stargazers_count,
        coordinator_key="information",
    ),
    GitHubSensorEntityDescription(
        key="subscribers_count",
        name="Subscribers",
        icon="mdi:glasses",
        native_unit_of_measurement="Subscribers",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.subscribers_count,
        coordinator_key="information",
    ),
    GitHubSensorEntityDescription(
        key="forks_count",
        name="Forks",
        icon="mdi:source-fork",
        native_unit_of_measurement="Forks",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.forks_count,
        coordinator_key="information",
    ),
    GitHubSensorEntityDescription(
        key="default_branch",
        name="Default branch",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.default_branch,
        coordinator_key="information",
    ),
    GitHubSensorEntityDescription(
        key="issues_count",
        name="Issues",
        native_unit_of_measurement="Issues",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.issues),
        coordinator_key="issue",
    ),
    GitHubSensorEntityDescription(
        key="pulls_count",
        name="Pull Requests",
        native_unit_of_measurement="Pull Requests",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.pulls),
        coordinator_key="issue",
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
        entities.extend(
            sensor(coordinators)
            for sensor in (
                GitHubSensorLatestCommitEntity,
                GitHubSensorLatestIssueEntity,
                GitHubSensorLatestPullEntity,
                GitHubSensorLatestReleaseEntity,
            )
        )

        entities.extend(
            GitHubSensorDescriptionEntity(coordinators, description)
            for description in SENSOR_DESCRIPTIONS
        )

    async_add_entities(entities)


class GitHubSensorBaseEntity(GitHubEntity, SensorEntity):
    """Defines a base GitHub sensor entity."""


class GitHubSensorDescriptionEntity(GitHubSensorBaseEntity):
    """Defines a GitHub sensor entity based on entity descriptions."""

    coordinator: GitHubBaseDataUpdateCoordinator
    entity_description: GitHubSensorEntityDescription

    def __init__(
        self,
        coordinators: DataUpdateCoordinators,
        description: GitHubSensorEntityDescription,
    ) -> None:
        """Initialize a GitHub sensor entity."""
        self.entity_description = description
        _coordinator = coordinators[description.coordinator_key]
        super().__init__(coordinator=_coordinator)
        self._attr_name = f"{_coordinator.repository} {description.name}"
        self._attr_unique_id = f"{_coordinator.repository}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)


class GitHubSensorLatestBaseEntity(GitHubSensorBaseEntity):
    """Defines a base GitHub latest sensor entity."""

    _name: str = "Latest"
    _coordinator_key: CoordinatorKeyType = "information"
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:github"

    def __init__(self, coordinators: DataUpdateCoordinators) -> None:
        """Initialize a GitHub sensor entity."""
        coordinator = coordinators[self._coordinator_key]
        super().__init__(coordinator=coordinator)
        self._attr_name = f"{coordinator.repository} {self._name}"
        self._attr_unique_id = (
            f"{coordinator.repository}_{self._name.lower().replace(' ', '_')}"
        )


class GitHubSensorLatestReleaseEntity(GitHubSensorLatestBaseEntity):
    """Defines a GitHub release sensor entity."""

    _coordinator_key: CoordinatorKeyType = "release"
    _name: str = "Latest Release"

    _attr_entity_registry_enabled_default = True

    coordinator: RepositoryReleaseDataUpdateCoordinator

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data.name

    @property
    def extra_state_attributes(self) -> Mapping[str, str | None]:
        """Return the extra state attributes."""
        return {
            "url": self.coordinator.data.html_url,
            "tag": self.coordinator.data.tag_name,
        }


class GitHubSensorLatestIssueEntity(GitHubSensorLatestBaseEntity):
    """Defines a GitHub issue sensor entity."""

    _name: str = "Latest Issue"
    _coordinator_key: CoordinatorKeyType = "issue"

    coordinator: RepositoryIssueDataUpdateCoordinator

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and len(self.coordinator.data.issues) != 0

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data.issues[0].title

    @property
    def extra_state_attributes(self) -> Mapping[str, str | int | None]:
        """Return the extra state attributes."""
        issue = self.coordinator.data.issues[0]
        return {
            "url": issue.html_url,
            "number": issue.number,
        }


class GitHubSensorLatestPullEntity(GitHubSensorLatestBaseEntity):
    """Defines a GitHub pull sensor entity."""

    _coordinator_key: CoordinatorKeyType = "issue"
    _name: str = "Latest Pull Request"

    coordinator: RepositoryIssueDataUpdateCoordinator

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and len(self.coordinator.data.pulls) != 0

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data.pulls[0].title

    @property
    def extra_state_attributes(self) -> Mapping[str, str | int | None]:
        """Return the extra state attributes."""
        pull = self.coordinator.data.pulls[0]
        return {
            "url": pull.html_url,
            "number": pull.number,
        }


class GitHubSensorLatestCommitEntity(GitHubSensorLatestBaseEntity):
    """Defines a GitHub commit sensor entity."""

    _coordinator_key: CoordinatorKeyType = "commit"
    _name: str = "Latest Commit"

    coordinator: RepositoryCommitDataUpdateCoordinator

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data.commit.message

    @property
    def extra_state_attributes(self) -> Mapping[str, str | int | None]:
        """Return the extra state attributes."""
        return {
            "sha": self.coordinator.data.sha,
            "url": self.coordinator.data.html_url,
            "author": self.coordinator.data.author.login,
        }
