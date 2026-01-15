"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os

# Add app to path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app("development")
    app.config["TESTING"] = True

    # Use temp directories for testing
    app.config["RASPILAPSE_CONFIG"] = tempfile.mktemp(suffix=".yml")
    app.config["JOB_STATUS_FILE"] = tempfile.mktemp(suffix=".json")

    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_config():
    """Sample YAML config for testing."""
    return """# Test config
camera:
  resolution: [1920, 1080]

output:
  base_directory: /tmp/test
  jpeg_quality: 75

timelapse:
  interval: 30
"""


@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary config file."""
    fd, path = tempfile.mkstemp(suffix=".yml")
    with os.fdopen(fd, "w") as f:
        f.write(sample_config)
    yield path
    os.unlink(path)
