"""Error handlers."""

from flask import render_template, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    """Register error handlers with Flask app."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        if request.is_json:
            return jsonify({"error": "Bad request"}), 400
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized."""
        if request.is_json:
            return jsonify({"error": "Unauthorized"}), 401
        return render_template("errors/401.html", error=error), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden."""
        if request.is_json:
            return jsonify({"error": "Forbidden"}), 403
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        if request.is_json:
            return jsonify({"error": "Not found"}), 404
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        if request.is_json:
            return jsonify({"error": "Internal server error"}), 500
        return render_template("errors/500.html", error=error), 500

    @app.errorhandler(429)
    def rate_limited(error):
        """Handle 429 Too Many Requests."""
        if request.is_json:
            return jsonify({"error": "Rate limit exceeded"}), 429
        return render_template("errors/429.html", error=error), 429

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions."""
        if request.is_json:
            return jsonify({"error": error.description}), error.code
        return render_template("errors/generic.html", error=error), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all other exceptions."""
        if request.is_json:
            return jsonify({"error": "An error occurred"}), 500
        return render_template("errors/500.html", error=error), 500


from flask import request
