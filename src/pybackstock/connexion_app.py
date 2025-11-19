"""Connexion-based Flask application with OpenAPI specification."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import connexion
from flask import request as flask_request
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Import shared database instance
from src.pybackstock.database import db


def _find_project_root() -> Path:
    """Find project root by looking for pyproject.toml.

    Returns:
        Path to the project root directory.

    Raises:
        RuntimeError: If pyproject.toml cannot be found.
    """
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    msg = "Could not find project root (no pyproject.toml found)"
    raise RuntimeError(msg)


# Get the root directory (project root containing pyproject.toml)
_root_dir = _find_project_root()

# Create Connexion app with Flask
connexion_app = connexion.FlaskApp(
    __name__,
    specification_dir=str(_root_dir),
)

# Get the underlying Flask app
flask_app = connexion_app.app

# Configure Flask app
flask_app.template_folder = str(_root_dir / "templates")
flask_app.config.from_object(os.environ.get("APP_SETTINGS", "src.pybackstock.config.DevelopmentConfig"))
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure app to trust Render.com's proxy headers (X-Forwarded-*)
# mypy: disable-error-code="unused-ignore"
flask_app.wsgi_app = ProxyFix(  # type: ignore
    flask_app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_prefix=1,
)

# Initialize security extensions
csrf = CSRFProtect(flask_app)

# Configure Talisman for security headers
is_production = not flask_app.config.get("DEBUG", False) and not flask_app.config.get("TESTING", False)


# Exempt Swagger UI from CSRF and Talisman
@flask_app.before_request
def before_request() -> None:
    """Configure per-request settings."""
    # Exempt Swagger UI paths from CSRF
    if flask_request.path.startswith("/ui") or flask_request.path.startswith("/openapi"):
        flask_request.environ["exempt_from_csrf"] = True


talisman = Talisman(
    flask_app,
    force_https=is_production,
    strict_transport_security=is_production,
    content_security_policy={
        "default-src": "'self'",
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "code.jquery.com",
            "netdna.bootstrapcdn.com",
            "cdn.jsdelivr.net",
            "'unsafe-eval'",  # Required for Swagger UI
        ],
        "style-src": ["'self'", "'unsafe-inline'", "netdna.bootstrapcdn.com"],
        "img-src": ["'self'", "data:", "online.swagger.io", "validator.swagger.io"],
    },
)

# Initialize the shared database with this Flask app
db.init_app(flask_app)

# Update the app module to use our Flask app instance
import src.pybackstock.app as app_module  # noqa: E402

# Import models after db is created
from src.pybackstock.models import Grocery  # noqa: E402, F401

app_module.app = flask_app
app_module.db = db
app_module.csrf = csrf
app_module.talisman = talisman

# Configure logging
logger = logging.getLogger(__name__)

# Add the OpenAPI specification
logger.info("Loading OpenAPI specification from openapi.yaml...")
try:
    api_result = connexion_app.add_api(
        "openapi.yaml",
        arguments={"title": "PyBackstock Inventory Management API"},
        pythonic_params=True,
        validate_responses=False,  # Disable for now to avoid validation issues
        # resolver_error=500,  # Uncomment for debugging operation resolution failures
    )
    logger.info("OpenAPI spec loaded successfully!")
    logger.debug("API result: %s", api_result)

    # In Connexion 3.x, routes are registered in ASGI middleware, NOT in Flask's url_map
    # This is expected behavior - Flask's url_map will only show Flask-specific routes
    flask_routes = [rule.rule for rule in flask_app.url_map.iter_rules()]
    logger.debug("Flask-specific routes in url_map: %s", flask_routes)
    logger.info(
        "Note: Connexion 3.x routes are in ASGI middleware layer. "
        "Use connexion_app.test_client() to test, not flask_app.test_client()"
    )
except (FileNotFoundError, ValueError, KeyError) as e:
    logger.exception("Error loading OpenAPI spec")
    raise RuntimeError(f"Failed to load OpenAPI specification: {e}") from e

# Export the Connexion app for ASGI deployment (Gunicorn with Uvicorn workers)
# The connexion_app wraps Flask and handles routing via ASGI middleware
app = connexion_app  # This is a connexion.FlaskApp instance


def main() -> None:
    """Run the Connexion application."""
    port = int(os.environ.get("PORT", "5000"))
    # Use uvicorn to serve the ASGI app
    connexion_app.run(host="0.0.0.0", port=port)  # noqa: S104


if __name__ == "__main__":
    main()
