"""Management script for the backstock application."""

import os

from flask_migrate import Migrate

from src.backstock import app, db

# Configure the app
app.config.from_object(os.environ.get("APP_SETTINGS", "src.backstock.config.DevelopmentConfig"))

# Initialize Flask-Migrate
migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run()
