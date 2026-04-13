"""
Category — Domain entity representing a product category tree.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """
    Category is **data**, not a service.
    Supports a simple parent→child tree via parent_id.
    """

    id: Optional[int] = None
    name: str = ''
    description: str = ''
    parent_id: Optional[int] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name or not self.name.strip():
            errors.append('Category name is required.')
        return errors

    @property
    def is_root(self) -> bool:
        return self.parent_id is None
