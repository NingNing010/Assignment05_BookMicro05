"""
Product — Core domain entity.
Pure Python, no framework dependency.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
import json


@dataclass
class Product:
    """
    Represents a single saleable product in the catalog.
    Product type (Book, Clothes, …) is determined by its ProductType reference.
    Category-specific attributes (author, isbn, size, color, …) live in the
    ``attributes`` dict which is persisted as JSON.
    """

    id: Optional[int] = None
    name: str = ''
    product_type_id: Optional[int] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    image_url: str = ''
    price: Decimal = Decimal('0.00')
    stock: int = 0
    description: str = ''
    attributes: dict = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # ── Business rules ──────────────────────────

    def validate(self) -> list[str]:
        """Return a list of validation error messages (empty = valid)."""
        errors: list[str] = []
        if not self.name or not self.name.strip():
            errors.append('Product name is required.')
        if self.price < Decimal('0'):
            errors.append('Price must be >= 0.')
        if self.stock < 0:
            errors.append('Stock must be >= 0.')
        return errors

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0

    def decrease_stock(self, quantity: int) -> None:
        if quantity > self.stock:
            raise ValueError(f'Cannot decrease stock by {quantity}; only {self.stock} available.')
        self.stock -= quantity

    def increase_stock(self, quantity: int) -> None:
        if quantity < 0:
            raise ValueError('Quantity must be positive.')
        self.stock += quantity

    def get_attribute(self, key: str, default=None):
        return self.attributes.get(key, default)

    def set_attribute(self, key: str, value) -> None:
        self.attributes[key] = value

    def attributes_json(self) -> str:
        return json.dumps(self.attributes, ensure_ascii=False)
