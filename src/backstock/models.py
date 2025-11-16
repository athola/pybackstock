"""Database models for the backstock application."""

from collections.abc import Iterator
from datetime import date, datetime
from typing import Any

from src.backstock.app import db


class Grocery(db.Model):  # type: ignore[name-defined]
    """Grocery item model representing items in the inventory."""

    __tablename__ = "grocery_items"

    id = db.Column(db.Integer, primary_key=True)  # type: ignore[has-type]
    description = db.Column(db.String(60), nullable=False)  # type: ignore[has-type]
    last_sold = db.Column(db.Date)  # type: ignore[has-type]
    shelf_life = db.Column(db.String(5), nullable=False)  # type: ignore[has-type]
    department = db.Column(db.String(40))  # type: ignore[has-type]
    price = db.Column(db.String(20), nullable=False)  # type: ignore[has-type]
    unit = db.Column(db.String(10), nullable=False)  # type: ignore[has-type]
    x_for = db.Column(db.Integer, nullable=False)  # type: ignore[has-type]
    cost = db.Column(db.String(20), nullable=False)  # type: ignore[has-type]

    def __init__(  # noqa: PLR0913
        self,
        item_id: int,
        description: str,
        last_sold: date | str | None,
        shelf_life: str,
        department: str | None,
        price: str,
        unit: str,
        x_for: int,
        cost: str,
    ) -> None:
        """Initialize a Grocery item.

        Args:
            item_id: Unique identifier for the grocery item.
            description: Description of the grocery item.
            last_sold: Date when the item was last sold (can be date object or string).
            shelf_life: Expected shelf life of the item.
            department: Department where the item is located.
            price: Price of the item.
            unit: Unit of measurement.
            x_for: Quantity for pricing (e.g., 2 for $5).
            cost: Cost of the item.
        """
        self.id = int(item_id)
        self.description = description
        # Convert string dates to date objects
        if isinstance(last_sold, str):
            try:
                self.last_sold = datetime.strptime(last_sold, "%Y-%m-%d").date()
            except (ValueError, AttributeError):
                self.last_sold = None
        else:
            self.last_sold = last_sold
        self.shelf_life = shelf_life
        self.department = department
        self.price = price
        self.unit = unit
        self.x_for = int(x_for)
        self.cost = cost

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        """Make the model iterable for JSON serialization.

        Yields:
            Tuples of (field_name, field_value) for each model field.
        """
        yield "id", self.id
        yield "description", self.description
        yield "last_sold", str(self.last_sold) if self.last_sold else None
        yield "shelf_life", self.shelf_life
        yield "department", self.department
        yield "price", self.price
        yield "unit", self.unit
        yield "x_for", self.x_for
        yield "cost", self.cost
