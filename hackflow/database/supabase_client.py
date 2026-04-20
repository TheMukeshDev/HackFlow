"""Supabase Client Module."""

from supabase import create_client, Client
from flask import current_app, g
from typing import Optional


class SupabaseManager:
    """Manages Supabase client connections."""

    def __init__(self, app=None):
        self.app = app
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None

    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        app.extensions["supabase"] = self

    def get_client(self) -> Client:
        """Get the anon client for public operations."""
        if self._client is None:
            self._client = create_client(
                current_app.config["SUPABASE_URL"], current_app.config["SUPABASE_KEY"]
            )
        return self._client

    def get_service_client(self) -> Client:
        """Get the service client for admin operations."""
        if self._service_client is None:
            self._service_client = create_client(
                current_app.config["SUPABASE_URL"],
                current_app.config["SUPABASE_SERVICE_KEY"],
            )
        return self._service_client

    def get_user_client(self) -> Client:
        """Get appropriate client based on user role."""
        user = g.get("user")
        if user and user.get("role") in ("volunteer", "admin"):
            return self.get_service_client()
        return self.get_client()


# Global instance
supabase_manager = SupabaseManager()


def get_supabase() -> Client:
    """Get Supabase client for current context."""
    return supabase_manager.get_client()


def get_supabase_service() -> Client:
    """Get Supabase service client for admin operations."""
    return supabase_manager.get_service_client()
