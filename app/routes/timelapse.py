from flask import Blueprint, render_template, jsonify, request, current_app
from app.services.job_service import (
    can_start_job, start_timelapse_job, get_job_status, cancel_job
)

bp = Blueprint('timelapse', __name__)


@bp.route('/')
def index():
    """Timelapse generator page"""
    return render_template('timelapse.html')


@bp.route('/api/generate', methods=['POST'])
def api_generate():
    """Start timelapse generation"""
    # Check if we can start
    can_start, reason = can_start_job()
    if not can_start:
        return jsonify({'error': reason, 'running': True}), 409

    # Get parameters from request
    data = request.get_json()
    args = []

    # Time parameters
    if data.get('start_time'):
        args.extend(['--start', data['start_time']])
    if data.get('end_time'):
        args.extend(['--end', data['end_time']])

    # Date parameters
    if data.get('today'):
        args.append('--today')
    else:
        if data.get('start_date'):
            args.extend(['--start-date', data['start_date']])
        if data.get('end_date'):
            args.extend(['--end-date', data['end_date']])

    # Flags
    if data.get('no_keogram'):
        args.append('--no-keogram')
    if data.get('hd'):
        args.append('--hd')
    if data.get('hw'):
        args.append('--hw')
    if data.get('slitscan'):
        args.append('--slitscan')

    # Optional parameters
    if data.get('fps'):
        args.extend(['--fps', str(data['fps'])])
    if data.get('limit'):
        args.extend(['--limit', str(data['limit'])])

    # Start the job
    raspilapse_root = current_app.config['RASPILAPSE_ROOT']
    job_status_file = current_app.config['JOB_STATUS_FILE']
    result = start_timelapse_job(raspilapse_root, args, job_status_file)

    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result)


@bp.route('/api/status')
def api_status():
    """Get current job status"""
    job_status_file = current_app.config['JOB_STATUS_FILE']
    status = get_job_status(job_status_file)
    return jsonify(status)


@bp.route('/api/cancel', methods=['POST'])
def api_cancel():
    """Cancel running job"""
    job_status_file = current_app.config['JOB_STATUS_FILE']
    success, message = cancel_job(job_status_file)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'error': message}), 400
