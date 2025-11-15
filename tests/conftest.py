"""Shared test fixtures for the inventory application tests."""

import os
from datetime import date
from typing import TypedDict

import pytest
from flask import Flask


class GroceryData(TypedDict):
    """Type definition for grocery item data."""

    item_id: int
    description: str
    last_sold: date | str | None
    shelf_life: str
    department: str | None
    price: str
    unit: str
    x_for: int
    cost: str


# Set test environment before importing app
os.environ["APP_SETTINGS"] = "config.TestingConfig"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture()
def app() -> Flask:  # type: ignore[misc]
    """Create and configure a test Flask application.

    Returns:
        Configured Flask test application.
    """
    from inventoryApp import app, db

    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app: Flask):  # type: ignore[no-untyped-def]
    """Create a test client for the app.

    Args:
        app: The Flask application fixture.

    Returns:
        Test client for making requests.
    """
    return app.test_client()


@pytest.fixture()
def runner(app: Flask):  # type: ignore[no-untyped-def]
    """Create a test CLI runner.

    Args:
        app: The Flask application fixture.

    Returns:
        CLI runner for testing commands.
    """
    return app.test_cli_runner()


@pytest.fixture()
def sample_grocery_data() -> GroceryData:
    """Sample grocery item data for testing.

    Returns:
        Dictionary containing sample grocery item data.
    """
    return {
        "item_id": 1,
        "description": "Test Item",
        "last_sold": date(2024, 1, 1),
        "shelf_life": "7d",
        "department": "Test Dept",
        "price": "1.99",
        "unit": "ea",
        "x_for": 1,
        "cost": "0.99",
    }


@pytest.fixture()
def sample_grocery(app: Flask, sample_grocery_data: GroceryData) -> None:
    """Create a sample grocery item in the database.

    Args:
        app: The Flask application fixture.
        sample_grocery_data: Sample grocery data fixture.
    """
    from inventoryApp import db
    from models import Grocery

    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        db.session.add(grocery)
        db.session.commit()
