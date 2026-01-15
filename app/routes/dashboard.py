from flask import Blueprint, render_template, jsonify, current_app
import os
from datetime import datetime
from app.services.system_service import get_quick_stats

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    """Dashboard home page with latest image"""
    return render_template("dashboard.html")


@bp.route("/api/status")
def api_status():
    """Get current status for auto-refresh"""
    status_image = current_app.config["STATUS_IMAGE"]
    stats = get_quick_stats()

    # Get last modified time of status image
    try:
        mtime = os.path.getmtime(status_image)
        last_capture = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except OSError:
        last_capture = "Unknown"

    return jsonify({"last_capture": last_capture, "stats": stats})
