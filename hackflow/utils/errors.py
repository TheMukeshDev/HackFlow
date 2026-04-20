"""Error handlers."""

import logging
from flask import render_template, jsonify, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register error handlers with Flask app."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        logger.warning(f"400 Bad Request: {request.path}")
        if request.is_json:
            return jsonify({"error": "Bad request", "message": str(error)}), 400
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized."""
        logger.warning(f"401 Unauthorized: {request.path}")
        if request.is_json:
            return jsonify({"error": "Unauthorized"}), 401
        return render_template("errors/401.html", error=error), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden."""
        logger.warning(f"403 Forbidden: {request.path}")
        if request.is_json:
            return jsonify({"error": "Forbidden"}), 403
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        logger.info(f"404 Not Found: {request.path}")
        if request.is_json:
            return jsonify({"error": "Not found"}), 404
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"500 Internal Error: {request.path} - {str(error)}")
        if request.is_json:
            return jsonify({"error": "Internal server error"}), 500
        return render_template("errors/500.html", error=error), 500

    @app.errorhandler(429)
    def rate_limited(error):
        """Handle 429 Too Many Requests."""
        logger.warning(f"429 Rate Limited: {request.path}")
        if request.is_json:
            return jsonify(
                {"error": "Rate limit exceeded", "retry_after": error.description}
            ), 429
        return render_template("errors/429.html", error=error), 429

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP {error.code}: {request.path} - {error.description}")
        if request.is_json:
            return jsonify({"error": error.description}), error.code
        return render_template("errors/generic.html", error=error), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all other exceptions."""
        logger.exception(f"Unhandled exception: {request.path} - {str(error)}")
        if request.is_json:
            return jsonify({"error": "An error occurred"}), 500
        return render_template("errors/500.html", error=error), 500
