from flask import Flask


def create_app(config_name="production"):
    app = Flask(__name__)

    # Load configuration
    if config_name == "development":
        app.config.from_object("app.config.DevelopmentConfig")
    else:
        app.config.from_object("app.config.ProductionConfig")

    # Register blueprints
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.config_editor import bp as config_bp
    from app.routes.timelapse import bp as timelapse_bp
    from app.routes.gallery import bp as gallery_bp
    from app.routes.videos import bp as videos_bp
    from app.routes.system import bp as system_bp
    from app.routes.logs import bp as logs_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(config_bp, url_prefix="/config")
    app.register_blueprint(timelapse_bp, url_prefix="/timelapse")
    app.register_blueprint(gallery_bp, url_prefix="/gallery")
    app.register_blueprint(videos_bp, url_prefix="/videos")
    app.register_blueprint(system_bp, url_prefix="/system")
    app.register_blueprint(logs_bp, url_prefix="/logs")

    return app
