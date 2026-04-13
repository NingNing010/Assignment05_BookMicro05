"""
FilterProducts query.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class FilterProductsQuery:
    category_id: Optional[int] = None
    product_type: Optional[str] = None
    keyword: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
