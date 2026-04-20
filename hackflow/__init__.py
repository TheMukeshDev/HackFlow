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

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(volunteer_bp, url_prefix="/volunteer")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    from flask import redirect, url_for, session, render_template

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
