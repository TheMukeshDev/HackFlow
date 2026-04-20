"""HackFlow Application Factory."""

import os
import logging
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from hackflow.config import config_by_name, ConfigValidator
from hackflow.utils.logging import setup_logging, app_logger

bcrypt = Bcrypt()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )

    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    setup_logging(app)

    if config_name == "production":
        config_by_name.get(config_name, config_by_name["default"]).init_app(app)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)

    app_logger.init_app(app)

    app.logger.info(f"HackFlow started in {config_name} mode")

    return app


def _init_extensions(app):
    """Initialize Flask extensions."""
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    app.config["RATELIMIT_ENABLED"] = app.config.get("RATELIMIT_ENABLED", True)


def _register_blueprints(app):
    """Register Flask blueprints."""
    from hackflow.blueprints.auth import auth_bp
    from hackflow.blueprints.user import user_bp
    from hackflow.blueprints.volunteer import volunteer_bp
    from hackflow.blueprints.admin import admin_bp
    from hackflow.blueprints.api import api_bp
    from hackflow.blueprints.main import main_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(volunteer_bp, url_prefix="/volunteer")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(main_bp)

    from flask import (
        redirect,
        url_for,
        session,
        render_template,
        jsonify,
        send_from_directory,
    )
    import os

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )

    @app.route("/health")
    def health():
        """Health check endpoint for Cloud Run."""
        from hackflow.database import get_supabase

        try:
            supabase = get_supabase()
            supabase.table("users").select("id").limit(1).execute()
            return jsonify({"status": "healthy", "service": "hackflow"}), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return jsonify({"status": "unhealthy"}), 503

    @app.route("/health/liveness")
    def liveness():
        """Liveness probe for Kubernetes/Cloud Run."""
        return jsonify({"status": "alive"}), 200

    @app.route("/health/readiness")
    def readiness():
        """Readiness probe - checks if app can serve traffic."""
        from hackflow.database import get_supabase

        try:
            supabase = get_supabase()
            supabase.table("users").select("id").limit(1).execute()
            return jsonify({"status": "ready"}), 200
        except Exception as e:
            app.logger.error(f"Readiness check failed: {str(e)}")
            return jsonify({"status": "not ready"}), 503

    @app.route("/")
    def index():
        if "user_id" in session:
            user_role = session.get("role")
            if user_role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user_role in ["volunteer"]:
                return redirect(url_for("volunteer.dashboard"))
            return redirect(url_for("user.dashboard"))
        return render_template("home.html")


def _register_error_handlers(app):
    """Register error handlers."""
    from hackflow.utils.errors import register_error_handlers

    register_error_handlers(app)


def _register_context_processors(app):
    """Register context processors."""
    from hackflow.utils.context_processors import inject_user_info

    app.context_processor(inject_user_info)
