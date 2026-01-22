from flask import Flask
import yaml


def create_app(config_name="production"):
    app = Flask(__name__)

    # Load configuration
    if config_name == "development":
        app.config.from_object("app.config.DevelopmentConfig")
    else:
        app.config.from_object("app.config.ProductionConfig")

    # Context processor to make camera name available to all templates
    @app.context_processor
    def inject_camera_name():
        camera_name = "Raspilapse"
        try:
            with open(app.config["RASPILAPSE_CONFIG"], "r") as f:
                config = yaml.safe_load(f)
                camera_name = config.get("overlay", {}).get("camera_name", camera_name)
        except Exception:
            pass
        return {"camera_name": camera_name}

    # Register blueprints
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.config_editor import bp as config_bp
    from app.routes.timelapse import bp as timelapse_bp
    from app.routes.gallery import bp as gallery_bp
    from app.routes.videos import bp as videos_bp
    from app.routes.uploads import bp as uploads_bp
    from app.routes.system import bp as system_bp
    from app.routes.logs import bp as logs_bp
    from app.routes.graphs import bp as graphs_bp
    from app.routes.charts import bp as charts_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(config_bp, url_prefix="/config")
    app.register_blueprint(timelapse_bp, url_prefix="/timelapse")
    app.register_blueprint(gallery_bp, url_prefix="/gallery")
    app.register_blueprint(videos_bp, url_prefix="/videos")
    app.register_blueprint(uploads_bp, url_prefix="/uploads")
    app.register_blueprint(system_bp, url_prefix="/system")
    app.register_blueprint(logs_bp, url_prefix="/logs")
    app.register_blueprint(graphs_bp, url_prefix="/graphs")
    app.register_blueprint(charts_bp, url_prefix="/charts")

    return app
