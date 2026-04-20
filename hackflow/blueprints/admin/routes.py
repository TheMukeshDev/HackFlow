"""Admin Blueprint Routes."""

import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from hackflow.database import get_supabase
from hackflow.decorators import admin_required, get_current_user
from hackflow.services.auth_service import Role, AuthService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
logger = logging.getLogger(__name__)


def _ensure_admin_exists():
    """Ensure at least one admin exists. Run this in development only."""
    if os.environ.get("FLASK_ENV") != "development":
        return

    admin_email = os.environ.get("ADMIN_EMAIL", "").strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()

    if not admin_email or not admin_password:
        return

    try:
        supabase = get_supabase()
        existing = (
            supabase.table("users")
            .select("id")
            .eq("email", admin_email.lower())
            .execute()
        )

        if not existing.data:
            password_hash = AuthService.hash_password(admin_password)

            new_admin = {
                "email": admin_email.lower(),
                "username": admin_email.split("@")[0][:50],
                "password_hash": password_hash,
                "full_name": "System Admin",
                "role": "admin",
                "provider": "email",
                "is_active": True,
            }
            supabase.table("users").insert(new_admin).execute()
            logger.info(f"Admin account created: {admin_email}")
    except Exception as e:
        logger.warning(f"Admin creation: {str(e)}")


# Try to ensure admin exists on import
_ensure_admin_exists()


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Admin dashboard."""
    admin_user = get_current_user()

    try:
        supabase = get_supabase()

        # User stats
        users_resp = supabase.table("users").select("id", count="exact").execute()
        total_users = users_resp.count or 0

        volunteers_resp = (
            supabase.table("users")
            .select("id", count="exact")
            .eq("role", "volunteer")
            .execute()
        )
        total_volunteers = volunteers_resp.count or 0

        pending_resp = (
            supabase.table("users")
            .select("id", count="exact")
            .eq("role", "pending_volunteer")
            .execute()
        )
        pending_approvals = pending_resp.count or 0

        # Counter stats
        counters_resp = supabase.table("food_counters").select("*").execute()
        all_counters = counters_resp.data or []
        active_counters = [c for c in all_counters if c.get("is_active")]

        # Queue stats
        queues_resp = (
            supabase.table("queue_entries")
            .select("id", count="exact")
            .eq("status", "waiting")
            .execute()
        )
        active_queues = queues_resp.count or 0

        # Help request stats
        help_resp = (
            supabase.table("help_requests")
            .select("id", count="exact")
            .neq("status", "resolved")
            .execute()
        )
        unresolved_help = help_resp.count or 0

        # Recent activity
        recent_users = (
            supabase.table("users")
            .select("id", "username", "email", "role", "created_at")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        ).data or []

        # Recent announcements
        recent_announcements = (
            supabase.table("notifications")
            .select("*")
            .order("created_at", desc=True)
            .limit(3)
            .execute()
        ).data or []

    except Exception as e:
        flash("Error loading dashboard.", "danger")
        print(f"Admin dashboard error: {e}")
        total_users = 0
        total_volunteers = 0
        pending_approvals = 0
        all_counters = []
        active_counters = []
        active_queues = 0
        unresolved_help = 0
        recent_users = []
        recent_announcements = []

    return render_template(
        "admin/dashboard.html",
        admin_user=admin_user,
        total_users=total_users,
        total_volunteers=total_volunteers,
        pending_approvals=pending_approvals,
        all_counters=all_counters,
        active_counters=active_counters,
        active_queues=active_queues,
        unresolved_help=unresolved_help,
        recent_users=recent_users,
        recent_announcements=recent_announcements,
    )


@admin_bp.route("/users")
@admin_required
def users():
    """Manage all users."""
    admin_user = get_current_user()
    role_filter = request.args.get("role", "")
    search = request.args.get("search", "")

    try:
        supabase = get_supabase()
        query = supabase.table("users").select("*").order("created_at", desc=True)
        if role_filter:
            query = query.eq("role", role_filter)
        if search:
            query = query.or_(f"username.ilike.%{search}%,email.ilike.%{search}%")
        users_list = query.limit(50).execute()
        users_data = users_list.data or []
    except Exception as e:
        flash("Error loading users.", "danger")
        users_data = []

    return render_template(
        "admin/users.html",
        admin_user=admin_user,
        users=users_data,
        role_filter=role_filter,
    )


@admin_bp.route("/volunteers")
@admin_required
def volunteers():
    """View all volunteers."""
    admin_user = get_current_user()
    status_filter = request.args.get("status", "")

    try:
        supabase = get_supabase()
        if status_filter == "pending":
            users_list = (
                supabase.table("users")
                .select("*")
                .eq("role", "pending_volunteer")
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
        else:
            users_list = (
                supabase.table("users")
                .select("*")
                .eq("role", "volunteer")
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
        users_data = users_list.data or []
    except Exception as e:
        flash("Error loading volunteers.", "danger")
        users_data = []

    return render_template(
        "admin/volunteers.html",
        admin_user=admin_user,
        volunteers=users_data,
        status_filter=status_filter,
    )


@admin_bp.route("/users/promote", methods=["POST"])
@admin_required
def promote_user():
    """Promote user to volunteer or admin."""
    user_id = request.form.get("user_id", "")
    new_role = request.form.get("role", "")

    if not user_id or new_role not in [Role.VOLUNTEER, Role.ADMIN, Role.PARTICIPANT]:
        flash("Invalid request.", "danger")
        return redirect(url_for("admin.users"))

    try:
        supabase = get_supabase()
        supabase.table("users").update({"role": new_role}).eq("id", user_id).execute()
        flash(f"User role updated to {new_role}.", "success")
    except Exception as e:
        flash("Error updating user.", "danger")
        print(f"Promote error: {e}")

    return redirect(url_for("admin.users"))


@admin_bp.route("/volunteer-approvals")
@admin_required
def volunteer_approvals():
    """View pending volunteer approvals."""
    admin_user = get_current_user()

    try:
        supabase = get_supabase()
        pending = (
            supabase.table("users")
            .select("*")
            .eq("role", "pending_volunteer")
            .order("created_at", desc=True)
            .execute()
        ).data or []
    except Exception as e:
        flash("Error loading approvals.", "danger")
        pending = []

    return render_template(
        "admin/approvals.html", admin_user=admin_user, pending_volunteers=pending
    )


@admin_bp.route("/volunteer-approvals/action", methods=["POST"])
@admin_required
def volunteer_approval_action():
    """Approve or reject volunteer."""
    user_id = request.form.get("user_id", "")
    action = request.form.get("action", "")

    if not user_id or action not in ["approve", "reject"]:
        flash("Invalid request.", "danger")
        return redirect(url_for("admin.volunteer_approvals"))

    try:
        supabase = get_supabase()
        new_role = Role.VOLUNTEER if action == "approve" else Role.PARTICIPANT
        supabase.table("users").update({"role": new_role}).eq("id", user_id).execute()

        if action == "approve":
            flash("Volunteer approved.", "success")
        else:
            flash("Volunteer request rejected.", "info")
    except Exception as e:
        flash("Error processing request.", "danger")
        print(f"Approval error: {e}")

    return redirect(url_for("admin.volunteer_approvals"))


@admin_bp.route("/counters", methods=["GET", "POST"])
@admin_required
def counters():
    """Manage food counters."""
    admin_user = get_current_user()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        action = request.form.get("action", "")

        if not name:
            flash("Counter name is required.", "danger")
        else:
            try:
                supabase = get_supabase()
                if action == "create":
                    supabase.table("food_counters").insert(
                        {
                            "name": name,
                            "location": location,
                            "is_active": True,
                        }
                    ).execute()
                    flash("Counter created.", "success")
                elif action == "deactivate":
                    counter_id = request.form.get("counter_id", "")
                    supabase.table("food_counters").update({"is_active": False}).eq(
                        "id", counter_id
                    ).execute()
                    flash("Counter deactivated.", "info")
                elif action == "activate":
                    counter_id = request.form.get("counter_id", "")
                    supabase.table("food_counters").update({"is_active": True}).eq(
                        "id", counter_id
                    ).execute()
                    flash("Counter activated.", "success")
            except Exception as e:
                flash("Error managing counter.", "danger")
                print(f"Counter error: {e}")

        return redirect(url_for("admin.counters"))

    try:
        supabase = get_supabase()
        all_counters = (
            supabase.table("food_counters").select("*").order("name").execute().data
            or []
        )
    except Exception as e:
        flash("Error loading counters.", "danger")
        all_counters = []

    return render_template(
        "admin/counters.html", admin_user=admin_user, counters=all_counters
    )


@admin_bp.route("/broadcast", methods=["GET", "POST"])
@admin_required
def broadcast():
    """Send system-wide announcements."""
    admin_user = get_current_user()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()

        if not title or not message:
            flash("Title and message are required.", "danger")
        else:
            try:
                supabase = get_supabase()
                # Create notification for all users
                supabase.table("notifications").insert(
                    {
                        "title": title,
                        "message": message,
                    }
                ).execute()
                flash("Announcement sent to all users.", "success")
            except Exception as e:
                flash("Error sending announcement.", "danger")
                print(f"Broadcast error: {e}")

        return redirect(url_for("admin.broadcast"))

    return render_template("admin/broadcast.html", admin_user=admin_user)


@admin_bp.route("/analytics")
@admin_required
def analytics():
    """View system analytics."""
    admin_user = get_current_user()

    try:
        supabase = get_supabase()

        # Get counts
        total_users = (
            supabase.table("users").select("id", count="exact").execute().count or 0
        )
        total_volunteers = (
            supabase.table("users")
            .select("id", count="exact")
            .eq("role", "volunteer")
            .execute()
            .count
            or 0
        )
        total_counters = (
            supabase.table("food_counters").select("id", count="exact").execute().count
            or 0
        )
        active_counters = (
            supabase.table("food_counters")
            .select("id", count="exact")
            .eq("is_active", True)
            .execute()
            .count
            or 0
        )

        total_queue_entries = (
            supabase.table("queue_entries").select("id", count="exact").execute().count
            or 0
        )
        waiting_in_queue = (
            supabase.table("queue_entries")
            .select("id", count="exact")
            .eq("status", "waiting")
            .execute()
            .count
            or 0
        )
        served = (
            supabase.table("queue_entries")
            .select("id", count="exact")
            .eq("status", "served")
            .execute()
            .count
            or 0
        )

        total_help = (
            supabase.table("help_requests").select("id", count="exact").execute().count
            or 0
        )
        pending_help = (
            supabase.table("help_requests")
            .select("id", count="exact")
            .eq("status", "pending")
            .execute()
            .count
            or 0
        )
        resolved_help = (
            supabase.table("help_requests")
            .select("id", count="exact")
            .eq("status", "resolved")
            .execute()
            .count
            or 0
        )

    except Exception as e:
        flash("Error loading analytics.", "danger")
        total_users = total_volunteers = total_counters = active_counters = 0
        total_queue_entries = waiting_in_queue = served = 0
        total_help = pending_help = resolved_help = 0

    return render_template(
        "admin/analytics.html",
        admin_user=admin_user,
        total_users=total_users,
        total_volunteers=total_volunteers,
        total_counters=total_counters,
        active_counters=active_counters,
        total_queue_entries=total_queue_entries,
        waiting_in_queue=waiting_in_queue,
        served=served,
        total_help=total_help,
        pending_help=pending_help,
        resolved_help=resolved_help,
    )
