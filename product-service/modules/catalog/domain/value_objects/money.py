"""
Money — Value Object representing a monetary amount.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = 'VND'

    def __post_init__(self):
        if self.amount < Decimal('0'):
            raise ValueError('Money amount must be >= 0.')

    @classmethod
    def from_raw(cls, raw_value, currency: str = 'VND') -> Money:
        try:
            return cls(amount=Decimal(str(raw_value)), currency=currency)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f'Invalid money value: {raw_value}') from exc

    def __str__(self) -> str:
        return f'{self.amount} {self.currency}'
