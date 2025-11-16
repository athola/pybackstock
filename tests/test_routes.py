"""Integration tests for Flask routes."""

import io

import pytest
from flask.testing import FlaskClient


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
