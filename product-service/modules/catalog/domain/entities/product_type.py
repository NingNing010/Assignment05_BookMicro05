"""
ProductType — Domain entity distinguishing product kinds (Book, Clothes, …).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductType:
    """
    Lookup entity.  Examples: 'Book', 'Clothes', 'Electronics'.
    Controls which JSON attributes are expected in Product.attributes.
    """

    id: Optional[int] = None
    name: str = ''
    description: str = ''

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name or not self.name.strip():
            errors.append('ProductType name is required.')
        return errors
