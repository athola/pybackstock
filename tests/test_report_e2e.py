"""End-to-end integration tests for report generation with actual server.

These tests start an actual server process to simulate production environment
and verify that report generation works correctly with the full stack.
"""

import concurrent.futures
import os
import pathlib
import time
from datetime import date
from multiprocessing import Process
from typing import Any

import pytest
import requests

# Must set environment before importing app modules
os.environ["APP_SETTINGS"] = "src.pybackstock.config.TestingConfig"
os.environ["DATABASE_URL"] = "sqlite:///test_e2e.db"

from src.pybackstock import Grocery, db
from src.pybackstock.connexion_app import create_app


def run_test_server(port: int) -> None:
    """Run a test server in a separate process.

    Args:
        port: Port number to run the server on.
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

    # Run the server
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


@pytest.fixture(scope="module")
def live_server() -> Any:
    """Start a live server for end-to-end testing.

    Yields:
        Server URL base.
    """
    port = 5555
    server_process = Process(target=run_test_server, args=(port,))
    server_process.start()

    # Wait for server to start
    base_url = f"http://127.0.0.1:{port}"
    max_retries = 30
    for _ in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    else:
        server_process.terminate()
        server_process.join()
        pytest.fail("Server failed to start in time")

    yield base_url

    # Cleanup
    server_process.terminate()
    server_process.join(timeout=5)
    if server_process.is_alive():
        server_process.kill()

    # Remove test database
    db_path = pathlib.Path("test_e2e.db")
    if db_path.exists():
        db_path.unlink()


@pytest.mark.e2e
class TestReportGenerationE2E:
    """End-to-end tests for report generation with live server."""

    def test_health_endpoint(self, live_server: str) -> None:
        """Test that health endpoint works.

        Args:
            live_server: Base URL of the live server.
        """
        response = requests.get(f"{live_server}/health", timeout=5)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_diagnostic_endpoint(self, live_server: str) -> None:
        """Test that diagnostic endpoint works and system is healthy.

        Args:
            live_server: Base URL of the live server.
        """
        response = requests.get(f"{live_server}/api/diagnostic", timeout=5)
        assert response.status_code in (200, 500)  # May have warnings but should respond
        data = response.json()
        assert "status" in data
        assert "checks" in data
        # Database should be ok
        assert data["checks"]["database"]["status"] == "ok"
        # Templates should be ok
        assert data["checks"]["templates"]["status"] == "ok"

    def test_report_generation_returns_html(self, live_server: str) -> None:
        """Test that /report endpoint returns HTML.

        Args:
            live_server: Base URL of the live server.
        """
        response = requests.get(f"{live_server}/report", timeout=10)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")
        assert "<!DOCTYPE html>" in response.text or "Inventory" in response.text

    def test_report_with_filters(self, live_server: str) -> None:
        """Test that /report works with visualization filters.

        Args:
            live_server: Base URL of the live server.
        """
        response = requests.get(
            f"{live_server}/report",
            params={"viz": ["stock_health", "department"]},
            timeout=10,
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")

    def test_report_data_api(self, live_server: str) -> None:
        """Test that /api/report/data returns JSON.

        Args:
            live_server: Base URL of the live server.
        """
        response = requests.get(f"{live_server}/api/report/data", timeout=10)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")
        data = response.json()
        assert "item_count" in data
        assert "total_items" in data
        assert data["item_count"] >= 0

    def test_concurrent_report_requests(self, live_server: str) -> None:
        """Test that multiple concurrent requests work.

        Args:
            live_server: Base URL of the live server.
        """

        def make_request() -> int:
            response = requests.get(f"{live_server}/report", timeout=10)
            return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(status == 200 for status in results)

    def test_report_error_handling(self, live_server: str) -> None:
        """Test that report endpoint handles errors gracefully.

        Args:
            live_server: Base URL of the live server.
        """
        # This should still work even with potentially invalid parameters
        response = requests.get(
            f"{live_server}/report",
            params={"viz": ["invalid_viz_name"]},
            timeout=10,
        )
        # Should return 200 even with invalid viz names (they're just ignored)
        assert response.status_code == 200
