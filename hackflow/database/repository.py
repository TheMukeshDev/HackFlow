"""Base Repository for database operations."""

from typing import Optional, List, Dict, Any
from supabase import Client
from flask import current_app


class BaseRepository:
    """Base repository with common database operations."""

    def __init__(self, table_name: str, client: Optional[Client] = None):
        self.table_name = table_name
        self._client = client

    @property
    def client(self) -> Client:
        """Get Supabase client."""
        if self._client:
            return self._client
        from hackflow.database import get_supabase

        return get_supabase()

    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID."""
        response = self.client.table(self.table_name).select("*").eq("id", id).execute()
        return response.data[0] if response.data else None

    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all records with optional filters."""
        query = self.client.table(self.table_name).select("*")

        if filters:
            for key, value in filters.items():
                if value is not None:
                    query = query.eq(key, value)

        if order_by:
            query = query.order(order_by, desc=not ascending)

        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        response = query.execute()
        return response.data

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        response = self.client.table(self.table_name).insert(data).execute()
        if response.data:
            return response.data[0]
        raise Exception(f"Failed to create record in {self.table_name}")

    def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by ID."""
        response = (
            self.client.table(self.table_name).update(data).eq("id", id).execute()
        )
        return response.data[0] if response.data else None

    def delete(self, id: str) -> bool:
        """Delete a record by ID."""
        response = self.client.table(self.table_name).delete().eq("id", id).execute()
        return len(response.data) > 0

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        query = self.client.table(self.table_name).select("*", count="exact")

        if filters:
            for key, value in filters.items():
                if value is not None:
                    query = query.eq(key, value)

        response = query.execute()
        return response.count or 0

    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if a record exists."""
        return self.count(filters) > 0

    def get_one_by(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get a single record by filters."""
        records = self.get_all(filters=filters, limit=1)
        return records[0] if records else None
