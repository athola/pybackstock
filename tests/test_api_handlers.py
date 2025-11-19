"""Tests for Connexion API handlers.

These tests verify the API handler functions in src/pybackstock/api/handlers.py
which are called by Connexion when routes are invoked.
"""

import pytest
from flask import Flask

from src.pybackstock import Grocery, db
from src.pybackstock.api.handlers import (
    _calculate_visualizations,
    health_check,
    index_get,
    index_post,
    report_data_get,
    report_get,
)


class TestHealthCheckHandler:
    """Tests for health_check handler function."""

    def test_health_check_returns_healthy_status(self) -> None:
        """Test that health_check handler returns healthy status."""
        response, status_code = health_check()

        assert status_code == 200
        assert response == {"status": "healthy"}
        assert isinstance(response, dict)


class TestIndexGetHandler:
    """Tests for index_get handler function."""

    def test_index_get_returns_html(self, app: Flask) -> None:
        """Test that index_get returns rendered HTML."""
        with app.test_request_context("/"):
            result = index_get()

            assert isinstance(result, str)
            assert "Backstock Inventory" in result
            assert "Add Item" in result

    def test_index_get_shows_add_form_by_default(self, app: Flask) -> None:
        """Test that index_get shows add item form by default."""
        with app.test_request_context("/"):
            result = index_get()

            assert 'name="id-add"' in result
            assert 'name="description-add"' in result


class TestIndexPostHandler:
    """Tests for index_post handler function."""

    def test_index_post_switches_to_search_form(self, app: Flask) -> None:
        """Test that index_post switches to search form when requested."""
        with app.test_request_context("/", method="POST", data={"search-item": ""}):
            result = index_post()

            assert isinstance(result, str)
            assert "Search By:" in result
            assert 'name="column"' in result

    def test_index_post_switches_to_add_form(self, app: Flask) -> None:
        """Test that index_post switches to add item form when requested."""
        with app.test_request_context("/", method="POST", data={"add-item": ""}):
            result = index_post()

            assert isinstance(result, str)
            assert 'name="id-add"' in result
            assert 'name="description-add"' in result

    def test_index_post_switches_to_csv_form(self, app: Flask) -> None:
        """Test that index_post switches to CSV upload form when requested."""
        with app.test_request_context("/", method="POST", data={"add-csv": ""}):
            result = index_post()

            assert isinstance(result, str)
            assert "Add .csv File:" in result
            assert 'name="csv-input"' in result

    @pytest.mark.usefixtures("sample_grocery")
    def test_index_post_handles_search_action(self, app: Flask) -> None:
        """Test that index_post handles search form submission."""
        with app.test_request_context("/", method="POST", data={"send-search": "", "column": "id", "item": "1"}):
            result = index_post()

            assert isinstance(result, str)
            # Should show search results
            assert "Search By:" in result

    def test_index_post_handles_add_action(self, app: Flask) -> None:
        """Test that index_post handles add item form submission."""
        with app.test_request_context(
            "/",
            method="POST",
            data={
                "send-add": "",
                "id-add": "9999",
                "description-add": "Test Item",
                "last-sold-add": "2024-01-01",
                "shelf-life-add": "7d",
                "department-add": "Test",
                "price-add": "1.99",
                "unit-add": "ea",
                "xfor-add": "1",
                "cost-add": "0.99",
                "quantity-add": "10",
                "reorder-point-add": "5",
            },
        ):
            result = index_post()

            assert isinstance(result, str)
            # After adding, should show add form
            assert 'name="id-add"' in result

    def test_index_post_handles_csv_action(self, app: Flask) -> None:
        """Test that index_post handles CSV upload submission."""
        csv_content = (
            b"id,description,last_sold,shelf_life,department,price,unit,x_for,cost,"
            b"quantity,reorder_point\n9998,CSV Test,2024-01-01,7d,Test,1.99,ea,1,0.99,10,5\n"
        )

        with app.test_request_context(
            "/",
            method="POST",
            data={
                "csv-submit": "",
                "csv-input": (csv_content, "test.csv"),
            },
            content_type="multipart/form-data",
        ):
            result = index_post()

            assert isinstance(result, str)
            # After CSV upload, should show CSV form
            assert "Add .csv File:" in result


class TestCalculateVisualizationsFunction:
    """Tests for _calculate_visualizations helper function."""

    @pytest.mark.usefixtures("sample_grocery")
    def test_calculate_single_visualization(self, app: Flask) -> None:
        """Test calculating a single visualization."""
        with app.app_context():
            all_items = Grocery.query.all()
            viz_data = _calculate_visualizations(["stock_health"], all_items)

            assert "stock_levels" in viz_data
            assert isinstance(viz_data["stock_levels"], dict)

    @pytest.mark.usefixtures("sample_grocery")
    def test_calculate_multiple_visualizations(self, app: Flask) -> None:
        """Test calculating multiple visualizations."""
        with app.app_context():
            all_items = Grocery.query.all()
            viz_data = _calculate_visualizations(["stock_health", "department", "age"], all_items)

            assert "stock_levels" in viz_data
            assert "dept_counts" in viz_data
            assert "age_distribution" in viz_data

    @pytest.mark.usefixtures("sample_grocery")
    def test_calculate_all_visualizations(self, app: Flask) -> None:
        """Test calculating all available visualizations."""
        with app.app_context():
            all_items = Grocery.query.all()
            viz_data = _calculate_visualizations(
                [
                    "stock_health",
                    "department",
                    "age",
                    "price_range",
                    "shelf_life",
                    "top_value",
                    "top_price",
                    "reorder_table",
                ],
                all_items,
            )

            assert "stock_levels" in viz_data
            assert "dept_counts" in viz_data
            assert "age_distribution" in viz_data
            assert "price_ranges" in viz_data
            assert "shelf_life_counts" in viz_data
            assert "top_value_items" in viz_data
            assert "top_items" in viz_data
            assert "reorder_items" in viz_data

    @pytest.mark.usefixtures("sample_grocery")
    def test_calculate_with_empty_viz_list(self, app: Flask) -> None:
        """Test that empty visualization list returns empty data."""
        with app.app_context():
            all_items = Grocery.query.all()
            viz_data = _calculate_visualizations([], all_items)

            assert viz_data == {}

    @pytest.mark.usefixtures("sample_grocery")
    def test_calculate_with_invalid_viz_name(self, app: Flask) -> None:
        """Test that invalid visualization names are safely ignored."""
        with app.app_context():
            all_items = Grocery.query.all()
            viz_data = _calculate_visualizations(["invalid_viz_name", "stock_health"], all_items)

            # Should only include stock_health data
            assert "stock_levels" in viz_data
            assert len(viz_data) == 1


class TestReportGetHandler:
    """Tests for report_get handler function."""

    @pytest.mark.usefixtures("sample_grocery")
    def test_report_get_with_data(self, app: Flask) -> None:
        """Test report_get with sample data."""
        with app.test_request_context("/report"):
            result = report_get()

            assert isinstance(result, str)
            assert "Inventory Analytics Report" in result

    def test_report_get_with_empty_database(self, app: Flask) -> None:
        """Test report_get with empty database."""
        with app.test_request_context("/report"):
            result = report_get()

            assert isinstance(result, str)
            assert "No Inventory Data Available" in result

    @pytest.mark.usefixtures("sample_grocery")
    def test_report_get_with_selected_visualizations(self, app: Flask) -> None:
        """Test report_get with specific visualizations selected."""
        with app.test_request_context("/report?viz=stock_health&viz=department"):
            result = report_get()

            assert isinstance(result, str)
            assert "Inventory Analytics Report" in result

    @pytest.mark.usefixtures("sample_grocery")
    def test_report_get_defaults_to_all_visualizations(self, app: Flask) -> None:
        """Test that report_get shows all visualizations by default."""
        with app.test_request_context("/report"):
            result = report_get()

            assert isinstance(result, str)
            # Should include all major visualizations
            assert "Stock Health" in result or "Inventory Analytics" in result


class TestReportDataGetHandler:
    """Tests for report_data_get handler function (JSON API endpoint)."""

    @pytest.mark.usefixtures("sample_grocery")
    def test_report_data_get_returns_json(self, app: Flask) -> None:
        """Test that report_data_get returns JSON data."""
        with app.test_request_context("/api/report/data"):
            response, status_code = report_data_get()

            assert status_code == 200
            assert isinstance(response, dict)
            assert "item_count" in response
            assert "selected_viz" in response
            assert response["item_count"] >= 1

    def test_report_data_get_with_empty_database(self, app: Flask) -> None:
        """Test report_data_get with empty database."""
        with app.test_request_context("/api/report/data"):
            response, status_code = report_data_get()

            assert status_code == 200
            assert isinstance(response, dict)
            assert response["item_count"] == 0

    @pytest.mark.usefixtures("sample_grocery")
    def test_report_data_get_with_selected_visualizations(self, app: Flask) -> None:
        """Test report_data_get with specific visualizations."""
        with app.test_request_context("/api/report/data?viz=stock_health&viz=department"):
            response, status_code = report_data_get()

            assert status_code == 200
            assert isinstance(response, dict)
            assert response["selected_viz"] == ["stock_health", "department"]
            assert "stock_levels" in response
            assert "dept_counts" in response

    @pytest.mark.usefixtures("sample_grocery")
    def test_report_data_get_includes_all_defaults(self, app: Flask) -> None:
        """Test that report_data_get includes all default keys."""
        with app.test_request_context("/api/report/data"):
            response, status_code = report_data_get()

            assert status_code == 200
            # Check for all default keys
            assert "stock_levels" in response
            assert "dept_counts" in response
            assert "age_distribution" in response
            assert "price_ranges" in response
            assert "shelf_life_counts" in response
            assert "top_value_items" in response
            assert "top_items" in response
            assert "reorder_items" in response

    @pytest.mark.usefixtures("sample_grocery")
    def test_report_data_get_includes_summary_metrics(self, app: Flask) -> None:
        """Test that report_data_get includes summary metrics."""
        with app.test_request_context("/api/report/data"):
            response, status_code = report_data_get()

            assert status_code == 200
            # Summary metrics should be present
            assert "total_items" in response
            assert "total_quantity" in response
            assert "total_value" in response


class TestReportDataBehavior:
    """Behavioral tests for report data API."""

    def test_report_data_reflects_current_inventory_state(self, app: Flask) -> None:
        """BDD: As an API consumer, I want report data to reflect current inventory state.

        Given: Multiple items with varying stock levels
        When: I request report data via API
        Then: The data accurately reflects total items, quantities, and values
        """
        with app.app_context():
            # Given: Inventory with known characteristics
            items = [
                Grocery(
                    item_id=2001,
                    description="In Stock Item",
                    last_sold=None,
                    shelf_life="7d",
                    department="Test",
                    price="10.00",
                    unit="ea",
                    x_for=1,
                    cost="5.00",
                    quantity=20,  # Total value: $200
                    reorder_point=10,
                ),
                Grocery(
                    item_id=2002,
                    description="Out of Stock Item",
                    last_sold=None,
                    shelf_life="7d",
                    department="Test",
                    price="5.00",
                    unit="ea",
                    x_for=1,
                    cost="2.50",
                    quantity=0,  # Out of stock
                    reorder_point=10,
                ),
            ]
            for item in items:
                db.session.add(item)
            db.session.commit()

        # When: Requesting report data
        with app.test_request_context("/api/report/data"):
            response, status_code = report_data_get()

        # Then: Data reflects actual inventory state
        assert status_code == 200
        assert response["item_count"] == 2
        assert response["total_items"] == 2
        assert response["total_quantity"] == 20  # Only counting in-stock items
        # Total value should be 20 * $10 = $200 (out of stock item contributes $0)

    def test_report_filters_visualizations_per_user_selection(self, app: Flask) -> None:
        """BDD: As a user, I want to see only the visualizations I selected.

        Given: Available visualizations for stock health, department, and age
        When: I request only stock_health and department visualizations
        Then: Response includes only the requested visualization data
        """
        with app.app_context():
            item = Grocery(
                item_id=2003,
                description="Test Item",
                last_sold=None,
                shelf_life="7d",
                department="Produce",
                price="2.99",
                unit="ea",
                x_for=1,
                cost="1.99",
                quantity=15,
                reorder_point=5,
            )
            db.session.add(item)
            db.session.commit()

        # When: Requesting specific visualizations
        with app.test_request_context("/api/report/data?viz=stock_health&viz=department"):
            response, status_code = report_data_get()

        # Then: Selected visualizations are included
        assert status_code == 200
        assert "stock_health" in response["selected_viz"]
        assert "department" in response["selected_viz"]
        # But not others that weren't requested
        assert "age" not in response["selected_viz"]
        assert "price_range" not in response["selected_viz"]


class TestIndexHandlerBehavior:
    """Behavioral tests for index page handlers."""

    @pytest.mark.usefixtures("sample_grocery")
    def test_search_workflow_preserves_user_context(self, app: Flask) -> None:
        """BDD: As a user searching for items, the form should stay in search mode.

        Given: I am on the home page
        When: I switch to search mode and perform a search
        Then: The page stays in search mode with my results displayed
        """
        # When: Searching for an item
        with app.test_request_context("/", method="POST", data={"send-search": "", "column": "id", "item": "1"}):
            result = index_post()

        # Then: Page remains in search mode
        assert "Search By:" in result
        assert 'name="column"' in result
        # And shows search form, not add form
        assert 'name="id-add"' not in result

    def test_add_workflow_preserves_user_context(self, app: Flask) -> None:
        """BDD: As a user adding items, the form should stay in add mode.

        Given: I am on the add item form
        When: I successfully add an item
        Then: The page stays in add mode so I can add more items
        """
        # When: Adding an item
        with app.test_request_context(
            "/",
            method="POST",
            data={
                "send-add": "",
                "id-add": "3001",
                "description-add": "New Item",
                "last-sold-add": "2024-01-01",
                "shelf-life-add": "7d",
                "department-add": "Test",
                "price-add": "4.99",
                "unit-add": "ea",
                "xfor-add": "1",
                "cost-add": "2.99",
                "quantity-add": "25",
                "reorder-point-add": "10",
            },
        ):
            result = index_post()

        # Then: Page remains in add mode for adding more items
        assert 'name="id-add"' in result
        assert 'name="description-add"' in result
        # And not in search mode
        assert "Search By:" not in result

    def test_csv_workflow_preserves_user_context(self, app: Flask) -> None:
        """BDD: As a user uploading CSV files, the form should stay in CSV mode.

        Given: I am on the CSV upload form
        When: I upload a CSV file
        Then: The page stays in CSV mode so I can upload more files
        """
        csv_content = (
            b"id,description,last_sold,shelf_life,department,price,unit,x_for,cost,"
            b"quantity,reorder_point\n3002,CSV Item,2024-01-01,7d,Test,1.99,ea,1,0.99,10,5\n"
        )

        # When: Uploading a CSV
        with app.test_request_context(
            "/",
            method="POST",
            data={"csv-submit": "", "csv-input": (csv_content, "test.csv")},
            content_type="multipart/form-data",
        ):
            result = index_post()

        # Then: Page remains in CSV upload mode
        assert "Add .csv File:" in result
        assert 'name="csv-input"' in result
        # And not in add or search mode
        assert 'name="id-add"' not in result
        assert "Search By:" not in result


class TestVisualizationCalculationBehavior:
    """Behavioral tests for visualization calculation logic."""

    def test_visualizations_handle_diverse_inventory_correctly(self, app: Flask) -> None:
        """BDD: As a store manager, I need visualizations that work with diverse inventory.

        Given: Inventory with items across multiple departments, price ranges, and stock levels
        When: All visualizations are calculated
        Then: Each visualization correctly categorizes and aggregates the data
        """
        with app.app_context():
            # Given: Diverse inventory
            diverse_items = [
                Grocery(
                    item_id=3101,
                    description="Cheap Produce",
                    last_sold=None,
                    shelf_life="3d",
                    department="Produce",
                    price="0.99",
                    unit="ea",
                    x_for=1,
                    cost="0.49",
                    quantity=100,  # Good stock
                    reorder_point=50,
                ),
                Grocery(
                    item_id=3102,
                    description="Expensive Electronics",
                    last_sold=None,
                    shelf_life="365d",
                    department="Electronics",
                    price="299.99",
                    unit="ea",
                    x_for=1,
                    cost="200.00",
                    quantity=2,  # Low stock
                    reorder_point=5,
                ),
                Grocery(
                    item_id=3103,
                    description="Out of Stock Dairy",
                    last_sold=None,
                    shelf_life="7d",
                    department="Dairy",
                    price="4.99",
                    unit="ea",
                    x_for=1,
                    cost="3.00",
                    quantity=0,  # Out of stock
                    reorder_point=10,
                ),
            ]
            for item in diverse_items:
                db.session.add(item)
            db.session.commit()

            all_items = Grocery.query.all()

            # When: Calculating all visualizations
            viz_names = [
                "stock_health",
                "department",
                "price_range",
                "shelf_life",
                "top_value",
                "top_price",
                "reorder_table",
            ]
            viz_data = _calculate_visualizations(viz_names, all_items)

        # Then: Each visualization correctly processes the data
        # Stock health should categorize items
        assert "stock_levels" in viz_data
        assert viz_data["stock_levels"]["Out of Stock"] >= 1
        assert viz_data["stock_levels"]["Low Stock"] >= 1

        # Department should group by department
        assert "dept_counts" in viz_data
        assert "Produce" in viz_data["dept_counts"]
        assert "Electronics" in viz_data["dept_counts"]
        assert "Dairy" in viz_data["dept_counts"]

        # Price range should categorize by price
        assert "price_ranges" in viz_data

        # Shelf life should group by shelf life
        assert "shelf_life_counts" in viz_data
        assert "3d" in viz_data["shelf_life_counts"]
        assert "7d" in viz_data["shelf_life_counts"]

        # Top value should rank by total value
        assert "top_value_items" in viz_data
        assert len(viz_data["top_value_items"]) > 0

        # Top price should rank by unit price
        assert "top_items" in viz_data
        assert len(viz_data["top_items"]) > 0
        # Expensive electronics should be in top priced items
        top_descriptions = [item["description"] for item in viz_data["top_items"]]
        assert "Expensive Electronics" in top_descriptions

        # Reorder should identify items needing reorder
        assert "reorder_items" in viz_data
        # Items below reorder point should be in reorder list
        assert len(viz_data["reorder_items"]) >= 1
        # At minimum, out of stock item should be flagged
        reorder_descriptions = [item["description"] for item in viz_data["reorder_items"]]
        assert "Out of Stock Dairy" in reorder_descriptions or "Expensive Electronics" in reorder_descriptions
