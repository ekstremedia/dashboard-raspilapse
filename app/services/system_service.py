import os
import subprocess
from datetime import datetime


def get_cpu_temperature():
    """Get CPU temperature in Celsius"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = int(f.read().strip()) / 1000
            return round(temp, 1)
    except (IOError, ValueError):
        return None


def get_disk_usage(path='/'):
    """Get disk usage for a path"""
    try:
        statvfs = os.statvfs(path)
        total = statvfs.f_frsize * statvfs.f_blocks
        free = statvfs.f_frsize * statvfs.f_bavail
        used = total - free
        percent = (used / total) * 100 if total > 0 else 0
        return {
            'total_gb': round(total / (1024**3), 1),
            'used_gb': round(used / (1024**3), 1),
            'free_gb': round(free / (1024**3), 1),
            'percent': round(percent, 1)
        }
    except OSError:
        return None


def get_memory_usage():
    """Get memory usage"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()

        meminfo = {}
        for line in lines:
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip().split()[0]
                meminfo[key] = int(value)

        total = meminfo.get('MemTotal', 0)
        available = meminfo.get('MemAvailable', 0)
        used = total - available
        percent = (used / total) * 100 if total > 0 else 0

        return {
            'total_mb': round(total / 1024, 0),
            'used_mb': round(used / 1024, 0),
            'available_mb': round(available / 1024, 0),
            'percent': round(percent, 1)
        }
    except (IOError, ValueError, KeyError):
        return None


def get_load_average():
    """Get system load average"""
    try:
        with open('/proc/loadavg', 'r') as f:
            parts = f.read().split()
            return {
                '1min': float(parts[0]),
                '5min': float(parts[1]),
                '15min': float(parts[2])
            }
    except (IOError, ValueError, IndexError):
        return None


def get_uptime():
    """Get system uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])

        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except (IOError, ValueError):
        return None


def get_service_status(service_name):
    """Check if a systemd service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == 'active'
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return None


def count_images_today(images_dir):
    """Count images captured today"""
    today = datetime.now()
    today_dir = os.path.join(
        images_dir,
        str(today.year),
        f"{today.month:02d}",
        f"{today.day:02d}"
    )
    try:
        if os.path.isdir(today_dir):
            return len([f for f in os.listdir(today_dir) if f.endswith('.jpg')])
        return 0
    except OSError:
        return 0


def get_system_metrics():
    """Get all system metrics"""
    return {
        'cpu_temp': get_cpu_temperature(),
        'disk': get_disk_usage('/'),
        'disk_images': get_disk_usage('/var/www/html'),
        'memory': get_memory_usage(),
        'load': get_load_average(),
        'uptime': get_uptime(),
        'raspilapse_service': get_service_status('raspilapse'),
        'timestamp': datetime.now().isoformat()
    }


def get_quick_stats():
    """Get quick stats for dashboard"""
    return {
        'cpu_temp': get_cpu_temperature(),
        'disk_percent': get_disk_usage('/').get('percent') if get_disk_usage('/') else None,
        'memory_percent': get_memory_usage().get('percent') if get_memory_usage() else None,
        'images_today': count_images_today('/var/www/html/images')
    }
