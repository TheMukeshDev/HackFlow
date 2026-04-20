"""HackFlow Configuration Module."""

import os
import secrets
from datetime import timedelta
from typing import List, Optional


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class ConfigValidator:
    """Validates required environment variables."""

    REQUIRED_VARS = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]

    PRODUCTION_REQUIRED_VARS = [
        "SECRET_KEY",
        "SUPABASE_SERVICE_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
    ]

    @classmethod
    def validate(cls, config_name: str = None) -> List[str]:
        """Validate required environment variables."""
        config_name = config_name or os.environ.get("FLASK_ENV", "development")
        missing = []

        for var in cls.REQUIRED_VARS:
            if not os.environ.get(var):
                missing.append(var)

        if config_name == "production":
            for var in cls.PRODUCTION_REQUIRED_VARS:
                if not os.environ.get(var):
                    missing.append(var)

        return missing

    @classmethod
    def validate_or_raise(cls, config_name: str = None):
        """Validate or raise exception."""
        missing = cls.validate(config_name)
        if missing:
            raise ConfigValidationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    @classmethod
    def get_missing_vars(cls, config_name: str = None) -> List[str]:
        """Get list of missing variables (non-raising)."""
        return cls.validate(config_name)


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = False
    TESTING = False

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    BCRYPT_LOG_ROUNDS = 12

    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")

    ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")

    @classmethod
    def init_app(cls, app):
        """Initialize app with configuration."""
        pass


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        config_name = os.environ.get("FLASK_ENV", "development")
        if config_name == "production":
            missing = ConfigValidator.get_missing_vars(config_name)
            if missing:
                app.logger.warning(
                    f"Missing production environment variables: {', '.join(missing)}"
                )


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4
    SECRET_KEY = "test-secret-key"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
