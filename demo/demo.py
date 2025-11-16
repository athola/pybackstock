"""Interactive demo of the Backstock App using Playwright.

This script demonstrates the core features of the backstock inventory management application
by automating browser interactions with Playwright.

Enhanced with:
- CLI arguments for configuration
- Screenshot capture
- Summary reporting
- Configurable speed modes
- Database management options
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from playwright.sync_api import Page, sync_playwright


class DemoReport:
    """Track and report demo actions and results."""

    def __init__(self) -> None:
        """Initialize demo report."""
        self.actions: list[dict[str, Any]] = []
        self.start_time = datetime.now()

    def add_action(self, action: str, status: str, message: str) -> None:
        """Add an action to the report.

        Args:
            action: Name of the action performed.
            status: Status of the action (success/failed).
            message: Descriptive message about the action.
        """
        self.actions.append({"action": action, "status": status, "message": message, "timestamp": datetime.now()})

    def get_statistics(self) -> dict[str, Any]:
        """Calculate statistics for the demo run.

        Returns:
            Dictionary with total, successful, failed counts and success rate.
        """
        total = len(self.actions)
        successful = sum(1 for action in self.actions if action["status"] == "success")
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0.0

        return {"total": total, "successful": successful, "failed": failed, "success_rate": success_rate}

    def generate_summary(self) -> str:
        """Generate a formatted summary report.

        Returns:
            Formatted string with demo summary.
        """
        stats = self.get_statistics()
        duration = (datetime.now() - self.start_time).total_seconds()

        summary = [
            "\n" + "=" * 70,
            "  DEMO SUMMARY REPORT",
            "=" * 70,
            f"\nDuration: {duration:.2f} seconds",
            f"Total Actions: {stats['total']}",
            f"Successful: {stats['successful']}",
            f"Failed: {stats['failed']}",
            f"Success Rate: {stats['success_rate']:.2f}%",
            "\nActions Performed:",
        ]

        for i, action in enumerate(self.actions, 1):
            status_symbol = "[OK]" if action["status"] == "success" else "[FAILED]"
            summary.append(f"  {i}. {status_symbol} {action['action']}: {action['message']}")

        summary.append("=" * 70 + "\n")
        return "\n".join(summary)


def parse_arguments(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Optional list of arguments (for testing).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="Run interactive demo of the Backstock App")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument(
        "--speed", choices=["slow", "normal", "fast"], default="normal", help="Demo speed (default: normal)"
    )
    parser.add_argument("--screenshots", action="store_true", help="Capture screenshots during demo")
    parser.add_argument("--keep-db", action="store_true", help="Keep demo database after completion")
    parser.add_argument("--port", type=int, default=5000, help="Flask server port (default: 5000)")

    return parser.parse_args(args)


def get_speed_delay(speed: str) -> float:
    """Get delay time based on speed mode.

    Args:
        speed: Speed mode (slow/normal/fast).

    Returns:
        Delay time in seconds.
    """
    speed_delays = {"slow": 2.0, "normal": 1.0, "fast": 0.3}
    return speed_delays.get(speed, 1.0)


def get_browser_config(headless: bool, speed: str) -> dict[str, Any]:
    """Get browser launch configuration.

    Args:
        headless: Whether to run in headless mode.
        speed: Speed mode for slow_mo.

    Returns:
        Browser configuration dictionary.
    """
    config: dict[str, Any] = {"headless": headless}

    if not headless:
        slow_mo_delays = {"slow": 1000, "normal": 500, "fast": 200}
        config["slow_mo"] = slow_mo_delays.get(speed, 500)

    return config


def ensure_screenshot_dir() -> Path:
    """Ensure screenshot directory exists.

    Returns:
        Path to screenshot directory.
    """
    screenshot_dir = Path("demo_screenshots")
    screenshot_dir.mkdir(exist_ok=True)
    return screenshot_dir


def generate_screenshot_name(action: str) -> str:
    """Generate screenshot filename with timestamp.

    Args:
        action: Action name for the screenshot.

    Returns:
        Screenshot filename.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_action = action.replace(" ", "_").lower()
    return f"{timestamp}_{safe_action}.png"


def capture_screenshot(page: Page, action: str) -> Path:
    """Capture a screenshot of the current page state.

    Args:
        page: Playwright page object.
        action: Description of current action.

    Returns:
        Path to saved screenshot.
    """
    screenshot_dir = ensure_screenshot_dir()
    filename = generate_screenshot_name(action)
    screenshot_path = screenshot_dir / filename

    page.screenshot(path=str(screenshot_path))
    return screenshot_path


def verify_flask_running(url: str, timeout: int = 2) -> bool:
    """Verify Flask app is running.

    Args:
        url: URL to check.
        timeout: Request timeout in seconds.

    Returns:
        True if Flask is running, False otherwise.
    """
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def wait_for_flask(url: str = "http://127.0.0.1:5000", max_retries: int = 10, delay: float = 1.0) -> bool:
    """Wait for Flask to start with retries.

    Args:
        url: Flask URL to check.
        max_retries: Maximum number of retries.
        delay: Delay between retries in seconds.

    Returns:
        True if Flask started successfully, False otherwise.
    """
    for _attempt in range(max_retries):
        if verify_flask_running(url):
            return True
        time.sleep(delay)
    return False


def cleanup_demo_database() -> None:
    """Clean up the demo database file."""
    demo_db = Path("demo.db")
    if demo_db.exists():
        demo_db.unlink()


def print_demo_header(text: str) -> None:
    """Print a formatted demo section header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def wait_and_highlight(page: Page, selector: str, duration: float = 1.0) -> None:
    """Wait for element and highlight it briefly."""
    element = page.wait_for_selector(selector, timeout=5000)
    if element:
        page.evaluate(
            """(element) => {
            element.style.border = '3px solid #4CAF50';
            element.style.backgroundColor = '#e8f5e9';
        }""",
            element,
        )
        time.sleep(duration)


class DemoRunner:
    """Main demo runner class."""

    def __init__(
        self,
        headless: bool = False,
        speed: str = "normal",
        screenshots: bool = False,
        keep_db: bool = False,
        port: int = 5000,
    ) -> None:
        """Initialize demo runner.

        Args:
            headless: Run browser in headless mode.
            speed: Demo speed mode.
            screenshots: Capture screenshots.
            keep_db: Keep database after demo.
            port: Flask server port.
        """
        self.headless = headless
        self.speed = speed
        self.screenshots = screenshots
        self.keep_db = keep_db
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self.report = DemoReport()
        self.flask_process: subprocess.Popen[bytes] | None = None
        self.delay = get_speed_delay(speed)

    def start_flask(self) -> None:
        """Start Flask application."""
        print("Starting Flask application...")

        self.flask_process = subprocess.Popen(
            [sys.executable, "manage.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={
                **subprocess.os.environ,  # type: ignore[attr-defined]
                "DATABASE_URL": "sqlite:///demo.db",
                "APP_SETTINGS": "src.backstock.config.DevelopmentConfig",
            },
        )

        print("Waiting for Flask to initialize...")
        if not wait_for_flask(self.url, max_retries=15, delay=0.5):
            msg = "Flask failed to start within timeout period"
            raise RuntimeError(msg)

        print(f"[OK] Flask started successfully on {self.url}\n")
        self.report.add_action("Flask Startup", "success", "Application started successfully")

    def stop_flask(self) -> None:
        """Stop Flask application."""
        if self.flask_process:
            print("\nShutting down Flask application...")
            self.flask_process.terminate()
            self.flask_process.wait()
            self.report.add_action("Flask Shutdown", "success", "Application stopped")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_flask()

        if not self.keep_db:
            cleanup_demo_database()
            print("[OK] Demo database cleaned up")
        else:
            print("[OK] Demo database preserved (demo.db)")

    def demo_search_functionality(self, page: Page) -> None:
        """Demonstrate the search functionality."""
        print_demo_header("DEMO 1: Searching for Items")

        try:
            print("1. Clicking 'Search for an Item' button...")
            page.click("button:has-text('Search for an Item')")
            time.sleep(self.delay)

            if self.screenshots:
                capture_screenshot(page, "search_form")

            print("2. Searching by Description for 'Apple'...")
            page.select_option("select[name='column']", "description")
            page.fill("input[name='item']", "Apple")
            wait_and_highlight(page, "input[name='item']", 0.5)

            print("3. Submitting search...")
            page.click("button:has-text('Search')")
            time.sleep(self.delay * 1.5)

            if self.screenshots:
                capture_screenshot(page, "search_results")

            if page.query_selector(".result-item, table"):
                print("   [OK] Search results displayed successfully")
                self.report.add_action("Search Items", "success", "Searched for items by description")
            else:
                print("   [INFO] No items found (database may be empty)")
                self.report.add_action("Search Items", "success", "Search completed (no results)")

            time.sleep(self.delay)
        except Exception as e:
            self.report.add_action("Search Items", "failed", str(e))
            raise

    def demo_add_item_functionality(self, page: Page) -> None:
        """Demonstrate adding a single item."""
        print_demo_header("DEMO 2: Adding a Single Item")

        try:
            print("1. Clicking 'Add an Item' button...")
            page.click("button:has-text('Add an Item')")
            time.sleep(self.delay)

            if self.screenshots:
                capture_screenshot(page, "add_item_form")

            print("2. Filling out the form with sample data...")
            form_data = {
                "id-add": "9999",
                "description-add": "Demo Product",
                "last-sold-add": "2024-01-15",
                "shelf-life-add": "7d",
                "department-add": "Demo Dept",
                "price-add": "5.99",
                "unit-add": "ea",
                "xfor-add": "1",
                "cost-add": "3.99",
            }

            for field, value in form_data.items():
                selector = f"input[name='{field}']"
                if page.query_selector(selector):
                    page.fill(selector, value)
                    print(f"   - {field.replace('-add', '')}: {value}")

            time.sleep(self.delay)

            print("3. Submitting the form...")
            page.click("button:has-text('Add Item')")
            time.sleep(self.delay * 1.5)

            if self.screenshots:
                capture_screenshot(page, "item_added")

            print("   [OK] Form submitted")
            self.report.add_action("Add Item", "success", "Added demo product to inventory")
            time.sleep(self.delay)
        except Exception as e:
            self.report.add_action("Add Item", "failed", str(e))
            raise

    def demo_csv_upload_functionality(self, page: Page) -> None:
        """Demonstrate CSV upload functionality."""
        print_demo_header("DEMO 3: CSV Upload Capability")

        try:
            print("1. Clicking 'Upload CSV' / 'Add CSV' button...")
            page.click("button:has-text('Upload CSV'), button:has-text('Add CSV')")
            time.sleep(self.delay)

            if self.screenshots:
                capture_screenshot(page, "csv_upload_form")

            csv_input = page.query_selector("input[type='file'], input[name='csv-input']")
            if csv_input:
                print("2. CSV upload form is available")
                print("   Note: The application accepts CSV files with inventory data")
                self.report.add_action("CSV Upload View", "success", "CSV upload form displayed")
            else:
                print("   [INFO] CSV upload form not found on this page")
                self.report.add_action("CSV Upload View", "success", "Checked CSV functionality")

            time.sleep(self.delay * 1.5)
        except Exception as e:
            self.report.add_action("CSV Upload View", "failed", str(e))
            raise

    def demo_navigation(self, page: Page) -> None:
        """Demonstrate navigation between different views."""
        print_demo_header("DEMO 4: Navigation Between Views")

        try:
            print("1. Switching between different views...")

            views = [("Search for an Item", "search view"), ("Add an Item", "add item view")]

            for button_text, view_name in views:
                button = page.query_selector(f"button:has-text('{button_text}')")
                if button:
                    print(f"   - Switching to {view_name}...")
                    page.click(f"button:has-text('{button_text}')")
                    time.sleep(self.delay * 0.8)

                    if self.screenshots:
                        capture_screenshot(page, f"view_{view_name.replace(' ', '_')}")

            print("   [OK] Navigation demonstration complete")
            self.report.add_action("Navigation", "success", "Demonstrated view switching")
            time.sleep(self.delay)
        except Exception as e:
            self.report.add_action("Navigation", "failed", str(e))
            raise

    def run(self) -> None:
        """Run the complete demo."""
        print("\n" + "=" * 70)
        print("  INVENTORY APP - INTERACTIVE DEMONSTRATION")
        print("=" * 70)
        print("\nConfiguration:")
        print(f"  * Mode: {'Headless' if self.headless else 'Headed'}")
        print(f"  * Speed: {self.speed}")
        print(f"  * Screenshots: {'Enabled' if self.screenshots else 'Disabled'}")
        print(f"  * Keep DB: {'Yes' if self.keep_db else 'No'}")
        print(f"  * Port: {self.port}\n")

        try:
            self.start_flask()

            browser_config = get_browser_config(self.headless, self.speed)

            with sync_playwright() as p:
                print("Launching browser...\n")
                browser = p.chromium.launch(**browser_config)
                page = browser.new_page()
                page.set_viewport_size({"width": 1280, "height": 800})

                print(f"Navigating to {self.url}\n")
                page.goto(self.url, wait_until="networkidle")
                time.sleep(self.delay)

                if self.screenshots:
                    capture_screenshot(page, "homepage")

                # Run demo sections
                self.demo_search_functionality(page)
                self.demo_add_item_functionality(page)
                self.demo_csv_upload_functionality(page)
                self.demo_navigation(page)

                # Print summary
                print(self.report.generate_summary())

                if not self.headless:
                    print("Press Enter to close the browser and exit...")
                    input()

                browser.close()

        except Exception as e:
            print(f"\n[ERROR] Demo encountered an error: {e}")
            self.report.add_action("Demo Execution", "failed", str(e))
            raise
        finally:
            self.cleanup()
            print("\nDemo complete!")


def main() -> None:
    """Main entry point."""
    args = parse_arguments()

    runner = DemoRunner(
        headless=args.headless, speed=args.speed, screenshots=args.screenshots, keep_db=args.keep_db, port=args.port
    )

    runner.run()


if __name__ == "__main__":
    main()
