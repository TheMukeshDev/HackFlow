"""Context processors for Jinja templates."""

from flask import session
from hackflow.services.auth_service import Role


def inject_user_info():
    """Inject user info into all templates."""
    user = None
    if "user_id" in session:
        user = {
            "id": session.get("user_id"),
            "email": session.get("email"),
            "username": session.get("username"),
            "role": session.get("role"),
            "full_name": session.get("full_name"),
            "is_volunteer": session.get("role") in [Role.VOLUNTEER, Role.ADMIN],
        }
    return {"current_user": user}


def inject_app_config():
    """Inject app configuration to templates."""
    from flask import current_app

    return {"app_name": "HackFlow", "app_version": "1.0.0"}
