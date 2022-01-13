"""Constants for the GitHub integration."""
from datetime import timedelta
from logging import Logger, getLogger

DOMAIN = "github"
LOGGER: Logger = getLogger(__package__)
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=300)
