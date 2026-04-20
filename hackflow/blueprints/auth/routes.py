"""Auth Blueprint Routes - Login, Register, Google OAuth, Profile."""

import os
import secrets
from urllib.parse import urlencode
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from hackflow.database import get_supabase
from hackflow.services.auth_service import AuthService, Role
from hackflow.decorators import set_current_user, clear_current_user, login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _get_google_redirect_uri():
    """Get the Google redirect URI based on environment."""
    base_url = os.environ.get(
        "GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback"
    )
    return base_url


def _check_profile_complete(user):
    """Check if user profile has all required fields."""
    required_fields = ["full_name", "email"]
    missing = [f for f in required_fields if not user.get(f)]
    return missing


def _create_or_login_google_user(google_user_info):
    """Create new user from Google info or login existing user."""
    supabase = get_supabase()
    email = google_user_info.get("email", "").lower()

    if not email:
        return None, "No email provided by Google"

    existing = supabase.table("users").select("*").eq("email", email).execute()

    if existing.data:
        user = existing.data[0]
        if not user.get("is_active", False):
            return None, "Account has been deactivated"
        supabase.table("users").update({"updated_at": "now()"}).eq(
            "id", user["id"]
        ).execute()
        return user, None

    username = email.split("@")[0][:50]
    base_username = username
    counter = 1
    while True:
        check = supabase.table("users").select("id").eq("username", username).execute()
        if not check.data:
            break
        username = f"{base_username}{counter}"
        counter += 1

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
        return result.data[0], None
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
                flash("Invalid email or password.", "danger")
                return render_template("auth/login.html")

            user = response.data[0]

            if not user.get("is_active", False):
                flash("Your account has been deactivated.", "danger")
                return render_template("auth/login.html")

            if user.get("password_hash", "").startswith("google_"):
                flash("Please sign in with Google.", "warning")
                return render_template("auth/login.html")

            if not AuthService.verify_password(password, user["password_hash"]):
                flash("Invalid email or password.", "danger")
                return render_template("auth/login.html")

            set_current_user(user)
            session.permanent = True

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
            flash("An error occurred. Please try again.", "danger")
            print(f"Login error: {e}")

    return render_template("auth/login.html")


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
                flash("Email already registered. Please sign in.", "danger")
                return render_template("auth/register.html")

            username = email.split("@")[0][:50]
            base_username = username
            counter = 1
            while True:
                check = (
                    supabase.table("users")
                    .select("id")
                    .eq("username", username)
                    .execute()
                )
                if not check.data:
                    break
                username = f"{base_username}{counter}"
                counter += 1

            password_hash = AuthService.hash_password(password)
            new_user = {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": "participant",
                "provider": "email",
            }

            supabase.table("users").insert(new_user).execute()
            flash("Account created! Please sign in.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            flash("An error occurred. Please try again.", "danger")
            print(f"Registration error: {e}")

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
                flash("Email already registered. Please sign in.", "danger")
                return render_template("auth/register_volunteer.html")

            username = email.split("@")[0][:50]
            base_username = username
            counter = 1
            while True:
                check = (
                    supabase.table("users")
                    .select("id")
                    .eq("username", username)
                    .execute()
                )
                if not check.data:
                    break
                username = f"{base_username}{counter}"
                counter += 1

            password_hash = AuthService.hash_password(password)
            new_user = {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": "participant",
                "provider": "email",
            }

            result = supabase.table("users").insert(new_user).execute()

            if result.data:
                # Update to pending_volunteer
                supabase.table("users").update({"role": "pending_volunteer"}).eq(
                    "id", result.data[0]["id"]
                ).execute()

            flash(
                "Volunteer application submitted! An admin will review your request.",
                "info",
            )
            return redirect(url_for("auth.login"))

        except Exception as e:
            flash("An error occurred. Please try again.", "danger")
            print(f"Volunteer registration error: {e}")

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
    params = {
        "client_id": google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return redirect(auth_url)


@auth_bp.route("/google/callback")
def google_callback():
    """Handle Google OAuth callback."""
    error = request.args.get("error")
    if error:
        flash(f"Google sign-in failed: {error}", "danger")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    if not code:
        flash("No authorization code received.", "danger")
        return redirect(url_for("auth.login"))

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
        )

        if token_response.status_code != 200:
            flash(f"Token exchange failed: {token_response.text[:100]}", "danger")
            return redirect(url_for("auth.login"))

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            flash("Failed to get user information.", "danger")
            return redirect(url_for("auth.login"))

        google_user = userinfo_response.json()
        user, error = _create_or_login_google_user(google_user)

        if error:
            flash(error, "danger")
            return redirect(url_for("auth.login"))

        set_current_user(user)
        session.permanent = True

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
        print(f"Google callback error: {e}")
        flash("An error occurred during Google sign-in.", "danger")
        return redirect(url_for("auth.login"))


@auth_bp.route("/complete-profile", methods=["GET", "POST"])
def complete_profile():
    """Complete profile for users with missing required fields."""
    user_id = session.get("user_id")
    if not user_id:
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
                flash("Profile completed!", "success")

                user_role = session.get("role")
                if user_role == "admin":
                    return redirect(url_for("admin.dashboard"))
                elif Role.can_access_volunteer(user_role):
                    return redirect(url_for("volunteer.dashboard"))
                return redirect(url_for("user.dashboard"))
            else:
                flash("Failed to update profile.", "danger")

        except Exception as e:
            flash("An error occurred.", "danger")
            print(f"Profile completion error: {e}")

    return render_template("auth/complete_profile.html")


@auth_bp.route("/logout")
def logout():
    """User logout."""
    user_name = session.get("full_name", "User")
    clear_current_user()
    session.clear()
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
                        flash("Current password is incorrect.", "danger")
                        return render_template("auth/profile.html")
                    update_data["password_hash"] = AuthService.hash_password(
                        new_password
                    )

            response = (
                supabase.table("users").update(update_data).eq("id", user_id).execute()
            )
            if response.data:
                session["full_name"] = update_data["full_name"]
                flash("Profile updated successfully.", "success")
            else:
                flash("Update failed.", "danger")

        except Exception as e:
            flash("An error occurred.", "danger")
            print(f"Profile update error: {e}")

    try:
        supabase = get_supabase()
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        user = response.data[0] if response.data else None
    except Exception as e:
        flash("Error loading profile.", "danger")
        user = None

    return render_template("auth/profile.html", user=user)
