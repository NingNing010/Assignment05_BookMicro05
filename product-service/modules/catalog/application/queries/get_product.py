"""
GetProduct query.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class GetProductQuery:
    product_id: int
