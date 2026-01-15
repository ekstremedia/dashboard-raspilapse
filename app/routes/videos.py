from flask import Blueprint, render_template, jsonify, current_app, send_from_directory
from app.services.video_service import get_video_list

bp = Blueprint("videos", __name__)


@bp.route("/")
def index():
    """Video library page"""
    return render_template("videos.html")


@bp.route("/api/list")
def api_list():
    """Get list of available videos"""
    videos_dir = current_app.config["VIDEOS_DIR"]
    videos = get_video_list(videos_dir)
    return jsonify({"videos": videos})


@bp.route("/view/<path:filepath>")
def view_video(filepath):
    """Video player page"""
    return render_template("video_player.html", filepath=filepath)


@bp.route("/file/<path:filepath>")
def serve_video(filepath):
    """Serve a video file"""
    videos_dir = current_app.config["VIDEOS_DIR"]
    return send_from_directory(videos_dir, filepath)
