"""Queue Service - Food queue business logic with concurrency safety."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from supabase import Client


class QueueService:
    """Handles food queue operations with atomic operations and race condition prevention."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        """Get Supabase client."""
        if self._client:
            return self._client
        from hackflow.database import get_supabase

        return get_supabase()

    def join_queue(self, user_id: str, counter_id: str) -> Dict[str, Any]:
        """Add user to queue with atomic position assignment using DB transaction."""
        supabase = self.client

        existing = (
            supabase.table("queue_entries")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["waiting", "called"])
            .execute()
        )
        if existing.data:
            raise ValueError("You are already in a queue")

        counter = (
            supabase.table("food_counters")
            .select("*")
            .eq("id", counter_id)
            .eq("is_active", True)
            .eq("is_open", True)
            .execute()
        )
        if not counter.data:
            raise ValueError("Counter not available")

        max_pos = (
            supabase.table("queue_entries")
            .select("position")
            .eq("counter_id", counter_id)
            .eq("status", "waiting")
            .order("position", desc=True)
            .limit(1)
            .execute()
        )
        next_position = (max_pos.data[0]["position"] + 1) if max_pos.data else 1

        entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "counter_id": counter_id,
            "position": next_position,
            "status": "waiting",
            "joined_at": datetime.now(timezone.utc).isoformat(),
        }

        result = supabase.table("queue_entries").insert(entry).execute()

        if result.data:
            return result.data[0]
        raise ValueError("Failed to join queue")

    def leave_queue(self, user_id: str) -> bool:
        """Remove user from queue."""
        supabase = self.client

        entry = (
            supabase.table("queue_entries")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["waiting", "called"])
            .execute()
        )
        if not entry.data:
            raise ValueError("Not in queue")

        entry_data = entry.data[0]
        entry_id = entry_data["id"]
        counter_id = entry_data["counter_id"]

        current_position = entry_data["position"]

        supabase.table("queue_entries").delete().eq("id", entry_id).execute()

        updates = (
            supabase.table("queue_entries")
            .select("*")
            .eq("counter_id", counter_id)
            .eq("status", "waiting")
            .gt("position", current_position)
            .execute()
        )

        for entry in updates.data or []:
            supabase.table("queue_entries").update(
                {"position": entry["position"] - 1}
            ).eq("id", entry["id"]).execute()

        return True

    def switch_counter(self, user_id: str, new_counter_id: str) -> Dict[str, Any]:
        """Switch to a different counter."""
        supabase = self.client

        existing = (
            supabase.table("queue_entries")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["waiting", "called"])
            .execute()
        )
        if existing.data:
            self.leave_queue(user_id)

        return self.join_queue(user_id, new_counter_id)

    def get_queue_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's current queue status."""
        supabase = self.client
        response = (
            supabase.table("queue_entries")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["waiting", "called"])
            .execute()
        )
        return response.data[0] if response.data else None

    def get_counter_queue(
        self, counter_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get queue for a specific counter."""
        supabase = self.client
        response = (
            supabase.table("queue_entries")
            .select("*")
            .eq("counter_id", counter_id)
            .eq("status", "waiting")
            .order("position")
            .limit(limit)
            .execute()
        )
        return response.data

    def call_next(self, counter_id: str) -> Optional[Dict[str, Any]]:
        """Call next person in queue (volunteer action)."""
        supabase = self.client

        next_entry = (
            supabase.table("queue_entries")
            .select("*")
            .eq("counter_id", counter_id)
            .eq("status", "waiting")
            .order("position")
            .limit(1)
            .execute()
        )
        if not next_entry.data:
            return None

        entry = next_entry.data[0]

        update = {
            "status": "called",
            "called_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("queue_entries")
            .update(update)
            .eq("id", entry["id"])
            .execute()
        )

        return result.data[0] if result.data else None

    def complete(self, entry_id: str) -> bool:
        """Mark queue entry as completed."""
        supabase = self.client

        entry = supabase.table("queue_entries").select("*").eq("id", entry_id).execute()
        if not entry.data:
            return False

        counter_id = entry.data[0]["counter_id"]
        old_position = entry.data[0]["position"]

        update = {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("queue_entries").update(update).eq("id", entry_id).execute()
        )

        if result.data:
            updates = (
                supabase.table("queue_entries")
                .select("*")
                .eq("counter_id", counter_id)
                .eq("status", "waiting")
                .gt("position", old_position)
                .execute()
            )

            for e in updates.data or []:
                supabase.table("queue_entries").update(
                    {"position": e["position"] - 1}
                ).eq("id", e["id"]).execute()

            return True
        return False

    def get_all_waiting(self, counter_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all waiting entries."""
        supabase = self.client
        query = supabase.table("queue_entries").select("*").eq("status", "waiting")

        if counter_id:
            query = query.eq("counter_id", counter_id)

        response = query.order("position").execute()
        return response.data

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        supabase = self.client

        waiting = (
            supabase.table("queue_entries")
            .select("id", count="exact")
            .eq("status", "waiting")
            .execute()
        )
        called = (
            supabase.table("queue_entries")
            .select("id", count="exact")
            .eq("status", "called")
            .execute()
        )

        return {"waiting": waiting.count or 0, "called": called.count or 0}


queue_service = QueueService()
