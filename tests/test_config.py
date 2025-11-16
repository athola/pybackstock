"""Unit tests for configuration module."""

import importlib
import os
import sys

import pytest

from src.backstock.config import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
    StagingConfig,
    TestingConfig,
)


@pytest.mark.unit
def test_config_base() -> None:
    """Test base Config class."""
    assert Config.DEBUG is False
    assert Config.TESTING is False
    assert Config.CSRF_ENABLED is True


@pytest.mark.unit
def test_production_config() -> None:
    """Test ProductionConfig class."""
    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.TESTING is False


@pytest.mark.unit
def test_development_config() -> None:
    """Test DevelopmentConfig class."""
    assert DevelopmentConfig.DEBUG is True
    assert DevelopmentConfig.DEVELOPMENT is True


@pytest.mark.unit
def test_testing_config() -> None:
    """Test TestingConfig class."""
    assert TestingConfig.TESTING is True


@pytest.mark.unit
def test_staging_config() -> None:
    """Test StagingConfig class."""
    assert StagingConfig.DEBUG is True
    assert StagingConfig.DEVELOPMENT is True


@pytest.mark.unit
def test_database_url_conversion() -> None:
    """Test PostgreSQL URL conversion from postgres:// to postgresql://."""
    # Set environment before importing
    old_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = "postgres://user:pass@localhost/db"

    # Need to reload the module to pick up new environment variable
    if "src.backstock.config" in sys.modules:
        del sys.modules["src.backstock.config"]

    from src.backstock.config import Config  # noqa: PLC0415 - Must import after env var manipulation

    assert Config.SQLALCHEMY_DATABASE_URI.startswith("postgresql://")
    assert "user:pass@localhost/db" in Config.SQLALCHEMY_DATABASE_URI

    # Clean up
    if old_database_url:
        os.environ["DATABASE_URL"] = old_database_url
    elif "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

    # Reload module again to restore original state
    if "src.backstock.config" in sys.modules:
        del sys.modules["src.backstock.config"]
    importlib.import_module("src.backstock.config")


@pytest.mark.unit
def test_secret_key_generation() -> None:
    """Test that SECRET_KEY is generated if not in environment."""
    # Make sure SECRET_KEY is not in environment
    if "SECRET_KEY" in os.environ:
        old_key = os.environ["SECRET_KEY"]
        del os.environ["SECRET_KEY"]
    else:
        old_key = None

    from src.backstock.config import Config  # noqa: PLC0415 - Must import after env var manipulation

    assert Config.SECRET_KEY is not None
    assert len(Config.SECRET_KEY) > 0

    # Restore old key if it existed
    if old_key:
        os.environ["SECRET_KEY"] = old_key
