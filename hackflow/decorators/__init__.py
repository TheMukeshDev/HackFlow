"""Custom decorators for authentication and authorization."""

from functools import wraps
from flask import session, redirect, url_for, flash, abort
from hackflow.services.auth_service import Role, Permission


def login_required(f):
    """Require user to be logged in."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        # Check if account is still active
        is_active = session.get("is_active", True)
        if is_active is False:
            session.clear()
            flash("Your account has been deactivated.", "danger")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated_function


def role_required(*allowed_roles: str):
    """Require specific role(s) to access route."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))

            user_role = session.get("role")
            if user_role not in allowed_roles:
                flash("You do not have permission to access this page.", "danger")
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def volunteer_required(f):
    """Require volunteer or admin role."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        user_role = str(session.get("role", ""))
        if not Role.can_access_volunteer(user_role):
            flash("Volunteer access required.", "danger")
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def participant_required(f):
    """Require participant (non-volunteer) role."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        user_role = session.get("role")
        if user_role in (Role.VOLUNTEER, Role.ADMIN):
            flash("Participant access required.", "danger")
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Require admin role."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        if session.get("role") != Role.ADMIN:
            flash("Administrator access required.", "danger")
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def get_current_user() -> dict:
    """Get current user from session."""
    return {
        "id": session.get("user_id"),
        "email": session.get("email"),
        "username": session.get("username"),
        "role": session.get("role"),
        "full_name": session.get("full_name"),
    }


def set_current_user(user_data: dict):
    """Set current user in session."""
    session["user_id"] = user_data.get("id")
    session["email"] = user_data.get("email")
    session["username"] = user_data.get("username")
    session["role"] = user_data.get("role")
    session["full_name"] = user_data.get("full_name")


def clear_current_user():
    """Clear current user from session."""
    session_keys = ["user_id", "email", "username", "role", "full_name", "is_active"]
    for key in session_keys:
        session.pop(key, None)
