"""Unit tests for database models."""

import pytest
from flask import Flask

from src.backstock import Grocery, db
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
