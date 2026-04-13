"""
CreateVariant command.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class CreateVariantCommand:
    product_id: int
    sku: str = ''
    size: str = ''
    color: str = ''
    price_override: Optional[Decimal] = None
    stock: int = 0
