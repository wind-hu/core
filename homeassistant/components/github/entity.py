"""Base GitHub entity."""
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GitHubBaseDataUpdateCoordinator


class GitHubEntity(CoordinatorEntity):
    """Defines a base GitHub entity."""

    coordinator: GitHubBaseDataUpdateCoordinator

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.coordinator.data is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this GitHub device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data.id)},
            name=self.coordinator.repository,
            configuration_url=self.coordinator.data.html_url,
            entry_type=DeviceEntryType.SERVICE,
        )
