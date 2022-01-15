"""conftest for the GitHub integration."""
from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_setup_entry() -> Generator[None, None, None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.github.async_setup_entry", return_value=True):
        yield
