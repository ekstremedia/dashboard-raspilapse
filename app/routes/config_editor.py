from flask import Blueprint, render_template, jsonify, request, current_app
from app.services.config_service import (
    load_config,
    save_config,
    validate_yaml,
    get_backups,
    restore_backup,
    backup_config,
)
from app.services.config_schema import get_schema, get_section_order

bp = Blueprint("config", __name__)


@bp.route("/")
def index():
    """Config editor page"""
    return render_template("config_editor.html")


@bp.route("/api/load")
def api_load():
    """Load current config"""
    config_path = current_app.config["RASPILAPSE_CONFIG"]
    content, error = load_config(config_path)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"content": content})


@bp.route("/api/save", methods=["POST"])
def api_save():
    """Save config with validation"""
    config_path = current_app.config["RASPILAPSE_CONFIG"]
    data = request.get_json()
    content = data.get("content", "")

    # Validate first
    valid, errors = validate_yaml(content)
    if not valid:
        return jsonify({"error": "Validation failed", "errors": errors}), 400

    # Save with backup
    success, error = save_config(config_path, content)
    if not success:
        return jsonify({"error": error}), 500

    return jsonify({"success": True, "message": "Config saved successfully"})


@bp.route("/api/validate", methods=["POST"])
def api_validate():
    """Validate YAML without saving"""
    data = request.get_json()
    content = data.get("content", "")
    valid, errors = validate_yaml(content)
    return jsonify({"valid": valid, "errors": errors})


@bp.route("/api/backups")
def api_backups():
    """List available backups"""
    config_path = current_app.config["RASPILAPSE_CONFIG"]
    backups = get_backups(config_path)
    return jsonify({"backups": backups})


@bp.route("/api/restore", methods=["POST"])
def api_restore():
    """Restore from backup"""
    config_path = current_app.config["RASPILAPSE_CONFIG"]
    data = request.get_json()
    backup_file = data.get("backup_file", "")

    success, error = restore_backup(config_path, backup_file)
    if not success:
        return jsonify({"error": error}), 400

    return jsonify({"success": True, "message": "Backup restored"})


@bp.route("/api/backup", methods=["POST"])
def api_backup():
    """Create a manual backup"""
    config_path = current_app.config["RASPILAPSE_CONFIG"]
    try:
        backup_path = backup_config(config_path)
        return jsonify({"success": True, "backup": backup_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/schema")
def api_schema():
    """Return the config schema for the visual editor"""
    return jsonify({
        "schema": get_schema(),
        "section_order": get_section_order()
    })
