"""Integration tests for deployment configuration.

These tests ensure that the application is correctly configured for
deployment on Render and other production environments.
"""

import subprocess
from pathlib import Path

import pytest
import yaml

from src.pybackstock.app import app


@pytest.mark.integration
def test_render_yaml_exists() -> None:
    """Test that render.yaml exists in the project root."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    assert render_yaml_path.exists(), "render.yaml file not found in project root"


@pytest.mark.integration
def test_render_yaml_valid() -> None:
    """Test that render.yaml is valid YAML."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)
    assert config is not None, "render.yaml is empty or invalid"
    assert "services" in config, "render.yaml missing 'services' key"


@pytest.mark.integration
def test_gunicorn_binding_configuration() -> None:
    """Test that Gunicorn is configured to bind to 0.0.0.0:$PORT.

    This is critical for Render deployment. Without binding to 0.0.0.0,
    the application will only be accessible within the container and
    will return 404 errors from external requests.
    """
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    start_command = web_service.get("startCommand", "")
    assert start_command, "startCommand is missing in render.yaml web service"

    # Verify Gunicorn is being used
    assert "gunicorn" in start_command, "startCommand does not use Gunicorn"

    # Verify correct binding to all interfaces (0.0.0.0) and PORT env var
    assert "--bind" in start_command, "Gunicorn startCommand missing --bind flag"
    assert "0.0.0.0" in start_command, "Gunicorn not binding to 0.0.0.0 (all interfaces)"
    assert "$PORT" in start_command or "${PORT}" in start_command, "Gunicorn not using $PORT environment variable"


@pytest.mark.integration
def test_gunicorn_app_path() -> None:
    """Test that Gunicorn startCommand references the correct app module."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    start_command = web_service.get("startCommand", "")

    # Verify the correct app module path
    assert "src.pybackstock.app:app" in start_command, (
        "Gunicorn startCommand does not reference correct app path 'src.pybackstock.app:app'"
    )


@pytest.mark.integration
def test_health_check_path_configured() -> None:
    """Test that health check path is configured for Render."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    health_check_path = web_service.get("healthCheckPath")
    assert health_check_path is not None, "healthCheckPath is not configured"
    assert health_check_path == "/", "healthCheckPath should be '/'"


@pytest.mark.integration
def test_production_config_in_render() -> None:
    """Test that Render is configured to use ProductionConfig."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    env_vars = web_service.get("envVars", [])
    app_settings = next((e for e in env_vars if e.get("key") == "APP_SETTINGS"), None)

    assert app_settings is not None, "APP_SETTINGS environment variable not found"
    assert app_settings.get("value") == "src.pybackstock.config.ProductionConfig", (
        "APP_SETTINGS should use ProductionConfig for production deployment"
    )


@pytest.mark.integration
def test_database_connection_configured() -> None:
    """Test that database connection is properly configured in render.yaml."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    env_vars = web_service.get("envVars", [])
    database_url = next((e for e in env_vars if e.get("key") == "DATABASE_URL"), None)

    assert database_url is not None, "DATABASE_URL environment variable not found"
    assert "fromDatabase" in database_url, "DATABASE_URL should reference database service"


@pytest.mark.integration
def test_gunicorn_installed() -> None:
    """Test that Gunicorn is listed as a project dependency."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path) as f:
        content = f.read()

    assert "gunicorn" in content.lower(), "Gunicorn not found in project dependencies"


@pytest.mark.integration
def test_gunicorn_can_import_app() -> None:
    """Test that Gunicorn can import the Flask app module.

    This simulates what happens when Gunicorn tries to load the application.
    """
    # The import at the top-level already validates that the module can be imported
    assert app is not None, "Failed to import Flask app"
    assert hasattr(app, "config"), "Imported object is not a Flask app"


@pytest.mark.integration
def test_gunicorn_syntax() -> None:
    """Test that the Gunicorn command in render.yaml has valid syntax."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    start_command = web_service.get("startCommand", "")

    # Test that gunicorn command can be validated
    # The command should follow pattern: gunicorn 'module:app' --bind host:port
    parts = start_command.split()

    # Find gunicorn in the command
    gunicorn_idx = None
    for i, part in enumerate(parts):
        if "gunicorn" in part:
            gunicorn_idx = i
            break

    assert gunicorn_idx is not None, "gunicorn not found in startCommand"

    # Verify app path comes after gunicorn (before --bind)
    app_path_found = False
    bind_idx = None
    for i in range(gunicorn_idx + 1, len(parts)):
        if "--bind" in parts[i]:
            bind_idx = i
            break
        if "src.pybackstock.app:app" in parts[i]:
            app_path_found = True

    assert app_path_found, "App path 'src.pybackstock.app:app' not found after gunicorn command"
    assert bind_idx is not None, "--bind flag not found in gunicorn command"

    # Verify bind address comes after --bind flag
    if bind_idx is not None and bind_idx + 1 < len(parts):
        bind_address = parts[bind_idx + 1]
        assert "0.0.0.0" in bind_address, "Bind address should include 0.0.0.0"
        assert "$PORT" in bind_address or "${PORT}" in bind_address, "Bind address should include $PORT variable"


@pytest.mark.integration
def test_render_runtime_python() -> None:
    """Test that Python runtime is correctly configured."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    assert web_service.get("runtime") == "python", "Runtime should be set to 'python'"

    env_vars = web_service.get("envVars", [])
    python_version = next((e for e in env_vars if e.get("key") == "PYTHON_VERSION"), None)

    assert python_version is not None, "PYTHON_VERSION not configured"
    version_value = python_version.get("value", "")
    assert version_value.startswith("3.11"), "Python version should be 3.11.x"


@pytest.mark.integration
def test_index_route_responds() -> None:
    """Test that the index route responds correctly.

    This validates that the health check endpoint configured in render.yaml
    will work correctly.
    """
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200, "Index route should return 200 OK"


@pytest.mark.integration
def test_gunicorn_version_check() -> None:
    """Test that Gunicorn can be executed and shows version info."""
    try:
        # Run gunicorn --version to verify it's installed and executable
        result = subprocess.run(
            ["uv", "run", "gunicorn", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        # Check that gunicorn runs (exit code 0) and returns version info
        assert result.returncode == 0, f"Gunicorn version check failed: {result.stderr}"
        assert "gunicorn" in result.stdout.lower(), "Gunicorn version output unexpected"
    except FileNotFoundError:
        pytest.skip("uv command not available in test environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Gunicorn version check timed out")


@pytest.mark.integration
def test_config_handles_missing_database_url() -> None:
    """Test that Config class handles missing DATABASE_URL gracefully.

    This prevents the SQLAlchemy ArgumentError that caused the "Not found"
    issue on Render when DATABASE_URL was not properly configured.
    """
    import importlib
    import os
    import sys

    # Save original DATABASE_URL if it exists
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Remove DATABASE_URL to simulate missing configuration
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Remove config module from cache to force re-import
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]

        # Import config module fresh
        config_module = importlib.import_module("src.pybackstock.config")
        config_class = config_module.Config

        # Verify that SQLALCHEMY_DATABASE_URI is set to a valid value
        assert hasattr(config_class, "SQLALCHEMY_DATABASE_URI"), "SQLALCHEMY_DATABASE_URI not set"
        assert config_class.SQLALCHEMY_DATABASE_URI, "SQLALCHEMY_DATABASE_URI is empty"
        assert config_class.SQLALCHEMY_DATABASE_URI != "", "SQLALCHEMY_DATABASE_URI should not be empty string"

        # Verify it's using SQLite fallback
        assert "sqlite:///" in config_class.SQLALCHEMY_DATABASE_URI, (
            "Config should fallback to SQLite when DATABASE_URL is not set"
        )
    finally:
        # Restore original DATABASE_URL
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Clean up module cache
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]


@pytest.mark.integration
def test_config_handles_empty_database_url() -> None:
    """Test that Config class handles empty DATABASE_URL string gracefully.

    Empty string DATABASE_URL previously caused SQLAlchemy to fail with:
    'Could not parse SQLAlchemy URL from given URL string'
    """
    import importlib
    import os
    import sys

    # Save original DATABASE_URL if it exists
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Set DATABASE_URL to empty string
        os.environ["DATABASE_URL"] = ""

        # Remove config module from cache to force re-import
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]

        # Import config module fresh
        config_module = importlib.import_module("src.pybackstock.config")
        config_class = config_module.Config

        # Verify that SQLALCHEMY_DATABASE_URI is set to a valid value
        assert hasattr(config_class, "SQLALCHEMY_DATABASE_URI"), "SQLALCHEMY_DATABASE_URI not set"
        assert config_class.SQLALCHEMY_DATABASE_URI, "SQLALCHEMY_DATABASE_URI is empty"
        assert config_class.SQLALCHEMY_DATABASE_URI != "", "SQLALCHEMY_DATABASE_URI should not be empty string"

        # Verify it's using SQLite fallback (since empty string is treated as None)
        assert "sqlite:///" in config_class.SQLALCHEMY_DATABASE_URI, (
            "Config should fallback to SQLite when DATABASE_URL is empty string"
        )
    finally:
        # Restore original DATABASE_URL
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Clean up module cache
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]


@pytest.mark.integration
def test_gunicorn_boots_without_database_url() -> None:
    """Test that Gunicorn can successfully boot the app without DATABASE_URL.

    This is critical for preventing deployment failures. The application should
    start even if DATABASE_URL is not configured, using the SQLite fallback.
    """
    import os

    # Save original DATABASE_URL if it exists
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Remove DATABASE_URL to simulate missing configuration
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Try to boot Gunicorn with a very short timeout
        # We just want to verify it starts without crashing, not run it
        result = subprocess.run(
            [
                "uv",
                "run",
                "gunicorn",
                "src.pybackstock.app:app",
                "--bind",
                "127.0.0.1:9999",
                "--timeout",
                "1",
                "--preload",  # Load app before forking to catch import errors
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env={**os.environ, "DATABASE_URL": ""},  # Explicitly set empty DATABASE_URL
        )

        # Check that Gunicorn didn't fail with import/startup errors
        # It's okay if it exits due to timeout, but not due to import errors
        assert "Could not parse SQLAlchemy URL" not in result.stderr, (
            "Gunicorn failed with SQLAlchemy URL parsing error. Config should handle missing DATABASE_URL gracefully."
        )
        assert "ArgumentError" not in result.stderr, (
            "Gunicorn failed with ArgumentError. Check DATABASE_URL handling in config."
        )
        assert "Exception in worker process" not in result.stderr or "Worker failed to boot" not in result.stderr, (
            "Gunicorn worker failed to boot. Application should start without DATABASE_URL."
        )
    except subprocess.TimeoutExpired:
        # Timeout is acceptable - we just want to verify it starts
        pass
    except FileNotFoundError:
        pytest.skip("uv command not available in test environment")
    finally:
        # Restore original DATABASE_URL
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


@pytest.mark.integration
def test_app_can_import_without_database_url() -> None:
    """Test that the app module can be imported without DATABASE_URL.

    This verifies that importing the app doesn't immediately crash when
    DATABASE_URL is missing.
    """
    import importlib
    import os
    import sys

    # Save original DATABASE_URL if it exists
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Remove DATABASE_URL
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Remove the module from cache to force re-import
        if "src.pybackstock.app" in sys.modules:
            del sys.modules["src.pybackstock.app"]
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]

        # Try to import the app - this should not crash
        try:
            app_module = importlib.import_module("src.pybackstock.app")
            assert app_module is not None, "Failed to import app module"
            assert hasattr(app_module, "app"), "App module doesn't have 'app' attribute"
        except Exception as e:
            if "Could not parse SQLAlchemy URL" in str(e):
                pytest.fail(
                    "App import failed with SQLAlchemy URL error. Config must handle missing DATABASE_URL gracefully."
                )
            raise
    finally:
        # Restore original DATABASE_URL
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Clean up module cache
        if "src.pybackstock.app" in sys.modules:
            del sys.modules["src.pybackstock.app"]
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]


@pytest.mark.integration
def test_config_postgres_url_conversion() -> None:
    """Test that Config properly converts postgres:// to postgresql:// URLs."""
    import importlib
    import os
    import sys

    # Save original DATABASE_URL if it exists
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Test old-style postgres:// URL
        os.environ["DATABASE_URL"] = "postgres://user:pass@host:5432/db"

        # Remove config module from cache to force re-import with new DATABASE_URL
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]

        # Import config module fresh
        config_module = importlib.import_module("src.pybackstock.config")
        config_class = config_module.Config

        # Verify conversion to postgresql://
        assert config_class.SQLALCHEMY_DATABASE_URI == "postgresql://user:pass@host:5432/db", (
            "Config should convert postgres:// to postgresql://"
        )
    finally:
        # Restore original DATABASE_URL
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Clean up module cache
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]
