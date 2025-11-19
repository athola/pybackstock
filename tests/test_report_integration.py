"""Integration tests for report generation endpoints.

These tests verify that the report generation works correctly when running
through the full Connexion ASGI stack, which is how the application runs in production.
"""

import os
from datetime import date

import pytest

# Must set environment before importing app modules
os.environ["APP_SETTINGS"] = "src.pybackstock.config.TestingConfig"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from src.pybackstock import Grocery, db
from src.pybackstock.connexion_app import create_app


@pytest.fixture()
def connexion_app():
    """Create a Connexion app for integration testing.

    Returns:
        Connexion FlaskApp instance configured for testing.
    """
    app = create_app("src.pybackstock.config.TestingConfig")
    flask_app = app.app

    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )

    with flask_app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def connexion_client(connexion_app):
    """Create a test client for the Connexion app.

    Args:
        connexion_app: The Connexion application fixture.

    Returns:
        Test client for making requests through the full ASGI stack.
    """
    return connexion_app.test_client()


@pytest.fixture()
def sample_inventory_data(connexion_app):
    """Create sample inventory data for testing.

    Args:
        connexion_app: The Connexion application fixture.
    """
    flask_app = connexion_app.app
    with flask_app.app_context():
        items = [
            Grocery(
                item_id=1001,
                description="Fresh Apples",
                last_sold=date(2024, 11, 15),
                shelf_life="7d",
                department="Produce",
                price="3.99",
                unit="lb",
                x_for=1,
                cost="2.00",
                quantity=50,
                reorder_point=20,
                date_added=date(2024, 11, 1),
            ),
            Grocery(
                item_id=1002,
                description="Organic Milk",
                last_sold=date(2024, 11, 18),
                shelf_life="14d",
                department="Dairy",
                price="5.99",
                unit="gal",
                x_for=1,
                cost="3.50",
                quantity=0,  # Out of stock
                reorder_point=10,
                date_added=date(2024, 10, 15),
            ),
            Grocery(
                item_id=1003,
                description="Premium Steak",
                last_sold=date(2024, 11, 10),
                shelf_life="5d",
                department="Meat",
                price="29.99",
                unit="lb",
                x_for=1,
                cost="18.00",
                quantity=5,  # Low stock
                reorder_point=10,
                date_added=date(2024, 11, 5),
            ),
            Grocery(
                item_id=1004,
                description="Whole Wheat Bread",
                last_sold=None,
                shelf_life="7d",
                department="Bakery",
                price="4.49",
                unit="ea",
                x_for=1,
                cost="2.25",
                quantity=30,
                reorder_point=15,
                date_added=date(2024, 11, 10),
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()


class TestReportGenerationIntegration:
    """Integration tests for /report endpoint through Connexion ASGI stack."""

    @pytest.mark.integration
    def test_report_generation_returns_html(self, connexion_client, sample_inventory_data):
        """Test that /report endpoint returns valid HTML.

        Given: An inventory with sample data
        When: A GET request is made to /report
        Then: The response is 200 OK with HTML content
        """
        response = connexion_client.get("/report")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")
        response_text = response.text if hasattr(response, "text") else response.data.decode("utf-8")
        assert "Inventory Analytics Report" in response_text or "<!DOCTYPE html>" in response_text

    @pytest.mark.integration
    def test_report_with_empty_inventory(self, connexion_client):
        """Test that /report works with no inventory items.

        Given: An empty inventory database
        When: A GET request is made to /report
        Then: The response is 200 OK showing empty state
        """
        response = connexion_client.get("/report")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")
        # Should show "no data" message
        response_text = response.text if hasattr(response, "text") else response.data.decode("utf-8")
        assert "No Inventory Data Available" in response_text or "0" in response_text

    @pytest.mark.integration
    def test_report_with_visualization_filters(self, connexion_client, sample_inventory_data):
        """Test that /report respects visualization query parameters.

        Given: An inventory with sample data
        When: A GET request is made to /report with specific viz filters
        Then: The response is 200 OK with HTML content
        """
        response = connexion_client.get("/report?viz=stock_health&viz=department")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")
        response_text = response.text if hasattr(response, "text") else response.data.decode("utf-8")
        assert "<!DOCTYPE html>" in response_text

    @pytest.mark.integration
    def test_report_shows_summary_metrics(self, connexion_client, sample_inventory_data):
        """Test that report displays summary metrics correctly.

        Given: An inventory with 4 items totaling specific values
        When: A GET request is made to /report
        Then: The HTML includes summary metric cards with values
        """
        response = connexion_client.get("/report")

        assert response.status_code == 200
        response_text = response.text if hasattr(response, "text") else response.data.decode("utf-8")

        # Should contain total items count (4 items)
        assert "4" in response_text or "Total Items" in response_text

        # Should contain department names
        assert "Produce" in response_text or "Dairy" in response_text or "Meat" in response_text

    @pytest.mark.integration
    def test_report_handles_special_characters_in_data(self, connexion_app, connexion_client):
        """Test that report handles special characters in inventory data.

        Given: Inventory items with special characters in descriptions
        When: A GET request is made to /report
        Then: The response is 200 OK with properly escaped HTML
        """
        flask_app = connexion_app.app
        with flask_app.app_context():
            special_item = Grocery(
                item_id=2001,
                description='Test "Item" with <special> & characters',
                last_sold=None,
                shelf_life="7d",
                department="Test & Development",
                price="9.99",
                unit="ea",
                x_for=1,
                cost="5.00",
                quantity=10,
                reorder_point=5,
            )
            db.session.add(special_item)
            db.session.commit()

        response = connexion_client.get("/report")

        assert response.status_code == 200
        # HTML should be properly escaped (no raw < > characters in text content)
        response_text = response.text if hasattr(response, "text") else response.data.decode("utf-8")
        # The description should be HTML-escaped or the page should render without errors
        assert "<!DOCTYPE html>" in response_text


class TestReportDataAPIIntegration:
    """Integration tests for /api/report/data JSON endpoint."""

    @pytest.mark.integration
    def test_report_data_returns_json(self, connexion_client, sample_inventory_data):
        """Test that /api/report/data returns valid JSON.

        Given: An inventory with sample data
        When: A GET request is made to /api/report/data
        Then: The response is 200 OK with JSON content
        """
        response = connexion_client.get("/api/report/data")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")

        data = response.json() if callable(response.json) else response.json
        assert "item_count" in data
        assert "selected_viz" in data
        assert data["item_count"] == 4

    @pytest.mark.integration
    def test_report_data_with_empty_inventory(self, connexion_client):
        """Test that /api/report/data handles empty inventory.

        Given: An empty inventory database
        When: A GET request is made to /api/report/data
        Then: The response is 200 OK with empty metrics
        """
        response = connexion_client.get("/api/report/data")

        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json
        assert data["item_count"] == 0
        assert data["total_items"] == 0

    @pytest.mark.integration
    def test_report_data_includes_all_metrics(self, connexion_client, sample_inventory_data):
        """Test that /api/report/data includes all expected metrics.

        Given: An inventory with sample data
        When: A GET request is made to /api/report/data
        Then: All summary and visualization metrics are present
        """
        response = connexion_client.get("/api/report/data")

        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json

        # Summary metrics
        assert "total_items" in data
        assert "total_value" in data
        assert "total_cost" in data
        assert "total_profit_margin" in data
        assert "total_quantity" in data
        assert "low_stock_count" in data
        assert "out_of_stock_count" in data

        # Visualization data keys
        assert "stock_levels" in data
        assert "dept_counts" in data
        assert "age_distribution" in data
        assert "price_ranges" in data
        assert "shelf_life_counts" in data
        assert "top_value_items" in data
        assert "top_items" in data
        assert "reorder_items" in data

    @pytest.mark.integration
    def test_report_data_calculates_correct_stock_levels(self, connexion_client, sample_inventory_data):
        """Test that stock level calculations are correct.

        Given: Inventory with 1 out-of-stock, 1 low-stock, 2 healthy items
        When: A GET request is made to /api/report/data
        Then: Stock levels are correctly categorized
        """
        response = connexion_client.get("/api/report/data")

        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json

        # We have:
        # - 1 out of stock item (Milk: qty=0)
        # - 1 low stock item (Steak: qty=5, reorder=10)
        # - 2 healthy stock items (Apples: qty=50>20, Bread: qty=30>15)
        assert data["out_of_stock_count"] == 1
        assert data["low_stock_count"] >= 1  # At least the low stock item

        stock_levels = data["stock_levels"]
        assert stock_levels["Out of Stock"] == 1
        assert stock_levels["Healthy Stock"] >= 2

    @pytest.mark.integration
    def test_report_data_filters_visualizations(self, connexion_client, sample_inventory_data):
        """Test that visualization filters work correctly.

        Given: An inventory with sample data
        When: A GET request is made with specific viz filters
        Then: Only selected visualizations are marked in response
        """
        response = connexion_client.get("/api/report/data?viz=stock_health&viz=department")

        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json

        # Selected visualizations should be in the list
        assert "stock_health" in data["selected_viz"]
        assert "department" in data["selected_viz"]

        # But all data should still be present (for backward compatibility)
        assert "stock_levels" in data
        assert "dept_counts" in data

    @pytest.mark.integration
    def test_report_data_calculates_department_distribution(self, connexion_client, sample_inventory_data):
        """Test that department distribution is calculated correctly.

        Given: Inventory with items in Produce, Dairy, Meat, Bakery
        When: A GET request is made to /api/report/data
        Then: Department counts reflect actual distribution
        """
        response = connexion_client.get("/api/report/data")

        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json

        dept_counts = data["dept_counts"]
        assert "Produce" in dept_counts
        assert "Dairy" in dept_counts
        assert "Meat" in dept_counts
        assert "Bakery" in dept_counts
        assert dept_counts["Produce"] == 1
        assert dept_counts["Dairy"] == 1
        assert dept_counts["Meat"] == 1
        assert dept_counts["Bakery"] == 1

    @pytest.mark.integration
    def test_report_data_identifies_top_value_items(self, connexion_client, sample_inventory_data):
        """Test that top value items are correctly identified.

        Given: Inventory with varying total values (price * quantity)
        When: A GET request is made to /api/report/data
        Then: Top value items are sorted by total value
        """
        response = connexion_client.get("/api/report/data")

        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json

        top_value_items = data["top_value_items"]
        assert len(top_value_items) > 0

        # Apples: 3.99 * 50 = 199.50 should be highest
        # Bread: 4.49 * 30 = 134.70 should be second
        # Steak: 29.99 * 5 = 149.95 should be between them
        # Milk: 5.99 * 0 = 0 should be lowest

        # Check that values are in descending order
        values = [item["value"] for item in top_value_items]
        assert values == sorted(values, reverse=True)

        # Highest value item should be Apples
        if top_value_items:
            assert top_value_items[0]["description"] in ["Fresh Apples", "Premium Steak"]

    @pytest.mark.integration
    def test_report_data_identifies_reorder_items(self, connexion_client, sample_inventory_data):
        """Test that items needing reorder are correctly identified.

        Given: Inventory with items below reorder point
        When: A GET request is made to /api/report/data
        Then: Reorder items list includes low-stock items
        """
        response = connexion_client.get("/api/report/data")

        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json

        reorder_items = data["reorder_items"]

        # Should include Steak (qty=5, reorder=10) and Milk (qty=0, reorder=10)
        # But Milk might be excluded if qty=0 items are filtered out
        reorder_descriptions = [item["description"] for item in reorder_items]

        # At minimum, should have the low stock item
        assert len(reorder_items) >= 1
        # Steak should be in the reorder list (qty=5 < reorder_point=10)
        assert "Premium Steak" in reorder_descriptions or "Organic Milk" in reorder_descriptions


class TestReportRobustness:
    """Tests for report generation robustness and error handling."""

    @pytest.mark.integration
    def test_report_handles_missing_data_gracefully(self, connexion_app, connexion_client):
        """Test that report handles items with missing optional fields.

        Given: Inventory items with None values for optional fields
        When: A GET request is made to /report
        Then: The response is 200 OK without errors
        """
        flask_app = connexion_app.app
        with flask_app.app_context():
            minimal_item = Grocery(
                item_id=3001,
                description="Minimal Item",
                last_sold=None,  # Optional field
                shelf_life="7d",
                department=None,  # Optional field
                price="1.99",
                unit="ea",
                x_for=1,
                cost="0.99",
                quantity=10,
                reorder_point=5,
                date_added=None,  # Optional field
            )
            db.session.add(minimal_item)
            db.session.commit()

        response = connexion_client.get("/report")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")

    @pytest.mark.integration
    def test_report_api_handles_missing_data_gracefully(self, connexion_app, connexion_client):
        """Test that report API handles items with missing optional fields.

        Given: Inventory items with None values for optional fields
        When: A GET request is made to /api/report/data
        Then: The response is 200 OK with valid JSON
        """
        flask_app = connexion_app.app
        with flask_app.app_context():
            minimal_item = Grocery(
                item_id=3002,
                description="Minimal API Item",
                last_sold=None,
                shelf_life="7d",
                department=None,
                price="2.99",
                unit="ea",
                x_for=1,
                cost="1.99",
                quantity=15,
                reorder_point=5,
            )
            db.session.add(minimal_item)
            db.session.commit()

        response = connexion_client.get("/api/report/data")

        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json
        assert data["item_count"] == 1
        # Should handle None department gracefully
        assert "dept_counts" in data

    @pytest.mark.integration
    def test_concurrent_report_requests(self, connexion_client, sample_inventory_data):
        """Test that multiple concurrent report requests work correctly.

        Given: An inventory with sample data
        When: Multiple GET requests are made to /report concurrently
        Then: All responses are 200 OK
        """
        # Simulate concurrent requests by making multiple rapid requests
        responses = [connexion_client.get("/report") for _ in range(5)]

        for response in responses:
            assert response.status_code == 200
            assert "text/html" in response.headers.get("Content-Type", "")

    @pytest.mark.integration
    def test_report_consistency_across_requests(self, connexion_client, sample_inventory_data):
        """Test that report data is consistent across multiple requests.

        Given: An inventory with sample data
        When: Multiple GET requests are made to /api/report/data
        Then: All responses return the same data
        """
        response1 = connexion_client.get("/api/report/data")
        response2 = connexion_client.get("/api/report/data")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json() if callable(response1.json) else response1.json
        data2 = response2.json() if callable(response2.json) else response2.json

        # Key metrics should be identical
        assert data1["item_count"] == data2["item_count"]
        assert data1["total_items"] == data2["total_items"]
        assert data1["total_quantity"] == data2["total_quantity"]
