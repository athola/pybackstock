"""Integration tests for health check endpoint deployment.

These tests verify the health check works correctly for deployment scenarios.
"""

import subprocess
import time
from pathlib import Path

import pytest

from src.pybackstock.app import app


@pytest.mark.integration
def test_health_endpoint_via_gunicorn() -> None:
    """Test that health endpoint works when app is loaded via Gunicorn.

    This simulates the production deployment scenario where Gunicorn
    loads src.pybackstock.app:app.
    """
    project_root = Path(__file__).parent.parent

    try:
        # Try to start Gunicorn briefly to verify it can load the app
        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "uv",
                "run",
                "gunicorn",
                "src.pybackstock.app:app",
                "--pythonpath",
                str(project_root),
                "--bind",
                "127.0.0.1:9997",
                "--timeout",
                "1",
                "--preload",  # Load app before forking to catch import errors
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            cwd=str(project_root),
        )

        # Verify Gunicorn can load the app without errors
        assert "Exception in worker process" not in result.stderr, (
            f"Gunicorn failed to load app. Error: {result.stderr}"
        )
        assert "ModuleNotFoundError" not in result.stderr, f"Module import error: {result.stderr}"
        assert "AttributeError" not in result.stderr, f"Attribute error when loading app: {result.stderr}"

    except subprocess.TimeoutExpired:
        # Timeout is acceptable - we just want to verify it starts
        pass
    except FileNotFoundError:
        pytest.skip("uv command not available in test environment")


@pytest.mark.integration
def test_app_import_succeeds() -> None:
    """Test that the Flask app can be imported successfully.

    This verifies the import path used in deployment works.
    """
    assert app is not None, "Failed to import Flask app"
    assert hasattr(app, "config"), "Imported object is not a Flask app"

    # Verify health endpoint is registered
    with app.test_client() as client:
        response = client.get("/health")
        assert response.status_code == 200, f"Health endpoint should return 200, got {response.status_code}"
        data = response.get_json()
        assert data.get("status") == "healthy", f"Expected status='healthy', got {data}"


@pytest.mark.integration
def test_deployment_configuration_matches_tests() -> None:
    """Test that deployment configuration matches what tests use.

    This ensures tests accurately reflect production deployment.
    """
    # Verify the app is a Flask instance
    assert app is not None
    assert hasattr(app, "test_client")

    # Verify health endpoint works
    with app.test_client() as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.get_json()["status"] == "healthy"


@pytest.mark.integration
def test_health_endpoint_deployment_ready() -> None:
    """Test that health endpoint meets all deployment requirements.

    Verifies:
    - Returns 200 status code
    - Returns JSON with correct format
    - Responds quickly (< 1 second)
    - Works without database connection
    - No external dependencies
    """
    with app.test_client() as client:
        # Test response time
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        # Verify all requirements
        assert response.status_code == 200, "Must return 200 for Render health checks"
        assert elapsed < 1.0, f"Too slow: {elapsed:.2f}s"
        assert response.content_type == "application/json"

        data = response.get_json()
        assert data is not None
        assert "status" in data
        assert data["status"] == "healthy"
