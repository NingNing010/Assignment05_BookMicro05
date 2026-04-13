"""
ProductRepository — Abstract interface (port) for Product persistence.
Infrastructure layer provides the concrete adapter.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from modules.catalog.domain.entities.product import Product


class ProductRepository(ABC):

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]:
        ...

    @abstractmethod
    def list_all(self, product_type: Optional[str] = None) -> list[Product]:
        ...

    @abstractmethod
    def filter_by_category(self, category_id: int) -> list[Product]:
        ...

    @abstractmethod
    def save(self, product: Product) -> Product:
        ...

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        ...

    @abstractmethod
    def search(self, keyword: str) -> list[Product]:
        ...
