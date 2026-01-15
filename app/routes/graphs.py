"""Routes for graphs page."""

from flask import Blueprint, render_template, jsonify, request, send_from_directory
from app.services.graphs_service import (
    list_graphs,
    run_graphs_generator,
    get_graphs_dir,
)

bp = Blueprint("graphs", __name__)


@bp.route("/")
def index():
    """Graphs page."""
    graphs = list_graphs()
    return render_template("graphs.html", graphs=graphs)


@bp.route("/image/<filename>")
def serve_image(filename):
    """Serve graph image files."""
    return send_from_directory(get_graphs_dir(), filename)


@bp.route("/api/list")
def api_list():
    """Get list of available graphs."""
    return jsonify(list_graphs())


@bp.route("/api/generate", methods=["POST"])
def api_generate():
    """Generate new graphs."""
    data = request.get_json() or {}
    time_range = data.get("time_range", "-24h")

    # Validate time range
    valid_ranges = ["1h", "6h", "12h", "24h", "7d", "30d", "--all"]
    if time_range not in valid_ranges:
        time_range = "24h"

    success, output = run_graphs_generator(time_range)

    return jsonify(
        {
            "success": success,
            "output": output,
        }
    )
