"""Constants for the GitHub integration."""
from datetime import timedelta
from logging import Logger, getLogger
from typing import NamedTuple

from aiogithubapi import GitHubIssueModel

DOMAIN = "github"
LOGGER: Logger = getLogger(__package__)
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=300)

# THIS NEED TO CHANGE!!!!
CLIENT_ID = "ce3981304697fb012542"
# THIS NEED TO CHANGE!!!!


class IssuesPulls(NamedTuple):
    """Issues and pull requests."""

    issues: list[GitHubIssueModel]
    pulls: list[GitHubIssueModel]
