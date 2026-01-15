import os
import shutil
import yaml
from datetime import datetime
from pathlib import Path
import glob


def load_config(config_path):
    """Load config file content"""
    try:
        with open(config_path, "r") as f:
            return f.read(), None
    except IOError as e:
        return None, str(e)


def validate_yaml(content):
    """Validate YAML syntax and basic schema"""
    errors = []

    # Check YAML syntax
    try:
        config = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return False, [f"YAML syntax error: {e}"]

    if not isinstance(config, dict):
        return False, ["Config must be a YAML dictionary"]

    # Check required sections exist
    required_sections = ["camera", "output", "timelapse"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")

    # Validate camera settings
    if "camera" in config:
        camera = config["camera"]
        if "resolution" in camera:
            res = camera["resolution"]
            if not isinstance(res, list) or len(res) != 2:
                errors.append("camera.resolution must be a list of [width, height]")

    # Validate output settings
    if "output" in config:
        output = config["output"]
        if "jpeg_quality" in output:
            quality = output["jpeg_quality"]
            if not isinstance(quality, int) or quality < 1 or quality > 100:
                errors.append("output.jpeg_quality must be between 1 and 100")

    # Validate video settings
    if "video" in config:
        video = config["video"]
        if "fps" in video:
            fps = video["fps"]
            if not isinstance(fps, (int, float)) or fps <= 0:
                errors.append("video.fps must be a positive number")

    return len(errors) == 0, errors


def backup_config(config_path):
    """Create a backup of the config file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.dirname(config_path)
    backup_name = f"{os.path.basename(config_path)}.backup.{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)

    shutil.copy2(config_path, backup_path)

    # Keep only last 10 backups
    cleanup_old_backups(config_path, keep=10)

    return backup_path


def cleanup_old_backups(config_path, keep=10):
    """Remove old backup files, keeping the most recent ones"""
    backup_pattern = f"{config_path}.backup.*"
    backups = sorted(glob.glob(backup_pattern), reverse=True)

    for old_backup in backups[keep:]:
        try:
            os.remove(old_backup)
        except OSError:
            pass


def save_config(config_path, content):
    """Save config with automatic backup"""
    try:
        # Create backup first
        if os.path.exists(config_path):
            backup_config(config_path)

        # Write to temp file first (atomic write)
        temp_path = config_path + ".tmp"
        with open(temp_path, "w") as f:
            f.write(content)

        # Atomic rename
        os.rename(temp_path, config_path)

        return True, None
    except Exception as e:
        return False, str(e)


def get_backups(config_path):
    """Get list of available backups"""
    backup_pattern = f"{config_path}.backup.*"
    backups = []

    for backup_path in sorted(glob.glob(backup_pattern), reverse=True):
        try:
            stat = os.stat(backup_path)
            backups.append(
                {
                    "filename": os.path.basename(backup_path),
                    "path": backup_path,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
        except OSError:
            pass

    return backups


def restore_backup(config_path, backup_filename):
    """Restore config from a backup file"""
    # Security: ensure backup is in same directory
    config_dir = os.path.dirname(config_path)
    backup_path = os.path.join(config_dir, backup_filename)

    # Validate path
    if not backup_path.startswith(config_dir):
        return False, "Invalid backup path"

    if not os.path.exists(backup_path):
        return False, "Backup file not found"

    if not backup_filename.startswith(os.path.basename(config_path) + ".backup."):
        return False, "Invalid backup filename"

    try:
        # Backup current config first
        backup_config(config_path)

        # Copy backup to config
        shutil.copy2(backup_path, config_path)

        return True, None
    except Exception as e:
        return False, str(e)
