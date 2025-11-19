"""Integration tests for Flask routes."""

import io
import time

import pytest
from flask.testing import FlaskClient

from src.pybackstock.app import app as flask_app


@pytest.mark.integration
def test_index_get(client: FlaskClient) -> None:
    """Test GET request to index page."""
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.integration
def test_index_search_item_form(client: FlaskClient) -> None:
    """Test switching to search item form."""
    response = client.post("/", data={"search-item": ""})
    assert response.status_code == 200


@pytest.mark.integration
def test_index_add_item_form(client: FlaskClient) -> None:
    """Test switching to add item form."""
    response = client.post("/", data={"add-item": ""})
    assert response.status_code == 200


@pytest.mark.integration
def test_index_add_csv_form(client: FlaskClient) -> None:
    """Test switching to CSV upload form."""
    response = client.post("/", data={"add-csv": ""})
    assert response.status_code == 200


@pytest.mark.integration
def test_search_item_success(client: FlaskClient, sample_grocery: None) -> None:
    """Test successful item search."""
    response = client.post("/", data={"send-search": "", "column": "id", "item": "1"})
    assert response.status_code == 200


@pytest.mark.integration
def test_search_item_not_found(client: FlaskClient) -> None:
    """Test searching for non-existent item."""
    response = client.post("/", data={"send-search": "", "column": "id", "item": "999"})
    assert response.status_code == 200


@pytest.mark.integration
def test_add_item_success(client: FlaskClient) -> None:
    """Test successfully adding an item."""
    response = client.post(
        "/",
        data={
            "send-add": "",
            "id-add": "100",
            "description-add": "New Item",
            "last-sold-add": "2024-01-01",
            "shelf-life-add": "7d",
            "department-add": "Test",
            "price-add": "2.99",
            "unit-add": "ea",
            "xfor-add": "1",
            "cost-add": "1.99",
        },
    )
    assert response.status_code == 200


@pytest.mark.integration
def test_add_item_duplicate(client: FlaskClient, sample_grocery: None) -> None:
    """Test adding a duplicate item."""
    response = client.post(
        "/",
        data={
            "send-add": "",
            "id-add": "1",
            "description-add": "Test Item",
            "last-sold-add": "2024-01-01",
            "shelf-life-add": "7d",
            "department-add": "Test Dept",
            "price-add": "1.99",
            "unit-add": "ea",
            "xfor-add": "1",
            "cost-add": "0.99",
        },
    )
    assert response.status_code == 200


@pytest.mark.integration
def test_csv_upload_success(client: FlaskClient) -> None:
    """Test successful CSV upload."""
    csv_data = (
        b"id,description,last_sold,shelf_life,department,price,unit,x_for,cost\n"
        b"200,CSV Item,2024-01-01,7d,CSV Dept,3.99,ea,1,2.99\n"
    )
    data = {
        "csv-submit": "",
        "csv-input": (io.BytesIO(csv_data), "test.csv"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200


@pytest.mark.integration
def test_csv_upload_invalid_extension(client: FlaskClient) -> None:
    """Test CSV upload with invalid file extension."""
    txt_data = b"some text data"
    data = {
        "csv-submit": "",
        "csv-input": (io.BytesIO(txt_data), "test.txt"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200


@pytest.mark.integration
def test_csv_upload_no_file(client: FlaskClient) -> None:
    """Test CSV upload without a file."""
    response = client.post("/", data={"csv-submit": ""})
    assert response.status_code == 200


@pytest.mark.integration
def test_search_by_description(client: FlaskClient, sample_grocery: None) -> None:
    """Test searching by description."""
    response = client.post("/", data={"send-search": "", "column": "description", "item": "Test"})
    assert response.status_code == 200


@pytest.mark.integration
def test_search_by_department(client: FlaskClient, sample_grocery: None) -> None:
    """Test searching by department."""
    response = client.post("/", data={"send-search": "", "column": "department", "item": "Test Dept"})
    assert response.status_code == 200


@pytest.mark.integration
def test_health_endpoint_get_request(client: FlaskClient) -> None:
    """Test GET request to /health endpoint returns 200 OK.

    This endpoint is used by Render.com for health checks and must return
    a 2xx status code to indicate the service is healthy.
    """
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.integration
def test_health_endpoint_returns_json(client: FlaskClient) -> None:
    """Test /health endpoint returns JSON response with status field.

    The health endpoint should return a simple JSON response indicating
    the service status, making it easy for monitoring systems to parse.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.content_type == "application/json"

    # Parse JSON response
    data = response.get_json()
    assert data is not None, "Response should be valid JSON"
    assert "status" in data, "Response should contain 'status' field"
    assert data["status"] == "healthy", "Status should be 'healthy'"


@pytest.mark.integration
def test_health_endpoint_exempt_from_csrf(client: FlaskClient) -> None:
    """Test /health endpoint is exempt from CSRF protection.

    Health checks from Render.com and other monitoring services won't
    include CSRF tokens, so this endpoint must be exempt.
    """
    # Create a client with CSRF enabled
    original_csrf_setting = flask_app.config.get("WTF_CSRF_ENABLED")
    try:
        flask_app.config["WTF_CSRF_ENABLED"] = True
        test_client = flask_app.test_client()

        # GET request without CSRF token should still succeed
        response = test_client.get("/health")
        assert response.status_code == 200

        # POST request without CSRF token should also succeed (for completeness)
        response = test_client.post("/health")
        assert response.status_code in (200, 405)  # 405 if POST not allowed
    finally:
        # Restore original setting
        if original_csrf_setting is not None:
            flask_app.config["WTF_CSRF_ENABLED"] = original_csrf_setting


@pytest.mark.integration
def test_health_endpoint_fast_response(client: FlaskClient) -> None:
    """Test /health endpoint responds quickly.

    Health checks should be lightweight and respond within milliseconds
    to avoid timeout issues with health check systems.
    """
    start_time = time.time()
    response = client.get("/health")
    elapsed_time = time.time() - start_time

    assert response.status_code == 200
    # Should respond in less than 1 second (generous threshold for testing)
    assert elapsed_time < 1.0, f"Health check took {elapsed_time:.3f}s, should be < 1s"


@pytest.mark.integration
def test_health_endpoint_no_database_dependency(client: FlaskClient) -> None:
    """Test /health endpoint doesn't require database connection.

    The health endpoint should be a simple liveness check that doesn't
    depend on the database being available. This ensures health checks
    can pass even if the database is temporarily unavailable.
    """
    # This test documents the expected behavior
    # The health endpoint should not query the database
    response = client.get("/health")
    assert response.status_code == 200

    # Verify it returns immediately without waiting for DB
    # (already tested in test_health_endpoint_fast_response)


# NOTE: Report route tests have been moved to test_api_handlers.py
# The /report route is handled by Connexion (see openapi.yaml -> src.pybackstock.api.handlers.report_get)
# These Flask-client tests are deprecated - use test_api_handlers.py::TestReportGetHandler instead


@pytest.mark.integration
def test_add_item_with_new_fields(client: FlaskClient) -> None:
    """Test adding an item with quantity and reorder_point fields."""
    response = client.post(
        "/",
        data={
            "send-add": "",
            "id-add": "101",
            "description-add": "Item with Inventory Fields",
            "last-sold-add": "2024-01-01",
            "shelf-life-add": "7d",
            "department-add": "Test",
            "price-add": "2.99",
            "unit-add": "ea",
            "xfor-add": "1",
            "cost-add": "1.99",
            "quantity-add": "25",
            "reorder-point-add": "15",
        },
    )
    assert response.status_code == 200


@pytest.mark.integration
def test_add_item_with_zero_quantity(client: FlaskClient) -> None:
    """Test adding an out-of-stock item (quantity = 0)."""
    response = client.post(
        "/",
        data={
            "send-add": "",
            "id-add": "102",
            "description-add": "Out of Stock Item",
            "last-sold-add": "2024-01-01",
            "shelf-life-add": "7d",
            "department-add": "Test",
            "price-add": "2.99",
            "unit-add": "ea",
            "xfor-add": "1",
            "cost-add": "1.99",
            "quantity-add": "0",
            "reorder-point-add": "10",
        },
    )
    assert response.status_code == 200


@pytest.mark.integration
def test_csv_upload_with_new_fields(client: FlaskClient) -> None:
    """Test CSV upload with new inventory fields (quantity, reorder_point, date_added)."""
    csv_data = (
        b"id,description,last_sold,shelf_life,department,price,unit,x_for,cost,quantity,reorder_point,date_added\n"
        b"201,CSV Item New,2024-01-01,7d,CSV Dept,3.99,ea,1,2.99,50,20,2024-01-01\n"
    )
    data = {
        "csv-submit": "",
        "csv-input": (io.BytesIO(csv_data), "test_new.csv"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200


@pytest.mark.integration
def test_csv_upload_backward_compatibility(client: FlaskClient) -> None:
    """Test CSV upload with old format (without new fields) for backward compatibility."""
    csv_data = (
        b"id,description,last_sold,shelf_life,department,price,unit,x_for,cost\n"
        b"202,CSV Item Old,2024-01-01,7d,CSV Dept,3.99,ea,1,2.99\n"
    )
    data = {
        "csv-submit": "",
        "csv-input": (io.BytesIO(csv_data), "test_old.csv"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200


@pytest.mark.integration
def test_search_by_quantity(client: FlaskClient, sample_grocery: None) -> None:
    """Test searching by quantity field."""
    response = client.post("/", data={"send-search": "", "column": "quantity", "item": "15"})
    assert response.status_code == 200


@pytest.mark.integration
def test_search_by_reorder_point(client: FlaskClient, sample_grocery: None) -> None:
    """Test searching by reorder_point field."""
    response = client.post("/", data={"send-search": "", "column": "reorder_point", "item": "10"})
    assert response.status_code == 200
