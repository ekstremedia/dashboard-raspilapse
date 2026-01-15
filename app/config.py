import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'raspilapse-dashboard-secret-key')

    # Raspilapse paths
    RASPILAPSE_ROOT = '/home/pi/raspilapse'
    RASPILAPSE_CONFIG = '/home/pi/raspilapse/config/config.yml'
    RASPILAPSE_LOGS = '/home/pi/raspilapse/logs'

    # Web paths
    IMAGES_DIR = '/var/www/html/images'
    VIDEOS_DIR = '/var/www/html/videos'
    STATUS_IMAGE = '/var/www/html/status.jpg'

    # Job management
    JOB_STATUS_FILE = '/tmp/raspilapse-job.json'
    MAX_JOB_TIMEOUT = 7200  # 2 hours max


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
