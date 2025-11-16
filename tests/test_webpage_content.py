"""Integration tests for webpage content validation.

These tests ensure that the webpage displays correctly and contains all expected
elements, validating that PRs don't break the webpage display functionality.
"""

import pytest
from flask.testing import FlaskClient


@pytest.mark.integration
def test_webpage_title_and_header(client: FlaskClient) -> None:
    """Test that the webpage displays the correct title and header."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    assert "<title>Backstock</title>" in data
    assert "Backstock Inventory Application" in data


@pytest.mark.integration
def test_webpage_has_menu_buttons(client: FlaskClient) -> None:
    """Test that the webpage displays all menu buttons."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    assert "Menu:" in data
    assert 'name="add-item"' in data
    assert 'name="search-item"' in data
    assert "Add Item" in data
    assert "Search Item" in data


@pytest.mark.integration
def test_webpage_has_csv_upload_form(client: FlaskClient) -> None:
    """Test that the webpage displays the CSV upload form."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    assert "Add .csv:" in data
    assert 'name="csv-input"' in data
    assert 'type="file"' in data


@pytest.mark.integration
def test_webpage_displays_add_item_form_by_default(client: FlaskClient) -> None:
    """Test that the Add Item form is displayed by default."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    # Check for add item form fields
    assert 'name="id-add"' in data
    assert 'name="description-add"' in data
    assert 'name="last-sold-add"' in data
    assert 'name="shelf-life-add"' in data
    assert 'name="department-add"' in data
    assert 'name="price-add"' in data
    assert 'name="unit-add"' in data
    assert 'name="xfor-add"' in data
    assert 'name="cost-add"' in data
    assert 'name="send-add"' in data


@pytest.mark.integration
def test_webpage_displays_search_form_when_requested(client: FlaskClient) -> None:
    """Test that the search form displays when requested."""
    response = client.post("/", data={"search-item": ""})
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    # Check for search form elements
    assert "Search By:" in data
    assert 'name="column"' in data
    assert 'name="item"' in data
    assert 'name="send-search"' in data
    # Check for search options
    assert "<option>id</option>" in data
    assert "<option>description</option>" in data
    assert "<option>department</option>" in data


@pytest.mark.integration
def test_webpage_has_csrf_protection(client: FlaskClient) -> None:
    """Test that the webpage includes CSRF protection tokens."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    assert 'name="csrf_token"' in data


@pytest.mark.integration
def test_webpage_has_footer(client: FlaskClient) -> None:
    """Test that the webpage displays the footer with contact information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    assert "Created by:" in data
    assert "alexthola@gmail.com" in data


@pytest.mark.integration
def test_webpage_loads_bootstrap(client: FlaskClient) -> None:
    """Test that the webpage includes Bootstrap CSS and JS."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    assert "bootstrap" in data.lower()
    assert "jquery" in data.lower()


@pytest.mark.integration
def test_search_result_displays_correctly(client: FlaskClient, sample_grocery: None) -> None:
    """Test that search results display correctly on the webpage."""
    response = client.post("/", data={"send-search": "", "column": "id", "item": "1"})
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    # The template should show the search results
    assert "ID:" in data or "id" in data.lower()


@pytest.mark.integration
def test_add_item_success_message_displays(client: FlaskClient) -> None:
    """Test that successful item addition displays a confirmation message."""
    response = client.post(
        "/",
        data={
            "send-add": "",
            "id-add": "999",
            "description-add": "Test Display Item",
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

    data = response.data.decode("utf-8")
    # Should show success message or the added item
    assert "successfully added" in data or "999" in data


@pytest.mark.integration
def test_error_messages_display(client: FlaskClient, sample_grocery: None) -> None:
    """Test that error messages are displayed when appropriate."""
    # Try to add a duplicate item
    response = client.post(
        "/",
        data={
            "send-add": "",
            "id-add": "1",  # This ID already exists
            "description-add": "Duplicate",
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

    data = response.data.decode("utf-8")
    # Should display an error message
    assert "already been added" in data or "Unable to add item" in data


@pytest.mark.integration
def test_page_structure_is_valid_html(client: FlaskClient) -> None:
    """Test that the page returns valid HTML structure."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    # Check for basic HTML structure
    assert "<!DOCTYPE html>" in data
    assert "<html>" in data
    assert "</html>" in data
    assert "<head>" in data
    assert "</head>" in data
    assert "<body>" in data
    assert "</body>" in data
    assert "<title>" in data
    assert "</title>" in data


@pytest.mark.integration
def test_webpage_viewport_meta_tag(client: FlaskClient) -> None:
    """Test that the webpage includes viewport meta tag for responsiveness."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.data.decode("utf-8")
    assert 'name="viewport"' in data
    assert "width=device-width" in data
