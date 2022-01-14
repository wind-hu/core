"""Sensor platform for the GitHub integratiom."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from aiogithubapi.models.release import GitHubReleaseModel
from aiogithubapi.models.repository import GitHubRepositoryModel

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import DataUpdateCoordinators, GitHubBaseDataUpdateCoordinator
from .entity import GitHubEntity


@dataclass
class GitHubSensorEntityDescriptionMixin:
    """Mixin for required GitHub description keys."""

    state_fn: Callable[
        [GitHubRepositoryModel | GitHubReleaseModel],
        StateType | datetime,
    ]


@dataclass
class GitHubSensorEntityDescription(
    SensorEntityDescription, GitHubSensorEntityDescriptionMixin
):
    """Describes GitHub sensor entity."""

    entity_registry_enabled_default = False
    icon = "mdi:github"
    entity_category = EntityCategory.DIAGNOSTIC


INFORMATION_DESCRIPTIONS: tuple[GitHubSensorEntityDescription, ...] = (
    GitHubSensorEntityDescription(
        key="updated_at",
        name="Updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=None,
        state_fn=lambda data: datetime.fromisoformat(data.updated_at),
    ),
    GitHubSensorEntityDescription(
        key="stargazers_count",
        name="Stars",
        icon="mdi:star",
        native_unit_of_measurement="Stars",
        state_fn=lambda data: data.stargazers_count,
    ),
    GitHubSensorEntityDescription(
        key="watchers_count",
        name="Watchers",
        icon="mdi:glasses",
        native_unit_of_measurement="Watchers",
        state_fn=lambda data: data.watchers_count,
    ),
    GitHubSensorEntityDescription(
        key="forks_count",
        name="Forks",
        icon="mdi:source-fork",
        native_unit_of_measurement="Forks",
        state_fn=lambda data: data.forks_count,
    ),
    GitHubSensorEntityDescription(
        key="default_branch",
        name="Default branch",
        state_fn=lambda data: data.default_branch,
    ),
)

RELEASE_DESCRIPTIONS: tuple[GitHubSensorEntityDescription, ...] = (
    GitHubSensorEntityDescription(
        key="name",
        name="Release Name",
        entity_category=None,
        state_fn=lambda data: data.name,
    ),
    GitHubSensorEntityDescription(
        key="published_at",
        name="Release Published",
        device_class=SensorDeviceClass.TIMESTAMP,
        state_fn=lambda data: datetime.fromisoformat(data.published_at),
    ),
    GitHubSensorEntityDescription(
        key="html_url",
        name="Release URL",
        icon="mdi:web",
        state_fn=lambda data: data.html_url,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GitHub sensor based on a config entry."""
    repositories: dict[str, DataUpdateCoordinators] = hass.data[DOMAIN][entry.entry_id]

    entities: list[GitHubSensorEntity] = []

    for coordinators in repositories.values():
        for description in INFORMATION_DESCRIPTIONS:
            entities.append(GitHubSensorEntity(coordinators.information, description))

        if coordinators.release.data is not None:
            for description in RELEASE_DESCRIPTIONS:
                entities.append(GitHubSensorEntity(coordinators.release, description))

    async_add_entities(entities)


class GitHubSensorEntity(GitHubEntity, SensorEntity):
    """Defines a GitHub sensor entity."""

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
        self._attr_unique_id = f"{coordinator.data.id}_{description.key}"
