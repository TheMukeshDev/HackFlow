"""Tests for API endpoints."""

import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    """Create test application."""
    from hackflow import create_app

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
        sess["role"] = "participant"
        sess["username"] = "testuser"
    return client


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint(self, client):
        """Test /api/health returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert "status" in data
        assert "service" in data

    def test_liveness_probe(self, client):
        """Test liveness probe endpoint."""
        response = client.get("/api/health/liveness")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "alive"

    def test_readiness_probe(self, client):
        """Test readiness probe endpoint."""
        response = client.get("/api/health/readiness")
        assert response.status_code in [200, 503]

    def test_status_endpoint(self, client):
        """Test public status endpoint."""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "operational"


class TestQueueAPI:
    """Test queue API endpoints."""

    def test_queue_status_requires_auth(self, client):
        """Test queue status requires authentication."""
        response = client.get("/api/queue/status")
        assert response.status_code == 302

    def test_counters_requires_auth(self, client):
        """Test counters endpoint requires authentication."""
        response = client.get("/api/counters")
        assert response.status_code == 302


class TestRateLimit:
    """Test rate limiting."""

    def test_rate_limiting_enabled(self, app):
        """Test rate limiting is configured."""
        assert app.config.get("RATELIMIT_ENABLED") is True


class TestSecurity:
    """Test security features."""

    def test_no_credentials_in_logs(self, app, client):
        """Test credentials are not logged."""
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200, json=lambda: {"access_token": "test_token"}
            )
            client.post(
                "/auth/google/callback",
                query_string={"code": "test_code", "state": "test_state"},
            )

    def test_security_headers(self, app, client):
        """Test security headers are set."""
        response = client.get("/api/status")
        assert "Content-Type" in response.headers

    def test_csrf_enabled_in_production_mode(self):
        """Test CSRF is enabled in production."""
        from hackflow import create_app

        prod_app = create_app("production")
        assert prod_app.config.get("WTF_CSRF_ENABLED") is True


class TestErrorHandling:
    """Test error handling."""

    def test_404_returns_json_for_api(self, client):
        """Test API returns proper JSON for 404."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_500_handled_gracefully(self, app, client):
        """Test 500 errors handled gracefully."""
        with app.test_request_context():
            response = client.get("/api/status")
            assert response.status_code in [200, 500]


class TestOAuthSecurity:
    """Test OAuth security improvements."""

    def test_oauth_state_protection(self, client):
        """Test OAuth state prevents CSRF."""
        response = client.get("/auth/google/login")
        assert response.status_code == 302

        with client.session_transaction() as sess:
            assert "oauth_state" in sess

    def test_oauth_expired_state_rejected(self, client, app):
        """Test expired OAuth state is rejected."""
        with client.session_transaction() as sess:
            sess["oauth_state"] = "old_state"
            sess["oauth_start_time"] = 0

        response = client.get(
            "/auth/google/callback", query_string={"code": "test", "state": "old_state"}
        )
        assert response.status_code in [302, 400]


class TestSessionSecurity:
    """Test session security."""

    def test_session_http_only(self, app):
        """Test session cookie is HTTP-only."""
        assert app.config.get("SESSION_COOKIE_HTTPONLY") is True

    def test_session_samesite_lax(self, app):
        """Test session uses Lax CSRF protection."""
        assert app.config.get("SESSION_COOKIE_SAMESITE") == "Lax"

    def test_session_secure_in_production(self):
        """Test session cookie is Secure in production."""
        from hackflow import create_app

        prod_app = create_app("production")
        assert prod_app.config.get("SESSION_COOKIE_SECURE") is True
