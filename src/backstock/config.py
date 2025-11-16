"""Backstock application configuration classes for different environments."""

import os
import secrets
from pathlib import Path

basedir = Path(__file__).parent.resolve()


class Config:
    """Base configuration class with common settings."""

    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    # Use environment variable for SECRET_KEY, fall back to generated secret for development
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    # Handle both old and new PostgreSQL URI formats
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url

    # Security settings
    # Flask-WTF CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens don't expire

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Session security
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS in production


class StagingConfig(Config):
    """Staging environment configuration."""

    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF in tests (use dedicated security tests for CSRF testing)
