"""Test charts service functionality."""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

# Add app to path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import charts_service


@pytest.fixture
def temp_db():
    """Create a temporary database with test data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create captures table
    cursor.execute(
        """
        CREATE TABLE captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            unix_timestamp REAL NOT NULL,
            camera_id TEXT NOT NULL,
            image_path TEXT NOT NULL,
            lux REAL,
            mode TEXT,
            brightness_mean REAL,
            brightness_p5 REAL,
            brightness_p95 REAL,
            exposure_time_us INTEGER,
            analogue_gain REAL,
            weather_temperature REAL,
            weather_humidity INTEGER,
            weather_wind_speed REAL,
            system_cpu_temp REAL,
            system_load_1min REAL
        )
    """
    )

    # Insert test data
    now = datetime.now()
    for i in range(100):
        ts = now - timedelta(hours=i)
        cursor.execute(
            """
            INSERT INTO captures (
                timestamp, unix_timestamp, camera_id, image_path,
                lux, mode, brightness_mean, brightness_p5, brightness_p95,
                exposure_time_us, analogue_gain,
                weather_temperature, weather_humidity, weather_wind_speed,
                system_cpu_temp, system_load_1min
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ts.isoformat(),
                ts.timestamp(),
                "test_cam",
                f"/tmp/img_{i}.jpg",
                100.0 * (i + 1),  # lux
                "day" if i % 2 == 0 else "night",  # mode
                128.0 + i,  # brightness_mean
                50.0 + i,  # brightness_p5
                200.0 + i,  # brightness_p95
                1000 * (i + 1),  # exposure_time_us
                1.0 + i * 0.1,  # analogue_gain
                20.0 + i * 0.1,  # weather_temperature
                50 + i % 50,  # weather_humidity
                5.0 + i * 0.1,  # weather_wind_speed
                45.0 + i * 0.2,  # system_cpu_temp
                0.5 + i * 0.01,  # system_load_1min
            ),
        )

    conn.commit()
    conn.close()

    yield path

    os.close(fd)
    os.unlink(path)


class TestGetDataRange:
    """Test get_data_range function."""

    def test_get_data_range_with_data(self, temp_db):
        """Test getting data range with existing data."""
        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db)):
            result = charts_service.get_data_range()

        assert result["earliest"] is not None
        assert result["latest"] is not None
        assert result["count"] == 100

    def test_get_data_range_no_db(self):
        """Test getting data range when database doesn't exist."""
        with patch.object(
            charts_service, "DATABASE_PATH", Path("/nonexistent/db.sqlite")
        ):
            result = charts_service.get_data_range()

        assert result["earliest"] is None
        assert result["latest"] is None
        assert result["count"] == 0


class TestQueryChartData:
    """Test query_chart_data function."""

    def test_query_default_metrics(self, temp_db):
        """Test querying with default metrics."""
        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db)):
            result = charts_service.query_chart_data()

        assert "timestamps" in result
        assert "data" in result
        assert len(result["timestamps"]) > 0

    def test_query_specific_metrics(self, temp_db):
        """Test querying specific metrics."""
        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db)):
            result = charts_service.query_chart_data(metrics=["lux", "brightness_mean"])

        assert "lux" in result["data"]
        assert "brightness_mean" in result["data"]

    def test_query_with_time_range(self, temp_db):
        """Test querying with time range."""
        now = datetime.now()
        start = (now - timedelta(hours=12)).isoformat()
        end = now.isoformat()

        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db)):
            result = charts_service.query_chart_data(start=start, end=end)

        # Should have fewer than 100 points since we're limiting time range
        assert len(result["timestamps"]) <= 100

    def test_query_with_downsampling(self, temp_db):
        """Test that downsampling reduces point count."""
        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db)):
            result = charts_service.query_chart_data(downsample=20)

        assert len(result["timestamps"]) <= 20

    def test_query_invalid_metrics(self, temp_db):
        """Test querying with invalid metrics."""
        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db)):
            result = charts_service.query_chart_data(
                metrics=["invalid_metric", "another_invalid"]
            )

        assert result.get("error") == "No valid metrics specified"

    def test_query_no_db(self):
        """Test querying when database doesn't exist."""
        with patch.object(
            charts_service, "DATABASE_PATH", Path("/nonexistent/db.sqlite")
        ):
            result = charts_service.query_chart_data()

        assert result.get("error") == "Database not found"


class TestDownsampleData:
    """Test LTTB downsampling algorithm."""

    def test_downsample_reduces_points(self):
        """Test that downsampling reduces the number of points."""
        timestamps = list(range(100))
        data = {"metric": list(range(100))}

        new_ts, new_data = charts_service.downsample_data(timestamps, data, 20)

        assert len(new_ts) == 20
        assert len(new_data["metric"]) == 20

    def test_downsample_preserves_first_last(self):
        """Test that first and last points are preserved."""
        timestamps = list(range(100))
        data = {"metric": list(range(100))}

        new_ts, new_data = charts_service.downsample_data(timestamps, data, 20)

        assert new_ts[0] == 0
        assert new_ts[-1] == 99
        assert new_data["metric"][0] == 0
        assert new_data["metric"][-1] == 99

    def test_downsample_no_change_if_below_target(self):
        """Test that downsampling doesn't change data if already below target."""
        timestamps = list(range(10))
        data = {"metric": list(range(10))}

        new_ts, new_data = charts_service.downsample_data(timestamps, data, 20)

        assert new_ts == timestamps
        assert new_data == data

    def test_downsample_handles_null_values(self):
        """Test downsampling handles null values."""
        timestamps = list(range(100))
        data = {"metric": [None if i % 2 == 0 else i for i in range(100)]}

        new_ts, new_data = charts_service.downsample_data(timestamps, data, 20)

        assert len(new_ts) == 20


class TestGetModeZones:
    """Test get_mode_zones function."""

    def test_get_mode_zones(self, temp_db):
        """Test getting mode zones."""
        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db)):
            zones = charts_service.get_mode_zones()

        assert len(zones) > 0
        for zone in zones:
            assert "start" in zone
            assert "end" in zone
            assert "mode" in zone
            assert zone["mode"] in ["day", "night"]

    def test_get_mode_zones_no_db(self):
        """Test getting mode zones when database doesn't exist."""
        with patch.object(
            charts_service, "DATABASE_PATH", Path("/nonexistent/db.sqlite")
        ):
            zones = charts_service.get_mode_zones()

        assert zones == []


class TestGetAvailableMetrics:
    """Test get_available_metrics function."""

    def test_returns_metrics_list(self):
        """Test that it returns a list of metrics."""
        metrics = charts_service.get_available_metrics()

        assert len(metrics) > 0
        for metric in metrics:
            assert "id" in metric
            assert "name" in metric
            assert "column" in metric

    def test_contains_expected_metrics(self):
        """Test that expected metrics are included."""
        metrics = charts_service.get_available_metrics()
        metric_ids = [m["id"] for m in metrics]

        assert "lux" in metric_ids
        assert "brightness_mean" in metric_ids
        assert "exposure_time_us" in metric_ids
        assert "weather_temperature" in metric_ids
        assert "system_cpu_temp" in metric_ids
