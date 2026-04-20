"""Authentication Service - Handles all auth operations."""

import secrets
from typing import Optional, List
from flask import current_app
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


class AuthService:
    """Handles authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        rounds = current_app.config.get("BCRYPT_LOG_ROUNDS", 12)
        return bcrypt.generate_password_hash(password, rounds=rounds).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        if not password or not password_hash:
            return False
        return bcrypt.check_password_hash(password_hash, password)

    @staticmethod
    def create_session_token(user_id: str, role: str) -> str:
        """Create a secure session token."""
        raw_token = f"{user_id}:{role}:{secrets.token_hex(16)}"
        return bcrypt.generate_password_hash(raw_token, rounds=4).decode("utf-8")

    @staticmethod
    def validate_session_token(token: str, user_id: str, role: str) -> bool:
        """Validate a session token."""
        # TODO: Implement proper token validation
        return bool(token and user_id and role)


class Role:
    """User roles with constants and helper methods."""

    PARTICIPANT = "participant"
    PENDING_VOLUNTEER = "pending_volunteer"
    VOLUNTEER = "volunteer"
    ADMIN = "admin"

    ALL: List[str] = [PARTICIPANT, PENDING_VOLUNTEER, VOLUNTEER, ADMIN]

    @classmethod
    def is_valid(cls, role: str) -> bool:
        """Check if role is valid."""
        return role in cls.ALL

    @classmethod
    def can_access_volunteer(cls, role: Optional[str]) -> bool:
        """Check if role can access volunteer panel."""
        return role in (cls.VOLUNTEER, cls.ADMIN)

    @classmethod
    def can_access_user(cls, role: Optional[str]) -> bool:
        """Check if role can access user panel."""
        return True


class Permission:
    """Permission checks for role-based access."""

    @staticmethod
    def can_manage_queue(role: str) -> bool:
        """Check if role can manage food queue."""
        return role in (Role.VOLUNTEER, Role.ADMIN)

    @staticmethod
    def can_manage_requests(role: str) -> bool:
        """Check if role can manage help requests."""
        return role in (Role.VOLUNTEER, Role.ADMIN)

    @staticmethod
    def can_broadcast(role: str) -> bool:
        """Check if role can send broadcasts."""
        return role in (Role.VOLUNTEER, Role.ADMIN)

    @staticmethod
    def can_manage_users(role: str) -> bool:
        """Check if role can manage users."""
        return role == Role.ADMIN
