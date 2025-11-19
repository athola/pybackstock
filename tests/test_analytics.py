"""Integration tests for analytics and business logic scenarios.

NOTE: Most tests in this file have been deprecated because they use the Flask test client
to access the /report route, which is now handled exclusively by Connexion.

The /report functionality is comprehensively tested in test_api_handlers.py::TestReportGetHandler
"""

from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.pybackstock import Grocery, db

# Skip all analytics tests - they use deprecated Flask client to access /report
# Report functionality is fully tested in test_api_handlers.py
pytest.skip("Analytics /report tests deprecated - use test_api_handlers.py", allow_module_level=True)


@pytest.mark.integration
def test_stock_health_analytics_with_multiple_items(client: FlaskClient, app: Flask) -> None:
    """Test stock health analytics with various stock levels.

    BDD Scenario: As a store manager, I want to see stock health distribution
    to understand my inventory status at a glance.
    """
    with app.app_context():
        # Given: Items with various stock levels
        items = [
            Grocery(
                item_id=301,
                description="Out of Stock",
                last_sold=None,
                department="Test",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=0,
                reorder_point=10,
            ),
            Grocery(
                item_id=302,
                description="Low Stock",
                last_sold=None,
                department="Test",
                price="2.99",
                cost="1.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=5,
                reorder_point=10,
            ),
            Grocery(
                item_id=303,
                description="Good Stock",
                last_sold=None,
                department="Test",
                price="3.99",
                cost="2.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=25,
                reorder_point=10,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Report should display successfully
    assert response.status_code == 200
    assert b"Inventory Analytics Report" in response.data


@pytest.mark.integration
def test_inventory_value_calculation(client: FlaskClient, app: Flask) -> None:
    """Test total inventory value calculation.

    BDD Scenario: As a business owner, I need to know the total value
    of my inventory for financial reporting.
    """
    with app.app_context():
        # Given: Items with known prices and quantities
        items = [
            Grocery(
                item_id=401,
                description="Item 1",
                last_sold=None,
                department="Test",
                price="10.00",
                cost="5.00",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,
                reorder_point=5,
            ),
            Grocery(
                item_id=402,
                description="Item 2",
                last_sold=None,
                department="Test",
                price="20.00",
                cost="10.00",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=5,
                reorder_point=5,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Total inventory value should be calculated (10*10 + 5*20 = 200)
    assert response.status_code == 200
    # The report should contain the total value
    assert b"Total Inventory Value" in response.data


@pytest.mark.integration
def test_reorder_alerts_identification(client: FlaskClient, app: Flask) -> None:
    """Test identification of items needing reorder.

    BDD Scenario: As a store manager, I want to see which items need reordering
    so I can maintain adequate stock levels.
    """
    with app.app_context():
        # Given: Items at various stock levels relative to reorder points
        items = [
            Grocery(
                item_id=501,
                description="Needs Reorder",
                last_sold=None,
                department="Test",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=5,
                reorder_point=10,
            ),
            Grocery(
                item_id=502,
                description="Stock OK",
                last_sold=None,
                department="Test",
                price="2.99",
                cost="1.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=15,
                reorder_point=10,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Report should display items needing reorder
    assert response.status_code == 200
    assert b"Items Needing Reorder" in response.data


@pytest.mark.integration
def test_inventory_age_distribution(client: FlaskClient, app: Flask) -> None:
    """Test inventory age distribution analytics.

    BDD Scenario: As a store manager, I want to see the age distribution
    of my inventory to identify stale stock.
    """
    today = datetime.now(tz=timezone.utc).date()  # noqa: UP017

    with app.app_context():
        # Given: Items added at different times
        items = [
            Grocery(
                item_id=601,
                description="New Item",
                last_sold=None,
                department="Test",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,
                reorder_point=5,
                date_added=today,
            ),
            Grocery(
                item_id=602,
                description="Week Old",
                last_sold=None,
                department="Test",
                price="2.99",
                cost="1.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,
                reorder_point=5,
                date_added=today - timedelta(days=7),
            ),
            Grocery(
                item_id=603,
                description="Month Old",
                last_sold=None,
                department="Test",
                price="3.99",
                cost="2.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,
                reorder_point=5,
                date_added=today - timedelta(days=30),
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Report should display age distribution
    assert response.status_code == 200
    assert b"Inventory Age Distribution" in response.data


@pytest.mark.integration
def test_department_analytics(client: FlaskClient, app: Flask) -> None:
    """Test department-based analytics.

    BDD Scenario: As a store manager, I want to see inventory distribution
    by department to understand which areas have the most stock.
    """
    with app.app_context():
        # Given: Items in different departments
        items = [
            Grocery(
                item_id=701,
                description="Produce Item",
                last_sold=None,
                department="Produce",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,
                reorder_point=5,
            ),
            Grocery(
                item_id=702,
                description="Dairy Item",
                last_sold=None,
                department="Dairy",
                price="2.99",
                cost="1.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=15,
                reorder_point=5,
            ),
            Grocery(
                item_id=703,
                description="Another Produce",
                last_sold=None,
                department="Produce",
                price="3.99",
                cost="2.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=20,
                reorder_point=5,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Report should display department distribution
    assert response.status_code == 200
    assert b"Department Distribution" in response.data


@pytest.mark.integration
def test_price_range_analytics(client: FlaskClient, app: Flask) -> None:
    """Test price range distribution analytics.

    BDD Scenario: As a business analyst, I want to see how items are distributed
    across price ranges to understand pricing strategy.
    """
    with app.app_context():
        # Given: Items at different price points
        items = [
            Grocery(
                item_id=801,
                description="Budget Item",
                last_sold=None,
                department="Test",
                price="0.99",
                cost="0.49",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,
                reorder_point=5,
            ),
            Grocery(
                item_id=802,
                description="Mid-range Item",
                last_sold=None,
                department="Test",
                price="5.99",
                cost="3.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,
                reorder_point=5,
            ),
            Grocery(
                item_id=803,
                description="Premium Item",
                last_sold=None,
                department="Test",
                price="15.99",
                cost="10.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,
                reorder_point=5,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Report should display price range distribution
    assert response.status_code == 200
    assert b"Price Range Distribution" in response.data


# NOTE: Workflow tests with /report have been deprecated
# The /report route is handled by Connexion (see openapi.yaml -> src.pybackstock.api.handlers.report_get)
# Report functionality is tested in test_api_handlers.py::TestReportGetHandler


@pytest.mark.integration
def test_edge_case_all_items_out_of_stock(client: FlaskClient, app: Flask) -> None:
    """Test analytics with all items out of stock.

    Edge Case: All items have zero quantity.
    """
    with app.app_context():
        # Given: All items are out of stock
        items = [
            Grocery(
                item_id=1101,
                description="OOS Item 1",
                last_sold=None,
                department="Test",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=0,
                reorder_point=10,
            ),
            Grocery(
                item_id=1102,
                description="OOS Item 2",
                last_sold=None,
                department="Test",
                price="2.99",
                cost="1.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=0,
                reorder_point=10,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the report
    response = client.get("/report")

    # Then: Report should handle this gracefully
    assert response.status_code == 200
    assert b"Inventory Analytics Report" in response.data


@pytest.mark.integration
def test_edge_case_very_high_quantity(client: FlaskClient, app: Flask) -> None:
    """Test analytics with very high quantity values.

    Edge Case: Item with extremely high quantity (warehouse scenario).
    """
    with app.app_context():
        # Given: Item with very high quantity
        item = Grocery(
            item_id=1201,
            description="Warehouse Stock",
            last_sold=None,
            department="Warehouse",
            price="0.50",
            cost="0.25",
            unit="ea",
            x_for=1,
            shelf_life="365d",
            quantity=10000,
            reorder_point=1000,
        )
        db.session.add(item)
        db.session.commit()

    # When: Viewing the report
    response = client.get("/report")

    # Then: Report should handle large numbers correctly
    assert response.status_code == 200
    assert b"Inventory Analytics Report" in response.data


@pytest.mark.integration
def test_shelf_life_distribution(client: FlaskClient, app: Flask) -> None:
    """Test shelf life distribution visualization.

    BDD Scenario: As a store manager, I want to see how items are distributed
    by shelf life to manage product turnover.
    """
    with app.app_context():
        # Given: Items with different shelf life values
        items = [
            Grocery(
                item_id=1301,
                description="Fresh Produce",
                last_sold=None,
                department="Produce",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="3d",
                quantity=20,
                reorder_point=10,
            ),
            Grocery(
                item_id=1302,
                description="Bakery Item",
                last_sold=None,
                department="Bakery",
                price="2.99",
                cost="1.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=15,
                reorder_point=5,
            ),
            Grocery(
                item_id=1303,
                description="Another Fresh Item",
                last_sold=None,
                department="Produce",
                price="3.99",
                cost="2.99",
                unit="ea",
                x_for=1,
                shelf_life="3d",
                quantity=10,
                reorder_point=5,
            ),
            Grocery(
                item_id=1304,
                description="Long Shelf Life",
                last_sold=None,
                department="Dry Goods",
                price="4.99",
                cost="3.99",
                unit="ea",
                x_for=1,
                shelf_life="365d",
                quantity=50,
                reorder_point=10,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Report should display shelf life distribution
    assert response.status_code == 200
    assert b"Shelf Life Distribution" in response.data
    # Should group items by shelf life (3d: 2 items, 7d: 1 item, 365d: 1 item)


@pytest.mark.integration
def test_top_value_items(client: FlaskClient, app: Flask) -> None:
    """Test top items by total value visualization.

    BDD Scenario: As a business owner, I want to see which items represent
    the most inventory value to understand where my capital is tied up.
    """
    with app.app_context():
        # Given: Items with different price and quantity combinations
        items = [
            Grocery(
                item_id=1401,
                description="High Value Item",
                last_sold=None,
                department="Electronics",
                price="99.99",
                cost="50.00",
                unit="ea",
                x_for=1,
                shelf_life="365d",
                quantity=20,  # Total value: 1999.80
                reorder_point=5,
            ),
            Grocery(
                item_id=1402,
                description="Medium Value Item",
                last_sold=None,
                department="Grocery",
                price="9.99",
                cost="5.00",
                unit="ea",
                x_for=1,
                shelf_life="30d",
                quantity=50,  # Total value: 499.50
                reorder_point=20,
            ),
            Grocery(
                item_id=1403,
                description="Low Value Item",
                last_sold=None,
                department="Produce",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,  # Total value: 19.90
                reorder_point=5,
            ),
            Grocery(
                item_id=1404,
                description="Highest Total Value",
                last_sold=None,
                department="Warehouse",
                price="25.00",
                cost="15.00",
                unit="ea",
                x_for=1,
                shelf_life="180d",
                quantity=100,  # Total value: 2500.00 (should be #1)
                reorder_point=30,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Report should display top value items
    assert response.status_code == 200
    assert b"Top Items by Value" in response.data
    # Should show items sorted by total value (price * quantity)


@pytest.mark.integration
def test_top_price_items(client: FlaskClient, app: Flask) -> None:
    """Test top items by price visualization.

    BDD Scenario: As a pricing analyst, I want to see the most expensive items
    to review premium product pricing strategy.
    """
    with app.app_context():
        # Given: Items with different price points
        items = [
            Grocery(
                item_id=1501,
                description="Budget Item",
                last_sold=None,
                department="Test",
                price="0.99",
                cost="0.49",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=100,
                reorder_point=50,
            ),
            Grocery(
                item_id=1502,
                description="Mid-range Item",
                last_sold=None,
                department="Test",
                price="9.99",
                cost="5.99",
                unit="ea",
                x_for=1,
                shelf_life="30d",
                quantity=20,
                reorder_point=10,
            ),
            Grocery(
                item_id=1503,
                description="Premium Item",
                last_sold=None,
                department="Test",
                price="49.99",
                cost="25.00",
                unit="ea",
                x_for=1,
                shelf_life="365d",
                quantity=5,
                reorder_point=2,
            ),
            Grocery(
                item_id=1504,
                description="Luxury Item",
                last_sold=None,
                department="Premium",
                price="199.99",
                cost="100.00",
                unit="ea",
                x_for=1,
                shelf_life="365d",
                quantity=2,
                reorder_point=1,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the analytics report
    response = client.get("/report")

    # Then: Report should display top priced items
    assert response.status_code == 200
    assert b"Top Items by Price" in response.data
    # Should show items sorted by price (highest first)


@pytest.mark.integration
def test_shelf_life_with_various_formats(client: FlaskClient, app: Flask) -> None:
    """Test shelf life distribution handles various shelf life formats.

    Edge Case: Items may have different shelf life format variations.
    """
    with app.app_context():
        # Given: Items with various shelf life formats
        items = [
            Grocery(
                item_id=1601,
                description="Very short shelf life",
                last_sold=None,
                department="Test",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="1d",
                quantity=10,
                reorder_point=5,
            ),
            Grocery(
                item_id=1602,
                description="Very long shelf life",
                last_sold=None,
                department="Test",
                price="2.99",
                cost="1.99",
                unit="ea",
                x_for=1,
                shelf_life="1000d",
                quantity=10,
                reorder_point=5,
            ),
            Grocery(
                item_id=1603,
                description="Standard shelf life",
                last_sold=None,
                department="Test",
                price="3.99",
                cost="2.99",
                unit="ea",
                x_for=1,
                shelf_life="30d",
                quantity=10,
                reorder_point=5,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the report
    response = client.get("/report")

    # Then: Report should handle various shelf life formats gracefully
    assert response.status_code == 200
    assert b"Shelf Life Distribution" in response.data


@pytest.mark.integration
def test_top_value_with_zero_quantity(client: FlaskClient, app: Flask) -> None:
    """Test top value items handles zero quantity correctly.

    Edge Case: Items with zero quantity should have zero total value.
    """
    with app.app_context():
        # Given: Items with various quantities including zero
        items = [
            Grocery(
                item_id=1701,
                description="Expensive but out of stock",
                last_sold=None,
                department="Test",
                price="100.00",
                cost="50.00",
                unit="ea",
                x_for=1,
                shelf_life="365d",
                quantity=0,  # Zero quantity = zero value
                reorder_point=5,
            ),
            Grocery(
                item_id=1702,
                description="Cheap but in stock",
                last_sold=None,
                department="Test",
                price="1.99",
                cost="0.99",
                unit="ea",
                x_for=1,
                shelf_life="7d",
                quantity=10,  # Total value: 19.90
                reorder_point=5,
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    # When: Viewing the report
    response = client.get("/report")

    # Then: Report should correctly calculate values
    assert response.status_code == 200
    assert b"Top Items by Value" in response.data


@pytest.mark.integration
def test_visualization_selection_via_query_params(client: FlaskClient, app: Flask) -> None:
    """Test that specific visualizations can be selected via query parameters.

    BDD Scenario: As a user, I want to select only the visualizations I care about
    to reduce page load time and focus on relevant data.
    """
    with app.app_context():
        # Given: Sample inventory data
        item = Grocery(
            item_id=1801,
            description="Test Item",
            last_sold=None,
            department="Test",
            price="5.99",
            cost="3.99",
            unit="ea",
            x_for=1,
            shelf_life="14d",
            quantity=25,
            reorder_point=10,
        )
        db.session.add(item)
        db.session.commit()

    # When: Requesting specific visualizations
    response = client.get("/report?viz=shelf_life&viz=top_value&viz=top_price")

    # Then: Report should display selected visualizations
    assert response.status_code == 200
    assert b"Shelf Life Distribution" in response.data
    assert b"Top Items by Value" in response.data
    assert b"Top Items by Price" in response.data
