"""Test config service."""
import pytest
import os
import tempfile
from app.services.config_service import (
    load_config,
    save_config,
    validate_yaml,
    backup_config,
    get_backups,
)


def test_load_config(temp_config_file):
    """Test loading a config file."""
    content, error = load_config(temp_config_file)
    assert error is None
    assert content is not None
    assert 'camera' in content


def test_load_config_not_found():
    """Test loading a non-existent config file."""
    content, error = load_config('/nonexistent/path.yml')
    assert content is None
    assert error is not None


def test_validate_yaml_valid(sample_config):
    """Test validating valid YAML."""
    valid, errors = validate_yaml(sample_config)
    assert valid is True
    assert len(errors) == 0


def test_validate_yaml_invalid():
    """Test validating invalid YAML."""
    invalid_yaml = "invalid: yaml: content:"
    valid, errors = validate_yaml(invalid_yaml)
    assert valid is False
    assert len(errors) > 0


def test_validate_yaml_missing_sections():
    """Test validating YAML with missing required sections."""
    incomplete_yaml = """
location:
  latitude: 68.7
"""
    valid, errors = validate_yaml(incomplete_yaml)
    assert valid is False
    assert any('camera' in e for e in errors)


def test_save_config(temp_config_file):
    """Test saving a config file."""
    new_content = """# Updated config
camera:
  resolution: [3840, 2160]

output:
  jpeg_quality: 90

timelapse:
  interval: 60
"""
    success, error = save_config(temp_config_file, new_content)
    assert success is True
    assert error is None

    # Verify content was saved
    with open(temp_config_file, 'r') as f:
        saved_content = f.read()
    assert '3840' in saved_content


def test_backup_config(temp_config_file):
    """Test creating a backup."""
    backup_path = backup_config(temp_config_file)
    assert backup_path is not None
    assert os.path.exists(backup_path)
    # Clean up
    os.unlink(backup_path)


def test_get_backups(temp_config_file):
    """Test listing backups."""
    # Create a backup first
    backup_path = backup_config(temp_config_file)

    backups = get_backups(temp_config_file)
    assert len(backups) >= 1
    assert '.backup.' in backups[0]['filename']

    # Clean up
    os.unlink(backup_path)
