"""Unit tests for application helper functions."""

from typing import Any

import pytest
from flask import Flask

from src.pybackstock.app import add_item, get_matching_items, report_exception
from src.pybackstock.models import Grocery
from tests.conftest import GroceryData


@pytest.mark.unit
def test_get_matching_items_by_id(app: Flask, sample_grocery: None) -> None:
    """Test searching for items by ID."""
    with app.app_context():
        result = get_matching_items("id", "1")
        items = list(result)
        assert len(items) == 1
        assert items[0].id == 1


@pytest.mark.unit
def test_get_matching_items_by_id_not_found(app: Flask) -> None:
    """Test searching for non-existent ID."""
    with app.app_context():
        result = get_matching_items("id", "999")
        items = list(result)
        assert len(items) == 0


@pytest.mark.unit
def test_get_matching_items_invalid_id(app: Flask) -> None:
    """Test searching with invalid ID format."""
    with app.app_context():
        result = get_matching_items("id", "abc")
        assert result == {}


@pytest.mark.unit
def test_get_matching_items_by_description(app: Flask, sample_grocery: None) -> None:
    """Test searching by description."""
    with app.app_context():
        result = get_matching_items("description", "Test")
        items = list(result)
        assert len(items) == 1
        assert "Test" in items[0].description


@pytest.mark.unit
def test_get_matching_items_sql_injection_protection(app: Flask) -> None:
    """Test SQL injection protection via SQLAlchemy ORM.

    SQLAlchemy uses parameterized queries automatically, so malicious
    input like 'DROP TABLE' is treated as a literal search string.
    """
    with app.app_context():
        # Should return a Query object, not execute malicious SQL
        result = get_matching_items("description", "DROP TABLE")
        # Verify it's a Query object (safe) and executing it returns no results
        items = list(result)
        assert len(items) == 0  # No items with description "DROP TABLE"


@pytest.mark.unit
def test_get_matching_items_wildcard(app: Flask, sample_grocery: None) -> None:
    """Test wildcard search."""
    with app.app_context():
        result = get_matching_items("description", "Test*")
        items = list(result)
        assert len(items) == 1


@pytest.mark.unit
def test_report_exception(app: Flask, caplog: Any) -> None:
    """Test exception reporting.

    Verifies that:
    1. Detailed errors are logged server-side (logger)
    2. Generic errors are shown to users (no internal details)
    """
    with app.app_context():
        errors: list[str] = []
        ex = ValueError("Test error")
        result = report_exception(ex, "Error: ", errors)

        # User-facing error should be generic (no exception details)
        assert len(result) == 1
        assert result[0] == "Error:"
        assert "Test error" not in result[0]  # Security: don't expose details

        # Server-side log should contain full details
        assert "Test error" in caplog.text
        assert "line no:" in caplog.text


@pytest.mark.unit
def test_add_item_new(app: Flask, sample_grocery_data: GroceryData) -> None:
    """Test adding a new item."""
    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        errors: list[str] = []
        items: list[str] = []

        errors, items = add_item(grocery, errors, items)

        assert len(errors) == 0
        assert len(items) == 1


@pytest.mark.unit
def test_add_item_duplicate(app: Flask, sample_grocery: None, sample_grocery_data: GroceryData) -> None:
    """Test adding a duplicate item."""
    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        errors: list[str] = []
        items: list[str] = []

        errors, items = add_item(grocery, errors, items)

        assert len(errors) == 1
        assert "already been added" in errors[0]
        assert len(items) == 0
