"""Logging configuration for HackFlow."""

import logging
import os
import json
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional


class StructuredLogger:
    """Structured JSON logger for production."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        }
        if extra:
            log_data.update(extra)
        self.logger.log(logging.getLevelName(level), json.dumps(log_data))

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log("INFO", message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log("WARNING", message, kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log("ERROR", message, kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", message, kwargs)


def setup_logging(app):
    """Configure application logging."""
    if not app.debug:
        if not os.path.exists("logs"):
            os.mkdir("logs")

        file_handler = RotatingFileHandler(
            "logs/hackflow.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("HackFlow startup")
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


class AppLogger:
    """Application logger with context."""

    def __init__(self, app=None):
        self.app = app
        self._logger = None

    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        self._logger = logging.getLogger("hackflow")

    def log_auth(self, action: str, user_id: Optional[str] = None, **kwargs):
        """Log authentication events."""
        extra = (
            {"action": action, "user_id": user_id} if user_id else {"action": action}
        )
        extra.update(kwargs)
        self._logger.info(f"Auth: {action}", extra=extra)

    def log_error(self, context: str, error: Exception, **kwargs):
        """Log error with context."""
        extra = {"context": context, "error_type": type(error).__name__}
        extra.update(kwargs)
        self._logger.error(f"Error in {context}: {str(error)}", extra=extra)

    def log_request(self, method: str, path: str, **kwargs):
        """Log HTTP request."""
        extra = {"method": method, "path": path}
        extra.update(kwargs)
        self._logger.info(f"Request: {method} {path}", extra=extra)


app_logger = AppLogger()
