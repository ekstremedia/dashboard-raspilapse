"""
Upload Queue Management Routes

Provides dashboard for monitoring and managing the video upload retry queue.
"""

import os
import sys
from pathlib import Path

import yaml
from flask import Blueprint, current_app, jsonify, render_template, request

# Add raspilapse to path for UploadService
sys.path.insert(0, "/home/pi/raspilapse")
from src.upload_service import UploadService

bp = Blueprint("uploads", __name__)


def get_upload_service():
    """Get an UploadService instance with current config."""
    config_path = current_app.config["RASPILAPSE_CONFIG"]
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return UploadService(config, config_path)


@bp.route("/")
def index():
    """Upload queue control panel page."""
    return render_template("uploads.html")


@bp.route("/api/status")
def api_status():
    """Get queue status and history."""
    service = get_upload_service()

    stats = service.get_queue_stats()
    pending = service.get_pending_uploads()
    history = service.get_upload_history(limit=50)

    return jsonify(
        {
            "stats": stats,
            "pending": pending,
            "history": history,
        }
    )


@bp.route("/api/retry/<int:upload_id>", methods=["POST"])
def api_retry(upload_id):
    """Retry a single upload."""
    service = get_upload_service()

    success, message = service.retry_single_upload(upload_id, force=True)

    return jsonify(
        {
            "success": success,
            "message": message,
        }
    )


@bp.route("/api/retry-all", methods=["POST"])
def api_retry_all():
    """Retry all pending uploads."""
    service = get_upload_service()

    results = service.process_retry_queue(force=True)

    return jsonify(
        {
            "success": results["failed"] == 0,
            "results": results,
        }
    )


@bp.route("/api/cancel/<int:upload_id>", methods=["POST"])
def api_cancel(upload_id):
    """Cancel/remove an upload from the queue."""
    service = get_upload_service()

    success = service.cancel_upload(upload_id)

    return jsonify(
        {
            "success": success,
            "message": "Upload cancelled" if success else "Failed to cancel upload",
        }
    )


@bp.route("/api/upload-video", methods=["POST"])
def api_upload_video():
    """Manually queue a video for upload."""
    service = get_upload_service()

    data = request.json or {}
    video_path = data.get("video_path")
    video_date = data.get("video_date")
    keogram_path = data.get("keogram_path")
    slitscan_path = data.get("slitscan_path")

    if not video_path or not video_date:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "video_path and video_date are required",
                }
            ),
            400,
        )

    # Validate video file exists
    if not Path(video_path).exists():
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Video file not found: {video_path}",
                }
            ),
            400,
        )

    queue_id = service.queue_upload(
        video_path=video_path,
        keogram_path=keogram_path,
        slitscan_path=slitscan_path,
        video_date=video_date,
    )

    if queue_id:
        return jsonify(
            {
                "success": True,
                "message": f"Queued for upload (id={queue_id})",
                "queue_id": queue_id,
            }
        )
    else:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to queue upload",
                }
            ),
            500,
        )
