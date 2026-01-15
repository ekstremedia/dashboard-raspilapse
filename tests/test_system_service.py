"""Test system service."""

import pytest
from unittest.mock import patch, mock_open
from app.services.system_service import (
    get_cpu_temperature,
    get_disk_usage,
    get_memory_usage,
    get_load_average,
    get_uptime,
    get_system_metrics,
    get_quick_stats,
)


def test_get_cpu_temperature():
    """Test getting CPU temperature."""
    with patch("builtins.open", mock_open(read_data="45000")):
        temp = get_cpu_temperature()
        assert temp == 45.0


def test_get_cpu_temperature_error():
    """Test CPU temperature when file doesn't exist."""
    with patch("builtins.open", side_effect=IOError):
        temp = get_cpu_temperature()
        assert temp is None


def test_get_disk_usage():
    """Test getting disk usage."""
    disk = get_disk_usage("/")
    assert disk is not None
    assert "total_gb" in disk
    assert "used_gb" in disk
    assert "free_gb" in disk
    assert "percent" in disk
    assert disk["percent"] >= 0
    assert disk["percent"] <= 100


def test_get_memory_usage():
    """Test getting memory usage."""
    mock_meminfo = """MemTotal:        4000000 kB
MemFree:         1000000 kB
MemAvailable:    2000000 kB
Buffers:          100000 kB
Cached:           500000 kB
"""
    with patch("builtins.open", mock_open(read_data=mock_meminfo)):
        memory = get_memory_usage()
        assert memory is not None
        assert "total_mb" in memory
        assert "used_mb" in memory
        assert "percent" in memory


def test_get_load_average():
    """Test getting load average."""
    with patch("builtins.open", mock_open(read_data="1.50 1.25 1.00 1/234 5678")):
        load = get_load_average()
        assert load is not None
        assert load["1min"] == 1.50
        assert load["5min"] == 1.25
        assert load["15min"] == 1.00


def test_get_uptime():
    """Test getting uptime."""
    # 90061 seconds = 1 day, 1 hour, 1 minute
    with patch("builtins.open", mock_open(read_data="90061.23 180000.00")):
        uptime = get_uptime()
        assert uptime is not None
        assert "1d" in uptime
        assert "1h" in uptime


def test_get_system_metrics():
    """Test getting all system metrics."""
    metrics = get_system_metrics()
    assert metrics is not None
    assert "timestamp" in metrics
    # These may be None on non-Pi systems
    assert "cpu_temp" in metrics
    assert "disk" in metrics
    assert "memory" in metrics


def test_get_quick_stats():
    """Test getting quick stats."""
    stats = get_quick_stats()
    assert stats is not None
    assert "cpu_temp" in stats
    assert "disk_percent" in stats
    assert "memory_percent" in stats
    assert "images_today" in stats
