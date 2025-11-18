"""Unit tests for database models."""

from datetime import datetime, timezone

import pytest
from flask import Flask

from src.pybackstock import Grocery, db
from tests.conftest import GroceryData


@pytest.mark.unit
def test_grocery_model_creation(app: Flask, sample_grocery_data: GroceryData) -> None:
    """Test creating a Grocery model instance."""
    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        assert grocery.id == sample_grocery_data["item_id"]
        assert grocery.description == sample_grocery_data["description"]
        assert grocery.last_sold == sample_grocery_data["last_sold"]
        assert grocery.shelf_life == sample_grocery_data["shelf_life"]
        assert grocery.department == sample_grocery_data["department"]
        assert grocery.price == sample_grocery_data["price"]
        assert grocery.unit == sample_grocery_data["unit"]
        assert grocery.x_for == sample_grocery_data["x_for"]
        assert grocery.cost == sample_grocery_data["cost"]


@pytest.mark.unit
def test_grocery_model_iter(app: Flask, sample_grocery_data: GroceryData) -> None:
    """Test Grocery model iteration for JSON serialization."""
    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        grocery_dict = dict(grocery)

        assert grocery_dict["id"] == sample_grocery_data["item_id"]
        assert grocery_dict["description"] == sample_grocery_data["description"]
        assert grocery_dict["last_sold"] == "2024-01-01"
        assert grocery_dict["shelf_life"] == sample_grocery_data["shelf_life"]
        assert grocery_dict["department"] == sample_grocery_data["department"]
        assert grocery_dict["price"] == sample_grocery_data["price"]
        assert grocery_dict["unit"] == sample_grocery_data["unit"]
        assert grocery_dict["x_for"] == sample_grocery_data["x_for"]
        assert grocery_dict["cost"] == sample_grocery_data["cost"]


@pytest.mark.unit
def test_grocery_model_none_last_sold(app: Flask) -> None:
    """Test Grocery model with None last_sold date."""
    with app.app_context():
        grocery = Grocery(
            item_id=2,
            description="Test Item",
            last_sold=None,
            shelf_life="7d",
            department="Test",
            price="1.99",
            unit="ea",
            x_for=1,
            cost="0.99",
        )
        grocery_dict = dict(grocery)
        assert grocery_dict["last_sold"] is None


@pytest.mark.unit
def test_grocery_model_save_to_db(app: Flask, sample_grocery_data: GroceryData) -> None:
    """Test saving Grocery model to database."""
    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        db.session.add(grocery)
        db.session.commit()

        retrieved = db.session.query(Grocery).filter_by(id=sample_grocery_data["item_id"]).first()
        assert retrieved is not None
        assert retrieved.description == sample_grocery_data["description"]


@pytest.mark.unit
def test_grocery_model_new_fields(app: Flask, sample_grocery_data: GroceryData) -> None:
    """Test new inventory management fields (quantity, reorder_point, date_added)."""
    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        assert grocery.quantity == sample_grocery_data["quantity"]
        assert grocery.reorder_point == sample_grocery_data["reorder_point"]
        assert grocery.date_added == sample_grocery_data["date_added"]


@pytest.mark.unit
def test_grocery_model_default_quantity(app: Flask) -> None:
    """Test that quantity defaults to 0 when not provided."""
    with app.app_context():
        grocery = Grocery(
            item_id=3,
            description="Test Item",
            last_sold=None,
            shelf_life="7d",
            department="Test",
            price="1.99",
            unit="ea",
            x_for=1,
            cost="0.99",
        )
        assert grocery.quantity == 0


@pytest.mark.unit
def test_grocery_model_default_reorder_point(app: Flask) -> None:
    """Test that reorder_point defaults to 10 when not provided."""
    with app.app_context():
        grocery = Grocery(
            item_id=4,
            description="Test Item",
            last_sold=None,
            shelf_life="7d",
            department="Test",
            price="1.99",
            unit="ea",
            x_for=1,
            cost="0.99",
        )
        assert grocery.reorder_point == 10


@pytest.mark.unit
def test_grocery_model_default_date_added(app: Flask) -> None:
    """Test that date_added defaults to today when not provided."""
    with app.app_context():
        grocery = Grocery(
            item_id=5,
            description="Test Item",
            last_sold=None,
            shelf_life="7d",
            department="Test",
            price="1.99",
            unit="ea",
            x_for=1,
            cost="0.99",
        )
        assert grocery.date_added == datetime.now(tz=timezone.utc).date()  # noqa: UP017


@pytest.mark.unit
def test_grocery_model_iter_includes_new_fields(app: Flask, sample_grocery_data: GroceryData) -> None:
    """Test that __iter__ includes new inventory fields."""
    with app.app_context():
        grocery = Grocery(**sample_grocery_data)
        grocery_dict = dict(grocery)

        assert grocery_dict["quantity"] == sample_grocery_data["quantity"]
        assert grocery_dict["reorder_point"] == sample_grocery_data["reorder_point"]
        assert grocery_dict["date_added"] == "2024-01-01"


@pytest.mark.unit
def test_grocery_model_zero_quantity(app: Flask) -> None:
    """Test grocery item with zero quantity (out of stock)."""
    with app.app_context():
        grocery = Grocery(
            item_id=6,
            description="Out of Stock Item",
            last_sold=None,
            shelf_life="7d",
            department="Test",
            price="1.99",
            unit="ea",
            x_for=1,
            cost="0.99",
            quantity=0,
            reorder_point=10,
        )
        db.session.add(grocery)
        db.session.commit()

        retrieved = db.session.query(Grocery).filter_by(id=6).first()
        assert retrieved is not None
        assert retrieved.quantity == 0


@pytest.mark.unit
def test_grocery_model_low_stock_scenario(app: Flask) -> None:
    """Test item below reorder point (business logic scenario)."""
    with app.app_context():
        grocery = Grocery(
            item_id=7,
            description="Low Stock Item",
            last_sold=None,
            shelf_life="7d",
            department="Test",
            price="1.99",
            unit="ea",
            x_for=1,
            cost="0.99",
            quantity=5,
            reorder_point=10,
        )
        # Business logic: item needs reorder if quantity < reorder_point
        assert grocery.quantity < grocery.reorder_point


@pytest.mark.unit
def test_grocery_model_at_reorder_point(app: Flask) -> None:
    """Test item exactly at reorder point."""
    with app.app_context():
        grocery = Grocery(
            item_id=8,
            description="At Reorder Point Item",
            last_sold=None,
            shelf_life="7d",
            department="Test",
            price="1.99",
            unit="ea",
            x_for=1,
            cost="0.99",
            quantity=10,
            reorder_point=10,
        )
        assert grocery.quantity == grocery.reorder_point
