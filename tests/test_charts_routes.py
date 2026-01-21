"""Test charts routes and API endpoints."""

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


@pytest.fixture
def temp_db_with_data():
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
    for i in range(50):
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
                100.0 * (i + 1),
                "day" if i % 2 == 0 else "night",
                128.0 + i,
                50.0 + i,
                200.0 + i,
                1000 * (i + 1),
                1.0 + i * 0.1,
                20.0 + i * 0.1,
                50 + i % 50,
                5.0 + i * 0.1,
                45.0 + i * 0.2,
                0.5 + i * 0.01,
            ),
        )

    conn.commit()
    conn.close()

    yield path

    os.close(fd)
    os.unlink(path)


class TestChartsPage:
    """Test charts page route."""

    def test_charts_page_loads(self, client):
        """Test that the charts page loads successfully."""
        response = client.get("/charts/")
        assert response.status_code == 200

    def test_charts_page_contains_canvases(self, client):
        """Test that the charts page contains canvas elements."""
        response = client.get("/charts/")
        assert b"canvas" in response.data
        assert b"lightChart" in response.data
        assert b"brightnessChart" in response.data
        assert b"exposureChart" in response.data
        assert b"weatherChart" in response.data
        assert b"systemChart" in response.data

    def test_charts_page_contains_controls(self, client):
        """Test that the charts page contains control elements."""
        response = client.get("/charts/")
        assert b"preset-btn" in response.data
        assert b"startDate" in response.data
        assert b"endDate" in response.data
        assert b"autoRefresh" in response.data

    def test_charts_page_includes_chartjs(self, client):
        """Test that the charts page includes Chart.js."""
        response = client.get("/charts/")
        assert b"chart.js" in response.data or b"chart.umd.min.js" in response.data


class TestChartsApiRange:
    """Test /charts/api/range endpoint."""

    def test_api_range_returns_json(self, client):
        """Test that API range endpoint returns JSON."""
        response = client.get("/charts/api/range")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_api_range_structure(self, client):
        """Test API range response structure."""
        response = client.get("/charts/api/range")
        data = response.get_json()

        assert "earliest" in data
        assert "latest" in data
        assert "count" in data


class TestChartsApiData:
    """Test /charts/api/data endpoint."""

    def test_api_data_returns_json(self, client, temp_db_with_data):
        """Test that API data endpoint returns JSON."""
        from app.services import charts_service

        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db_with_data)):
            response = client.get("/charts/api/data")

        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_api_data_structure(self, client, temp_db_with_data):
        """Test API data response structure."""
        from app.services import charts_service

        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db_with_data)):
            response = client.get("/charts/api/data?metrics=lux,brightness_mean")

        data = response.get_json()
        assert "timestamps" in data
        assert "data" in data

    def test_api_data_with_metrics(self, client, temp_db_with_data):
        """Test API data with specific metrics."""
        from app.services import charts_service

        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db_with_data)):
            response = client.get("/charts/api/data?metrics=lux,brightness_mean")

        data = response.get_json()
        assert "lux" in data.get("data", {})
        assert "brightness_mean" in data.get("data", {})

    def test_api_data_with_time_range(self, client, temp_db_with_data):
        """Test API data with time range parameters."""
        from app.services import charts_service

        now = datetime.now()
        start = (now - timedelta(hours=6)).isoformat()
        end = now.isoformat()

        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db_with_data)):
            response = client.get(f"/charts/api/data?start={start}&end={end}")

        assert response.status_code == 200

    def test_api_data_with_downsample(self, client, temp_db_with_data):
        """Test API data with downsample parameter."""
        from app.services import charts_service

        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db_with_data)):
            response = client.get("/charts/api/data?downsample=100")

        data = response.get_json()
        assert len(data.get("timestamps", [])) <= 100

    def test_api_data_downsample_clamping(self, client, temp_db_with_data):
        """Test that downsample is clamped to valid range."""
        from app.services import charts_service

        # Test too small value
        with patch.object(charts_service, "DATABASE_PATH", Path(temp_db_with_data)):
            response = client.get("/charts/api/data?downsample=10")

        data = response.get_json()
        # Should be clamped to minimum of 50
        assert len(data.get("timestamps", [])) >= 0


class TestChartsApiModes:
    """Test /charts/api/modes endpoint."""

    def test_api_modes_returns_json(self, client):
        """Test that API modes endpoint returns JSON."""
        response = client.get("/charts/api/modes")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_api_modes_structure(self, client):
        """Test API modes response structure."""
        response = client.get("/charts/api/modes")
        data = response.get_json()

        assert "zones" in data
        assert isinstance(data["zones"], list)


class TestChartsApiMetrics:
    """Test /charts/api/metrics endpoint."""

    def test_api_metrics_returns_json(self, client):
        """Test that API metrics endpoint returns JSON."""
        response = client.get("/charts/api/metrics")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_api_metrics_structure(self, client):
        """Test API metrics response structure."""
        response = client.get("/charts/api/metrics")
        data = response.get_json()

        assert "metrics" in data
        assert len(data["metrics"]) > 0

        for metric in data["metrics"]:
            assert "id" in metric
            assert "name" in metric
            assert "column" in metric

    def test_api_metrics_contains_expected(self, client):
        """Test that API metrics contains expected metrics."""
        response = client.get("/charts/api/metrics")
        data = response.get_json()
        metric_ids = [m["id"] for m in data["metrics"]]

        assert "lux" in metric_ids
        assert "brightness_mean" in metric_ids
        assert "exposure_time_us" in metric_ids
        assert "weather_temperature" in metric_ids
        assert "system_cpu_temp" in metric_ids
