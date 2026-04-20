"""Main Blueprint Routes - Static pages like docs, privacy, terms."""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/docs")
def docs():
    """Documentation page."""
    return render_template("main/docs.html")


@main_bp.route("/privacy")
def privacy():
    """Privacy policy page."""
    return render_template("main/privacy.html")


@main_bp.route("/terms")
def terms():
    """Terms of service page."""
    return render_template("main/terms.html")
