"""Auth Blueprint Routes - Login, Register, Google OAuth, Profile."""

import os
import secrets
import logging
import time
from urllib.parse import urlencode
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)
from hackflow.database import get_supabase
from hackflow.services.auth_service import AuthService, Role
from hackflow.decorators import set_current_user, clear_current_user, login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

logger = logging.getLogger(__name__)


def _get_google_redirect_uri():
    """Get the Google redirect URI - uses env var or auto-detects for local dev."""
    base_url = os.environ.get("GOOGLE_REDIRECT_URI")
    if base_url:
        return base_url

    port = os.environ.get("PORT", "5000")
    flask_env = os.environ.get("FLASK_ENV", "development")

    if flask_env in ["development", "testing"]:
        return f"http://127.0.0.1:{port}/auth/google/callback"

    return None


def _generate_oauth_state():
    """Generate secure OAuth state parameter."""
    state_data = f"{secrets.token_hex(16)}:{int(time.time())}"
    return state_data


def _validate_oauth_state(state: str, stored_state: str) -> bool:
    """Validate OAuth state parameter to prevent CSRF."""
    if not state or not stored_state:
        return False
    if state != stored_state:
        return False
    return True


def _check_profile_complete(user):
    """Check if user profile has all required fields."""
    required_fields = ["full_name", "email"]
    missing = [f for f in required_fields if not user.get(f)]
    return missing


def _generate_unique_username(supabase, base_username: str) -> str:
    """Generate a unique username by appending a counter if needed."""
    username = base_username[:50]
    base_username = username
    counter = 1

    while True:
        check = supabase.table("users").select("id").eq("username", username).execute()
        if not check.data:
            break
        username = f"{base_username}{counter}"
        counter += 1

    return username


def _create_or_login_google_user(google_user_info):
    """Create new user from Google info or login existing user."""
    supabase = get_supabase()
    email = google_user_info.get("email", "").lower()

    if not email:
        return None, "No email provided by Google"

    existing = supabase.table("users").select("*").eq("email", email).execute()

    if existing.data:
        user = existing.data[0]
        is_active = user.get("is_active")
        if is_active is False:
            return None, "Account has been deactivated"
        supabase.table("users").update({"updated_at": "now()"}).eq(
            "id", user["id"]
        ).execute()
        logger.info(f"Google user logged in: {email}")
        return user, None

    username = _generate_unique_username(supabase, email.split("@")[0])

    new_user = {
        "email": email,
        "username": username,
        "full_name": google_user_info.get("name", username),
        "password_hash": f"google_{secrets.token_hex(32)}",
        "role": "participant",
        "is_active": True,
        "phone": google_user_info.get("phone", ""),
        "provider": "google",
        "provider_id": google_user_info.get("sub", ""),
    }

    result = supabase.table("users").insert(new_user).execute()
    if result.data:
        logger.info(f"New Google user created: {email}")
        return result.data[0], None
    logger.error(f"Failed to create Google user: {email}")
    return None, "Failed to create user account"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Email/password login."""
    if "user_id" in session:
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("auth/login.html")

        if "@" not in email:
            flash("Invalid email format.", "danger")
            return render_template("auth/login.html")

        try:
            supabase = get_supabase()
            response = supabase.table("users").select("*").eq("email", email).execute()

            if not response.data:
                logger.warning(f"Login attempt for non-existent user: {email}")
                flash("Invalid email or password.", "danger")
                return render_template("auth/login.html")

            user = response.data[0]

            is_active = user.get("is_active")
            if is_active is False:
                logger.warning(f"Login attempt for inactive user: {email}")
                flash("Your account has been deactivated.", "danger")
                return render_template("auth/login.html")

            password_hash = user.get("password_hash", "")

            if not password_hash:
                logger.error(f"User has no password_hash: {email}")
                flash("Account error. Please contact support.", "danger")
                return render_template("auth/login.html")

            if password_hash.startswith("google_"):
                flash("Please sign in with Google.", "warning")
                return render_template("auth/login.html")

            if not AuthService.verify_password(password, password_hash):
                logger.warning(f"Invalid password attempt for user: {email}")
                flash("Invalid email or password.", "danger")
                return render_template("auth/login.html")

            _set_user_session(user)
            logger.info(f"User logged in successfully: {email}")

            flash(
                f"Welcome back, {user.get('full_name', user.get('username'))}!",
                "success",
            )

            missing = _check_profile_complete(user)
            if missing:
                return redirect(url_for("auth.complete_profile"))

            if user.get("role") == "admin":
                return redirect(url_for("admin.dashboard"))
            elif Role.can_access_volunteer(user.get("role")):
                return redirect(url_for("volunteer.dashboard"))
            return redirect(url_for("user.dashboard"))

        except Exception as e:
            logger.error(f"Login error for {email}: {str(e)}", exc_info=True)
            flash("An error occurred. Please try again.", "danger")

    return render_template("auth/login.html")


def _set_user_session(user):
    """Set all required user data in session."""
    session["user_id"] = user.get("id")
    session["email"] = user.get("email")
    session["username"] = user.get("username")
    session["role"] = user.get("role", "participant")
    session["full_name"] = user.get("full_name")
    session["is_active"] = user.get("is_active", True)
    session["profile_complete"] = user.get("profile_complete", False)
    session.permanent = True
    session["login_time"] = int(time.time())
    session["last_activity"] = int(time.time())


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Email/password registration - creates participant role."""
    if "user_id" in session:
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not email or "@" not in email:
            errors.append("Valid email is required.")
        if not full_name or len(full_name) < 2:
            errors.append("Full name is required.")
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/register.html")

        try:
            supabase = get_supabase()
            response = supabase.table("users").select("id").eq("email", email).execute()
            if response.data:
                logger.info(f"Registration attempt for existing email: {email}")
                flash("Email already registered. Please sign in.", "danger")
                return render_template("auth/register.html")

            username = _generate_unique_username(supabase, email.split("@")[0])

            password_hash = AuthService.hash_password(password)
            new_user = {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": "participant",
                "is_active": True,
                "provider": "email",
                "profile_complete": False,
            }

            result = supabase.table("users").insert(new_user).execute()

            if result.data:
                logger.info(f"New user registered: {email}")
                flash("Account created! Please sign in.", "success")
            else:
                logger.error(f"Failed to create user: {email}")
                flash("Failed to create account. Please try again.", "danger")

            return redirect(url_for("auth.login"))

        except Exception as e:
            logger.error(f"Registration error for {email}: {str(e)}", exc_info=True)
            flash("An error occurred. Please try again.", "danger")

    return render_template("auth/register.html")


@auth_bp.route("/register/volunteer", methods=["GET", "POST"])
def register_volunteer():
    """Volunteer registration - creates pending_volunteer role requiring admin approval."""
    if "user_id" in session:
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        college = request.form.get("college", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not email or "@" not in email:
            errors.append("Valid email is required.")
        if not full_name or len(full_name) < 2:
            errors.append("Full name is required.")
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/register_volunteer.html")

        try:
            supabase = get_supabase()
            response = supabase.table("users").select("id").eq("email", email).execute()
            if response.data:
                logger.info(
                    f"Volunteer registration attempt for existing email: {email}"
                )
                flash("Email already registered. Please sign in.", "danger")
                return render_template("auth/register_volunteer.html")

            username = _generate_unique_username(supabase, email.split("@")[0])

            password_hash = AuthService.hash_password(password)
            new_user = {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": "pending_volunteer",
                "is_active": True,
                "provider": "email",
                "college": college,
                "phone": phone,
                "profile_complete": False,
            }

            result = supabase.table("users").insert(new_user).execute()

            if result.data:
                logger.info(f"Volunteer application submitted: {email}")
                flash(
                    "Volunteer application submitted! An admin will review your request.",
                    "info",
                )
            else:
                logger.error(f"Failed to create volunteer: {email}")
                flash("Failed to submit application. Please try again.", "danger")

            return redirect(url_for("auth.login"))

        except Exception as e:
            logger.error(
                f"Volunteer registration error for {email}: {str(e)}", exc_info=True
            )
            flash("An error occurred. Please try again.", "danger")

    return render_template("auth/register_volunteer.html")


@auth_bp.route("/google/login")
def google_login():
    """Start Google OAuth flow."""
    if "user_id" in session:
        return redirect(url_for("user.dashboard"))

    google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not google_client_id:
        flash("Google sign-in is not configured.", "warning")
        return redirect(url_for("auth.login"))

    redirect_uri = _get_google_redirect_uri()
    if not redirect_uri:
        current_app.logger.warning("Google OAuth: redirect URI not configured")
        flash("Google OAuth is not configured for this environment.", "warning")
        return redirect(url_for("auth.login"))

    state = _generate_oauth_state()
    session["oauth_state"] = state
    session["oauth_start_time"] = int(time.time())

    params = {
        "client_id": google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    logger.info("Google OAuth initiated")
    return redirect(auth_url)


@auth_bp.route("/google/callback")
def google_callback():
    """Handle Google OAuth callback."""
    error = request.args.get("error")
    if error:
        logger.warning(f"Google OAuth error: {error}")
        flash(f"Google sign-in failed: {error}", "danger")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        flash("No authorization code received.", "danger")
        return redirect(url_for("auth.login"))

    stored_state = session.get("oauth_state")
    oauth_time = session.get("oauth_start_time", 0)

    if not _validate_oauth_state(state, stored_state):
        logger.warning("Invalid OAuth state - possible CSRF attack")
        flash("Invalid request. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    if int(time.time()) - oauth_time > 600:
        logger.warning("OAuth state expired")
        flash("Session expired. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    session.pop("oauth_state", None)
    session.pop("oauth_start_time", None)

    try:
        google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        redirect_uri = _get_google_redirect_uri()

        import requests

        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            timeout=10,
        )

        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text[:100]}")
            flash(f"Token exchange failed. Please try again.", "danger")
            return redirect(url_for("auth.login"))

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )

        if userinfo_response.status_code != 200:
            logger.error("Failed to get user info from Google")
            flash("Failed to get user information.", "danger")
            return redirect(url_for("auth.login"))

        google_user = userinfo_response.json()
        user, error = _create_or_login_google_user(google_user)

        if error:
            flash(error, "danger")
            return redirect(url_for("auth.login"))

        _set_user_session(user)
        logger.info(f"Google user authenticated: {user.get('email')}")

        missing = _check_profile_complete(user)
        if missing:
            return redirect(url_for("auth.complete_profile"))

        flash(f"Welcome, {user.get('full_name', 'User')}!", "success")

        if user.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        elif Role.can_access_volunteer(user.get("role")):
            return redirect(url_for("volunteer.dashboard"))
        return redirect(url_for("user.dashboard"))

    except Exception as e:
        logger.error(f"Google callback error: {str(e)}", exc_info=True)
        flash("An error occurred during Google sign-in.", "danger")
        return redirect(url_for("auth.login"))


@auth_bp.route("/complete-profile", methods=["GET", "POST"])
def complete_profile():
    """Complete profile for users with missing required fields."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        college = request.form.get("college", "").strip()
        phone = request.form.get("phone", "").strip()

        if not full_name:
            flash("Full name is required.", "danger")
            return render_template("auth/complete_profile.html")

        try:
            supabase = get_supabase()
            update_data = {
                "full_name": full_name,
                "college": college,
                "phone": phone,
                "profile_complete": True,
            }
            result = (
                supabase.table("users").update(update_data).eq("id", user_id).execute()
            )

            if result.data:
                session["full_name"] = full_name
                session["profile_complete"] = True
                stored_user = result.data[0]
                session["role"] = stored_user.get("role", "participant")
                flash("Profile completed!", "success")
                logger.info(f"Profile completed for user_id: {user_id}")

                user_role = session.get("role")
                if user_role == "admin":
                    return redirect(url_for("admin.dashboard"))
                elif Role.can_access_volunteer(user_role):
                    return redirect(url_for("volunteer.dashboard"))
                return redirect(url_for("user.dashboard"))
            else:
                flash("Failed to update profile.", "danger")

        except Exception as e:
            logger.error(f"Profile completion error: {str(e)}", exc_info=True)
            flash("An error occurred.", "danger")

    try:
        supabase = get_supabase()
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        user = response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Profile load error: {str(e)}", exc_info=True)
        flash("Error loading profile.", "danger")
        user = None

    return render_template("auth/complete_profile.html", user=user)


@auth_bp.route("/logout")
def logout():
    """User logout."""
    user_id = session.get("user_id")
    user_name = session.get("full_name", "User")
    user_email = session.get("email")
    clear_current_user()
    logger.info(f"User logged out: {user_email} (user_id: {user_id})")
    flash(f"Goodbye, {user_name}!", "info")
    return redirect(url_for("index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile page."""
    user_id = session.get("user_id")

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        college = request.form.get("college", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")

        errors = []
        if not full_name:
            errors.append("Full name is required.")

        update_data = {"full_name": full_name, "phone": phone, "college": college}

        if new_password:
            if not current_password:
                errors.append("Current password required to change password.")
            elif len(new_password) < 8:
                errors.append("New password must be at least 8 characters.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/profile.html")

        try:
            supabase = get_supabase()

            if new_password:
                response = (
                    supabase.table("users")
                    .select("password_hash")
                    .eq("id", user_id)
                    .execute()
                )
                if not response.data:
                    flash("User not found.", "danger")
                    return render_template("auth/profile.html")

                pw_hash = response.data[0].get("password_hash", "")
                if not pw_hash.startswith("google_"):
                    if not AuthService.verify_password(current_password, pw_hash):
                        logger.warning(
                            f"Invalid current password for user_id: {user_id}"
                        )
                        flash("Current password is incorrect.", "danger")
                        return render_template("auth/profile.html")
                    update_data["password_hash"] = AuthService.hash_password(
                        new_password
                    )
                    logger.info(f"Password changed for user_id: {user_id}")

            response = (
                supabase.table("users").update(update_data).eq("id", user_id).execute()
            )
            if response.data:
                session["full_name"] = update_data["full_name"]
                flash("Profile updated successfully.", "success")
                logger.info(f"Profile updated for user_id: {user_id}")
            else:
                flash("Update failed.", "danger")

        except Exception as e:
            logger.error(f"Profile update error: {str(e)}", exc_info=True)
            flash("An error occurred.", "danger")

    try:
        supabase = get_supabase()
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        user = response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Profile load error: {str(e)}", exc_info=True)
        flash("Error loading profile.", "danger")
        user = None

    return render_template("auth/profile.html", user=user)
