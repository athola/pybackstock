"""Flask pybackstock inventory management application."""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from werkzeug.middleware.proxy_fix import ProxyFix

# Constants for analytics calculations
PRICE_RANGE_BOUNDARIES = (5, 10, 20, 50)
AGE_RANGE_BOUNDARIES = (30, 60, 90)
CSV_OLD_FORMAT_COLUMNS = 9
CSV_QUANTITY_COLUMN = 9
CSV_REORDER_COLUMN = 10
CSV_DATE_COLUMN = 11

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
app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
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
        "script-src": ["'self'", "'unsafe-inline'", "code.jquery.com", "netdna.bootstrapcdn.com", "cdn.jsdelivr.net"],
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


@app.route("/health", methods=["GET"])
@csrf.exempt
@talisman(force_https=False)
def health_check() -> tuple[dict[str, str], int]:
    """Health check endpoint for monitoring and deployment platforms.

    This endpoint is used by Render.com and other platforms to verify
    the service is running and responsive. It must:
    - Return 200 status code
    - Be exempt from CSRF protection (monitoring systems don't send tokens)
    - Be exempt from HTTPS forcing (health checks may come over HTTP internally)
    - Respond quickly without database dependencies

    Returns:
        JSON response with status and HTTP 200 code.
    """
    return {"status": "healthy"}, 200


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


def calculate_summary_metrics(items: list[Grocery]) -> dict[str, Any]:
    """Calculate summary metrics for all inventory items.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing summary metrics.
    """
    total_items = len(items)
    prices: list[float] = []
    costs: list[float] = []
    quantities: list[int] = []

    for item in items:
        try:
            price_val = float(item.price.replace("$", "").replace(",", ""))
            cost_val = float(item.cost.replace("$", "").replace(",", ""))
            prices.append(price_val)
            costs.append(cost_val)
            quantities.append(item.quantity)
        except (ValueError, AttributeError):
            pass

    total_inventory_value = sum(p * q for p, q in zip(prices, quantities, strict=True))
    total_inventory_cost = sum(c * q for c, q in zip(costs, quantities, strict=True))
    total_profit_margin = (
        ((total_inventory_value - total_inventory_cost) / total_inventory_cost * 100) if total_inventory_cost > 0 else 0
    )
    total_quantity = sum(quantities)

    # Recent activity - items sold in last 30 days
    recent_threshold = datetime.now(tz=timezone.utc).date() - timedelta(days=30)  # noqa: UP017
    recent_sales = sum(1 for item in items if item.last_sold and item.last_sold >= recent_threshold)

    # Stock level counts
    low_stock_items = [item for item in items if item.quantity <= item.reorder_point]
    out_of_stock_items = [item for item in items if item.quantity == 0]

    return {
        "total_items": total_items,
        "total_value": total_inventory_value,
        "total_cost": total_inventory_cost,
        "total_profit_margin": total_profit_margin,
        "total_quantity": total_quantity,
        "recent_sales": recent_sales,
        "low_stock_count": len(low_stock_items),
        "out_of_stock_count": len(out_of_stock_items),
    }


def calculate_stock_health_data(items: list[Grocery]) -> dict[str, Any]:
    """Calculate stock health visualization data.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing stock level distribution.
    """
    low_stock_items = [item for item in items if item.quantity <= item.reorder_point]
    out_of_stock_items = [item for item in items if item.quantity == 0]
    healthy_stock_items = [item for item in items if item.quantity > item.reorder_point]

    stock_levels = {
        "Out of Stock": len(out_of_stock_items),
        "Low Stock": len(low_stock_items) - len(out_of_stock_items),
        "Healthy Stock": len(healthy_stock_items),
    }

    return {"stock_levels": stock_levels}


def calculate_department_data(items: list[Grocery]) -> dict[str, Any]:
    """Calculate department distribution visualization data.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing department counts.
    """
    dept_counts: dict[str, int] = {}
    for item in items:
        dept = item.department if item.department else "Uncategorized"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    return {"dept_counts": dept_counts}


def calculate_age_data(items: list[Grocery]) -> dict[str, Any]:
    """Calculate inventory age distribution visualization data.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing age distribution.
    """
    today = datetime.now(tz=timezone.utc).date()  # noqa: UP017
    age_distribution = {"0-30 days": 0, "31-60 days": 0, "61-90 days": 0, "90+ days": 0}

    for item in items:
        if item.date_added:
            age_days = (today - item.date_added).days
            if age_days <= AGE_RANGE_BOUNDARIES[0]:
                age_distribution["0-30 days"] += 1
            elif age_days <= AGE_RANGE_BOUNDARIES[1]:
                age_distribution["31-60 days"] += 1
            elif age_days <= AGE_RANGE_BOUNDARIES[2]:
                age_distribution["61-90 days"] += 1
            else:
                age_distribution["90+ days"] += 1

    return {"age_distribution": age_distribution}


def calculate_price_range_data(items: list[Grocery]) -> dict[str, Any]:
    """Calculate price range distribution visualization data.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing price range counts.
    """
    price_ranges = {"$0-$5": 0, "$5-$10": 0, "$10-$20": 0, "$20-$50": 0, "$50+": 0}
    prices: list[float] = []

    for item in items:
        try:
            price_val = float(item.price.replace("$", "").replace(",", ""))
            prices.append(price_val)
        except (ValueError, AttributeError):
            pass

    for price in prices:
        if price < PRICE_RANGE_BOUNDARIES[0]:
            price_ranges["$0-$5"] += 1
        elif price < PRICE_RANGE_BOUNDARIES[1]:
            price_ranges["$5-$10"] += 1
        elif price < PRICE_RANGE_BOUNDARIES[2]:
            price_ranges["$10-$20"] += 1
        elif price < PRICE_RANGE_BOUNDARIES[3]:
            price_ranges["$20-$50"] += 1
        else:
            price_ranges["$50+"] += 1

    return {"price_ranges": price_ranges}


def calculate_shelf_life_data(items: list[Grocery]) -> dict[str, Any]:
    """Calculate shelf life distribution visualization data.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing shelf life counts.
    """
    shelf_life_counts: dict[str, int] = {}
    for item in items:
        shelf = item.shelf_life if item.shelf_life else "Unknown"
        shelf_life_counts[shelf] = shelf_life_counts.get(shelf, 0) + 1

    return {"shelf_life_counts": shelf_life_counts}


def calculate_top_value_data(items: list[Grocery]) -> dict[str, Any]:
    """Calculate top 10 items by total value visualization data.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing top value items.
    """
    items_by_value = []
    for item in items:
        try:
            price_val = float(item.price.replace("$", "").replace(",", ""))
            total_val = price_val * item.quantity
            items_by_value.append({"description": item.description, "value": total_val})
        except (ValueError, AttributeError):
            pass

    items_by_value.sort(key=lambda x: x["value"], reverse=True)
    top_value_items = items_by_value[:10]

    return {"top_value_items": top_value_items}


def calculate_top_price_data(items: list[Grocery]) -> dict[str, Any]:
    """Calculate top 10 most expensive items visualization data.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing top priced items.
    """
    items_with_prices = [
        {"description": item.description, "price": float(item.price.replace("$", "").replace(",", ""))}
        for item in items
        if item.price
    ]
    items_with_prices.sort(key=lambda x: x["price"], reverse=True)
    top_items = items_with_prices[:10]

    return {"top_items": top_items}


def calculate_reorder_data(items: list[Grocery]) -> dict[str, Any]:
    """Calculate items needing reorder visualization data.

    Args:
        items: List of all grocery items.

    Returns:
        Dictionary containing items needing reorder.
    """
    low_stock_items = [item for item in items if item.quantity <= item.reorder_point]

    reorder_items = [
        {
            "description": item.description,
            "quantity": item.quantity,
            "reorder_point": item.reorder_point,
            "department": item.department or "Uncategorized",
        }
        for item in low_stock_items
        if item.quantity > 0  # Exclude out of stock for this list
    ]
    reorder_items.sort(key=lambda x: x["quantity"])
    reorder_items = reorder_items[:10]  # Top 10 items needing reorder

    return {"reorder_items": reorder_items}


@app.route("/report", methods=["GET"])
def report() -> str:
    """Generate and display inventory analytics report.

    Only calculates data for selected visualizations to optimize performance.

    Returns:
        Rendered HTML template with report data.
    """
    # Get selected visualizations from query parameters
    selected_viz = request.args.getlist("viz")
    # If no visualizations selected, show all by default
    if not selected_viz:
        selected_viz = [
            "stock_health",
            "department",
            "age",
            "price_range",
            "shelf_life",
            "top_value",
            "top_price",
            "reorder_table",
        ]

    # Query all items from database
    all_items = Grocery.query.all()

    # Always calculate summary metrics (shown in summary cards)
    summary_data = calculate_summary_metrics(all_items)

    # Initialize visualization data dictionary
    viz_data: dict[str, Any] = {}

    # Only calculate data for selected visualizations
    if "stock_health" in selected_viz:
        viz_data.update(calculate_stock_health_data(all_items))

    if "department" in selected_viz:
        viz_data.update(calculate_department_data(all_items))

    if "age" in selected_viz:
        viz_data.update(calculate_age_data(all_items))

    if "price_range" in selected_viz:
        viz_data.update(calculate_price_range_data(all_items))

    if "shelf_life" in selected_viz:
        viz_data.update(calculate_shelf_life_data(all_items))

    if "top_value" in selected_viz:
        viz_data.update(calculate_top_value_data(all_items))

    if "top_price" in selected_viz:
        viz_data.update(calculate_top_price_data(all_items))

    if "reorder_table" in selected_viz:
        viz_data.update(calculate_reorder_data(all_items))

    # Merge summary data and visualization data
    template_data = {**summary_data, **viz_data, "selected_viz": selected_viz}

    # Provide empty defaults for visualizations that weren't selected
    # This prevents template errors if a visualization references missing data
    template_data.setdefault("stock_levels", {})
    template_data.setdefault("dept_counts", {})
    template_data.setdefault("age_distribution", {})
    template_data.setdefault("price_ranges", {})
    template_data.setdefault("shelf_life_counts", {})
    template_data.setdefault("top_value_items", [])
    template_data.setdefault("top_items", [])
    template_data.setdefault("reorder_items", [])

    return render_template("report.html", **template_data)


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
    # Handle exact integer searches for id, x_for, quantity, and reorder_point columns
    if search_column in ("id", "x_for", "quantity", "reorder_point"):
        if not search_item.isdigit():
            return {}
        column_map = {
            "id": Grocery.id,
            "x_for": Grocery.x_for,
            "quantity": Grocery.quantity,
            "reorder_point": Grocery.reorder_point,
        }
        column = column_map[search_column]
        return Grocery.query.filter(column == int(search_item))  # type: ignore[no-any-return]

    # Build search term based on input
    if "*" in search_item or "_" in search_item:
        search_term = search_item.replace("_", "__").replace("*", "%").replace("?", "_")
    elif search_item and search_item[-1] == "s":
        search_term = f"%{search_item[:-1]}%"
    else:
        search_term = f"%{search_item}%"

    # Build and return query
    if search_column in ("last_sold", "date_added"):
        date_column = Grocery.last_sold if search_column == "last_sold" else Grocery.date_added
        query = Grocery.query.filter(func.to_char(date_column, "%YYYY-MM-DD%").ilike(search_term))
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
    quantity = int(request.form.get("quantity-add", 0))
    reorder_point = int(request.form.get("reorder-point-add", 10))
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
        quantity=quantity,
        reorder_point=reorder_point,
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
            # Support both old format (9 columns) and new format (12 columns)
            quantity = int(row[CSV_QUANTITY_COLUMN]) if len(row) > CSV_OLD_FORMAT_COLUMNS else 0
            reorder_point = int(row[CSV_REORDER_COLUMN]) if len(row) > CSV_REORDER_COLUMN else 10
            date_added = row[CSV_DATE_COLUMN] if len(row) > CSV_DATE_COLUMN else None

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
                quantity=quantity,
                reorder_point=reorder_point,
                date_added=date_added,
            )
            add_item(csv_item_to_add, errors, items)
