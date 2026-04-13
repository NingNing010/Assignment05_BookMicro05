"""
CreateProduct command — data-transfer object for product creation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class CreateProductCommand:
    name: str
    price: Decimal
    product_type_id: Optional[int] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    image_url: str = ''
    stock: int = 0
    description: str = ''
    attributes: dict = field(default_factory=dict)
