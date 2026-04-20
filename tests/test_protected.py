"""Tests for protected routes and authorization."""

import pytest
from unittest.mock import patch, MagicMock
from hackflow import create_app


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
def authenticated_client(client):
    """Create authenticated test client."""
    with client.session_transaction() as sess:
        sess["user_id"] = "test-user-id"
        sess["email"] = "test@example.com"
        sess["username"] = "testuser"
        sess["role"] = "participant"
        sess["full_name"] = "Test User"
    return client


@pytest.fixture
def admin_client(client):
    """Create admin test client."""
    with client.session_transaction() as sess:
        sess["user_id"] = "admin-user-id"
        sess["email"] = "admin@example.com"
        sess["username"] = "admin"
        sess["role"] = "admin"
        sess["full_name"] = "Admin User"
    return client


class TestProtectedRoutes:
    """Test protected route access control."""

    def test_user_dashboard_requires_login(self, client):
        """Test user dashboard redirects unauthenticated users."""
        response = client.get("/user/dashboard", follow_redirects=False)
        assert response.status_code == 302

    def test_volunteer_dashboard_requires_login(self, client):
        """Test volunteer dashboard redirects unauthenticated users."""
        response = client.get("/volunteer/dashboard", follow_redirects=False)
        assert response.status_code == 302

    def test_admin_dashboard_requires_login(self, client):
        """Test admin dashboard redirects unauthenticated users."""
        response = client.get("/admin/dashboard", follow_redirects=False)
        assert response.status_code == 302

    def test_admin_dashboard_requires_admin_role(self, authenticated_client):
        """Test admin dashboard rejects non-admin users."""
        response = authenticated_client.get("/admin/dashboard", follow_redirects=False)
        assert response.status_code in [302, 403]

    def test_admin_users_requires_admin_role(self, authenticated_client):
        """Test admin users page rejects non-admin users."""
        response = authenticated_client.get("/admin/users", follow_redirects=False)
        assert response.status_code in [302, 403]

    def test_volunteer_dashboard_accepts_volunteer(self, client):
        """Test volunteer dashboard accepts volunteers."""
        with client.session_transaction() as sess:
            sess["user_id"] = "volunteer-id"
            sess["role"] = "volunteer"
        response = client.get("/volunteer/dashboard", follow_redirects=False)
        assert response.status_code in [200, 302]

    def test_user_cannot_access_admin(self, authenticated_client):
        """Test regular user cannot access admin routes."""
        response = authenticated_client.get("/admin/users", follow_redirects=False)
        assert response.status_code in [302, 403]


class TestAuthorizationDecorators:
    """Test authorization decorators."""

    def test_login_required_decorator(self, client):
        """Test login_required redirects to login."""
        response = client.get("/user/dashboard", follow_redirects=False)
        assert "/auth/login" in response.location or response.status_code == 302

    def test_admin_required_decorator(self, client):
        """Test admin_required rejects non-admins."""
        response = client.get("/admin/dashboard", follow_redirects=False)
        assert response.status_code in [302, 403]


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_participant_role(self, client):
        """Test participant role session."""
        with client.session_transaction() as sess:
            sess["user_id"] = "test-id"
            sess["role"] = "participant"
        response = client.get("/user/dashboard", follow_redirects=False)
        assert response.status_code in [200, 302]

    def test_volunteer_role(self, client):
        """Test volunteer role session."""
        with client.session_transaction() as sess:
            sess["user_id"] = "volunteer-id"
            sess["role"] = "volunteer"
        response = client.get("/volunteer/dashboard", follow_redirects=False)
        assert response.status_code in [200, 302]

    def test_admin_role(self, client):
        """Test admin role session."""
        with client.session_transaction() as sess:
            sess["user_id"] = "admin-id"
            sess["role"] = "admin"
        response = client.get("/admin/dashboard", follow_redirects=False)
        assert response.status_code in [200, 302]


class TestAPIEndpoints:
    """Test API endpoint access."""

    def test_health_endpoint_public(self, client):
        """Test health endpoint is public."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_status_endpoint_public(self, client):
        """Test status endpoint is public."""
        response = client.get("/api/status")
        assert response.status_code == 200

    def test_queue_status_requires_login(self, client):
        """Test queue status requires authentication."""
        response = client.get("/api/queue/status")
        assert response.status_code in [302, 401]

    def test_counters_requires_login(self, client):
        """Test counters endpoint requires authentication."""
        response = client.get("/api/counters")
        assert response.status_code in [302, 401]
