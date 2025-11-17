#!/usr/bin/env python
"""Startup script for Render deployment (free tier).

This runs database migrations before starting the application server.
"""

import os
import sys

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
# Use os.execvp to replace the current process with gunicorn
port = os.environ.get("PORT", "10000")
os.execvp(
    "gunicorn",
    ["gunicorn", "src.pybackstock.app:app", "--bind", f"0.0.0.0:{port}"],
)
