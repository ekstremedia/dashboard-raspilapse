import os
import json
import subprocess
import signal
from datetime import datetime
from pathlib import Path


def can_start_job():
    """Check if we can start a new timelapse job"""
    # Check for running make_timelapse.py
    result = subprocess.run(
        ['pgrep', '-f', 'make_timelapse.py'],
        capture_output=True
    )
    if result.returncode == 0:
        pids = result.stdout.decode().strip()
        return False, f"make_timelapse.py already running (PID: {pids})"

    # Check for ANY running ffmpeg process
    result = subprocess.run(
        ['pgrep', '-f', 'ffmpeg'],
        capture_output=True
    )
    if result.returncode == 0:
        pids = result.stdout.decode().strip()
        return False, f"ffmpeg already running (PID: {pids})"

    return True, "OK"


def start_timelapse_job(raspilapse_root, args, job_status_file):
    """Start a timelapse generation job"""
    # Build command
    cmd = [
        '/usr/bin/python3',
        os.path.join(raspilapse_root, 'src', 'make_timelapse.py'),
    ] + args

    # Create log file for output
    log_file = '/tmp/raspilapse-job.log'

    try:
        # Open log file for writing
        with open(log_file, 'w') as log:
            # Start background process
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=raspilapse_root,
                start_new_session=True  # Detach from terminal
            )

        # Write status file
        status = {
            'pid': process.pid,
            'started': datetime.now().isoformat(),
            'args': args,
            'command': ' '.join(cmd),
            'status': 'running',
            'log_file': log_file
        }
        Path(job_status_file).write_text(json.dumps(status, indent=2))

        return {
            'status': 'started',
            'pid': process.pid,
            'command': ' '.join(cmd)
        }

    except Exception as e:
        return {'error': str(e)}


def is_process_running(pid):
    """Check if a specific process is still running."""
    try:
        os.kill(pid, 0)
        # Process exists, but check if it's a zombie
        try:
            with open(f'/proc/{pid}/status', 'r') as f:
                for line in f:
                    if line.startswith('State:'):
                        state = line.split()[1]
                        # Z = zombie, process finished but not reaped
                        if state == 'Z':
                            return False
                        return True
        except (IOError, IndexError):
            # Can't read status, assume running if kill succeeded
            return True
    except OSError:
        return False


def get_job_status(job_status_file):
    """Get current job status"""
    if not Path(job_status_file).exists():
        # Also check if ffmpeg or make_timelapse is running without status file
        can_run, reason = can_start_job()
        if not can_run:
            return {
                'status': 'running',
                'message': reason,
                'external': True
            }
        return {'status': 'idle'}

    try:
        status = json.loads(Path(job_status_file).read_text())
    except (json.JSONDecodeError, IOError):
        return {'status': 'idle'}

    # If already marked as completed or cancelled, return as-is
    if status.get('status') in ('completed', 'cancelled'):
        log_file = status.get('log_file', '/tmp/raspilapse-job.log')
        status['output'] = read_recent_output(log_file, lines=50)
        return status

    # Check if process still running
    pid = status.get('pid')
    if pid:
        # Check both the original process AND if ffmpeg/make_timelapse is still running
        process_alive = is_process_running(pid)
        can_run, _ = can_start_job()  # This checks for ffmpeg and make_timelapse

        if process_alive or not can_run:
            # Still running - read recent log output
            log_file = status.get('log_file', '/tmp/raspilapse-job.log')
            output = read_recent_output(log_file)
            status['output'] = output
            status['status'] = 'running'
            return status
        else:
            # Process finished
            status['status'] = 'completed'
            status['finished'] = datetime.now().isoformat()

            # Read final output
            log_file = status.get('log_file', '/tmp/raspilapse-job.log')
            status['output'] = read_recent_output(log_file, lines=50)

            # Update status file
            Path(job_status_file).write_text(json.dumps(status, indent=2))
            return status

    return {'status': 'idle'}


def read_recent_output(log_file, lines=20):
    """Read recent lines from log file"""
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except IOError:
        return ''


def cancel_job(job_status_file):
    """Cancel running timelapse job"""
    # First try to kill make_timelapse.py
    result = subprocess.run(['pkill', '-f', 'make_timelapse.py'], capture_output=True)
    killed_timelapse = result.returncode == 0

    # Then kill ffmpeg (child process)
    result = subprocess.run(['pkill', '-f', 'ffmpeg'], capture_output=True)
    killed_ffmpeg = result.returncode == 0

    # Update status file
    if Path(job_status_file).exists():
        try:
            status = json.loads(Path(job_status_file).read_text())
            status['status'] = 'cancelled'
            status['cancelled_at'] = datetime.now().isoformat()
            Path(job_status_file).write_text(json.dumps(status, indent=2))
        except (json.JSONDecodeError, IOError):
            pass

    if killed_timelapse or killed_ffmpeg:
        return True, "Job cancelled"
    else:
        return False, "No running job found"
