"""Test sentry data filter."""
import os
from unittest.mock import patch

from awesomeversion import AwesomeVersion
import pytest

from supervisor.const import SUPERVISOR_VERSION, CoreState
from supervisor.exceptions import AddonConfigurationError
from supervisor.misc.filter import filter_data
from supervisor.resolution.const import (
    ContextType,
    IssueType,
    SuggestionType,
    UnhealthyReason,
    UnsupportedReason,
)

SAMPLE_EVENT = {"sample": "event", "extra": {"Test": "123"}}


@pytest.fixture
def sys_env(autouse=True):
    """Fixture to inject oppio env."""
    with patch.dict(os.environ, {"Test": "123"}):
        yield


def test_ignored_exception(coresys):
    """Test ignored exceptions."""
    hint = {"exc_info": (None, AddonConfigurationError(), None)}
    assert filter_data(coresys, SAMPLE_EVENT, hint) is None


def test_diagnostics_disabled(coresys):
    """Test if diagnostics is disabled."""
    coresys.config.diagnostics = False
    assert filter_data(coresys, SAMPLE_EVENT, {}) is None


def test_not_supported(coresys):
    """Test if not supported."""
    coresys.config.diagnostics = True
    coresys.resolution.unsupported = UnsupportedReason.DOCKER_VERSION
    assert filter_data(coresys, SAMPLE_EVENT, {}) is None


def test_is_dev(coresys):
    """Test if dev."""
    coresys.config.diagnostics = True
    with patch("os.environ", return_value=[("ENV_SUPERVISOR_DEV", "1")]):
        assert filter_data(coresys, SAMPLE_EVENT, {}) is None


def test_not_started(coresys):
    """Test if supervisor not fully started."""
    coresys.config.diagnostics = True

    coresys.core.state = CoreState.INITIALIZE
    assert filter_data(coresys, SAMPLE_EVENT, {}) == SAMPLE_EVENT

    coresys.core.state = CoreState.SETUP
    assert filter_data(coresys, SAMPLE_EVENT, {}) == SAMPLE_EVENT


def test_defaults(coresys):
    """Test event defaults."""
    coresys.config.diagnostics = True

    coresys.core.state = CoreState.RUNNING
    with patch("shutil.disk_usage", return_value=(42, 42, 2 * (1024.0 ** 3))):
        filtered = filter_data(coresys, SAMPLE_EVENT, {})

    assert ["installation_type", "supervised"] in filtered["tags"]
    assert filtered["contexts"]["host"]["arch"] == "amd64"
    assert filtered["contexts"]["host"]["machine"] == "qemux86-64"
    assert filtered["contexts"]["versions"]["supervisor"] == AwesomeVersion(
        SUPERVISOR_VERSION
    )
    assert filtered["user"]["id"] == coresys.machine_id


def test_sanitize(coresys):
    """Test event sanitation."""
    event = {
        "tags": [["url", "https://mydomain.com"]],
        "request": {
            "url": "https://mydomain.com",
            "headers": [
                ["Host", "mydomain.com"],
                ["Referer", "https://mydomain.com/api/oppio_ingress/xxx-xxx/"],
                ["X-Forwarded-Host", "mydomain.com"],
                ["X-Oppio-Key", "xxx"],
            ],
        },
    }
    coresys.config.diagnostics = True

    coresys.core.state = CoreState.RUNNING
    with patch("shutil.disk_usage", return_value=(42, 42, 2 * (1024.0 ** 3))):
        filtered = filter_data(coresys, event, {})

    assert ["url", "https://example.com"] in filtered["tags"]

    assert filtered["request"]["url"] == "https://example.com"

    assert ["Host", "example.com"] in filtered["request"]["headers"]
    assert ["Referer", "https://example.com/api/oppio_ingress/xxx-xxx/"] in filtered[
        "request"
    ]["headers"]
    assert ["X-Forwarded-Host", "example.com"] in filtered["request"]["headers"]
    assert ["X-Oppio-Key", "XXXXXXXXXXXXXXXXXXX"] in filtered["request"]["headers"]
