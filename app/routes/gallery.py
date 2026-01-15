from flask import Blueprint, render_template, jsonify, current_app, send_from_directory
from app.services.gallery_service import get_available_dates, get_images_for_date

bp = Blueprint('gallery', __name__)


@bp.route('/')
@bp.route('/<int:year>/<int:month>/<int:day>')
def index(year=None, month=None, day=None):
    """Image gallery page"""
    return render_template('gallery.html', year=year, month=month, day=day)


@bp.route('/api/dates')
def api_dates():
    """Get available dates with images"""
    images_dir = current_app.config['IMAGES_DIR']
    dates = get_available_dates(images_dir)
    return jsonify({'dates': dates})


@bp.route('/api/images/<int:year>/<int:month>/<int:day>')
def api_images(year, month, day):
    """Get images for a specific date"""
    images_dir = current_app.config['IMAGES_DIR']
    images = get_images_for_date(images_dir, year, month, day)
    return jsonify({'images': images})


@bp.route('/image/<path:filepath>')
def serve_image(filepath):
    """Serve an image file"""
    images_dir = current_app.config['IMAGES_DIR']
    return send_from_directory(images_dir, filepath)
