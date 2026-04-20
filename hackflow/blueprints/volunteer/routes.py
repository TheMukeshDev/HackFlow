"""Volunteer Blueprint Routes."""

import logging
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from hackflow.database import get_supabase
from hackflow.decorators import login_required, volunteer_required, get_current_user

volunteer_bp = Blueprint("volunteer", __name__, url_prefix="/volunteer")
logger = logging.getLogger(__name__)


@volunteer_bp.route("/dashboard")
@login_required
@volunteer_required
def dashboard():
    """Volunteer overview dashboard."""
    user = get_current_user()

    stats = {
        "waiting": 0,
        "called": 0,
        "pending_requests": 0,
        "in_progress": 0,
        "active_counters": 0,
    }
    recent_queue_list = []
    recent_requests_list = []

    try:
        supabase = get_supabase()

        try:
            r1 = (
                supabase.table("queue_entries")
                .select("id", count="exact")
                .eq("status", "waiting")
                .execute()
            )
            stats["waiting"] = getattr(r1, "count", 0) or 0
        except Exception:
            pass

        try:
            r2 = (
                supabase.table("queue_entries")
                .select("id", count="exact")
                .eq("status", "called")
                .execute()
            )
            stats["called"] = getattr(r2, "count", 0) or 0
        except Exception:
            pass

        try:
            r3 = (
                supabase.table("help_requests")
                .select("id", count="exact")
                .eq("status", "pending")
                .execute()
            )
            stats["pending_requests"] = getattr(r3, "count", 0) or 0
        except Exception:
            pass

        try:
            r4 = (
                supabase.table("help_requests")
                .select("id", count="exact")
                .eq("status", "in_progress")
                .execute()
            )
            stats["in_progress"] = getattr(r4, "count", 0) or 0
        except Exception:
            pass

        try:
            r5 = (
                supabase.table("food_counters")
                .select("id", count="exact")
                .eq("is_active", True)
                .execute()
            )
            stats["active_counters"] = getattr(r5, "count", 0) or 0
        except Exception:
            pass

        try:
            r6 = (
                supabase.table("queue_entries")
                .select("*")
                .order("joined_at", desc=True)
                .limit(10)
                .execute()
            )
            recent_queue_list = r6.data if r6.data else []
        except Exception:
            pass

        try:
            r7 = (
                supabase.table("help_requests")
                .select("*")
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            recent_requests_list = r7.data if r7.data else []
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Volunteer dashboard error: {str(e)}")

    stats.setdefault("waiting", 0)
    stats.setdefault("called", 0)
    stats.setdefault("pending_requests", 0)
    stats.setdefault("in_progress", 0)
    stats.setdefault("active_counters", 0)

    return render_template(
        "volunteer/dashboard.html",
        user=user,
        stats=stats,
        recent_queue=recent_queue_list,
        recent_requests=recent_requests_list,
    )


@volunteer_bp.route("/food")
@login_required
@volunteer_required
def food():
    """Food counter operations."""
    user = get_current_user()

    try:
        supabase = get_supabase()

        # Get all counters
        counters_response = (
            supabase.table("food_counters")
            .select("*")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        counters = counters_response.data or []

        # Build counter data with stats
        counter_data = []
        total_waiting = 0
        total_called = 0
        counters_open = 0

        for counter in counters:
            # Get waiting count
            wait_resp = (
                supabase.table("queue_entries")
                .select("id", count="exact")
                .eq("counter_id", counter["id"])
                .eq("status", "waiting")
                .execute()
            )
            waiting_count = wait_resp.count or 0

            # Get called count
            called_resp = (
                supabase.table("queue_entries")
                .select("id", count="exact")
                .eq("counter_id", counter["id"])
                .eq("status", "called")
                .execute()
            )
            called_count = called_resp.count or 0

            # Get waiting list
            waiting_resp = (
                supabase.table("queue_entries")
                .select("*")
                .eq("counter_id", counter["id"])
                .eq("status", "waiting")
                .order("position")
                .execute()
            )
            waiting_list = waiting_resp.data or []

            # Calculate load
            capacity = counter.get("capacity", 50)
            load_percent = (
                min(100, int((waiting_count / capacity) * 100)) if capacity > 0 else 0
            )

            counter_data.append(
                {
                    "counter": counter,
                    "waiting_count": waiting_count,
                    "called_count": called_count,
                    "load_percent": load_percent,
                    "waiting_list": waiting_list,
                }
            )

            total_waiting += waiting_count
            total_called += called_count
            if counter.get("is_open"):
                counters_open += 1

    except Exception as e:
        flash("Error loading food data.", "danger")
        logger.error(f"Food operations error: {str(e)}")
        counter_data = []
        total_waiting = 0
        total_called = 0
        counters_open = 0

    return render_template(
        "volunteer/food.html",
        user=user,
        counter_data=counter_data,
        total_waiting=total_waiting,
        total_called=total_called,
        counters_open=counters_open,
    )


@volunteer_bp.route("/crowd")
@login_required
@volunteer_required
def crowd():
    """Crowd monitoring."""
    user = get_current_user()

    try:
        supabase = get_supabase()

        # Get all zones
        zones_response = (
            supabase.table("crowd_zones")
            .select("*")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        zones = zones_response.data

        # Get counters
        counters_response = (
            supabase.table("food_counters")
            .select("*")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        counters = counters_response.data

        # Queue totals
        total_waiting = (
            supabase.table("queue_entries")
            .select("id", count="exact")
            .eq("status", "waiting")
            .execute()
        )

        stats = {
            "total_waiting": total_waiting.count or 0,
            "zones": len(zones) if zones else 0,
            "counters": len(counters) if counters else 0,
        }

    except Exception as e:
        flash("Error loading crowd data.", "danger")
        zones = []
        counters = []
        stats = {"total_waiting": 0, "zones": 0, "counters": 0}

    return render_template(
        "volunteer/crowd.html", user=user, zones=zones, counters=counters, stats=stats
    )


@volunteer_bp.route("/requests")
@login_required
@volunteer_required
def requests():
    """Help requests management."""
    user = get_current_user()

    status_filter = request.args.get("status", "pending")

    try:
        supabase = get_supabase()

        if status_filter == "all":
            requests_response = (
                supabase.table("help_requests")
                .select("*")
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
        else:
            requests_response = (
                supabase.table("help_requests")
                .select("*")
                .eq("status", status_filter)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )

        help_requests = requests_response.data

    except Exception as e:
        flash("Error loading requests.", "danger")
        help_requests = []

    return render_template(
        "volunteer/requests.html",
        user=user,
        requests=help_requests,
        status_filter=status_filter,
    )


@volunteer_bp.route("/broadcasts", methods=["GET", "POST"])
@login_required
@volunteer_required
def broadcasts():
    """Broadcast/announcement system."""
    user = get_current_user()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()
        notification_type = request.form.get("type", "announcement")

        if not title or not message:
            flash("Title and message are required.", "danger")
            return render_template("volunteer/broadcasts.html", user=user)

        try:
            supabase = get_supabase()

            new_notification = {
                "title": title,
                "message": message,
                "type": notification_type,
                "created_by": user["id"],
            }

            response = (
                supabase.table("notifications").insert(new_notification).execute()
            )

            if response.data:
                flash("Broadcast sent successfully!", "success")

        except Exception as e:
            flash("Error sending broadcast.", "danger")
            logger.error(f"Broadcast error: {str(e)}")

    try:
        supabase = get_supabase()

        notifications_response = (
            supabase.table("notifications")
            .select("*")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        notifications = notifications_response.data

    except Exception as e:
        notifications = []

    return render_template(
        "volunteer/broadcasts.html", user=user, notifications=notifications
    )


@volunteer_bp.route("/tasks")
@login_required
@volunteer_required
def tasks():
    """Task assignment page."""
    user = get_current_user()

    try:
        supabase = get_supabase()

        # Get pending tasks
        tasks_response = (
            supabase.table("volunteer_assignments")
            .select("*")
            .eq("status", "pending")
            .order("created_at", desc=True)
            .execute()
        )
        tasks = tasks_response.data

        # Get volunteers for assignment
        volunteers_response = (
            supabase.table("users")
            .select("*")
            .eq("role", "volunteer")
            .eq("is_active", True)
            .execute()
        )
        volunteers = volunteers_response.data

    except Exception as e:
        flash("Error loading tasks.", "danger")
        tasks = []
        volunteers = []

    return render_template(
        "volunteer/tasks.html", user=user, tasks=tasks, volunteers=volunteers
    )


@volunteer_bp.route("/analytics")
@login_required
@volunteer_required
def analytics():
    """Analytics page."""
    user = get_current_user()

    try:
        supabase = get_supabase()

        # Basic analytics
        total_users = supabase.table("users").select("id", count="exact").execute()
        total_volunteers = (
            supabase.table("users")
            .select("id", count="exact")
            .eq("role", "volunteer")
            .execute()
        )
        total_queue = (
            supabase.table("queue_entries").select("id", count="exact").execute()
        )
        total_requests = (
            supabase.table("help_requests").select("id", count="exact").execute()
        )

        analytics = {
            "total_users": total_users.count or 0,
            "total_volunteers": total_volunteers.count or 0,
            "total_queue_entries": total_queue.count or 0,
            "total_help_requests": total_requests.count or 0,
        }

    except Exception as e:
        flash("Error loading analytics.", "danger")
        analytics = {
            "total_users": 0,
            "total_volunteers": 0,
            "total_queue_entries": 0,
            "total_help_requests": 0,
        }

    return render_template("volunteer/analytics.html", user=user, analytics=analytics)


@volunteer_bp.route("/queue/call/<counter_id>", methods=["POST"])
@login_required
@volunteer_required
def queue_call(counter_id):
    """Call next person in queue."""
    user = get_current_user()

    try:
        from hackflow.services.queue_service import QueueService

        queue_service = QueueService()
        entry = queue_service.call_next(counter_id)

        if entry:
            flash(f"Called position #{entry.get('position')}", "success")
        else:
            flash("No one waiting in queue.", "warning")
    except Exception as e:
        flash("Error calling next person.", "danger")
        logger.error(f"Queue call error: {str(e)}")

    return redirect(url_for("volunteer.food"))


@volunteer_bp.route("/queue/complete/<entry_id>", methods=["POST"])
@login_required
@volunteer_required
def queue_complete(entry_id):
    """Mark queue entry as completed."""
    user = get_current_user()

    try:
        from hackflow.services.queue_service import QueueService

        queue_service = QueueService()
        queue_service.complete(entry_id)
        flash("Entry completed.", "success")
    except Exception as e:
        flash("Error completing entry.", "danger")
        logger.error(f"Queue complete error: {str(e)}")

    return redirect(url_for("volunteer.food"))


@volunteer_bp.route("/counter/toggle/<counter_id>", methods=["POST"])
@login_required
@volunteer_required
def counter_toggle(counter_id):
    """Toggle counter open/closed status."""
    user = get_current_user()

    try:
        supabase = get_supabase()

        counter = (
            supabase.table("food_counters").select("*").eq("id", counter_id).execute()
        )

        if not counter.data:
            flash("Counter not found.", "danger")
            return redirect(url_for("volunteer.food"))

        current_status = counter.data[0].get("is_open", True)

        supabase.table("food_counters").update({"is_open": not current_status}).eq(
            "id", counter_id
        ).execute()

        flash(
            f"Counter is now {'Open' if not current_status else 'Closed'}.", "success"
        )
    except Exception as e:
        flash("Error toggling counter.", "danger")
        logger.error(f"Counter toggle error: {str(e)}")

    return redirect(url_for("volunteer.food"))
