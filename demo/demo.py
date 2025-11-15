"""Interactive demo of the Inventory App using Playwright.

This script demonstrates the core features of the inventory management application
by automating browser interactions with Playwright.
"""

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


def print_demo_header(text: str) -> None:
    """Print a formatted demo section header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def wait_and_highlight(page: Page, selector: str, duration: float = 1.0) -> None:
    """Wait for element and highlight it briefly."""
    element = page.wait_for_selector(selector)
    if element:
        page.evaluate(
            """(element) => {
            element.style.border = '3px solid #4CAF50';
            element.style.backgroundColor = '#e8f5e9';
        }""",
            element,
        )
        time.sleep(duration)


def demo_search_functionality(page: Page) -> None:
    """Demonstrate the search functionality."""
    print_demo_header("DEMO 1: Searching for Items")

    print("1. Clicking 'Search for an Item' button...")
    page.click("button:has-text('Search for an Item')")
    time.sleep(1)

    print("2. Searching by Description for 'Apple'...")
    page.select_option("select[name='column']", "description")
    page.fill("input[name='item']", "Apple")
    wait_and_highlight(page, "input[name='item']", 0.5)

    print("3. Submitting search...")
    page.click("button:has-text('Search')")
    time.sleep(1.5)

    # Check if results are displayed
    if page.query_selector(".result-item, table"):
        print("   ✓ Search results displayed successfully")
    else:
        print("   ℹ No items found (database may be empty)")

    time.sleep(1)


def demo_add_item_functionality(page: Page) -> None:
    """Demonstrate adding a single item."""
    print_demo_header("DEMO 2: Adding a Single Item")

    print("1. Clicking 'Add an Item' button...")
    page.click("button:has-text('Add an Item')")
    time.sleep(1)

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

    time.sleep(1)

    print("3. Submitting the form...")
    page.click("button:has-text('Add Item')")
    time.sleep(1.5)

    # Check for success or error message
    if page.query_selector(".success, .alert-success"):
        print("   ✓ Item added successfully")
    elif page.query_selector(".error, .alert"):
        print("   ℹ Item may already exist or validation error occurred")
    else:
        print("   ✓ Form submitted")

    time.sleep(1)


def demo_csv_upload_functionality(page: Page) -> None:
    """Demonstrate CSV upload functionality."""
    print_demo_header("DEMO 3: Uploading CSV Data")

    print("1. Clicking 'Upload CSV' button...")
    page.click("button:has-text('Upload CSV'), button:has-text('Add CSV')")
    time.sleep(1)

    # Check if CSV upload form is available
    csv_input = page.query_selector("input[type='file'], input[name='csv-input']")
    if csv_input:
        print("2. CSV upload form is available")
        print("   Note: In a live demo, you would select a CSV file here")
        print("   The application accepts CSV files with inventory data")
        time.sleep(1.5)
    else:
        print("   ℹ CSV upload form not found on this page")

    time.sleep(1)


def demo_navigation(page: Page) -> None:
    """Demonstrate navigation between different views."""
    print_demo_header("DEMO 4: Navigating Between Views")

    print("1. Switching between Search, Add Item, and CSV Upload views...")

    views = [
        ("Search for an Item", "search view"),
        ("Add an Item", "add item view"),
    ]

    for button_text, view_name in views:
        button = page.query_selector(f"button:has-text('{button_text}')")
        if button:
            print(f"   - Switching to {view_name}...")
            page.click(f"button:has-text('{button_text}')")
            time.sleep(0.8)

    print("   ✓ Navigation demonstration complete")
    time.sleep(1)


def run_demo() -> None:
    """Run the complete inventory app demo."""
    print("\n" + "=" * 70)
    print("  INVENTORY APP - INTERACTIVE DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo will showcase the key features of the Inventory Management App:")
    print("  • Searching for items by various criteria")
    print("  • Adding individual items to the inventory")
    print("  • Uploading bulk data via CSV")
    print("  • Navigating between different views")
    print("\nStarting Flask application...\n")

    # Start Flask app in background
    flask_process = subprocess.Popen(
        [sys.executable, "manage.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**subprocess.os.environ, "DATABASE_URL": "sqlite:///demo.db", "APP_SETTINGS": "config.DevelopmentConfig"},
    )

    # Wait for Flask to start
    print("Waiting for Flask to initialize...")
    time.sleep(3)

    try:
        with sync_playwright() as p:
            print("Launching browser...\n")
            browser = p.chromium.launch(headless=False, slow_mo=500)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})

            # Navigate to the app
            print("Navigating to http://127.0.0.1:5000\n")
            page.goto("http://127.0.0.1:5000", wait_until="networkidle")
            time.sleep(1)

            # Run demo sections
            demo_search_functionality(page)
            demo_add_item_functionality(page)
            demo_csv_upload_functionality(page)
            demo_navigation(page)

            # Final summary
            print_demo_header("DEMO COMPLETE")
            print("The Inventory App demonstration has finished successfully!")
            print("\nKey Features Demonstrated:")
            print("  ✓ Item search with multiple criteria")
            print("  ✓ Single item addition with form validation")
            print("  ✓ CSV bulk upload capability")
            print("  ✓ Intuitive navigation between views")
            print("\nPress Enter to close the browser and exit...")
            input()

            browser.close()

    finally:
        # Clean up Flask process
        print("\nShutting down Flask application...")
        flask_process.terminate()
        flask_process.wait()
        print("Demo complete!\n")


if __name__ == "__main__":
    run_demo()
