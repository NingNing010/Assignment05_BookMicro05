"""
UpdateProduct command.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class UpdateProductCommand:
    id: int
    name: Optional[str] = None
    price: Optional[Decimal] = None
    product_type_id: Optional[int] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    description: Optional[str] = None
    attributes: Optional[dict] = None
