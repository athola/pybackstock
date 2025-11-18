"""Database models for the pybackstock application."""

from collections.abc import Iterator
from datetime import date, datetime, timezone
from typing import Any

from src.pybackstock.database import db


class Grocery(db.Model):  # type: ignore[name-defined]
    """Grocery item model representing items in the inventory."""

    __tablename__ = "grocery_items"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(60), nullable=False)
    last_sold = db.Column(db.Date)
    shelf_life = db.Column(db.String(5), nullable=False)
    department = db.Column(db.String(40))
    price = db.Column(db.String(20), nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    x_for = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_point = db.Column(db.Integer, nullable=False, default=10)
    date_added = db.Column(db.Date, nullable=False, default=date.today)

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
        quantity: int = 0,
        reorder_point: int = 10,
        date_added: date | str | None = None,
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
            quantity: Current quantity in stock (default: 0).
            reorder_point: Minimum quantity before reordering (default: 10).
            date_added: Date when item was added to inventory (default: today).
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
        self.quantity = int(quantity)
        self.reorder_point = int(reorder_point)
        # Handle date_added
        if date_added is None:
            self.date_added = datetime.now(tz=timezone.utc).date()  # noqa: UP017
        elif isinstance(date_added, str):
            try:
                self.date_added = datetime.strptime(date_added, "%Y-%m-%d").date()
            except (ValueError, AttributeError):
                self.date_added = datetime.now(tz=timezone.utc).date()  # noqa: UP017
        else:
            self.date_added = date_added

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
        yield "quantity", self.quantity
        yield "reorder_point", self.reorder_point
        yield "date_added", str(self.date_added) if self.date_added else None
