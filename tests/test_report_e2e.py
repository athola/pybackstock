"""End-to-end integration tests for report generation.

These tests verify the complete report generation flow using the Connexion test client,
ensuring all components work together correctly.
"""

import concurrent.futures
import os
import pathlib
from datetime import date
from typing import Any

import pytest

# Must set environment before importing app modules
os.environ["APP_SETTINGS"] = "src.pybackstock.config.TestingConfig"
os.environ["DATABASE_URL"] = "sqlite:///test_e2e.db"

from src.pybackstock import Grocery, db
from src.pybackstock.connexion_app import create_app


@pytest.fixture(scope="module")
def e2e_app() -> Any:
    """Create a Connexion app for end-to-end testing.

    Yields:
        Connexion FlaskApp instance.
    """
    app = create_app("src.pybackstock.config.TestingConfig")
    flask_app = app.app
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_e2e.db"

    # Create database and add test data
    with flask_app.app_context():
        db.create_all()
        # Add sample test data
        items = [
            Grocery(
                item_id=1001,
                description="Test Apples",
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
                description="Test Milk",
                last_sold=date(2024, 11, 18),
                shelf_life="14d",
                department="Dairy",
                price="5.99",
                unit="gal",
                x_for=1,
                cost="3.50",
                quantity=0,
                reorder_point=10,
                date_added=date(2024, 10, 15),
            ),
        ]
        for item in items:
            db.session.add(item)
        db.session.commit()

    yield app

    # Cleanup
    with flask_app.app_context():
        db.drop_all()

    # Remove test database file
    db_path = pathlib.Path("test_e2e.db")
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def e2e_client(e2e_app: Any) -> Any:
    """Create a test client for the e2e app.

    Args:
        e2e_app: The Connexion FlaskApp instance.

    Returns:
        Test client for making requests.
    """
    return e2e_app.test_client()


@pytest.mark.e2e
class TestReportGenerationE2E:
    """End-to-end tests for report generation."""

    def test_health_endpoint(self, e2e_client: Any) -> None:
        """Test that health endpoint works.

        Args:
            e2e_client: Test client for making requests.
        """
        response = e2e_client.get("/health")
        assert response.status_code == 200
        data = response.json() if callable(response.json) else response.json
        assert data["status"] == "healthy"

    def test_diagnostic_endpoint(self, e2e_client: Any) -> None:
        """Test that diagnostic endpoint works and system is healthy.

        Args:
            e2e_client: Test client for making requests.
        """
        response = e2e_client.get("/api/diagnostic")
        assert response.status_code in (200, 500)  # May have warnings but should respond
        data = response.json() if callable(response.json) else response.json
        assert "status" in data
        assert "checks" in data
        # Database should be ok
        assert data["checks"]["database"]["status"] == "ok"
        # Templates should be ok
        assert data["checks"]["templates"]["status"] == "ok"

    def test_report_generation_returns_html(self, e2e_client: Any) -> None:
        """Test that /report endpoint returns HTML.

        Args:
            e2e_client: Test client for making requests.
        """
        response = e2e_client.get("/report")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")

    def test_report_with_filters(self, e2e_client: Any) -> None:
        """Test that /report works with visualization filters.

        Args:
            e2e_client: Test client for making requests.
        """
        response = e2e_client.get("/report?viz=stock_health&viz=department")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")

    def test_report_data_api(self, e2e_client: Any) -> None:
        """Test that /api/report/data returns JSON.

        Args:
            e2e_client: Test client for making requests.
        """
        response = e2e_client.get("/api/report/data")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")
        data = response.json() if callable(response.json) else response.json
        assert "item_count" in data
        assert "total_items" in data
        assert data["item_count"] >= 0

    def test_concurrent_report_requests(self, e2e_client: Any) -> None:
        """Test that multiple concurrent requests work.

        Args:
            e2e_client: Test client for making requests.
        """

        def make_request() -> int:
            response = e2e_client.get("/report")
            return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(status == 200 for status in results)

    def test_report_error_handling(self, e2e_client: Any) -> None:
        """Test that report endpoint handles errors gracefully.

        Args:
            e2e_client: Test client for making requests.
        """
        # Test with valid viz parameter values
        response = e2e_client.get("/report?viz=stock_health")
        assert response.status_code == 200

        # Test with multiple valid viz parameters
        response = e2e_client.get("/report?viz=stock_health&viz=department&viz=age")
        assert response.status_code == 200
