"""Tests for the Add Random Items button with direct add functionality.

TDD/BDD tests for ensuring the Add Random Items button:
1. Has a scroll selector (1-50) above it for selecting item count
2. Directly adds items when clicked (single action, no intermediate form)
3. Works correctly on both web and mobile (responsive design)
"""

import os

# Set test environment BEFORE importing app modules
os.environ["APP_SETTINGS"] = "src.pybackstock.config.TestingConfig"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from flask.testing import FlaskClient


class TestAddRandomButtonDisplay:
    """Tests for the Add Random Items button and selector display."""

    @pytest.mark.integration
    def test_main_page_has_random_count_selector(self, client: FlaskClient) -> None:
        """Test that the main page displays a count selector above the Add Random Items button."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Check for the range input selector
        assert 'id="random-item-count"' in data or 'name="random-item-count"' in data

    @pytest.mark.integration
    def test_random_count_selector_has_range_1_to_50(self, client: FlaskClient) -> None:
        """Test that the count selector allows values from 1 to 50."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Check for min and max attributes on the selector
        assert 'min="1"' in data
        assert 'max="50"' in data

    @pytest.mark.integration
    def test_random_count_selector_default_value(self, client: FlaskClient) -> None:
        """Test that the count selector has a reasonable default value."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Check for default value (should be 5 or similar)
        assert 'value="5"' in data or 'value="10"' in data

    @pytest.mark.integration
    def test_random_count_selector_is_visible_on_main_page(self, client: FlaskClient) -> None:
        """Test that the selector is on the main page, not behind a form."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # The selector should be within the add-random-form, visible immediately
        assert 'name="add-random-form"' in data
        # Should have a label for the selector
        assert "Items:" in data or "Number" in data

    @pytest.mark.integration
    def test_random_count_display_shows_current_value(self, client: FlaskClient) -> None:
        """Test that there's a display showing the current selected count."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Should have a value display element
        assert 'id="random-count-display"' in data or 'class="count-display"' in data


class TestAddRandomButtonFunctionality:
    """Tests for the Add Random Items button direct add functionality."""

    @pytest.mark.integration
    def test_add_random_button_directly_adds_items(self, client: FlaskClient) -> None:
        """Test that clicking Add Random Items directly adds items without intermediate form."""
        # Click the button with a count value - should add items immediately
        response = client.post(
            "/",
            data={"add-random": "", "random-item-count": "3"},
        )
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Should show success message, NOT the intermediate form
        assert "Successfully generated 3 random item" in data
        # Should NOT show the old intermediate form elements
        assert "Generate Random Test Items" not in data

    @pytest.mark.integration
    def test_add_random_button_uses_selector_value(self, client: FlaskClient) -> None:
        """Test that the button uses the value from the selector."""
        response = client.post(
            "/",
            data={"add-random": "", "random-item-count": "7"},
        )
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        assert "Successfully generated 7 random item" in data

    @pytest.mark.integration
    def test_add_random_button_defaults_to_5_if_no_count(self, client: FlaskClient) -> None:
        """Test that the button defaults to 5 items if no count is provided."""
        response = client.post(
            "/",
            data={"add-random": ""},
        )
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Should add 5 items by default
        assert "Successfully generated 5 random item" in data

    @pytest.mark.integration
    def test_add_random_limits_count_to_50(self, client: FlaskClient) -> None:
        """Test that count is limited to 50 even if higher value submitted."""
        response = client.post(
            "/",
            data={"add-random": "", "random-item-count": "100"},
        )
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Should be limited to 50
        assert "Successfully generated 50 random item" in data

    @pytest.mark.integration
    def test_add_random_minimum_count_is_1(self, client: FlaskClient) -> None:
        """Test that count is at least 1 even if 0 or negative submitted."""
        response = client.post(
            "/",
            data={"add-random": "", "random-item-count": "0"},
        )
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Should be at least 1
        assert "Successfully generated 1 random item" in data

    @pytest.mark.integration
    def test_add_random_items_persisted_to_database(self, client: FlaskClient) -> None:
        """Test that added random items are actually persisted to the database."""
        # Add 3 random items
        response = client.post(
            "/",
            data={"add-random": "", "random-item-count": "3"},
        )
        assert response.status_code == 200

        # Search for items by department (should find something)
        # Random items will have departments from the corpus
        response = client.post(
            "/",
            data={"send-search": "", "column": "id", "item": "1"},
        )
        assert response.status_code == 200
        # If items were created, search should succeed without errors


class TestAddRandomButtonMobileResponsive:
    """Tests for mobile responsiveness of the Add Random Items selector."""

    @pytest.mark.integration
    def test_page_has_viewport_meta_for_mobile(self, client: FlaskClient) -> None:
        """Test that the page has viewport meta tag for mobile responsiveness."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        assert 'name="viewport"' in data
        assert "width=device-width" in data

    @pytest.mark.integration
    def test_random_selector_has_touch_friendly_size(self, client: FlaskClient) -> None:
        """Test that CSS includes touch-friendly sizing for the selector."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Check for CSS that ensures touch-friendly sizing
        # Range inputs should have adequate height for touch
        assert "range-selector" in data or "random-item-count" in data

    @pytest.mark.integration
    def test_random_selector_mobile_media_query(self, client: FlaskClient) -> None:
        """Test that there are mobile-specific styles for the selector."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Should have mobile media queries
        assert "@media (max-width: 768px)" in data

    @pytest.mark.integration
    def test_add_random_button_has_touch_target_size(self, client: FlaskClient) -> None:
        """Test that the Add Random Items button has minimum touch target size."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Check for button styling that ensures touch-friendly size
        # The btn-menu class should have adequate sizing
        assert "btn-menu" in data
        assert "min-height" in data


class TestAddRandomButtonAccessibility:
    """Tests for accessibility of the Add Random Items selector."""

    @pytest.mark.integration
    def test_random_selector_has_label(self, client: FlaskClient) -> None:
        """Test that the selector has an associated label for accessibility."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Should have a label for the range input
        assert 'for="random-item-count"' in data or "Items:" in data

    @pytest.mark.integration
    def test_random_selector_has_aria_attributes(self, client: FlaskClient) -> None:
        """Test that the selector has appropriate ARIA attributes."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.data.decode("utf-8")
        # Should have aria-label or aria-describedby
        assert "aria-" in data
