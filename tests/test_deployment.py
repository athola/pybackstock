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
