from flask import Blueprint, render_template, jsonify
from app.services.system_service import get_system_metrics, get_system_info

bp = Blueprint("system", __name__)


@bp.route("/")
def index():
    """System status page"""
    system_info = get_system_info()
    return render_template("system.html", system_info=system_info)


@bp.route("/api/metrics")
def api_metrics():
    """Get current system metrics"""
    metrics = get_system_metrics()
    return jsonify(metrics)
