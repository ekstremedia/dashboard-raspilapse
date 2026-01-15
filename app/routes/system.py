from flask import Blueprint, render_template, jsonify
from app.services.system_service import get_system_metrics

bp = Blueprint('system', __name__)


@bp.route('/')
def index():
    """System status page"""
    return render_template('system.html')


@bp.route('/api/metrics')
def api_metrics():
    """Get current system metrics"""
    metrics = get_system_metrics()
    return jsonify(metrics)
