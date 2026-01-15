import os
from datetime import datetime
from pathlib import Path


def get_log_files(logs_dir):
    """Get list of available log files"""
    files = []

    try:
        for filename in os.listdir(logs_dir):
            filepath = os.path.join(logs_dir, filename)
            if not os.path.isfile(filepath):
                continue

            # Only show .log files
            if not filename.endswith(".log"):
                continue

            try:
                stat = os.stat(filepath)
                files.append(
                    {
                        "filename": filename,
                        "size": stat.st_size,
                        "size_kb": round(stat.st_size / 1024, 1),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )
            except OSError:
                pass

    except OSError:
        pass

    # Sort by modified date, newest first
    files.sort(key=lambda x: x["modified"], reverse=True)

    return files


def read_log_file(logs_dir, filename, lines=100):
    """Read last N lines from a log file"""
    # Security: ensure filename doesn't contain path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        return None, "Invalid filename"

    filepath = os.path.join(logs_dir, filename)

    # Verify path is within logs_dir
    if not os.path.abspath(filepath).startswith(os.path.abspath(logs_dir)):
        return None, "Invalid path"

    if not os.path.exists(filepath):
        return None, "File not found"

    try:
        with open(filepath, "r") as f:
            all_lines = f.readlines()
            # Return last N lines
            return "".join(all_lines[-lines:]), None
    except IOError as e:
        return None, str(e)
