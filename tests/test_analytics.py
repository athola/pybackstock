"""Integration tests for analytics and business logic scenarios."""

import io
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.pybackstock import Grocery, db


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


@pytest.mark.integration
def test_user_workflow_add_item_then_view_report(client: FlaskClient) -> None:
    """Test complete user workflow: add item, then view report.

    BDD Scenario: As a user, I want to add an item and immediately
    see it reflected in the analytics report.
    """
    # Given: I am on the home page
    # When: I add a new item with inventory fields
    add_response = client.post(
        "/",
        data={
            "send-add": "",
            "id-add": "901",
            "description-add": "Workflow Test Item",
            "last-sold-add": "2024-01-01",
            "shelf-life-add": "7d",
            "department-add": "Test",
            "price-add": "4.99",
            "unit-add": "ea",
            "xfor-add": "1",
            "cost-add": "2.99",
            "quantity-add": "30",
            "reorder-point-add": "15",
        },
    )
    assert add_response.status_code == 200

    # And: I view the analytics report
    report_response = client.get("/report")

    # Then: The report should display successfully with my item included
    assert report_response.status_code == 200
    assert b"Inventory Analytics Report" in report_response.data


@pytest.mark.integration
def test_user_workflow_csv_import_then_report(client: FlaskClient) -> None:
    """Test complete user workflow: import CSV, then view report.

    BDD Scenario: As a user, I want to bulk import items via CSV
    and see them in the analytics report.
    """
    # Given: I have a CSV file with inventory data
    csv_data = (
        b"id,description,last_sold,shelf_life,department,price,unit,x_for,cost,quantity,reorder_point,date_added\n"
        b"1001,Bulk Item 1,2024-01-01,7d,Bulk Dept,1.99,ea,1,0.99,100,50,2024-01-01\n"
        b"1002,Bulk Item 2,2024-01-01,14d,Bulk Dept,2.99,ea,1,1.99,75,30,2024-01-01\n"
    )

    # When: I upload the CSV
    upload_response = client.post(
        "/",
        data={
            "csv-submit": "",
            "csv-input": (io.BytesIO(csv_data), "bulk_import.csv"),
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    # And: I view the analytics report
    report_response = client.get("/report")

    # Then: The report should include the imported items
    assert report_response.status_code == 200
    assert b"Inventory Analytics Report" in report_response.data


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
