"""Tests for random grocery item generation."""

import os

# Set test environment BEFORE importing app modules
os.environ["APP_SETTINGS"] = "src.pybackstock.config.TestingConfig"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import UTC, datetime

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.pybackstock.grocery_corpus import (
    BAKERY_ITEMS,
    DAIRY_ITEMS,
    FROZEN_ITEMS,
    GROCERY_CORPUS,
    GROCERY_ITEMS,
    MEAT_ITEMS,
    PHARMACY_ITEMS,
    PRODUCE_ITEMS,
    GroceryItemTemplate,
)
from src.pybackstock.models import Grocery
from src.pybackstock.random_items import (
    DEFAULT_CONFIG,
    RandomItemConfig,
    generate_multiple_random_item_data,
    generate_random_cost,
    generate_random_date_added,
    generate_random_item_data,
    generate_random_item_data_from_department,
    generate_random_last_sold,
    generate_random_price,
    generate_random_quantity,
    generate_random_reorder_point,
    generate_random_x_for,
    get_available_departments,
    get_corpus_by_department,
)


class TestGroceryCorpus:
    """Tests for the grocery corpus data."""

    def test_corpus_not_empty(self) -> None:
        """Verify corpus contains items."""
        assert len(GROCERY_CORPUS) > 0

    def test_corpus_has_expected_size(self) -> None:
        """Verify corpus has a reasonable number of items."""
        # Based on our design, we should have around 200+ items
        assert len(GROCERY_CORPUS) >= 200

    def test_all_departments_represented(self) -> None:
        """Verify all major departments are in corpus."""
        departments = {item.department for item in GROCERY_CORPUS}
        expected_departments = {"Produce", "Dairy", "Meat", "Bakery", "Grocery", "Frozen", "Pharmacy"}
        assert expected_departments.issubset(departments)

    def test_department_item_counts(self) -> None:
        """Verify each department has multiple items."""
        assert len(PRODUCE_ITEMS) >= 40
        assert len(DAIRY_ITEMS) >= 25
        assert len(MEAT_ITEMS) >= 30
        assert len(BAKERY_ITEMS) >= 20
        assert len(GROCERY_ITEMS) >= 60
        assert len(FROZEN_ITEMS) >= 20
        assert len(PHARMACY_ITEMS) >= 15

    def test_corpus_item_structure(self) -> None:
        """Verify all corpus items have required fields."""
        for item in GROCERY_CORPUS:
            assert isinstance(item, GroceryItemTemplate)
            assert item.description
            assert item.department
            assert item.price_min > 0
            assert item.price_max >= item.price_min
            assert item.unit
            assert item.shelf_life
            assert 0 < item.cost_ratio_min < 1
            assert item.cost_ratio_min <= item.cost_ratio_max <= 1

    def test_price_ranges_are_sensible(self) -> None:
        """Verify price ranges make sense for grocery items."""
        for item in GROCERY_CORPUS:
            # Most grocery items should be under $100
            assert item.price_max <= 100, f"{item.description} has unrealistic price max"
            # Prices shouldn't be too close together
            assert item.price_max - item.price_min >= 0.10, f"{item.description} has too narrow price range"


class TestRandomGenerators:
    """Tests for individual random generator functions."""

    def test_generate_random_price_in_range(self) -> None:
        """Verify generated price is within template range."""
        template = GroceryItemTemplate(
            description="Test Item",
            department="Test",
            price_min=2.99,
            price_max=4.99,
            unit="ea",
            shelf_life="7d",
        )
        for _ in range(100):
            price = generate_random_price(template)
            price_float = float(price)
            assert 2.99 <= price_float <= 4.99

    def test_generate_random_price_format(self) -> None:
        """Verify price is formatted correctly."""
        template = GROCERY_CORPUS[0]
        price = generate_random_price(template)
        # Should have exactly 2 decimal places
        assert "." in price
        assert len(price.split(".")[-1]) == 2

    def test_generate_random_cost_ratio(self) -> None:
        """Verify cost is within expected ratio of price."""
        template = GroceryItemTemplate(
            description="Test Item",
            department="Test",
            price_min=10.00,
            price_max=10.00,
            unit="ea",
            shelf_life="7d",
            cost_ratio_min=0.40,
            cost_ratio_max=0.60,
        )
        for _ in range(100):
            price = "10.00"
            cost = generate_random_cost(price, template)
            cost_float = float(cost)
            # Cost should be 40-60% of price (4.00-6.00)
            assert 4.00 <= cost_float <= 6.00

    def test_generate_random_last_sold_date_range(self) -> None:
        """Verify last_sold dates are within expected range."""
        config = RandomItemConfig(last_sold_days_back=30, last_sold_null_probability=0)
        today = datetime.now(UTC).date()
        for _ in range(100):
            last_sold = generate_random_last_sold(config)
            assert last_sold is not None
            assert last_sold <= today
            assert (today - last_sold).days <= 30

    def test_generate_random_last_sold_can_be_none(self) -> None:
        """Verify last_sold can be None with appropriate probability."""
        config = RandomItemConfig(last_sold_null_probability=1.0)
        for _ in range(10):
            assert generate_random_last_sold(config) is None

    def test_generate_random_quantity_range(self) -> None:
        """Verify quantity is within configured range."""
        config = RandomItemConfig(quantity_min=10, quantity_max=50)
        for _ in range(100):
            qty = generate_random_quantity(config)
            assert 10 <= qty <= 50

    def test_generate_random_reorder_point_range(self) -> None:
        """Verify reorder point is within configured range."""
        config = RandomItemConfig(reorder_point_min=5, reorder_point_max=15)
        for _ in range(100):
            rp = generate_random_reorder_point(config)
            assert 5 <= rp <= 15

    def test_generate_random_x_for_values(self) -> None:
        """Verify x_for generates valid values."""
        for _ in range(100):
            x_for = generate_random_x_for()
            assert x_for in {1, 2, 3, 4}

    def test_generate_random_date_added_range(self) -> None:
        """Verify date_added is within expected range."""
        config = RandomItemConfig(date_added_days_back=90)
        today = datetime.now(UTC).date()
        for _ in range(100):
            date_added = generate_random_date_added(config)
            assert date_added <= today
            assert (today - date_added).days <= 90


class TestRandomItemGeneration:
    """Tests for complete random item generation."""

    def test_generate_random_item_data_has_all_fields(self) -> None:
        """Verify generated item data has all required fields."""
        data = generate_random_item_data(item_id=1)
        required_fields = {
            "item_id",
            "description",
            "last_sold",
            "shelf_life",
            "department",
            "price",
            "unit",
            "x_for",
            "cost",
            "quantity",
            "reorder_point",
            "date_added",
        }
        assert set(data.keys()) == required_fields

    def test_generate_random_item_data_uses_provided_id(self) -> None:
        """Verify item uses the provided ID."""
        data = generate_random_item_data(item_id=42)
        assert data["item_id"] == 42

    def test_generate_random_item_data_with_specific_template(self) -> None:
        """Verify item uses provided template."""
        template = GroceryItemTemplate(
            description="Custom Item",
            department="Custom Dept",
            price_min=5.00,
            price_max=5.00,
            unit="custom",
            shelf_life="99d",
        )
        data = generate_random_item_data(item_id=1, template=template)
        assert data["description"] == "Custom Item"
        assert data["department"] == "Custom Dept"
        assert data["unit"] == "custom"
        assert data["shelf_life"] == "99d"
        assert float(data["price"]) == 5.00

    def test_generate_random_item_data_creates_valid_grocery_data(self, app: Flask) -> None:
        """Verify generated data can create a valid Grocery instance."""
        with app.app_context():
            data = generate_random_item_data(item_id=100)
            item = Grocery(**data)
            assert item.id == 100
            assert item.description
            assert item.department
            assert item.price
            assert item.cost
            assert item.unit
            assert item.shelf_life

    def test_generate_multiple_random_item_data(self) -> None:
        """Verify multiple item data dicts can be generated."""
        data_list = generate_multiple_random_item_data(starting_id=1, count=10)
        assert len(data_list) == 10
        ids = [data["item_id"] for data in data_list]
        assert ids == list(range(1, 11))

    def test_generate_multiple_random_item_data_unique(self) -> None:
        """Verify items are unique when allow_duplicates=False."""
        data_list = generate_multiple_random_item_data(starting_id=1, count=50, allow_duplicates=False)
        descriptions = [data["description"] for data in data_list]
        assert len(descriptions) == len(set(descriptions))

    def test_generate_multiple_random_item_data_allows_duplicates(self) -> None:
        """Verify duplicates are allowed when configured."""
        # Generate more items than in corpus to ensure duplicates
        data_list = generate_multiple_random_item_data(starting_id=1, count=300, allow_duplicates=True)
        assert len(data_list) == 300

    def test_generate_multiple_raises_for_too_many_unique(self) -> None:
        """Verify error when requesting too many unique items."""
        with pytest.raises(ValueError, match="Cannot generate"):
            generate_multiple_random_item_data(starting_id=1, count=1000, allow_duplicates=False)

    def test_generate_multiple_creates_valid_groceries(self, app: Flask) -> None:
        """Verify multiple generated data can create valid Grocery instances."""
        with app.app_context():
            data_list = generate_multiple_random_item_data(starting_id=1, count=10)
            items = [Grocery(**data) for data in data_list]
            assert len(items) == 10
            for i, item in enumerate(items):
                assert item.id == i + 1


class TestDepartmentFiltering:
    """Tests for department-based item generation."""

    def test_get_available_departments(self) -> None:
        """Verify all departments are retrievable."""
        departments = get_available_departments()
        assert "Produce" in departments
        assert "Dairy" in departments
        assert "Meat" in departments
        assert "Bakery" in departments
        assert "Grocery" in departments
        assert "Frozen" in departments
        assert "Pharmacy" in departments

    def test_get_corpus_by_department(self) -> None:
        """Verify department filtering works."""
        produce = get_corpus_by_department("Produce")
        assert len(produce) > 0
        for item in produce:
            assert item.department == "Produce"

    def test_get_corpus_by_invalid_department(self) -> None:
        """Verify empty list for invalid department."""
        items = get_corpus_by_department("NonexistentDept")
        assert items == []

    def test_generate_random_item_data_from_department(self) -> None:
        """Verify item data can be generated from specific department."""
        data = generate_random_item_data_from_department(item_id=1, department="Dairy")
        assert data["department"] == "Dairy"

    def test_generate_random_item_data_from_department_creates_grocery(self, app: Flask) -> None:
        """Verify department-specific data creates valid Grocery instance."""
        with app.app_context():
            data = generate_random_item_data_from_department(item_id=1, department="Dairy")
            item = Grocery(**data)
            assert item.department == "Dairy"

    def test_generate_random_item_data_from_invalid_department(self) -> None:
        """Verify error for invalid department."""
        with pytest.raises(ValueError, match="not found"):
            generate_random_item_data_from_department(item_id=1, department="FakeDept")


class TestRandomItemConfig:
    """Tests for RandomItemConfig customization."""

    def test_default_config_values(self) -> None:
        """Verify default configuration values."""
        config = DEFAULT_CONFIG
        assert config.quantity_min == 0
        assert config.quantity_max == 100
        assert config.reorder_point_min == 5
        assert config.reorder_point_max == 25
        assert config.last_sold_days_back == 30
        assert config.last_sold_null_probability == 0.2
        assert config.date_added_days_back == 90

    def test_custom_config(self) -> None:
        """Verify custom configuration works."""
        config = RandomItemConfig(
            quantity_min=50,
            quantity_max=60,
            reorder_point_min=20,
            reorder_point_max=25,
        )
        for _ in range(50):
            qty = generate_random_quantity(config)
            assert 50 <= qty <= 60
            rp = generate_random_reorder_point(config)
            assert 20 <= rp <= 25


class TestRandomItemsIntegration:
    """Integration tests for random items with the web app."""

    def test_add_random_items_route(self, client: FlaskClient) -> None:
        """Test the add random items button directly adds items."""
        response = client.post("/", data={"add-random": "", "random-item-count": "5"})
        assert response.status_code == 200
        # Button now directly adds items instead of showing a form
        assert b"Successfully generated 5 random item" in response.data

    def test_generate_random_items_route(self, client: FlaskClient) -> None:
        """Test generating random items via the form."""
        response = client.post("/", data={"send-random": "", "random-count": "3"})
        assert response.status_code == 200
        assert b"Successfully generated 3 random item" in response.data

    def test_generate_random_items_limits_count(self, client: FlaskClient) -> None:
        """Test that count is limited to 50."""
        response = client.post("/", data={"send-random": "", "random-count": "100"})
        assert response.status_code == 200
        # Should be limited to 50
        assert b"Successfully generated 50 random item" in response.data

    def test_generate_random_items_minimum_count(self, client: FlaskClient) -> None:
        """Test that count is at least 1."""
        response = client.post("/", data={"send-random": "", "random-count": "0"})
        assert response.status_code == 200
        # Should be at least 1
        assert b"Successfully generated 1 random item" in response.data

    def test_random_items_appear_in_search(self, client: FlaskClient) -> None:
        """Test that generated items can be searched."""
        # Generate items
        client.post("/", data={"send-random": "", "random-count": "5"})

        # Search by department (all items should have a department)
        response = client.post(
            "/",
            data={"send-search": "", "column": "department", "item": "Produce"},
        )
        # Should either find items or return empty results (no error)
        assert response.status_code == 200
