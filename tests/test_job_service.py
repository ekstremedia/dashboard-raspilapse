"""Test job service."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from app.services.job_service import (
    can_start_job,
    get_job_status,
)


def test_can_start_job_no_processes():
    """Test can_start_job when no processes are running."""
    with patch("subprocess.run") as mock_run:
        # Simulate no processes found (returncode 1)
        mock_run.return_value = MagicMock(returncode=1, stdout=b"")

        can_start, reason = can_start_job()
        assert can_start is True
        assert reason == "OK"


def test_can_start_job_ffmpeg_running():
    """Test can_start_job when ffmpeg is running."""
    with patch("subprocess.run") as mock_run:

        def side_effect(cmd, *args, **kwargs):
            result = MagicMock()
            if "make_timelapse" in str(cmd):
                result.returncode = 1
                result.stdout = b""
            else:  # ffmpeg check
                result.returncode = 0
                result.stdout = b"12345"
            return result

        mock_run.side_effect = side_effect

        can_start, reason = can_start_job()
        assert can_start is False
        assert "ffmpeg" in reason.lower()


def test_can_start_job_timelapse_running():
    """Test can_start_job when make_timelapse.py is running."""
    with patch("subprocess.run") as mock_run:

        def side_effect(cmd, *args, **kwargs):
            result = MagicMock()
            if "make_timelapse" in str(cmd):
                result.returncode = 0
                result.stdout = b"12345"
            else:
                result.returncode = 1
                result.stdout = b""
            return result

        mock_run.side_effect = side_effect

        can_start, reason = can_start_job()
        assert can_start is False
        assert "make_timelapse" in reason.lower()


def test_get_job_status_idle():
    """Test get_job_status when no job is running."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        job_file = f.name

    # Delete the file to simulate no job
    os.unlink(job_file)

    with patch("app.services.job_service.can_start_job", return_value=(True, "OK")):
        status = get_job_status(job_file)
        assert status["status"] == "idle"


def test_get_job_status_completed():
    """Test get_job_status when job has completed."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(
            {
                "pid": 99999,  # Non-existent PID
                "started": "2024-01-01T12:00:00",
                "status": "running",
            },
            f,
        )
        job_file = f.name

    try:
        status = get_job_status(job_file)
        assert status["status"] == "completed"
    finally:
        os.unlink(job_file)
