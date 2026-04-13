"""
Variant — Product variant (size, color, SKU).
Pure Python entity.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Variant:
    """
    Represents a specific variant of a product.
    e.g. a T-shirt in size L / color Black with its own SKU and stock.
    """

    id: Optional[int] = None
    product_id: Optional[int] = None
    sku: str = ''
    size: str = ''
    color: str = ''
    price_override: Optional[Decimal] = None
    stock: int = 0

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.product_id:
            errors.append('Variant must belong to a product.')
        if self.stock < 0:
            errors.append('Variant stock must be >= 0.')
        if self.price_override is not None and self.price_override < Decimal('0'):
            errors.append('Price override must be >= 0.')
        return errors

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0
