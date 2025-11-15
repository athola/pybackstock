"""Unit tests for application helper functions."""

from typing import Any

import pytest
from flask import Flask

from tests.conftest import GroceryData


@pytest.mark.unit
def test_get_matching_items_by_id(app: Flask, sample_grocery: None) -> None:
    """Test searching for items by ID."""
    from inventoryApp import get_matching_items

    with app.app_context():
        result = get_matching_items("id", "1")
        items = list(result)
        assert len(items) == 1
        assert items[0].id == 1


@pytest.mark.unit
def test_get_matching_items_by_id_not_found(app: Flask) -> None:
    """Test searching for non-existent ID."""
    from inventoryApp import get_matching_items

    with app.app_context():
        result = get_matching_items("id", "999")
        items = list(result)
        assert len(items) == 0


@pytest.mark.unit
def test_get_matching_items_invalid_id(app: Flask) -> None:
    """Test searching with invalid ID format."""
    from inventoryApp import get_matching_items

    with app.app_context():
        result = get_matching_items("id", "abc")
        assert result == {}


@pytest.mark.unit
def test_get_matching_items_by_description(app: Flask, sample_grocery: None) -> None:
    """Test searching by description."""
    from inventoryApp import get_matching_items

    with app.app_context():
        result = get_matching_items("description", "Test")
        items = list(result)
        assert len(items) == 1
        assert "Test" in items[0].description


@pytest.mark.unit
def test_get_matching_items_sql_injection_protection(app: Flask) -> None:
    """Test SQL injection protection."""
    from inventoryApp import get_matching_items

    with app.app_context():
        result = get_matching_items("description", "DROP TABLE")
        assert result == {}


@pytest.mark.unit
def test_get_matching_items_wildcard(app: Flask, sample_grocery: None) -> None:
    """Test wildcard search."""
    from inventoryApp import get_matching_items

    with app.app_context():
        result = get_matching_items("description", "Test*")
        items = list(result)
        assert len(items) == 1


@pytest.mark.unit
def test_report_exception(app: Flask, capsys: Any) -> None:  # type: ignore[no-untyped-def]
    """Test exception reporting."""
    from inventoryApp import report_exception

    with app.app_context():
        errors: list[str] = []
        ex = ValueError("Test error")
        result = report_exception(ex, "Error: ", errors)

        assert len(result) == 1
        assert "Test error" in result[0]
        assert "Error: " in result[0]

        captured = capsys.readouterr()
        assert "Test error" in captured.out


@pytest.mark.unit
def test_add_item_new(app: Flask, sample_grocery_data: GroceryData) -> None:
    """Test adding a new item."""
    from inventoryApp import add_item
    from models import Grocery

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
    from inventoryApp import add_item
    from models import Grocery

    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        errors: list[str] = []
        items: list[str] = []

        errors, items = add_item(grocery, errors, items)

        assert len(errors) == 1
        assert "already been added" in errors[0]
        assert len(items) == 0
