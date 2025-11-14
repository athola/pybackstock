# InventoryApp
Python application which searches for and updates inventory items in a database

## Technology Stack
- **Python**: 3.11+ (minimum 3.9)
- **Framework**: Flask 3.x
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Package Manager**: UV (modern, fast Python package manager)

## Setup

### Using UV (Recommended)

This application uses [uv](https://github.com/astral-sh/uv) for fast, reliable dependency management.

1. Install uv (if not already installed):
```bash
pip install uv
```

2. Create virtual environment and install dependencies:
```bash
uv venv
uv pip install -r requirements.txt
```

3. Activate virtual environment:
```bash
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

4. Set up environment variables (copy .env.example to .env and configure):
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running app:

This app can be viewed via webserver hosted on heroku at the following addresses:
Staging:
https://inventory-app-stage.herokuapp.com/

Production:
https://inventory-app-pro.herokuapp.com/

To run locally (with virtual environment activated):
```bash
python manage.py runserver
```

Or using gunicorn (production-like):
```bash
gunicorn inventoryApp:inventoryApp
```

The app will run on http://127.0.0.1:5000/

## Database Management

This database uses PostgreSQL with SQLAlchemy 2.0 ORM.

Initialize the database:
```bash
python manage.py db init
```

Create a migration:
```bash
python manage.py db migrate
```

Apply migrations:
```bash
python manage.py db upgrade
```

## PostgreSQL Database Commands

Connect to the database:
```bash
psql -d inventory_dev
```

Or within psql:
```sql
\c inventory_dev
```

List tables:
```sql
\dt
```

Describe table structure:
```sql
\d grocery_items
```

## Deployment (Heroku)

Check staging configuration:
```bash
heroku config --app inventory-app-stage
```

Add PostgreSQL database:
```bash
heroku addons:create heroku-postgresql:hobby-dev --app inventory-app-stage
```

Deploy to staging:
```bash
git push stage main
```

Run migrations on staging:
```bash
heroku run python manage.py db upgrade --app inventory-app-stage
```

For production (same commands with production app name):
```bash
heroku config --app inventory-app-pro
heroku addons:create heroku-postgresql:hobby-dev --app inventory-app-pro
git push pro main
heroku run python manage.py db upgrade --app inventory-app-pro
```

## Security Updates

This codebase has been modernized with:
- Updated to Python 3.11+ (from 3.7)
- All dependencies updated to latest secure versions
- Fixed hardcoded SECRET_KEY vulnerability
- Updated to SQLAlchemy 2.0 (from 1.3)
- Updated to Flask 3.x (from 1.1)
- Improved error handling and session management
