"""API handlers for Connexion OpenAPI endpoints."""

from __future__ import annotations

import sys
import traceback
from typing import Any

from flask import render_template, request

from src.pybackstock.app import (
    FormAction,
    Grocery,
    calculate_age_data,
    calculate_department_data,
    calculate_price_range_data,
    calculate_reorder_data,
    calculate_shelf_life_data,
    calculate_stock_health_data,
    calculate_summary_metrics,
    calculate_top_price_data,
    calculate_top_value_data,
    handle_add_action,
    handle_csv_action,
    handle_search_action,
    render_index_template,
)
from src.pybackstock.connexion_app import flask_app


def health_check() -> tuple[dict[str, str], int]:
    """Health check endpoint for monitoring and deployment platforms.

    Returns:
        JSON response with status and HTTP 200 code.
    """
    return {"status": "healthy"}, 200


def index_get() -> str:
    """Handle GET requests to the index page.

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

    return render_index_template(
        errors, items, col, load_search, load_add_item, load_add_csv, item_searched, item_added
    )


def index_post() -> str:
    """Handle POST requests to the index page.

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


def _calculate_visualizations(selected_viz: list[str], all_items: list[Any]) -> dict[str, Any]:
    """Calculate data for selected visualizations.

    Args:
        selected_viz: List of visualization names to calculate.
        all_items: List of all grocery items from database.

    Returns:
        Dictionary containing calculated visualization data.
    """
    # Map visualization names to their calculation functions
    viz_calculators = {
        "stock_health": calculate_stock_health_data,
        "department": calculate_department_data,
        "age": calculate_age_data,
        "price_range": calculate_price_range_data,
        "shelf_life": calculate_shelf_life_data,
        "top_value": calculate_top_value_data,
        "top_price": calculate_top_price_data,
        "reorder_table": calculate_reorder_data,
    }

    viz_data: dict[str, Any] = {}
    for viz_name in selected_viz:
        if viz_name in viz_calculators:
            viz_data.update(viz_calculators[viz_name](all_items))

    return viz_data


def report_get() -> str:
    """Generate and display inventory analytics report.

    Returns:
        Rendered HTML template.
    """
    try:
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

        # Query all items from database - must be within app context
        with flask_app.app_context():
            all_items = Grocery.query.all()

            # Always calculate summary metrics (shown in summary cards)
            summary_data = calculate_summary_metrics(all_items)

            # Calculate data for selected visualizations
            viz_data = _calculate_visualizations(selected_viz, all_items)

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
    except Exception as ex:
        # Log detailed error for debugging
        exc_tb = sys.exc_info()[-1]
        tb_lineno: int | str = exc_tb.tb_lineno if exc_tb is not None else "unknown"
        error_msg = f"Report generation error: {ex!s} at line {tb_lineno}"
        print(error_msg)  # noqa: T201
        print(traceback.format_exc())  # noqa: T201
        raise


def report_data_get() -> tuple[dict[str, Any], int]:
    """Get report data as JSON for debugging.

    Returns:
        JSON response with report data or error details.
    """
    try:
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

        # Query all items from database - must be within app context
        with flask_app.app_context():
            all_items = Grocery.query.all()

            # Always calculate summary metrics
            summary_data = calculate_summary_metrics(all_items)

            # Calculate data for selected visualizations
            viz_data = _calculate_visualizations(selected_viz, all_items)

            # Merge all data
            response_data = {
                **summary_data,
                **viz_data,
                "selected_viz": selected_viz,
                "item_count": len(all_items),
            }

            # Provide empty defaults
            response_data.setdefault("stock_levels", {})
            response_data.setdefault("dept_counts", {})
            response_data.setdefault("age_distribution", {})
            response_data.setdefault("price_ranges", {})
            response_data.setdefault("shelf_life_counts", {})
            response_data.setdefault("top_value_items", [])
            response_data.setdefault("top_items", [])
            response_data.setdefault("reorder_items", [])
    except (AttributeError, ValueError, KeyError, TypeError) as ex:
        # Return detailed error information
        exc_tb = sys.exc_info()[-1]
        tb_lineno: int | str = exc_tb.tb_lineno if exc_tb is not None else "unknown"

        error_response = {
            "error": str(type(ex).__name__),
            "detail": str(ex),
            "line": tb_lineno,
            "traceback": traceback.format_exc(),
        }
        return error_response, 500
    else:
        return response_data, 200
