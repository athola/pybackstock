"""Random grocery item generator using the grocery corpus.

This module provides functionality to generate randomized grocery item data
from a curated corpus of common grocery items with realistic pricing.

Note: This module uses the standard random module for test data generation.
The S311 warnings are suppressed as cryptographic randomness is not required.

This module returns dictionaries of item data rather than Grocery model instances
to avoid circular import issues. Callers should create Grocery instances from
the returned data as needed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from src.pybackstock.grocery_corpus import GROCERY_CORPUS, GroceryItemTemplate


@dataclass
class RandomItemConfig:
    """Configuration for random item generation.

    Attributes:
        quantity_min: Minimum quantity in stock.
        quantity_max: Maximum quantity in stock.
        reorder_point_min: Minimum reorder point.
        reorder_point_max: Maximum reorder point.
        last_sold_days_back: Maximum days in the past for last_sold date.
        last_sold_null_probability: Probability (0-1) that last_sold is None.
        x_for_weights: Weights for x_for values (1, 2, 3, 4).
        date_added_days_back: Maximum days in the past for date_added.
    """

    quantity_min: int = 0
    quantity_max: int = 100
    reorder_point_min: int = 5
    reorder_point_max: int = 25
    last_sold_days_back: int = 30
    last_sold_null_probability: float = 0.2
    x_for_weights: tuple[float, ...] = (0.85, 0.10, 0.04, 0.01)  # 1, 2, 3, 4
    date_added_days_back: int = 90


# Default configuration
DEFAULT_CONFIG = RandomItemConfig()


def generate_random_price(template: GroceryItemTemplate) -> str:
    """Generate a random price within the template's price range.

    Args:
        template: The grocery item template with price bounds.

    Returns:
        Formatted price string (e.g., "3.49").
    """
    price = random.uniform(template.price_min, template.price_max)  # noqa: S311
    return f"{price:.2f}"


def generate_random_cost(price_str: str, template: GroceryItemTemplate) -> str:
    """Generate a random cost based on the price and cost ratio.

    Args:
        price_str: The price as a string.
        template: The grocery item template with cost ratio bounds.

    Returns:
        Formatted cost string (e.g., "1.99").
    """
    price = float(price_str)
    cost_ratio = random.uniform(template.cost_ratio_min, template.cost_ratio_max)  # noqa: S311
    cost = price * cost_ratio
    return f"{cost:.2f}"


def generate_random_last_sold(config: RandomItemConfig = DEFAULT_CONFIG) -> date | None:
    """Generate a random last_sold date or None.

    Args:
        config: Configuration for random generation.

    Returns:
        A date within the configured range, or None.
    """
    if random.random() < config.last_sold_null_probability:  # noqa: S311
        return None

    days_back = random.randint(0, config.last_sold_days_back)  # noqa: S311
    return datetime.now(UTC).date() - timedelta(days=days_back)


def generate_random_quantity(config: RandomItemConfig = DEFAULT_CONFIG) -> int:
    """Generate a random quantity in stock.

    Args:
        config: Configuration for random generation.

    Returns:
        Random quantity between configured bounds.
    """
    return random.randint(config.quantity_min, config.quantity_max)  # noqa: S311


def generate_random_reorder_point(config: RandomItemConfig = DEFAULT_CONFIG) -> int:
    """Generate a random reorder point.

    Args:
        config: Configuration for random generation.

    Returns:
        Random reorder point between configured bounds.
    """
    return random.randint(config.reorder_point_min, config.reorder_point_max)  # noqa: S311


def generate_random_x_for(config: RandomItemConfig = DEFAULT_CONFIG) -> int:
    """Generate a random x_for value (for bulk pricing).

    Args:
        config: Configuration for random generation.

    Returns:
        Random x_for value (1, 2, 3, or 4) based on configured weights.
    """
    return random.choices([1, 2, 3, 4], weights=config.x_for_weights, k=1)[0]  # noqa: S311


def generate_random_date_added(config: RandomItemConfig = DEFAULT_CONFIG) -> date:
    """Generate a random date_added within the configured range.

    Args:
        config: Configuration for random generation.

    Returns:
        A date within the configured range.
    """
    days_back = random.randint(0, config.date_added_days_back)  # noqa: S311
    return datetime.now(UTC).date() - timedelta(days=days_back)


def generate_random_item_data(
    item_id: int,
    config: RandomItemConfig = DEFAULT_CONFIG,
    template: GroceryItemTemplate | None = None,
) -> dict[str, Any]:
    """Generate random item data from a corpus template.

    Args:
        item_id: The unique ID for the generated item.
        config: Configuration for random generation.
        template: Optional specific template to use. If None, randomly selected.

    Returns:
        Dictionary with all fields needed to create a Grocery item.
    """
    if template is None:
        template = random.choice(GROCERY_CORPUS)  # noqa: S311

    price = generate_random_price(template)
    cost = generate_random_cost(price, template)
    last_sold = generate_random_last_sold(config)

    return {
        "item_id": item_id,
        "description": template.description,
        "last_sold": last_sold,
        "shelf_life": template.shelf_life,
        "department": template.department,
        "price": price,
        "unit": template.unit,
        "x_for": generate_random_x_for(config),
        "cost": cost,
        "quantity": generate_random_quantity(config),
        "reorder_point": generate_random_reorder_point(config),
        "date_added": generate_random_date_added(config),
    }


def generate_multiple_random_item_data(
    starting_id: int,
    count: int,
    config: RandomItemConfig = DEFAULT_CONFIG,
    *,
    allow_duplicates: bool = False,
) -> list[dict[str, Any]]:
    """Generate multiple random item data dictionaries.

    Args:
        starting_id: The ID for the first item.
        count: Number of items to generate.
        config: Configuration for random generation.
        allow_duplicates: If False, each item will be unique from the corpus.

    Returns:
        List of dictionaries with item data.

    Raises:
        ValueError: If count > corpus size and allow_duplicates is False.
    """
    if not allow_duplicates and count > len(GROCERY_CORPUS):
        msg = f"Cannot generate {count} unique items from corpus of {len(GROCERY_CORPUS)} items"
        raise ValueError(msg)

    if allow_duplicates:
        templates = [random.choice(GROCERY_CORPUS) for _ in range(count)]  # noqa: S311
    else:
        templates = random.sample(GROCERY_CORPUS, count)

    return [generate_random_item_data(starting_id + i, config, template) for i, template in enumerate(templates)]


def get_corpus_by_department(department: str) -> list[GroceryItemTemplate]:
    """Get all corpus items for a specific department.

    Args:
        department: The department name to filter by.

    Returns:
        List of templates matching the department.
    """
    return [item for item in GROCERY_CORPUS if item.department == department]


def get_available_departments() -> list[str]:
    """Get a list of all departments in the corpus.

    Returns:
        Sorted list of unique department names.
    """
    return sorted({item.department for item in GROCERY_CORPUS})


def generate_random_item_data_from_department(
    item_id: int,
    department: str,
    config: RandomItemConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Generate random item data from a specific department.

    Args:
        item_id: The unique ID for the generated item.
        department: The department to select from.
        config: Configuration for random generation.

    Returns:
        Dictionary with all fields needed to create a Grocery item.

    Raises:
        ValueError: If the department doesn't exist in the corpus.
    """
    dept_items = get_corpus_by_department(department)
    if not dept_items:
        available = ", ".join(get_available_departments())
        msg = f"Department '{department}' not found. Available: {available}"
        raise ValueError(msg)

    template = random.choice(dept_items)  # noqa: S311
    return generate_random_item_data(item_id, config, template)
