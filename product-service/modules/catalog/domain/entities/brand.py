"""
Brand — Domain entity.
Replaces both the old Publisher (for books) and Brand (for clothes).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Brand:
    id: Optional[int] = None
    name: str = ''
    address: str = ''
    email: str = ''
    description: str = ''

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name or not self.name.strip():
            errors.append('Brand name is required.')
        return errors
