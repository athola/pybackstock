"""Flask pybackstock inventory management application."""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from werkzeug.middleware.proxy_fix import ProxyFix

if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from werkzeug.datastructures import FileStorage

# Get the root directory (project root, not src/pybackstock)
_root_dir = Path(__file__).parent.parent.parent
app = Flask(__name__, template_folder=str(_root_dir / "templates"))
app.config.from_object(os.environ.get("APP_SETTINGS", "src.pybackstock.config.DevelopmentConfig"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure app to trust Render.com's proxy headers (X-Forwarded-*)
# This is required for Flask-Talisman to correctly detect HTTPS behind Render's reverse proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,  # Trust X-Forwarded-For from 1 proxy
    x_proto=1,  # Trust X-Forwarded-Proto from 1 proxy (critical for HTTPS detection)
    x_host=1,  # Trust X-Forwarded-Host from 1 proxy
    x_prefix=1,  # Trust X-Forwarded-Prefix from 1 proxy
)

# Initialize security extensions
csrf = CSRFProtect(app)

# Configure Talisman for security headers
# Disable HTTPS enforcement in development and testing, enable in production
is_production = not app.config.get("DEBUG", False) and not app.config.get("TESTING", False)
talisman = Talisman(
    app,
    force_https=is_production,
    strict_transport_security=is_production,
    content_security_policy={
        "default-src": "'self'",
        "script-src": ["'self'", "'unsafe-inline'", "code.jquery.com", "netdna.bootstrapcdn.com"],
        "style-src": ["'self'", "'unsafe-inline'", "netdna.bootstrapcdn.com"],
    },
)

db = SQLAlchemy(app)

# Import models after db is created to avoid circular import
from src.pybackstock.models import Grocery  # noqa: E402


class FormAction:
    """Constants for form actions."""

    SEARCH_ITEM = "search-item"
    ADD_ITEM = "add-item"
    ADD_CSV = "add-csv"
    SEND_SEARCH = "send-search"
    SEND_ADD = "send-add"
    CSV_SUBMIT = "csv-submit"


def render_index_template(
    errors: list[str],
    items: list[Any],
    col: str,
    load_search: bool,
    load_add_item: bool,
    load_add_csv: bool,
    item_searched: bool,
    item_added: bool,
) -> str:
    """Render the index template with given parameters.

    Args:
        errors: List of error messages.
        items: List of items to display.
        col: Column name for search.
        load_search: Whether to load the search form.
        load_add_item: Whether to load the add item form.
        load_add_csv: Whether to load the CSV upload form.
        item_searched: Whether a search was performed.
        item_added: Whether an item was added.

    Returns:
        Rendered HTML template.
    """
    return render_template(
        "index.html",
        errors=errors,
        items=items,
        column=col,
        loading_search=load_search,
        loading_add_item=load_add_item,
        loading_add_csv=load_add_csv,
        item_searched=item_searched,
        item_added=item_added,
    )


def handle_search_action() -> tuple[list[str], list[Any], bool, bool]:
    """Handle search form submission.

    Returns:
        Tuple of (errors, items, item_searched, item_added).
    """
    errors: list[str] = []
    items: list[Any] = []
    try:
        col = request.form["column"]
        search_item = request.form["item"]
        matching_items = get_matching_items(col, search_item)
        items.extend(matching_items)
    except (KeyError, ValueError, TypeError) as ex:
        error_type = "Unable to search for item. Please double check your search parameters. "
        errors = report_exception(ex, error_type, errors)
    return errors, items, True, False


def handle_add_action() -> tuple[list[str], list[Any], bool, bool]:
    """Handle add item form submission.

    Returns:
        Tuple of (errors, items, item_searched, item_added).
    """
    errors: list[str] = []
    items: list[Any] = []
    try:
        item = set_item()
        errors, items = add_item(item, errors, items)
        item_added = True
    except (KeyError, ValueError, TypeError) as ex:
        error_type = "Unable to add item. Please double check your item parameters. "
        errors = report_exception(ex, error_type, errors)
        item_added = False
    return errors, items, False, item_added


def handle_csv_action() -> tuple[list[str], list[Any]]:
    """Handle CSV upload form submission.

    Returns:
        Tuple of (errors, items).
    """
    errors: list[str] = []
    items: list[Any] = []
    try:
        file: FileStorage | None = request.files.get("csv-input")
        if not file or not file.filename:
            errors.append("No file")
            return errors, items

        if "." not in file.filename:
            errors.append("Invalid file type. Needs to be .csv")
            return errors, items

        file_ext = file.filename.rsplit(".", 1)[1].lower()
        if file_ext == "csv":
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)
            iterate_through_csv(csv_input, errors, items)
        else:
            errors.append("Invalid file type. Needs to be .csv")
    except (KeyError, ValueError, TypeError, UnicodeDecodeError) as ex:
        error_type = "Unable to process CSV file. Please check the file format. "
        errors = report_exception(ex, error_type, errors)
    return errors, items


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    """Handle the main index page for inventory management.

    Returns:
        Rendered HTML template.
    """
    errors: list[str] = []
    items: list[Any] = []
    col = "ID"
    load_search = False
    load_add_item = True
    load_add_csv = False
    item_searched = False
    item_added = False

    if request.method == "POST":
        # Handle form view switching
        if FormAction.SEARCH_ITEM in request.form:
            load_search, load_add_item, load_add_csv = True, False, False
        elif FormAction.ADD_ITEM in request.form:
            load_search, load_add_item, load_add_csv = False, True, False
        elif FormAction.ADD_CSV in request.form:
            load_search, load_add_item, load_add_csv = False, False, True
        # Handle form submissions
        elif FormAction.SEND_SEARCH in request.form:
            load_search, load_add_item, load_add_csv = True, False, False
            errors, items, item_searched, item_added = handle_search_action()
        elif FormAction.SEND_ADD in request.form:
            load_search, load_add_item, load_add_csv = False, True, False
            errors, items, item_searched, item_added = handle_add_action()
        elif FormAction.CSV_SUBMIT in request.form:
            load_search, load_add_item, load_add_csv = False, False, True
            errors, items = handle_csv_action()

    return render_index_template(
        errors, items, col, load_search, load_add_item, load_add_csv, item_searched, item_added
    )


def report_exception(ex: Exception, error_type: str, errors: list[str]) -> list[str]:
    """Report an exception by adding it to the errors list.

    Args:
        ex: The exception that occurred.
        error_type: Description of the error type.
        errors: Current list of errors.

    Returns:
        Updated list of errors.
    """
    # Log detailed error information server-side for debugging
    exc_tb = sys.exc_info()[-1]
    tb_lineno: int | str = exc_tb.tb_lineno if exc_tb is not None else "unknown"
    detailed_error = f"{error_type}{ex!s} - Error on line no: {tb_lineno}"
    print(detailed_error)  # noqa: T201

    # Show generic error message to user (don't expose internal details)
    errors.append(error_type.strip())
    return errors


def get_matching_items(search_column: str, search_item: str) -> Query[Any] | dict[str, Any]:
    """Get items matching the search criteria.

    Args:
        search_column: Column to search in.
        search_item: Value to search for.

    Returns:
        Query result with matching items or empty dict.

    Note:
        SQLAlchemy ORM provides SQL injection protection through parameterized queries.
        No manual SQL injection checks are needed.
    """
    # Handle exact integer searches for id and x_for columns
    if search_column in ("id", "x_for"):
        if not search_item.isdigit():
            return {}
        column = Grocery.id if search_column == "id" else Grocery.x_for
        return Grocery.query.filter(column == int(search_item))  # type: ignore[no-any-return]

    # Build search term based on input
    if "*" in search_item or "_" in search_item:
        search_term = search_item.replace("_", "__").replace("*", "%").replace("?", "_")
    elif search_item and search_item[-1] == "s":
        search_term = f"%{search_item[:-1]}%"
    else:
        search_term = f"%{search_item}%"

    # Build and return query
    if search_column == "last_sold":
        query = Grocery.query.filter(func.to_char(Grocery.last_sold, "%YYYY-MM-DD%").ilike(search_term))
    else:
        query = Grocery.query.filter(getattr(Grocery, search_column).ilike(search_term))

    return query.order_by(Grocery.id)  # type: ignore[no-any-return]


def set_item() -> Grocery:
    """Create a Grocery item from form data.

    Returns:
        New Grocery instance.
    """
    item_id = int(request.form["id-add"])
    description = request.form["description-add"]
    last_sold = request.form["last-sold-add"]
    shelf_life = request.form["shelf-life-add"]
    department = request.form["department-add"]
    price = request.form["price-add"]
    unit = request.form["unit-add"]
    x_for = int(request.form["xfor-add"])
    cost = request.form["cost-add"]
    return Grocery(
        item_id=item_id,
        description=description,
        last_sold=last_sold,
        shelf_life=shelf_life,
        department=department,
        price=price,
        unit=unit,
        x_for=x_for,
        cost=cost,
    )


def add_item(item: Grocery, errors: list[str], items: list[Any]) -> tuple[list[str], list[Any]]:
    """Add a grocery item to the database.

    Args:
        item: Grocery item to add.
        errors: Current list of errors.
        items: Current list of items.

    Returns:
        Tuple of (errors, items).
    """
    try:
        # SQLAlchemy 2.0 compatible exists check
        item_exists = db.session.query(Grocery).filter(Grocery.id == item.id).first() is not None
        if not item_exists:
            db.session.add(item)
            db.session.commit()
            json_obj = json.dumps(dict(item))
            items.append(json_obj)
        else:
            errors.append(f"Unable to add item to database. This item has already been added with ID: {item.id}")
    except (ValueError, TypeError) as ex:
        db.session.rollback()
        errors.append(f"Unable to add item to database. {ex!s}")
    return errors, items


def iterate_through_csv(csv_input: Any, errors: list[str], items: list[Any]) -> None:
    """Process CSV input and add items to database.

    Args:
        csv_input: CSV reader object.
        errors: Current list of errors.
        items: Current list of items.
    """
    row: list[str]
    for idx, row in enumerate(csv_input):
        if idx != 0:  # Skip header row
            csv_item_to_add = Grocery(
                item_id=int(row[0]),
                description=row[1],
                last_sold=row[2],
                shelf_life=row[3],
                department=row[4],
                price=row[5],
                unit=row[6],
                x_for=int(row[7]),
                cost=row[8],
            )
            add_item(csv_item_to_add, errors, items)
