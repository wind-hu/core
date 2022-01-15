"""Common helpers for GitHub integration tests."""
import json

from homeassistant.components.github.const import DOMAIN

from tests.common import load_fixture

MOCK_ACCESS_TOKEN = "gho_16C7e42F292c6912E7710c838347Ae178B4a"


def load_json_fixture(fixture_name: str) -> dict:
    """Load a fixture from the tests/fixtures folder."""
    return json.loads(load_fixture(f"{fixture_name}.json", DOMAIN))
