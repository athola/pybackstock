"""API handlers for Connexion OpenAPI endpoints."""

from __future__ import annotations

import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any

from flask import Response, current_app, make_response, render_template, request

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
)

logger = logging.getLogger(__name__)


def health_check() -> tuple[dict[str, str], int]:
    """Health check endpoint for monitoring and deployment platforms.

    Returns:
        JSON response with status and HTTP 200 code.
    """
    return {"status": "healthy"}, 200


def diagnostic_check() -> tuple[dict[str, Any], int]:
    """Diagnostic endpoint to check system status and configuration.

    Returns:
        JSON response with diagnostic information.
    """
    diagnostics: dict[str, Any] = {
        "status": "ok",
        "checks": {},
    }

    # Check database connection
    try:
        Grocery.query.count()
        diagnostics["checks"]["database"] = {"status": "ok", "message": "Database connection successful"}
    except (OSError, RuntimeError, ValueError, AttributeError) as ex:
        diagnostics["checks"]["database"] = {"status": "error", "message": f"Database error: {ex!s}"}
        diagnostics["status"] = "degraded"

    # Check template folder
    try:
        template_folder = current_app.template_folder
        if template_folder and Path(template_folder).exists():
            report_template = Path(template_folder) / "report.html"
            if report_template.exists():
                diagnostics["checks"]["templates"] = {
                    "status": "ok",
                    "template_folder": str(template_folder),
                    "report_template_exists": True,
                }
            else:
                diagnostics["checks"]["templates"] = {
                    "status": "error",
                    "template_folder": str(template_folder),
                    "report_template_exists": False,
                    "message": "report.html not found",
                }
                diagnostics["status"] = "degraded"
        else:
            diagnostics["checks"]["templates"] = {
                "status": "error",
                "template_folder": str(template_folder) if template_folder else None,
                "message": "Template folder not found or not set",
            }
            diagnostics["status"] = "degraded"
    except (OSError, RuntimeError, ValueError, AttributeError) as ex:
        diagnostics["checks"]["templates"] = {"status": "error", "message": f"Template check failed: {ex!s}"}
        diagnostics["status"] = "degraded"

    # Check app configuration
    diagnostics["checks"]["config"] = {
        "status": "ok",
        "app_settings": os.environ.get("APP_SETTINGS", "not set"),
        "debug_mode": current_app.config.get("DEBUG", False),
        "testing_mode": current_app.config.get("TESTING", False),
    }

    # Check calculation functions
    try:
        test_items: list[Any] = []
        calculate_summary_metrics(test_items)
        diagnostics["checks"]["calculations"] = {"status": "ok", "message": "Calculation functions working"}
    except (ValueError, TypeError, AttributeError, KeyError) as ex:
        diagnostics["checks"]["calculations"] = {
            "status": "error",
            "message": f"Calculation functions failed: {ex!s}",
        }
        diagnostics["status"] = "degraded"

    return diagnostics, 200 if diagnostics["status"] == "ok" else 500


def index_get() -> str:
    """Handle GET requests to the index page.

    Returns:
        Rendered HTML template.
    """
    errors: list[str] = []
    items: list[Any] = []
    return render_template(
        "index.html",
        errors=errors,
        items=items,
        column="ID",
        loading_search=False,
        loading_add_item=True,
        loading_add_csv=False,
        item_searched=False,
        item_added=False,
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


def report_get() -> Response | tuple[dict[str, Any], int]:
    """Generate and display inventory analytics report.

    Returns:
        Flask Response object with rendered HTML template or error dict with status code.
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

        # Query all items from database
        # No need for app_context() - Connexion already provides Flask app context
        try:
            all_items = Grocery.query.all()
        except Exception as db_ex:
            logger.exception("Database query failed in report generation")
            return {
                "type": "database_error",
                "title": "Database Error",
                "detail": f"Failed to query inventory database: {db_ex!s}",
                "status": 500,
            }, 500

        # Always calculate summary metrics (shown in summary cards)
        try:
            summary_data = calculate_summary_metrics(all_items)
        except Exception as calc_ex:
            logger.exception("Failed to calculate summary metrics")
            return {
                "type": "calculation_error",
                "title": "Calculation Error",
                "detail": f"Failed to calculate summary metrics: {calc_ex!s}",
                "status": 500,
            }, 500

        # Calculate data for selected visualizations
        try:
            viz_data = _calculate_visualizations(selected_viz, all_items)
        except Exception as viz_ex:
            logger.exception("Failed to calculate visualization data")
            return {
                "type": "visualization_error",
                "title": "Visualization Error",
                "detail": f"Failed to calculate visualization data: {viz_ex!s}",
                "status": 500,
            }, 500

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

        # Render template and explicitly set content type for Connexion
        try:
            html_content = render_template("report.html", **template_data)
        except Exception as template_ex:
            logger.exception("Template rendering failed")
            return {
                "type": "template_error",
                "title": "Template Rendering Error",
                "detail": f"Failed to render report template: {template_ex!s}",
                "status": 500,
            }, 500

        response = make_response(html_content, 200)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response  # noqa: TRY300
    except Exception as ex:
        # Catch-all for any unexpected errors
        exc_tb = sys.exc_info()[-1]
        tb_lineno: int | str = exc_tb.tb_lineno if exc_tb is not None else "unknown"
        error_msg = f"Unexpected error in report generation at line {tb_lineno}: {ex!s}"
        logger.exception(error_msg)
        return {
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": error_msg,
            "status": 500,
            "traceback": traceback.format_exc(),
        }, 500


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

        # Query all items from database
        # No need for app_context() - Connexion already provides Flask app context
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
