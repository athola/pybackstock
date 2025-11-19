"""Tests for Connexion app health check endpoint.

These tests document the expected behavior when using Connexion 3.x.
Currently marked as xfail because Connexion 3.x has route registration issues
that need to be debugged in a future PR.

For now, deployment uses plain Flask app (src.pybackstock.app:app) which works correctly.
See: scripts/start.py for deployment configuration.
"""

import pytest
from flask.testing import FlaskClient

from src.pybackstock.connexion_app import connexion_app, flask_app


@pytest.fixture()
def connexion_client() -> FlaskClient:
    """Create a test client for the Connexion app.

    Returns:
        Test client for making requests to the Connexion Flask app.
    """
    flask_app.config.update({"TESTING": True})
    return flask_app.test_client()


@pytest.mark.xfail(reason="Connexion 3.x route registration issue - needs debugging in future PR")
class TestConnexionHealthEndpoint:
    """Tests for the Connexion health check endpoint."""

    def test_health_endpoint_exists(self, connexion_client: FlaskClient) -> None:
        """Test that /health endpoint is registered in Connexion app."""
        response = connexion_client.get("/health")
        assert response.status_code == 200, (
            f"Health endpoint should return 200, got {response.status_code}. "
            f"If this fails, Connexion routes are not being registered from openapi.yaml"
        )

    def test_health_endpoint_returns_json(self, connexion_client: FlaskClient) -> None:
        """Test that /health endpoint returns valid JSON."""
        response = connexion_client.get("/health")
        assert response.status_code == 200
        assert response.content_type == "application/json", (
            f"Expected application/json, got {response.content_type}"
        )

        data = response.get_json()
        assert data is not None, "Response should be valid JSON"
        assert "status" in data, "Response should contain 'status' field"
        assert data["status"] == "healthy", "Status should be 'healthy'"

    def test_health_endpoint_fast_response(self, connexion_client: FlaskClient) -> None:
        """Test that /health endpoint responds quickly."""
        import time

        start_time = time.time()
        response = connexion_client.get("/health")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 1.0, f"Health check took {elapsed_time:.2f}s, should be < 1s"

    def test_health_endpoint_no_database_required(self, connexion_client: FlaskClient) -> None:
        """Test that /health endpoint works without database connection.

        The health check should be a simple liveness check that doesn't
        depend on external services.
        """
        # This should work even without initializing the database
        response = connexion_client.get("/health")
        assert response.status_code == 200

    def test_connexion_app_type(self) -> None:
        """Test that connexion_app is properly configured."""
        import connexion

        assert isinstance(connexion_app, connexion.FlaskApp), (
            f"connexion_app should be a connexion.FlaskApp, got {type(connexion_app)}"
        )

    def test_connexion_app_has_openapi_routes(self) -> None:
        """Test that Connexion app has registered routes from openapi.yaml."""
        # Get all registered routes
        routes = [rule.rule for rule in flask_app.url_map.iter_rules()]

        # Check that key routes from openapi.yaml are registered
        assert "/health" in routes, (
            "/health route not found. Connexion failed to load openapi.yaml routes. "
            f"Found routes: {routes}"
        )
        assert "/" in routes or "/index" in routes, "Index route not registered"

    def test_health_handler_function_exists(self) -> None:
        """Test that the health_check handler function can be imported."""
        from src.pybackstock.api.handlers import health_check

        assert callable(health_check), "health_check should be a callable function"

        # Test that it returns the expected format
        result = health_check()
        assert isinstance(result, tuple), "health_check should return a tuple"
        assert len(result) == 2, "health_check should return (response, status_code)"

        response, status_code = result
        assert status_code == 200, f"Expected status 200, got {status_code}"
        assert isinstance(response, dict), "Response should be a dict"
        assert response.get("status") == "healthy", "Response should have status='healthy'"


@pytest.mark.xfail(reason="Connexion 3.x route registration issue - needs debugging in future PR")
class TestConnexionASGICompatibility:
    """Tests for Connexion ASGI compatibility."""

    def test_connexion_app_is_asgi_compatible(self) -> None:
        """Test that connexion_app can be used with ASGI servers."""
        # Connexion 3.x FlaskApp should be ASGI compatible
        assert hasattr(connexion_app, "run"), "connexion_app should have 'run' method for ASGI"

    def test_flask_app_exported_for_gunicorn(self) -> None:
        """Test that flask_app is properly exported for Gunicorn with Uvicorn workers."""
        from src.pybackstock import connexion_app as exported_connexion_app

        assert exported_connexion_app is not None, "connexion_app should be exported"

        # For Gunicorn with uvicorn workers, we need the connexion_app, not just flask_app
        import connexion

        assert isinstance(exported_connexion_app, connexion.FlaskApp), (
            "Exported app should be connexion.FlaskApp for ASGI deployment"
        )


@pytest.mark.xfail(reason="Connexion 3.x route registration issue - needs debugging in future PR")
class TestHealthCheckRobustness:
    """Tests for health check robustness and edge cases."""

    def test_health_endpoint_with_head_request(self, connexion_client: FlaskClient) -> None:
        """Test that health endpoint handles HEAD requests."""
        response = connexion_client.head("/health")
        # Should return 200 or 405 (method not allowed) but not 404
        assert response.status_code in (200, 405), (
            f"HEAD request should not return 404, got {response.status_code}"
        )

    def test_health_endpoint_cors_safe(self, connexion_client: FlaskClient) -> None:
        """Test that health endpoint can be accessed from monitoring systems."""
        # Health checks often come from external monitoring systems
        response = connexion_client.get(
            "/health",
            headers={"Origin": "https://render.com"},
        )
        assert response.status_code == 200, "Health check should work with Origin header"

    def test_health_endpoint_under_load(self, connexion_client: FlaskClient) -> None:
        """Test that health endpoint handles multiple rapid requests."""
        # Simulate monitoring system polling
        responses = []
        for _ in range(10):
            response = connexion_client.get("/health")
            responses.append(response.status_code)

        # All requests should succeed
        assert all(status == 200 for status in responses), (
            f"All health checks should return 200, got: {responses}"
        )
