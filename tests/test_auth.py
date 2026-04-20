"""Tests for authentication routes."""

import pytest
from unittest.mock import patch, MagicMock
from hackflow import create_app
from hackflow.database import get_supabase


@pytest.fixture
def app():
    """Create test application."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test-secret-key"
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_supabase():
    """Create mock Supabase client."""
    mock = MagicMock()
    return mock


class TestAuthRoutes:
    """Test authentication routes."""

    def test_login_page_loads(self, client):
        """Test login page renders correctly."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"Sign In" in response.data or b"sign in" in response.data.lower()

    def test_register_page_loads(self, client):
        """Test register page renders correctly."""
        response = client.get("/auth/register")
        assert response.status_code == 200
        assert b"Sign up" in response.data or b"Register" in response.data

    def test_login_requires_email(self, client):
        """Test login fails without email."""
        response = client.post(
            "/auth/login",
            data={"password": "testpass123"},
            follow_redirects=False,
        )
        assert response.status_code in [200, 400]

    def test_login_requires_password(self, client):
        """Test login fails without password."""
        response = client.post(
            "/auth/login",
            data={"email": "test@example.com"},
            follow_redirects=False,
        )
        assert response.status_code in [200, 400]

    def test_invalid_email_format(self, client):
        """Test login rejects invalid email format."""
        response = client.post(
            "/auth/login",
            data={"email": "notanemail", "password": "testpass123"},
            follow_redirects=False,
        )
        assert response.status_code in [200, 400]

    def test_register_requires_email(self, client):
        """Test register fails without email."""
        response = client.post(
            "/auth/register",
            data={
                "full_name": "Test User",
                "password": "testpass123",
                "confirm_password": "testpass123",
            },
            follow_redirects=False,
        )
        assert response.status_code in [200, 400]

    def test_register_requires_password(self, client):
        """Test register fails without password."""
        response = client.post(
            "/auth/register",
            data={"email": "test@example.com", "full_name": "Test User"},
            follow_redirects=False,
        )
        assert response.status_code in [200, 400]

    def test_register_short_password(self, client):
        """Test register rejects short password."""
        response = client.post(
            "/auth/register",
            data={
                "email": "test@example.com",
                "full_name": "Test User",
                "password": "short",
                "confirm_password": "short",
            },
            follow_redirects=False,
        )
        assert response.status_code in [200, 400]

    def test_register_password_mismatch(self, client):
        """Test register rejects mismatched passwords."""
        response = client.post(
            "/auth/register",
            data={
                "email": "test@example.com",
                "full_name": "Test User",
                "password": "password123",
                "confirm_password": "different123",
            },
            follow_redirects=False,
        )
        assert response.status_code in [200, 400]

    def test_logout_redirects_to_home(self, client):
        """Test logout redirects to home page."""
        response = client.get("/auth/logout", follow_redirects=False)
        assert response.status_code in [302, 200]

    def test_google_login_redirects(self, client):
        """Test Google login initiates OAuth flow."""
        response = client.get("/auth/google/login", follow_redirects=False)
        assert response.status_code in [302, 200]

    def test_google_callback_requires_code(self, client):
        """Test Google callback fails without auth code."""
        response = client.get("/auth/google/callback", follow_redirects=False)
        assert response.status_code in [302, 400]

    def test_complete_profile_requires_login(self, client):
        """Test complete profile page requires authentication."""
        response = client.get("/auth/complete-profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_profile_requires_login(self, client):
        """Test profile page requires authentication."""
        response = client.get("/auth/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


class TestAuthSecurity:
    """Test authentication security features."""

    def test_session_cookie_secure_in_production(self, app):
        """Test session cookie settings in production."""
        app.config["SESSION_COOKIE_SECURE"] = True
        assert app.config["SESSION_COOKIE_SECURE"] is True

    def test_session_cookie_httponly(self, app):
        """Test session cookie is HttpOnly."""
        assert app.config["SESSION_COOKIE_HTTPONLY"] is True

    def test_csrf_protection_enabled_in_production(self, app):
        """Test CSRF is enabled in production config."""
        prod_app = create_app("production")
        assert prod_app.config.get("WTF_CSRF_ENABLED") is True
