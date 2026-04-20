"""API Blueprint Routes."""

import os
import time
import logging
from flask import Blueprint, jsonify, request, session, current_app
from hackflow.decorators import login_required
from hackflow.services.queue_service import QueueService
from hackflow.database import get_supabase

api_bp = Blueprint("api", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)


@api_bp.route("/health")
def health():
    """Health check endpoint for Cloud Run."""
    try:
        supabase = get_supabase()
        supabase.table("users").select("id").limit(1).execute()

        return jsonify(
            {
                "status": "healthy",
                "service": "hackflow",
                "timestamp": int(time.time()),
                "database": "connected",
            }
        ), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify(
            {
                "status": "unhealthy",
                "service": "hackflow",
                "timestamp": int(time.time()),
                "database": "disconnected",
                "error": str(e)
                if os.environ.get("FLASK_ENV") == "development"
                else "Internal error",
            }
        ), 503


@api_bp.route("/health/liveness")
def liveness():
    """Liveness probe for Kubernetes/Cloud Run."""
    return jsonify({"status": "alive"}), 200


@api_bp.route("/health/readiness")
def readiness():
    """Readiness probe - checks if app can serve traffic."""
    try:
        supabase = get_supabase()
        supabase.table("users").select("id").limit(1).execute()
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({"status": "not ready"}), 503


@api_bp.route("/status")
def status():
    """Public status endpoint."""
    return jsonify(
        {
            "status": "operational",
            "version": os.environ.get("APP_VERSION", "1.0.0"),
            "environment": os.environ.get("FLASK_ENV", "unknown"),
        }
    )


@api_bp.route("/queue/status")
@login_required
def queue_status():
    """Get current user's queue status."""
    user_id = session.get("user_id") or ""

    try:
        queue_service = QueueService()
        status = queue_service.get_queue_status(str(user_id))
        return jsonify({"success": True, "queue": status})
    except Exception as e:
        logger.error(f"Queue status error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/queue/join", methods=["POST"])
@login_required
def queue_join_api():
    """Join queue via API."""
    user_id = session.get("user_id") or ""
    data = request.get_json() or {}
    counter_id = data.get("counter_id")

    if not counter_id:
        return jsonify({"success": False, "error": "counter_id required"}), 400

    try:
        queue_service = QueueService()
        entry = queue_service.join_queue(str(user_id), counter_id)
        return jsonify({"success": True, "entry": entry})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Queue join error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to join queue"}), 500


@api_bp.route("/queue/leave", methods=["POST"])
@login_required
def queue_leave_api():
    """Leave queue via API."""
    user_id = session.get("user_id") or ""

    try:
        queue_service = QueueService()
        queue_service.leave_queue(str(user_id))
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Queue leave error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to leave queue"}), 500


@api_bp.route("/counters")
@login_required
def counters():
    """Get all food counters."""
    try:
        supabase = get_supabase()
        response = (
            supabase.table("food_counters")
            .select("*")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        return jsonify({"success": True, "counters": response.data})
    except Exception as e:
        logger.error(f"Counters fetch error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/queue/<counter_id>")
@login_required
def queue_list(counter_id):
    """Get queue for a specific counter."""
    try:
        queue_service = QueueService()
        entries = queue_service.get_counter_queue(counter_id)
        return jsonify({"success": True, "entries": entries})
    except Exception as e:
        logger.error(f"Queue list error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/queue-stats")
@login_required
def queue_stats():
    """Get queue statistics."""
    try:
        queue_service = QueueService()
        stats = queue_service.get_queue_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        logger.error(f"Queue stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
