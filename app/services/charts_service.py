"""Charts service for querying timelapse data and LTTB downsampling."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Database path
DATABASE_PATH = Path("/home/pi/raspilapse/data/timelapse.db")

# Available metrics and their database columns
AVAILABLE_METRICS = {
    # Light levels
    "lux": "lux",
    "mode": "mode",
    "sun_elevation": "sun_elevation",
    # Brightness
    "brightness_mean": "brightness_mean",
    "brightness_median": "brightness_median",
    "brightness_std": "brightness_std",
    "brightness_p5": "brightness_p5",
    "brightness_p25": "brightness_p25",
    "brightness_p75": "brightness_p75",
    "brightness_p95": "brightness_p95",
    "underexposed_pct": "underexposed_pct",
    "overexposed_pct": "overexposed_pct",
    # Exposure
    "exposure_time_us": "exposure_time_us",
    "analogue_gain": "analogue_gain",
    "digital_gain": "digital_gain",
    # Weather
    "weather_temperature": "weather_temperature",
    "weather_humidity": "weather_humidity",
    "weather_wind_speed": "weather_wind_speed",
    "weather_wind_gust": "weather_wind_gust",
    "weather_pressure": "weather_pressure",
    "weather_rain": "weather_rain",
    # System
    "system_cpu_temp": "system_cpu_temp",
    "system_load_1min": "system_load_1min",
    "system_load_5min": "system_load_5min",
    "system_load_15min": "system_load_15min",
}


def get_db_connection() -> sqlite3.Connection:
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_data_range() -> Dict[str, Optional[str]]:
    """Get the earliest and latest timestamps in the database."""
    if not DATABASE_PATH.exists():
        return {"earliest": None, "latest": None, "count": 0}

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest,
                COUNT(*) as count
            FROM captures
        """
        )
        row = cursor.fetchone()
        return {
            "earliest": row["earliest"],
            "latest": row["latest"],
            "count": row["count"],
        }
    finally:
        conn.close()


def query_chart_data(
    start: Optional[str] = None,
    end: Optional[str] = None,
    metrics: Optional[List[str]] = None,
    downsample: int = 500,
) -> Dict[str, Any]:
    """
    Query chart data from the database.

    Args:
        start: ISO timestamp for start of range (default: 24h ago)
        end: ISO timestamp for end of range (default: now)
        metrics: List of metric names to include
        downsample: Maximum number of points per metric

    Returns:
        Dict with timestamps and metric data arrays
    """
    if not DATABASE_PATH.exists():
        return {"timestamps": [], "data": {}, "error": "Database not found"}

    # Default time range: last 24 hours
    if not end:
        end = datetime.now().isoformat()
    if not start:
        start = (datetime.now() - timedelta(hours=24)).isoformat()

    # Validate and filter metrics
    if not metrics:
        metrics = ["lux", "brightness_mean", "exposure_time_us", "weather_temperature"]
    valid_metrics = [m for m in metrics if m in AVAILABLE_METRICS]

    if not valid_metrics:
        return {"timestamps": [], "data": {}, "error": "No valid metrics specified"}

    # Build column list
    columns = ["unix_timestamp", "timestamp"] + [
        AVAILABLE_METRICS[m] for m in valid_metrics
    ]
    columns_str = ", ".join(columns)

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            f"""
            SELECT {columns_str}
            FROM captures
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY unix_timestamp ASC
        """,
            (start, end),
        )

        rows = cursor.fetchall()

        if not rows:
            return {"timestamps": [], "data": {m: [] for m in valid_metrics}}

        # Convert to lists for downsampling
        timestamps = [row["unix_timestamp"] for row in rows]
        data = {m: [row[AVAILABLE_METRICS[m]] for row in rows] for m in valid_metrics}

        # Apply LTTB downsampling if needed
        if len(timestamps) > downsample:
            timestamps, data = downsample_data(timestamps, data, downsample)

        # Convert unix timestamps to ISO strings for JSON
        iso_timestamps = [datetime.fromtimestamp(ts).isoformat() for ts in timestamps]

        return {
            "timestamps": iso_timestamps,
            "data": data,
            "point_count": len(timestamps),
            "original_count": len(rows),
        }

    finally:
        conn.close()


def downsample_data(
    timestamps: List[float], data: Dict[str, List], target: int
) -> Tuple[List[float], Dict[str, List]]:
    """
    Apply Largest-Triangle-Three-Buckets (LTTB) downsampling.

    This algorithm preserves visual fidelity by keeping points that
    have the largest triangular area with their neighbors.

    Args:
        timestamps: List of unix timestamps
        data: Dict of metric name -> values
        target: Target number of points

    Returns:
        Downsampled timestamps and data
    """
    n = len(timestamps)
    if n <= target:
        return timestamps, data

    # Use the first metric for triangle calculation (they share timestamps)
    # We'll pick the first numeric metric
    reference_metric = None
    for metric, values in data.items():
        if any(v is not None for v in values):
            reference_metric = metric
            break

    if reference_metric is None:
        # No valid data, just do uniform sampling
        indices = [int(i * (n - 1) / (target - 1)) for i in range(target)]
        return (
            [timestamps[i] for i in indices],
            {m: [vals[i] for i in indices] for m, vals in data.items()},
        )

    # LTTB algorithm
    reference_values = data[reference_metric]

    # Replace None with 0 for calculation purposes
    ref_clean = [v if v is not None else 0 for v in reference_values]

    # Always keep first and last points
    selected_indices = [0]

    # Bucket size
    bucket_size = (n - 2) / (target - 2)

    a = 0  # Previous selected point index

    for i in range(target - 2):
        # Calculate bucket range
        bucket_start = int((i + 1) * bucket_size) + 1
        bucket_end = int((i + 2) * bucket_size) + 1
        bucket_end = min(bucket_end, n - 1)

        # Calculate average point in next bucket for triangle calculation
        next_bucket_start = bucket_end
        next_bucket_end = int((i + 3) * bucket_size) + 1
        next_bucket_end = min(next_bucket_end, n)

        avg_x = 0
        avg_y = 0
        count = 0
        for j in range(next_bucket_start, next_bucket_end):
            avg_x += timestamps[j]
            avg_y += ref_clean[j]
            count += 1

        if count > 0:
            avg_x /= count
            avg_y /= count
        else:
            avg_x = timestamps[-1]
            avg_y = ref_clean[-1]

        # Find point in current bucket with largest triangle area
        max_area = -1
        max_idx = bucket_start

        point_a_x = timestamps[a]
        point_a_y = ref_clean[a]

        for j in range(bucket_start, bucket_end):
            # Triangle area calculation (simplified, sign doesn't matter)
            area = abs(
                (point_a_x - avg_x) * (ref_clean[j] - point_a_y)
                - (point_a_x - timestamps[j]) * (avg_y - point_a_y)
            )

            if area > max_area:
                max_area = area
                max_idx = j

        selected_indices.append(max_idx)
        a = max_idx

    # Add last point
    selected_indices.append(n - 1)

    # Extract selected points
    new_timestamps = [timestamps[i] for i in selected_indices]
    new_data = {m: [vals[i] for i in selected_indices] for m, vals in data.items()}

    return new_timestamps, new_data


def get_mode_zones(
    start: Optional[str] = None, end: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get mode transition zones for background shading.

    Returns list of {start, end, mode} dicts.
    """
    if not DATABASE_PATH.exists():
        return []

    # Default time range: last 24 hours
    if not end:
        end = datetime.now().isoformat()
    if not start:
        start = (datetime.now() - timedelta(hours=24)).isoformat()

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT timestamp, mode
            FROM captures
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY unix_timestamp ASC
        """,
            (start, end),
        )

        rows = cursor.fetchall()
        if not rows:
            return []

        zones = []
        current_mode = rows[0]["mode"]
        zone_start = rows[0]["timestamp"]

        for row in rows[1:]:
            if row["mode"] != current_mode:
                zones.append(
                    {"start": zone_start, "end": row["timestamp"], "mode": current_mode}
                )
                current_mode = row["mode"]
                zone_start = row["timestamp"]

        # Add final zone
        zones.append(
            {"start": zone_start, "end": rows[-1]["timestamp"], "mode": current_mode}
        )

        return zones

    finally:
        conn.close()


def get_available_metrics() -> List[Dict[str, str]]:
    """Get list of available metrics with display names."""
    return [
        {"id": k, "name": k.replace("_", " ").title(), "column": v}
        for k, v in AVAILABLE_METRICS.items()
    ]
