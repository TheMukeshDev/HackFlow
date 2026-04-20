"""Custom decorators for authentication and authorization."""

from functools import wraps
from flask import session, redirect, url_for, flash, abort, g
from hackflow.services.auth_service import Role, Permission


def login_required(f):
    """Require user to be logged in."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def role_required(*allowed_roles):
    """Require specific role(s) to access route."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
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
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        user_role = session.get("role") or ""
        if not Role.can_access_volunteer(str(user_role)):
            flash("Volunteer access required.", "danger")
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def participant_required(f):
    """Require participant (non-volunteer) role."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        user_role = session.get("role")
        if user_role == Role.VOLUNTEER or user_role == Role.ADMIN:
            flash("Participant access required.", "danger")
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Require admin role."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        user_role = session.get("role")
        if user_role != Role.ADMIN:
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
    session.pop("user_id", None)
    session.pop("email", None)
    session.pop("username", None)
    session.pop("role", None)
    session.pop("full_name", None)
