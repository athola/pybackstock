"""Management script for the inventory application."""

import os

from flask_migrate import Migrate

from inventoryApp import app, db

# Configure the app
app.config.from_object(os.environ.get("APP_SETTINGS", "config.DevelopmentConfig"))

# Initialize Flask-Migrate
migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run()
