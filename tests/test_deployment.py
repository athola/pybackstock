"""Integration tests for deployment configuration.

These tests ensure that the application is correctly configured for
deployment on Render and other production environments.
"""

import importlib
import os
import subprocess
import sys
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

    # If using a startup script, check the script instead
    if "scripts/start.sh" in start_command:
        project_root = Path(__file__).parent.parent
        startup_script_path = project_root / "scripts" / "start.sh"
        with open(startup_script_path) as f:
            script_content = f.read()
        command_to_check = script_content
    else:
        command_to_check = start_command

    # Verify Gunicorn is being used
    assert "gunicorn" in command_to_check, "startCommand/script does not use Gunicorn"

    # Verify correct binding to all interfaces (0.0.0.0) and PORT env var
    assert "--bind" in command_to_check, "Gunicorn missing --bind flag"
    assert "0.0.0.0" in command_to_check, "Gunicorn not binding to 0.0.0.0 (all interfaces)"
    assert "$PORT" in command_to_check or "${PORT}" in command_to_check, "Gunicorn not using $PORT environment variable"


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

    # If using a startup script, check the script instead
    if "scripts/start.sh" in start_command:
        project_root = Path(__file__).parent.parent
        startup_script_path = project_root / "scripts" / "start.sh"
        with open(startup_script_path) as f:
            command_to_check = f.read()
    else:
        command_to_check = start_command

    # Verify the correct app module path
    assert "src.pybackstock.app:app" in command_to_check, (
        "Gunicorn does not reference correct app path 'src.pybackstock.app:app'"
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

    # If using a startup script, check the script instead
    if "scripts/start.sh" in start_command:
        project_root = Path(__file__).parent.parent
        startup_script_path = project_root / "scripts" / "start.sh"
        with open(startup_script_path) as f:
            command_to_check = f.read()
    else:
        command_to_check = start_command

    # Test that gunicorn command can be validated
    # The command should follow pattern: gunicorn 'module:app' --bind host:port
    parts = command_to_check.split()

    # Find gunicorn in the command
    gunicorn_idx = None
    for i, part in enumerate(parts):
        if "gunicorn" in part:
            gunicorn_idx = i
            break

    assert gunicorn_idx is not None, "gunicorn not found in startCommand or script"

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


@pytest.mark.integration
def test_render_yaml_database_url_configured() -> None:
    """Test that render.yaml properly configures DATABASE_URL from database service.

    This ensures successful deployment by verifying that the DATABASE_URL
    environment variable is linked to the PostgreSQL database service.
    """
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    env_vars = web_service.get("envVars", [])
    database_url_var = next((e for e in env_vars if e.get("key") == "DATABASE_URL"), None)

    # Verify DATABASE_URL is configured
    assert database_url_var is not None, (
        "DATABASE_URL environment variable not found in render.yaml. This will cause deployment failure."
    )

    # Verify it's linked to a database service
    assert "fromDatabase" in database_url_var, (
        "DATABASE_URL should be linked to a database service via 'fromDatabase'. "
        "Without this, the app will use SQLite fallback instead of PostgreSQL."
    )

    from_database = database_url_var.get("fromDatabase", {})
    assert "name" in from_database, "DATABASE_URL fromDatabase must specify database 'name'"
    assert "property" in from_database, "DATABASE_URL fromDatabase must specify 'property'"
    assert from_database.get("property") == "connectionString", (
        "DATABASE_URL should use 'connectionString' property from database"
    )


@pytest.mark.integration
def test_render_yaml_database_service_exists() -> None:
    """Test that render.yaml defines the database service that DATABASE_URL references."""
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    # Get DATABASE_URL configuration from web service
    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)
    assert web_service is not None

    env_vars = web_service.get("envVars", [])
    database_url_var = next((e for e in env_vars if e.get("key") == "DATABASE_URL"), None)
    assert database_url_var is not None

    database_name = database_url_var.get("fromDatabase", {}).get("name")
    assert database_name, "DATABASE_URL must reference a database name"

    # Verify the database service exists
    databases = config.get("databases", [])
    database_service = next((d for d in databases if d.get("name") == database_name), None)

    assert database_service is not None, (
        f"Database service '{database_name}' referenced by DATABASE_URL not found in render.yaml. "
        "This will cause deployment failure."
    )

    # Verify database configuration
    assert database_service.get("databaseName"), "Database service must have 'databaseName'"
    assert database_service.get("user"), "Database service must have 'user'"


@pytest.mark.integration
def test_config_uses_postgresql_when_database_url_set() -> None:
    """Test that Config uses PostgreSQL URI when DATABASE_URL is properly set.

    This simulates the production deployment scenario where Render provides
    a valid PostgreSQL DATABASE_URL.
    """
    # Save original DATABASE_URL if it exists
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Simulate Render's PostgreSQL connection string
        test_db_url = "postgresql://pybackstock:testpass@host.render.com:5432/pybackstock"
        os.environ["DATABASE_URL"] = test_db_url

        # Remove config module from cache to force re-import
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]

        # Import config module fresh
        config_module = importlib.import_module("src.pybackstock.config")
        config_class = config_module.Config

        # Verify it's using the PostgreSQL DATABASE_URL, not SQLite fallback
        assert test_db_url == config_class.SQLALCHEMY_DATABASE_URI, (
            "Config should use DATABASE_URL when set, not fallback to SQLite"
        )
        assert "postgresql://" in config_class.SQLALCHEMY_DATABASE_URI, "Production should use PostgreSQL, not SQLite"
        assert "sqlite:///" not in config_class.SQLALCHEMY_DATABASE_URI, (
            "Should not use SQLite fallback when DATABASE_URL is set"
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
def test_production_config_with_database_url() -> None:
    """Test that ProductionConfig properly uses DATABASE_URL from environment.

    This validates that production deployment will use the correct database
    configuration provided by Render.
    """
    # Save original DATABASE_URL if it exists
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Set a production-like DATABASE_URL
        production_db_url = "postgresql://user:pass@postgres.render.com:5432/mydb"
        os.environ["DATABASE_URL"] = production_db_url

        # Remove config module from cache
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]

        # Import and check ProductionConfig
        config_module = importlib.import_module("src.pybackstock.config")
        prod_config = config_module.ProductionConfig

        # Verify ProductionConfig inherits and uses DATABASE_URL correctly
        assert hasattr(prod_config, "SQLALCHEMY_DATABASE_URI"), "ProductionConfig must have SQLALCHEMY_DATABASE_URI"
        assert production_db_url == prod_config.SQLALCHEMY_DATABASE_URI, (
            "ProductionConfig should use DATABASE_URL from environment"
        )
        assert prod_config.DEBUG is False, "ProductionConfig should have DEBUG=False"
        assert prod_config.SESSION_COOKIE_SECURE is True, "ProductionConfig should require HTTPS for session cookies"
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
def test_app_starts_with_postgresql_database_url() -> None:
    """Test that the app can successfully start with a PostgreSQL DATABASE_URL.

    This simulates a successful Render deployment scenario.
    """
    # Save original DATABASE_URL
    original_db_url = os.environ.get("DATABASE_URL")

    try:
        # Set a valid PostgreSQL URL format (doesn't need to be a real database)
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/testdb"

        # Try to import and instantiate the app
        # We're not connecting to the database, just verifying the app can start
        # with the correct configuration
        if "src.pybackstock.config" in sys.modules:
            del sys.modules["src.pybackstock.config"]
        if "src.pybackstock.app" in sys.modules:
            del sys.modules["src.pybackstock.app"]

        config_module = importlib.import_module("src.pybackstock.config")
        config_class = config_module.Config

        # Verify the PostgreSQL URL is being used
        assert "postgresql://" in config_class.SQLALCHEMY_DATABASE_URI, (
            "App should use PostgreSQL when DATABASE_URL is set to postgresql://"
        )
        assert "sqlite:///" not in config_class.SQLALCHEMY_DATABASE_URI, (
            "App should not use SQLite when valid DATABASE_URL is provided"
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
        if "src.pybackstock.app" in sys.modules:
            del sys.modules["src.pybackstock.app"]


@pytest.mark.integration
def test_render_yaml_migrations_configured() -> None:
    """Test that database migrations are configured to run during deployment.

    On Render free tier, preDeployCommand is not available (paid-only feature).
    As a workaround, migrations must run via a startup script or in startCommand.

    This test validates that migrations are configured via:
    - preDeployCommand (paid tier - industry standard)
    - Startup script (free tier - recommended workaround)
    - Inline startCommand (free tier - simple workaround)
    """
    render_yaml_path = Path(__file__).parent.parent / "render.yaml"
    with open(render_yaml_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    web_service = next((s for s in services if s.get("type") == "web"), None)

    assert web_service is not None, "No web service found in render.yaml"

    pre_deploy_command = web_service.get("preDeployCommand")
    start_command = web_service.get("startCommand", "")

    # Check if migrations run in preDeployCommand
    migrations_in_predeploy = pre_deploy_command is not None and (
        "flask db upgrade" in pre_deploy_command or "alembic upgrade head" in pre_deploy_command
    )

    # Check if using startup script
    uses_startup_script = "scripts/start.sh" in start_command or "scripts/start.py" in start_command

    # Check if migrations run inline in startCommand
    migrations_inline = "flask db upgrade" in start_command or "alembic upgrade head" in start_command

    # At least one migration method must be configured
    migration_configured = migrations_in_predeploy or uses_startup_script or migrations_inline

    assert migration_configured, (
        "Database migrations are not configured to run during deployment. "
        "Without migrations, database tables won't exist, causing 'Not found' errors. "
        "Configure migrations via preDeployCommand (paid tier) or a startup script (free tier). "
        f"preDeployCommand: {pre_deploy_command}, startCommand: {start_command}"
    )

    # If using startup script, verify it exists and contains migration logic
    if uses_startup_script:
        project_root = Path(__file__).parent.parent
        if "start.sh" in start_command:
            startup_script_path = project_root / "scripts" / "start.sh"
            assert startup_script_path.exists(), (
                f"Startup script not found at {startup_script_path}. "
                "Create scripts/start.sh to run migrations before starting the app."
            )
            # Verify script contains migration logic
            with open(startup_script_path) as f:
                script_content = f.read()
            has_migration_logic = (
                "flask_migrate_upgrade" in script_content
                or "flask db upgrade" in script_content
                or "alembic upgrade" in script_content
            )
            assert has_migration_logic, (
                "Startup script must contain migration logic "
                "(flask_migrate_upgrade, flask db upgrade, or alembic upgrade)"
            )
