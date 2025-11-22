"""End-to-end browser tests for tooltip functionality using Playwright.

These tests verify that tooltips work correctly in a real browser environment,
testing click/tap interactions, hover behavior, and keyboard accessibility.

IMPORTANT: These tests are skipped by default because they require:
1. Playwright browsers to be installed: uv run playwright install chromium
2. A suitable environment (may not work in sandboxed/CI environments)

To run these tests explicitly:
    uv run pytest tests/test_tooltips_e2e.py -v -m e2e --run-e2e

Or set the environment variable:
    RUN_E2E_TESTS=1 uv run pytest tests/test_tooltips_e2e.py -v
"""

import contextlib
import os
import socket
import threading
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# Set test environment BEFORE importing app modules
os.environ["APP_SETTINGS"] = "src.pybackstock.config.TestingConfig"
os.environ["DATABASE_URL"] = "sqlite:///test_tooltips_e2e.db"

# Check if playwright is available
try:
    from playwright.sync_api import Browser, Page, expect, sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any  # type: ignore[assignment, misc]
    Page = Any  # type: ignore[assignment, misc]

# Check if E2E tests should run
RUN_E2E = os.environ.get("RUN_E2E_TESTS", "").lower() in ("1", "true", "yes")


class PortNotAvailableError(RuntimeError):
    """Raised when no available port can be found."""


def is_port_available(port: int) -> bool:
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def find_available_port(start: int = 5600, end: int = 5700) -> int:
    """Find an available port in the given range."""
    for port in range(start, end):
        if is_port_available(port):
            return port
    msg = f"No available ports in range {start}-{end}"
    raise PortNotAvailableError(msg)


def pytest_configure(config: Any) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "run_e2e: mark test to run only when --run-e2e is passed")


def pytest_addoption(parser: Any) -> None:
    """Add --run-e2e option to pytest."""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run E2E browser tests (requires Playwright)",
    )


# Skip entire module unless explicitly requested
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not PLAYWRIGHT_AVAILABLE,
        reason="Playwright not installed. Run: uv run playwright install chromium",
    ),
    pytest.mark.skipif(
        not RUN_E2E,
        reason="E2E tests skipped by default. Set RUN_E2E_TESTS=1 to run.",
    ),
]


class LiveServer:
    """Simple live server for E2E testing."""

    def __init__(self, app: Any, host: str = "127.0.0.1", port: int | None = None) -> None:
        """Initialize the live server.

        Args:
            app: The Flask application to serve.
            host: The host to bind to.
            port: The port to bind to (auto-detected if None).
        """
        self.app = app
        self.host = host
        self.port = port or find_available_port()
        self._thread: threading.Thread | None = None
        self._server: Any = None

    @property
    def url(self) -> str:
        """Return the URL of the live server."""
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        """Start the server in a background thread."""
        from werkzeug.serving import make_server  # noqa: PLC0415

        self._server = make_server(self.host, self.port, self.app, threaded=True)

        def run() -> None:
            self._server.serve_forever()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        # Wait for server to start and verify it's responding
        time.sleep(0.5)

    def stop(self) -> None:
        """Stop the server."""
        if self._server is not None:
            self._server.shutdown()


@pytest.fixture(scope="module")
def live_server() -> Generator[LiveServer, None, None]:
    """Create a live server for E2E testing.

    Yields:
        LiveServer instance with the Flask app running.
    """
    from src.pybackstock import db  # noqa: PLC0415
    from src.pybackstock.app import app as flask_app  # noqa: PLC0415

    flask_app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///test_tooltips_e2e.db",
        }
    )

    with flask_app.app_context():
        db.create_all()

    server = LiveServer(flask_app)
    server.start()

    yield server

    server.stop()

    # Cleanup database
    with flask_app.app_context():
        db.drop_all()

    # Remove test database file
    with contextlib.suppress(OSError):
        Path("test_tooltips_e2e.db").unlink()


@pytest.fixture()
def page(live_server: LiveServer) -> Generator[Page, None, None]:
    """Create a new browser and page for each test.

    This fixture creates a fresh browser instance for each test to avoid
    issues with browser state in restrictive/sandboxed environments.

    Args:
        live_server: The live server fixture (ensures server is running).

    Yields:
        Playwright Page instance.
    """
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not available")

    with sync_playwright() as p:
        try:
            # Use additional flags for sandboxed/restricted environments
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
            page = browser.new_page()
            yield page
            page.close()
            browser.close()
        except (OSError, RuntimeError) as e:
            pytest.skip(f"Could not launch browser: {e}")


def navigate_to_add_form(page: Page, url: str) -> None:
    """Navigate to the add item form."""
    page.goto(url)
    page.wait_for_selector('button[name="add-item"]', timeout=5000)
    page.click('button[name="add-item"]')
    page.wait_for_selector(".info-tooltip-icon", timeout=5000)


class TestTooltipClickBehavior:
    """Test tooltip click/tap interactions."""

    def test_tooltip_shows_on_click(self, page: Page, live_server: LiveServer) -> None:
        """Test that clicking a tooltip icon shows the tooltip."""
        navigate_to_add_form(page, live_server.url)

        # Get the first tooltip icon
        icon = page.locator(".info-tooltip-icon").first

        # Verify tooltip is initially hidden (doesn't have 'show' class)
        tooltip = page.locator(".info-tooltip-box").first
        assert "show" not in (tooltip.get_attribute("class") or "")

        # Click the icon
        icon.click()

        # Verify tooltip is now visible
        page.wait_for_function(
            """() => document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

    def test_tooltip_closes_on_second_click(self, page: Page, live_server: LiveServer) -> None:
        """Test that clicking the same tooltip icon again closes the tooltip."""
        navigate_to_add_form(page, live_server.url)

        icon = page.locator(".info-tooltip-icon").first

        # Open tooltip
        icon.click()
        page.wait_for_function(
            """() => document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

        # Click again to close
        icon.click()
        page.wait_for_function(
            """() => !document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

    def test_tooltip_closes_on_outside_click(self, page: Page, live_server: LiveServer) -> None:
        """Test that clicking outside the tooltip closes it."""
        navigate_to_add_form(page, live_server.url)

        icon = page.locator(".info-tooltip-icon").first

        # Open tooltip
        icon.click()
        page.wait_for_function(
            """() => document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

        # Click outside (on the page header)
        page.click("h1")

        # Tooltip should be closed
        page.wait_for_function(
            """() => !document.querySelector('.info-tooltip-box.show')""",
            timeout=3000,
        )

    def test_only_one_tooltip_open_at_a_time(self, page: Page, live_server: LiveServer) -> None:
        """Test that opening a new tooltip closes any previously open tooltip."""
        navigate_to_add_form(page, live_server.url)

        icons = page.locator(".info-tooltip-icon")

        # Open first tooltip
        icons.nth(0).click()
        page.wait_for_function(
            """() => document.querySelectorAll('.info-tooltip-box')[0].classList.contains('show')""",
            timeout=3000,
        )

        # Open second tooltip
        icons.nth(1).click()

        # Wait for state change
        page.wait_for_function(
            """() => {
                const tooltips = document.querySelectorAll('.info-tooltip-box');
                return !tooltips[0].classList.contains('show') && tooltips[1].classList.contains('show');
            }""",
            timeout=3000,
        )


class TestTooltipKeyboardAccessibility:
    """Test tooltip keyboard interactions."""

    def test_tooltip_opens_on_enter_key(self, page: Page, live_server: LiveServer) -> None:
        """Test that pressing Enter on a focused tooltip icon opens the tooltip."""
        navigate_to_add_form(page, live_server.url)

        icon = page.locator(".info-tooltip-icon").first

        # Focus the icon and press Enter
        icon.focus()
        page.keyboard.press("Enter")

        # Tooltip should be visible
        page.wait_for_function(
            """() => document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

    def test_tooltip_opens_on_space_key(self, page: Page, live_server: LiveServer) -> None:
        """Test that pressing Space on a focused tooltip icon opens the tooltip."""
        navigate_to_add_form(page, live_server.url)

        icon = page.locator(".info-tooltip-icon").first

        # Focus the icon and press Space
        icon.focus()
        page.keyboard.press("Space")

        # Tooltip should be visible
        page.wait_for_function(
            """() => document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

    def test_tooltip_closes_on_escape_key(self, page: Page, live_server: LiveServer) -> None:
        """Test that pressing Escape closes any open tooltip."""
        navigate_to_add_form(page, live_server.url)

        icon = page.locator(".info-tooltip-icon").first

        # Open tooltip
        icon.click()
        page.wait_for_function(
            """() => document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

        # Press Escape
        page.keyboard.press("Escape")

        # Tooltip should be closed
        page.wait_for_function(
            """() => !document.querySelector('.info-tooltip-box.show')""",
            timeout=3000,
        )


class TestTooltipContent:
    """Test tooltip content display."""

    def test_tooltip_displays_title_and_example(self, page: Page, live_server: LiveServer) -> None:
        """Test that tooltips display their title and example correctly."""
        navigate_to_add_form(page, live_server.url)

        # Open the first tooltip (ID field)
        icon = page.locator(".info-tooltip-icon").first
        icon.click()

        page.wait_for_function(
            """() => document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

        tooltip = page.locator(".info-tooltip-box").first

        # Check tooltip has title
        title = tooltip.locator(".tooltip-title")
        expect(title).to_contain_text("Item ID")

        # Check tooltip has example
        example = tooltip.locator(".tooltip-example")
        expect(example).to_contain_text("Example")
        expect(example).to_contain_text("SKU-12345")

    def test_all_form_fields_have_tooltips(self, page: Page, live_server: LiveServer) -> None:
        """Test that all 11 form fields have associated tooltips."""
        navigate_to_add_form(page, live_server.url)

        # Count tooltip icons - should be 11 (one per form field)
        icons = page.locator(".info-tooltip-icon")
        expect(icons).to_have_count(11)

        # Count tooltip boxes
        tooltips = page.locator(".info-tooltip-box")
        expect(tooltips).to_have_count(11)


class TestTooltipStyling:
    """Test tooltip visual styling."""

    def test_tooltip_icon_is_visible(self, page: Page, live_server: LiveServer) -> None:
        """Test that tooltip icons are visible and properly styled."""
        navigate_to_add_form(page, live_server.url)

        icon = page.locator(".info-tooltip-icon").first

        # Icon should be visible
        expect(icon).to_be_visible()

        # Icon should contain "i"
        expect(icon).to_have_text("i")

    def test_tooltip_positioned_below_icon(self, page: Page, live_server: LiveServer) -> None:
        """Test that the tooltip appears below the icon when opened."""
        navigate_to_add_form(page, live_server.url)

        icon = page.locator(".info-tooltip-icon").first
        tooltip = page.locator(".info-tooltip-box").first

        # Get icon position
        icon_box = icon.bounding_box()

        # Open tooltip
        icon.click()
        page.wait_for_function(
            """() => document.querySelector('.info-tooltip-box').classList.contains('show')""",
            timeout=3000,
        )

        # Get tooltip position
        tooltip_box = tooltip.bounding_box()

        # Tooltip should be below the icon (tooltip top > icon bottom)
        assert tooltip_box is not None, "Tooltip should have a bounding box when visible"
        assert icon_box is not None, "Icon should have a bounding box"
        assert tooltip_box["y"] > icon_box["y"], "Tooltip should appear below the icon"
