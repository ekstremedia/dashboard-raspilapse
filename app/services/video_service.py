import os
from datetime import datetime
from pathlib import Path


def get_video_list(videos_dir):
    """Get list of all videos organized by date"""
    videos = []

    try:
        # Walk through year/month structure
        for root, dirs, files in os.walk(videos_dir):
            for filename in files:
                if not filename.endswith((".mp4", ".mkv", ".avi", ".webm")):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, videos_dir)

                try:
                    stat = os.stat(filepath)
                    size_mb = stat.st_size / (1024 * 1024)

                    videos.append(
                        {
                            "filename": filename,
                            "path": rel_path,
                            "size_mb": round(size_mb, 1),
                            "size_bytes": stat.st_size,
                            "modified": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            "url": f"/videos/{rel_path}",
                            "view_url": f"/videos/view/{rel_path}",
                        }
                    )
                except OSError:
                    pass

    except OSError:
        pass

    # Sort by modified date, newest first
    videos.sort(key=lambda x: x["modified"], reverse=True)

    return videos


def get_image_list(videos_dir):
    """Get list of keograms and slitscans organized by date"""
    images = []

    try:
        for root, dirs, files in os.walk(videos_dir):
            for filename in files:
                if not filename.endswith((".jpg", ".jpeg", ".png")):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, videos_dir)

                # Determine image type from filename
                if "keogram" in filename.lower():
                    image_type = "keogram"
                elif "slitscan" in filename.lower():
                    image_type = "slitscan"
                else:
                    image_type = "image"

                try:
                    stat = os.stat(filepath)
                    size_kb = stat.st_size / 1024

                    images.append(
                        {
                            "filename": filename,
                            "path": rel_path,
                            "type": image_type,
                            "size_kb": round(size_kb, 1),
                            "size_bytes": stat.st_size,
                            "modified": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            "url": f"/videos/{rel_path}",
                        }
                    )
                except OSError:
                    pass

    except OSError:
        pass

    # Sort by modified date, newest first
    images.sort(key=lambda x: x["modified"], reverse=True)

    return images


def get_video_info(videos_dir, rel_path):
    """Get info for a specific video"""
    filepath = os.path.join(videos_dir, rel_path)

    # Security check
    if not os.path.abspath(filepath).startswith(os.path.abspath(videos_dir)):
        return None

    if not os.path.exists(filepath):
        return None

    try:
        stat = os.stat(filepath)
        return {
            "filename": os.path.basename(rel_path),
            "path": rel_path,
            "size_mb": round(stat.st_size / (1024 * 1024), 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "url": f"/videos/{rel_path}",
        }
    except OSError:
        return None
