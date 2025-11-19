#!/usr/bin/env python
"""Startup script for Render deployment (free tier).

This runs database migrations before starting the application server.
"""

import os
import sys
from pathlib import Path

# ============================================================================
# PYTHONPATH Configuration for Deployment Environments
# ============================================================================
# This section adds the project root directory to Python's module search path.
#
# WHY THIS IS NECESSARY:
# -----------------------
# When Render.com (or similar platforms) execute this script, the project root
# directory is NOT automatically included in Python's sys.path. This causes
# imports like "from src.pybackstock import app" to fail with:
#   ModuleNotFoundError: No module named 'src'
#
# Additionally, when this script launches Gunicorn with "src.pybackstock.app:app",
# Gunicorn also needs the project root in its Python path to locate the module.
#
# WHY THIS IS NOT A HACK:
# -----------------------
# This is a standard and recommended practice for deployment/orchestration scripts:
# 1. Deployment scripts often live in subdirectories (scripts/, bin/, etc.)
# 2. They need to import from the main application package
# 3. Adding the project root to sys.path is the conventional solution
# 4. This pattern is used extensively in production deployments (Django, Flask, etc.)
#
# ALTERNATIVES CONSIDERED:
# ------------------------
# 1. Setting PYTHONPATH environment variable in render.yaml
#    - Less portable; requires environment-specific configuration
#    - Harder to maintain across different deployment platforms
#
# 2. Installing the project as an editable package (pip install -e .)
#    - Overkill for a deployment script
#    - Adds complexity to the build process
#
# 3. Moving this script into src/pybackstock/
#    - Violates separation of concerns (mixing app code with operational scripts)
#    - Still requires sys.path modification for Gunicorn
#
# WHAT THIS DOES:
# ---------------
# Adds the project root (parent of scripts/) to the beginning of sys.path,
# allowing Python to find the 'src' package and all application modules.
#
# Project structure:
#   /project-root/          <- This directory gets added to sys.path
#   ├── src/
#   │   └── pybackstock/
#   │       └── app.py
#   └── scripts/
#       └── start.py        <- We are here
# ============================================================================

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 50)
print("Starting PyBackstock Deployment")
print("=" * 50)

# Set up app configuration
os.environ.setdefault("APP_SETTINGS", "src.pybackstock.config.ProductionConfig")

# Run database migrations
print("Running database migrations...")

try:
    from flask_migrate import Migrate
    from flask_migrate import upgrade as flask_migrate_upgrade

    from src.pybackstock import app, db

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # Run migrations
    with app.app_context():
        flask_migrate_upgrade()
        print("✓ Database migrations completed successfully")
except Exception as e:
    print(f"✗ Migration failed: {e}", file=sys.stderr)
    sys.exit(1)

print("Migrations complete. Starting Gunicorn...")
print("=" * 50)

# Start Gunicorn
# IMPORTANT: Using plain Flask app (not Connexion) because Connexion 3.x has route
# registration issues. The Flask app in src.pybackstock.app has all routes defined
# via @app.route decorators and works correctly.
# TODO: Debug Connexion 3.x route registration in future PR
# Use os.execvp to replace the current process with gunicorn
port = os.environ.get("PORT", "10000")
os.execvp(
    "gunicorn",
    [
        "gunicorn",
        "src.pybackstock.app:app",  # Use plain Flask app with @app.route decorators
        "--pythonpath",
        str(project_root),  # Add project root to Python path for module resolution
        "--bind",
        f"0.0.0.0:{port}",
        "--forwarded-allow-ips",
        "*",  # Trust forwarded headers from Render's proxy
    ],
)
