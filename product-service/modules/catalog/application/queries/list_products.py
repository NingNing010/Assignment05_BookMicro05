"""
ListProducts query.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductsQuery:
    product_type: Optional[str] = None
