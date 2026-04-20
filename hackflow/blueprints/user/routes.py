"""User Blueprint Routes."""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from hackflow.database import get_supabase
from hackflow.decorators import login_required, get_current_user
from hackflow.services.auth_service import Role

user_bp = Blueprint("user", __name__, url_prefix="/user")
logger = logging.getLogger(__name__)


@user_bp.route("/dashboard")
@login_required
def dashboard():
    """User dashboard."""
    user = get_current_user()

    try:
        supabase = get_supabase()
        counters = []
        notifications = []
        in_queue = None
        in_queue_counter = None
        recommended_counter = None

        # Queue status with counter name
        queue_response = (
            supabase.table("queue_entries")
            .select("*")
            .eq("user_id", user["id"])
            .in_("status", ["waiting", "called"])
            .execute()
        )
        if queue_response.data:
            in_queue = queue_response.data[0]
            # Get counter name
            if in_queue.get("counter_id"):
                counter_resp = (
                    supabase.table("food_counters")
                    .select("name", "location")
                    .eq("id", in_queue["counter_id"])
                    .execute()
                )
                if counter_resp.data:
                    in_queue_counter = {
                        "name": counter_resp.data[0].get("name"),
                        "location": counter_resp.data[0].get("location"),
                    }

        # Get counters with queue counts
        counters_response = (
            supabase.table("food_counters")
            .select("*")
            .eq("is_active", True)
            .order("name")
            .execute()
        )

        min_wait = 9999
        if counters_response.data:
            for counter in counters_response.data:
                # Count waiting for this counter
                wait_resp = (
                    supabase.table("queue_entries")
                    .select("id", count="exact")
                    .eq("counter_id", counter["id"])
                    .eq("status", "waiting")
                    .execute()
                )
                waiting_count = wait_resp.count or 0

                # Calculate load percentage
                capacity = counter.get("capacity", 50)
                load_percent = (
                    min(100, int((waiting_count / capacity) * 100))
                    if capacity > 0
                    else 0
                )

                estimated_wait = waiting_count * 5  # Estimate 5 min per person

                counter["waiting_count"] = waiting_count
                counter["load_percent"] = load_percent
                counter["is_active"] = counter.get("is_active", True)
                counter["average_wait_minutes"] = estimated_wait

                # Find recommended (shortest wait)
                if counter.get("is_active") and estimated_wait < min_wait:
                    min_wait = estimated_wait
                    recommended_counter = counter

                # Include all active counters
                if counter.get("is_active"):
                    counters.append(counter)

        # Recent notifications
        notifications_response = (
            supabase.table("notifications")
            .select("*")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        notifications = notifications_response.data or []

    except Exception as e:
        flash("Error loading dashboard data.", "danger")
        logger.error(f"Dashboard error: {str(e)}")
        in_queue = None
        in_queue_counter = None
        counters = []
        notifications = []
        recommended_counter = None

    return render_template(
        "user/dashboard.html",
        user=user,
        in_queue=in_queue,
        in_queue_counter=in_queue_counter,
        counters=counters,
        notifications=notifications,
        recommended_counter=recommended_counter,
    )


@user_bp.route("/queue")
@login_required
def queue():
    """Food queue page."""
    user = get_current_user()

    try:
        supabase = get_supabase()

        # Get all active counters
        counters_response = (
            supabase.table("food_counters")
            .select("*")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        counters = counters_response.data or []

        # Get user's current queue entry with counter name
        user_queue = None
        if user.get("id"):
            queue_entry_resp = (
                supabase.table("queue_entries")
                .select("*")
                .eq("user_id", user["id"])
                .in_("status", ["waiting", "called"])
                .execute()
            )
            if queue_entry_resp.data:
                q = queue_entry_resp.data[0]
                # Get counter name
                counter_resp = (
                    supabase.table("food_counters")
                    .select("name")
                    .eq("id", q["counter_id"])
                    .execute()
                )
                counter_name = (
                    counter_resp.data[0]["name"] if counter_resp.data else "Unknown"
                )
                user_queue = {
                    "counter_id": q["counter_id"],
                    "counter_name": counter_name,
                    "position": q.get("position"),
                    "status": q.get("status"),
                    "joined_at": q.get("joined_at"),
                }

        # Build counter data with queue counts
        counter_data = []
        recommended_counter = None
        min_wait = 999

        for counter in counters:
            # Count waiting for this counter
            wait_resp = (
                supabase.table("queue_entries")
                .select("id", count="exact")
                .eq("counter_id", counter["id"])
                .eq("status", "waiting")
                .execute()
            )
            waiting_count = wait_resp.count or 0

            # Calculate load percentage
            capacity = counter.get("capacity", 50)
            load_percent = (
                min(100, int((waiting_count / capacity) * 100)) if capacity > 0 else 0
            )

            counter_data.append(
                {
                    "counter": counter,
                    "waiting_count": waiting_count,
                    "load_percent": load_percent,
                }
            )

            # Find recommended (shortest wait, only open counters)
            if (
                counter.get("is_open")
                and counter.get("average_wait_minutes", 0) < min_wait
            ):
                min_wait = counter.get("average_wait_minutes", 0)
                recommended_counter = counter

        # Sort by wait time
        counter_data.sort(key=lambda x: x["counter"].get("average_wait_minutes", 0))

    except Exception as e:
        flash("Error loading queue data.", "danger")
        logger.error(f"Queue error: {str(e)}")
        counter_data = []
        user_queue = None
        recommended_counter = None

    return render_template(
        "user/queue.html",
        user=user,
        user_queue=user_queue,
        counter_data=counter_data,
        recommended_counter=recommended_counter,
    )


@user_bp.route("/crowd")
@login_required
def crowd():
    """Crowd status page."""
    user = get_current_user()

    try:
        supabase = get_supabase()

        # Get all zones with stats
        zones_response = (
            supabase.table("crowd_zones")
            .select("*")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        zones = zones_response.data

        # Get active counters
        counters_response = (
            supabase.table("food_counters")
            .select("*")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        counters = counters_response.data

    except Exception as e:
        flash("Error loading crowd data.", "danger")
        zones = []
        counters = []

    return render_template("user/crowd.html", user=user, zones=zones, counters=counters)


@user_bp.route("/notifications")
@login_required
def notifications():
    """Notifications page."""
    user = get_current_user()

    page = request.args.get("page", 1, type=int)
    per_page = 20

    try:
        supabase = get_supabase()

        # Get notifications (for user or all)
        response = (
            supabase.table("notifications")
            .select("*")
            .order("created_at", desc=True)
            .limit(per_page)
            .execute()
        )
        notifications = response.data

    except Exception as e:
        flash("Error loading notifications.", "danger")
        notifications = []

    return render_template(
        "user/notifications.html", user=user, notifications=notifications
    )


@user_bp.route("/help", methods=["GET", "POST"])
@login_required
def help():
    """Help request page."""
    user = get_current_user()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        urgency = request.form.get("urgency", "normal")

        if not title or not description:
            flash("Title and description are required.", "danger")
            return render_template("user/help.html", user=user)

        if len(description) < 20:
            flash("Please provide more details (at least 20 characters).", "danger")
            return render_template("user/help.html", user=user)

        try:
            supabase = get_supabase()

            new_request = {
                "user_id": user["id"],
                "title": title,
                "description": description,
                "urgency": urgency,
                "status": "pending",
            }

            response = supabase.table("help_requests").insert(new_request).execute()

            if response.data:
                flash(
                    "Help request submitted! A volunteer will respond soon.", "success"
                )
                return redirect(url_for("user.help"))

        except Exception as e:
            flash("Error submitting request.", "danger")
            logger.error(f"Help request error: {str(e)}")

    return render_template("user/help.html", user=user)


@user_bp.route("/venue")
@login_required
def venue():
    """Venue map page."""
    user = get_current_user()

    try:
        supabase = get_supabase()

        # Get counters for map
        counters = (
            supabase.table("food_counters")
            .select("*")
            .eq("is_active", True)
            .execute()
            .data
        )

        # Get zones
        zones = (
            supabase.table("crowd_zones")
            .select("*")
            .eq("is_active", True)
            .execute()
            .data
        )

    except Exception as e:
        flash("Error loading venue data.", "danger")
        counters = []
        zones = []

    return render_template("user/venue.html", user=user, counters=counters, zones=zones)


@user_bp.route("/queue/join", methods=["POST"])
@login_required
def queue_join():
    """Join food queue."""
    user = get_current_user()
    counter_id = request.form.get("counter_id", "").strip()

    if not counter_id:
        flash("Please select a counter.", "danger")
        return redirect(url_for("user.queue"))

    try:
        from hackflow.services.queue_service import QueueService

        queue_service = QueueService()
        entry = queue_service.join_queue(user["id"], counter_id)
        flash(f"Joined queue! Your position: {entry.get('position')}", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash("Error joining queue.", "danger")
        logger.error(f"Queue join error: {str(e)}")

    return redirect(url_for("user.queue"))


@user_bp.route("/queue/leave", methods=["POST"])
@login_required
def queue_leave():
    """Leave food queue."""
    user = get_current_user()

    try:
        from hackflow.services.queue_service import QueueService

        queue_service = QueueService()
        queue_service.leave_queue(user["id"])
        flash("Left queue successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash("Error leaving queue.", "danger")
        logger.error(f"Queue leave error: {str(e)}")

    return redirect(url_for("user.queue"))


@user_bp.route("/queue/switch", methods=["POST"])
@login_required
def queue_switch():
    """Switch to different counter."""
    user = get_current_user()
    new_counter_id = request.form.get("counter_id", "").strip()

    if not new_counter_id:
        flash("Please select a counter.", "danger")
        return redirect(url_for("user.queue"))

    try:
        from hackflow.services.queue_service import QueueService

        queue_service = QueueService()
        entry = queue_service.switch_counter(user["id"], new_counter_id)
        flash(f"Switched to new counter! Position: {entry.get('position')}", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash("Error switching counter.", "danger")
        logger.error(f"Queue switch error: {str(e)}")

    return redirect(url_for("user.queue"))


@user_bp.route("/profile")
@login_required
def profile():
    """User profile page."""
    user = get_current_user()
    return redirect(url_for("auth.profile"))
