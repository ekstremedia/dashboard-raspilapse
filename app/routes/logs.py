from flask import Blueprint, render_template, jsonify, request, current_app
from app.services.log_service import get_log_files, read_log_file

bp = Blueprint("logs", __name__)


@bp.route("/")
def index():
    """Log viewer page"""
    return render_template("logs.html")


@bp.route("/api/list")
def api_list():
    """List available log files"""
    logs_dir = current_app.config["RASPILAPSE_LOGS"]
    files = get_log_files(logs_dir)
    return jsonify({"files": files})


@bp.route("/api/read/<filename>")
def api_read(filename):
    """Read log file content"""
    logs_dir = current_app.config["RASPILAPSE_LOGS"]
    lines = request.args.get("lines", 100, type=int)
    content, error = read_log_file(logs_dir, filename, lines)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"content": content, "filename": filename})
