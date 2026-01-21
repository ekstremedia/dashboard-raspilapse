"""Routes for interactive charts page."""

from flask import Blueprint, render_template, jsonify, request
from app.services.charts_service import (
    get_data_range,
    query_chart_data,
    get_mode_zones,
    get_available_metrics,
)

bp = Blueprint("charts", __name__)


@bp.route("/")
def index():
    """Charts page."""
    data_range = get_data_range()
    metrics = get_available_metrics()
    return render_template("charts.html", data_range=data_range, metrics=metrics)


@bp.route("/api/data")
def api_data():
    """
    Query chart data with optional time range and metrics.

    Query params:
        start: ISO timestamp for start of range
        end: ISO timestamp for end of range
        metrics: Comma-separated list of metric names
        downsample: Maximum number of points (default: 500)
    """
    start = request.args.get("start")
    end = request.args.get("end")
    metrics_param = request.args.get("metrics", "")
    downsample = request.args.get("downsample", "500")

    # Parse metrics
    metrics = [m.strip() for m in metrics_param.split(",") if m.strip()]

    # Parse downsample
    try:
        downsample = int(downsample)
        downsample = max(50, min(2000, downsample))  # Clamp to reasonable range
    except ValueError:
        downsample = 500

    data = query_chart_data(
        start=start,
        end=end,
        metrics=metrics if metrics else None,
        downsample=downsample,
    )

    return jsonify(data)


@bp.route("/api/range")
def api_range():
    """Get available data range (earliest/latest timestamps)."""
    return jsonify(get_data_range())


@bp.route("/api/modes")
def api_modes():
    """
    Get mode zones for background shading.

    Query params:
        start: ISO timestamp for start of range
        end: ISO timestamp for end of range
    """
    start = request.args.get("start")
    end = request.args.get("end")

    zones = get_mode_zones(start=start, end=end)
    return jsonify({"zones": zones})


@bp.route("/api/metrics")
def api_metrics():
    """Get list of available metrics."""
    return jsonify({"metrics": get_available_metrics()})
