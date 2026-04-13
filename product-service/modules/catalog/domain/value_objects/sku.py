"""
SKU — Value Object for stock-keeping unit codes.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import uuid


@dataclass(frozen=True)
class SKU:
    value: str

    def __post_init__(self):
        if self.value and not re.match(r'^[A-Za-z0-9\-_]+$', self.value):
            raise ValueError(f'Invalid SKU format: {self.value}')

    @classmethod
    def generate(cls, prefix: str = 'PRD') -> SKU:
        short_id = uuid.uuid4().hex[:8].upper()
        return cls(value=f'{prefix}-{short_id}')

    def __str__(self) -> str:
        return self.value
